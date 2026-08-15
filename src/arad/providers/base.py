"""模型无关的 provider 接口与输出合同（M4 第二块）。

领域层不依赖任何 SDK 类型：这里只有 dataclass 与 pydantic 模型，
换 provider 只需换一个适配器实现。

三条边界在这里成为结构：

1. **角色隔离即进程隔离。**`ProviderRequest` 刻意**没有**会话 id、没有历史消息列表。
   每次调用都是独立上下文。proposer 与 interpreter 共享会话就等于盲化失效，
   而这里根本无法表达"共享"。
2. **盲化发生在 prompt 组装时。**`assert_blinded()` 在调用**之前**扫描 prompt，
   proposer 角色的 prompt 出现任何效果字段名即拒绝发送。查询层遮蔽不够 ——
   prompt 是模型真正看到的东西。
3. **Episode 预算是一等公民。**每次调用扣减预算，耗尽即结束 Episode，
   把剩余预算交回 Program。Service 不停（Merge-Plan-2 §6）。

坏 JSON 不丢任务：解析失败按合同重试，重试用尽后降级为结构化的 `ParseFailure`，
它是证据而非异常 —— 提案器反复产出坏 JSON 本身就是关于该提示词的研究信息。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from ..registry.specs import EFFECT_FIELD_PREFIXES, EFFECT_FIELDS, content_id

PROVIDER_VERSION = "0.1.0"


class Role(str, Enum):
    """调用角色。每个角色一次独立调用，上下文不共享。"""

    PROPOSER = "proposer"
    WORKER = "worker"
    INTERPRETER = "interpreter"
    RED_TEAM = "red_team"
    SEMANTIC_AUDITOR = "semantic_auditor"


#: 只能看到盲化视图的角色。它们的 prompt 不得出现任何效果字段。
BLINDED_ROLES = frozenset({Role.PROPOSER, Role.SEMANTIC_AUDITOR})


class ContextLeak(RuntimeError):
    """盲化角色的 prompt 里出现了效果字段。调用被拒绝，不会发送。"""


class EpisodeBudgetExhausted(RuntimeError):
    """Search Episode 的调用预算耗尽。结束 Episode，不是结束 Service。"""


class ProviderError(RuntimeError):
    """provider 调用本身失败（超时、非零退出、空输出）。任务不丢，交由队列重排。"""


def assert_blinded(prompt: str, role: Role) -> None:
    """盲化角色的 prompt 不得出现任何效果字段名。调用前检查。"""
    if role not in BLINDED_ROLES:
        return
    lowered = prompt.lower()
    hits = sorted(
        name for name in EFFECT_FIELDS if re.search(rf"\b{re.escape(name)}\b", lowered)
    )
    prefixes = "|".join(re.escape(p.rstrip("_")) for p in EFFECT_FIELD_PREFIXES)
    hits += sorted({m.group(0) for m in re.finditer(rf"\b(?:{prefixes})_[a-z0-9_]+", lowered)})
    if hits:
        raise ContextLeak(
            f"角色 {role.value!r} 的 prompt 出现效果字段 {hits}；"
            "盲化角色只能看到覆盖率、功效与失败分类。调用已拒绝，未发送"
        )


@dataclass
class EpisodeBudget:
    """一次 Search Episode 的调用预算。耗尽即结束 Episode，剩余交回 Program。"""

    max_calls: int
    calls_spent: int = 0
    output_tokens_spent: int = 0

    def remaining_calls(self) -> int:
        return max(0, self.max_calls - self.calls_spent)

    def exhausted(self) -> bool:
        return self.remaining_calls() <= 0

    def spend(self, output_tokens: int = 0) -> None:
        if self.exhausted():
            raise EpisodeBudgetExhausted(
                f"Episode 调用预算 {self.max_calls} 已耗尽；结束 Episode 并交回剩余预算。"
                "Research Service 不因此停止"
            )
        self.calls_spent += 1
        self.output_tokens_spent += output_tokens

    def describe(self) -> dict:
        return {
            "max_calls": self.max_calls,
            "calls_spent": self.calls_spent,
            "calls_remaining": self.remaining_calls(),
            "output_tokens_spent": self.output_tokens_spent,
        }


@dataclass(frozen=True)
class ProviderRequest:
    """一次调用。**没有会话 id、没有历史消息** —— 上下文不可跨角色携带。

    `system_prompt` 是模型能看到的第二段文本（方法说明与输出契约）。它必须是本对象的
    字段，而不是 provider 的命令行参数或工作目录里的某个文件：盲化检查扫的是本对象，
    `request_id` 内容寻址的也是本对象。凡是绕过这两者进入模型上下文的通道，
    审计上等于不存在 —— 这正是 M16 记下的那类缺陷，只是更彻底（内容根本到不了闸门）。
    """

    role: Role
    prompt: str
    schema_name: str
    max_output_tokens: int = 8000
    system_prompt: str = ""

    @property
    def request_id(self) -> str:
        return content_id(
            {
                "role": self.role.value,
                "prompt": self.prompt,
                "system_prompt": self.system_prompt,
                "schema_name": self.schema_name,
                "provider_version": PROVIDER_VERSION,
            }
        )


@dataclass(frozen=True)
class ProviderResponse:
    """一次调用的原始产出。解析在合同层做，不在 provider 里。"""

    request_id: str
    role: Role
    raw_text: str
    model_id: str
    output_tokens: int = 0
    attempt: int = 1
    meta: dict = field(default_factory=dict)


class ParseFailure(BaseModel):
    """解析失败的结构化记录。这是证据，不是异常。

    只记 `last_error` 是不够的：一次真实失败耗了八分钟三次调用，事后只能看到
    第三次错在 `direction`，前两次错在哪已经无从查起。因此逐次都记，
    并记下原始输出的**长度** —— 截断与格式错误在 500 字的摘录里长得一样。
    """

    request_id: str
    role: str
    schema_name: str
    attempts: int
    last_error: str
    #: 逐次尝试的错误，按尝试顺序。长度等于 attempts。
    attempt_errors: list[str] = []
    raw_excerpt: str
    #: 最后一次原始输出的完整字符数。摘录截在 500 字，靠它才能判断是不是被截断。
    raw_length: int = 0


class Provider(Protocol):
    """模型无关的 provider。实现只需一个方法。"""

    model_id: str

    def invoke(self, request: ProviderRequest) -> ProviderResponse: ...


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> Any:
    """从模型输出里取出 JSON。容忍围栏代码块与前后说明文字。"""
    candidates = [m.group(1) for m in _JSON_BLOCK.finditer(text)]
    candidates.append(text)
    for chunk in candidates:
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            start = min(
                (i for i in (chunk.find("{"), chunk.find("[")) if i >= 0), default=-1
            )
            end = max(chunk.rfind("}"), chunk.rfind("]"))
            if start >= 0 and end > start:
                try:
                    return json.loads(chunk[start : end + 1])
                except json.JSONDecodeError:
                    continue
    raise ValueError("输出中找不到可解析的 JSON")


REPAIR_INSTRUCTION = (
    "\n\n上一次输出无法解析为要求的结构：{error}\n"
    "请只输出符合 schema 的 JSON，不要有任何其他文字。"
)


def invoke_structured(
    provider: Provider,
    request: ProviderRequest,
    model: type[BaseModel],
    *,
    budget: EpisodeBudget,
    max_attempts: int = 3,
) -> tuple[BaseModel | None, ParseFailure | None, list[ProviderResponse]]:
    """调用并解析为结构化输出。

    返回 (解析结果, 解析失败记录, 全部原始响应)。解析失败不抛异常 ——
    它降级为 `ParseFailure` 记入证据，任务由队列按退避重排，不丢。
    盲化检查在**每次**发送前执行，包括修复重试。
    """
    responses: list[ProviderResponse] = []
    prompt = request.prompt
    last_error = ""
    attempt_errors: list[str] = []
    for attempt in range(1, max_attempts + 1):
        attempt_request = ProviderRequest(
            role=request.role,
            prompt=prompt,
            schema_name=request.schema_name,
            max_output_tokens=request.max_output_tokens,
            system_prompt=request.system_prompt,
        )
        # 两段文本都要过闸门。修复重试只改 prompt，system_prompt 逐次不变，
        # 但仍每次检查：漏检一次的代价是一次不可撤回的泄漏。
        assert_blinded(attempt_request.prompt, attempt_request.role)
        assert_blinded(attempt_request.system_prompt, attempt_request.role)
        budget.spend()
        response = provider.invoke(attempt_request)
        responses.append(response)
        try:
            payload = extract_json(response.raw_text)
            return model.model_validate(payload), None, responses
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)[:400]
            attempt_errors.append(last_error)
            prompt = request.prompt + REPAIR_INSTRUCTION.format(error=last_error)
    return (
        None,
        ParseFailure(
            request_id=request.request_id,
            role=request.role.value,
            schema_name=request.schema_name,
            attempts=max_attempts,
            last_error=last_error,
            attempt_errors=attempt_errors,
            raw_excerpt=responses[-1].raw_text[:500] if responses else "",
            raw_length=len(responses[-1].raw_text) if responses else 0,
        ),
        responses,
    )
