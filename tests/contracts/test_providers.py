"""provider 适配层与输出合同的合同测试（M4 第二块）。

三条边界：角色隔离即进程隔离、盲化发生在发送之前、预算耗尽结束 Episode 而非服务。
"""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from arad.providers.base import (
    BLINDED_ROLES,
    ContextLeak,
    EpisodeBudget,
    EpisodeBudgetExhausted,
    ProviderError,
    ProviderRequest,
    Role,
    assert_blinded,
    extract_json,
    invoke_structured,
)
from arad.providers.claude_cli import ClaudeCliProvider
from arad.providers.mock import MockProvider


class Answer(BaseModel):
    mechanism: str
    confidence: int


def a_request(role=Role.PROPOSER, prompt="请提出一个机制") -> ProviderRequest:
    return ProviderRequest(role=role, prompt=prompt, schema_name="Answer")


def ok_json() -> str:
    return json.dumps({"mechanism": "闭市地缘概率创新", "confidence": 3})


# ---------------------------------------------------------------- 角色隔离


def test_request_cannot_carry_a_session_or_history():
    """上下文不可跨角色携带：请求对象里根本没有会话与历史字段。"""
    fields = set(ProviderRequest.__dataclass_fields__)
    assert fields == {"role", "prompt", "schema_name", "max_output_tokens"}
    for forbidden in ("session_id", "conversation_id", "history", "messages", "thread"):
        assert forbidden not in fields


def test_each_invocation_is_independent(monkeypatch):
    provider = MockProvider(scripts={"proposer": [ok_json()]})
    budget = EpisodeBudget(max_calls=5)
    invoke_structured(provider, a_request(), Answer, budget=budget)
    invoke_structured(provider, a_request(), Answer, budget=budget)
    # 两次调用的 prompt 完全一样，provider 侧没有任何跨调用状态
    assert provider.calls[0].prompt == provider.calls[1].prompt
    assert provider.calls[0].request_id == provider.calls[1].request_id


def test_claude_cli_starts_a_fresh_process_per_call():
    """进程边界就是上下文边界。"""
    provider = ClaudeCliProvider(dry_run=True)
    r1 = provider.invoke(a_request(prompt="A"))
    r2 = provider.invoke(a_request(prompt="B"))
    assert r1.meta["command"] == r2.meta["command"]
    assert r1.request_id != r2.request_id  # prompt 不同即不同请求，无共享状态


# ---------------------------------------------------------------- 盲化


@pytest.mark.parametrize("leak", ["beta", "t_stat", "p_value", "sharpe", "ic"])
def test_effect_fields_in_a_proposer_prompt_are_rejected_before_sending(leak):
    with pytest.raises(ContextLeak, match="效果字段"):
        assert_blinded(f"上一轮的 {leak} 是 0.42，请据此提案", Role.PROPOSER)


def test_blinding_applies_to_every_blinded_role():
    assert Role.PROPOSER in BLINDED_ROLES
    for role in BLINDED_ROLES:
        with pytest.raises(ContextLeak):
            assert_blinded("beta = 0.1", role)


def test_interpreter_may_see_effects():
    """解释器的职责就是解释结果，它不受盲化约束。"""
    assert_blinded("beta = 0.1, t_stat = 3.4", Role.INTERPRETER)


def test_blinding_does_not_fire_on_substrings():
    """`alphabet` 不是 `alpha`；盲化不能靠子串匹配制造假警报。"""
    assert_blinded("请覆盖 alphabetical 顺序与 returns_to_scale 这类词", Role.PROPOSER)


def test_a_leaking_prompt_is_never_sent(monkeypatch):
    provider = MockProvider(scripts={"proposer": [ok_json()]})
    with pytest.raises(ContextLeak):
        invoke_structured(
            provider, a_request(prompt="beta 是 0.42"), Answer,
            budget=EpisodeBudget(max_calls=5),
        )
    assert provider.calls == []  # 一次都没发出去


def test_repair_retries_are_blinded_too():
    """修复重试也要过盲化检查，不能因为是重试就绕过。"""
    provider = MockProvider(scripts={"proposer": ["不是 JSON", "还是不是 JSON", "仍然不是"]})
    budget = EpisodeBudget(max_calls=5)
    parsed, failure, _ = invoke_structured(
        provider, a_request(), Answer, budget=budget, max_attempts=3
    )
    assert parsed is None and failure is not None
    for call in provider.calls:
        assert_blinded(call.prompt, call.role)  # 全部重试 prompt 都是盲化的


# ---------------------------------------------------------------- 预算


def test_budget_ends_the_episode_not_the_service():
    provider = MockProvider(scripts={"proposer": [ok_json()]})
    budget = EpisodeBudget(max_calls=2)
    invoke_structured(provider, a_request(), Answer, budget=budget)
    invoke_structured(provider, a_request(), Answer, budget=budget)
    assert budget.exhausted()
    with pytest.raises(EpisodeBudgetExhausted, match="Research Service 不因此停止"):
        invoke_structured(provider, a_request(), Answer, budget=budget)


def test_budget_counts_repair_attempts():
    """坏 JSON 的重试同样烧预算，否则预算不是真的上限。"""
    provider = MockProvider(scripts={"proposer": ["坏的"]})
    budget = EpisodeBudget(max_calls=10)
    invoke_structured(provider, a_request(), Answer, budget=budget, max_attempts=3)
    assert budget.calls_spent == 3


def test_budget_describe_reports_remaining():
    budget = EpisodeBudget(max_calls=3)
    budget.spend(output_tokens=100)
    d = budget.describe()
    assert d["calls_spent"] == 1 and d["calls_remaining"] == 2
    assert d["output_tokens_spent"] == 100


# ---------------------------------------------------------------- 输出合同


def test_parses_plain_json():
    parsed, failure, _ = invoke_structured(
        MockProvider(scripts={"proposer": [ok_json()]}), a_request(), Answer,
        budget=EpisodeBudget(max_calls=3),
    )
    assert failure is None
    assert parsed.mechanism == "闭市地缘概率创新"


def test_parses_json_inside_a_fenced_block_with_commentary():
    text = f"我的思路如下。\n\n```json\n{ok_json()}\n```\n\n希望有帮助。"
    parsed, failure, _ = invoke_structured(
        MockProvider(scripts={"proposer": [text]}), a_request(), Answer,
        budget=EpisodeBudget(max_calls=3),
    )
    assert failure is None and parsed.confidence == 3


def test_bad_json_degrades_to_structured_evidence_not_an_exception():
    """坏 JSON 是关于该提示词的研究信息，不是崩溃。"""
    provider = MockProvider(scripts={"proposer": ["完全不是 JSON"]})
    parsed, failure, responses = invoke_structured(
        provider, a_request(), Answer, budget=EpisodeBudget(max_calls=9), max_attempts=3
    )
    assert parsed is None
    assert failure.attempts == 3
    assert failure.role == "proposer"
    assert failure.last_error
    assert failure.raw_excerpt
    assert len(responses) == 3


def test_schema_violation_also_degrades():
    """能解析成 JSON 但不符合 schema，同样降级而不是抛出。"""
    provider = MockProvider(scripts={"proposer": ['{"mechanism": "x"}']})
    parsed, failure, _ = invoke_structured(
        provider, a_request(), Answer, budget=EpisodeBudget(max_calls=9), max_attempts=2
    )
    assert parsed is None and failure.attempts == 2


def test_a_later_attempt_can_succeed():
    provider = MockProvider(scripts={"proposer": ["坏的", ok_json()]})
    parsed, failure, responses = invoke_structured(
        provider, a_request(), Answer, budget=EpisodeBudget(max_calls=9), max_attempts=3
    )
    assert failure is None and parsed is not None
    assert len(responses) == 2  # 成功即停，不浪费预算


def test_repair_prompt_states_the_actual_error():
    provider = MockProvider(scripts={"proposer": ["坏的", ok_json()]})
    invoke_structured(
        provider, a_request(), Answer, budget=EpisodeBudget(max_calls=9), max_attempts=3
    )
    assert "无法解析" in provider.calls[1].prompt


@pytest.mark.parametrize(
    "text", ["", "   ", "这里没有任何括号", "{不是合法 JSON"]
)
def test_extract_json_raises_on_unparseable_text(text):
    with pytest.raises(ValueError, match="找不到可解析的 JSON"):
        extract_json(text)


# ---------------------------------------------------------------- provider 故障


def test_provider_failure_propagates_for_the_queue_to_requeue():
    """provider 故障不在这里吞掉：由队列按退避重排，任务不丢。"""
    provider = MockProvider(scripts={"proposer": [ok_json()]}, fail_on_call={1})
    with pytest.raises(ProviderError):
        invoke_structured(
            provider, a_request(), Answer, budget=EpisodeBudget(max_calls=3)
        )


def test_claude_cli_reports_a_missing_executable_instead_of_crashing():
    provider = ClaudeCliProvider(executable="definitely-not-installed-xyz")
    assert provider.available() is False
    with pytest.raises(ProviderError, match="找不到可执行文件"):
        provider.invoke(a_request())


def test_claude_cli_dry_run_shows_the_command_without_calling_anything():
    provider = ClaudeCliProvider(dry_run=True, model_id="claude-opus-5")
    response = provider.invoke(a_request(prompt="hello"))
    assert response.meta["dry_run"] is True
    assert response.meta["command"][0] == "claude"
    assert "-p" in response.meta["command"]
    assert response.meta["prompt_chars"] == len("hello")


def test_prompt_goes_through_stdin_not_the_command_line():
    """prompt 不进命令行：避免长度限制，也避免出现在进程列表里。"""
    provider = ClaudeCliProvider(dry_run=True)
    command = provider.command()
    assert not any("请提出" in part for part in command)
    assert len(command) <= 3
