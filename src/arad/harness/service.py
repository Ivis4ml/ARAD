"""连续研究服务（M6 第三块）：让循环真的不停。

此前每次 `run_episode` 都排干一个固定队列就结束，下一版从哪来没有答案 ——
演示里是一张写死的变体表，跑完即止。真正的连续研究要求下一版由**变异**产生，
而变异的方向由**盲化的语义诊断**给出，不是由结果给出。

三层停止语义（Merge-Plan-2 §6）在这里各归其位：

- **Search Episode 可以结束**：预算耗尽、无可运行任务，都只结束一个 Episode；
- **Study 必须形成判决**：每一轮无论走到哪一步都留下一个 verdict；
- **Research Service 只能由人停**。因此本函数的停止条件全部是**外部给定的边界**
  （轮数上限、调用预算）或**停滞**，而不是"觉得够了"。停滞会写进账本并请求人工复核，
  因为"该不该继续找"是人的判断，不是系统的。

停滞的判据刻意只用**与结果无关**的量：连续 k 轮没有产生新的 content id。
用"判决没有改善"当停滞判据就是在用结果决定搜索何时停止，那是另一种选择偏差。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from ..memory.ledger import EvidenceLedger
from ..orchestrator.queue import DurableQueue
from ..providers.base import EpisodeBudget, ProviderRequest, ProviderResponse, Role
from .episode import run_episode
from .mutate import next_proposal

SERVICE_VERSION = "0.2.0"

#: 基础设施失败，不是"问不出新东西"。这一轮压根没走到提案，把它记进停滞计数，
#: 一个 schema 缺陷就会被读成模型枯竭 —— 与此前按 `proposal_id` 计新颖性
#: 是同一类归因错误。实测：真实模型三次都把 direction 写成词，
#: 若按停滞算，三轮之后服务就会写下 human_review_required 说它没新想法了。
#: 判据是「这一轮有没有形成过提案」，不是「失败得像不像工程问题」：
#: 这四种结局都在 `record_proposal` 之前返回，既不进提案分母也没有内容身份，
#: 因此它们对"还有没有新问题可问"不构成任何证据。
INFRASTRUCTURE_OUTCOMES = frozenset({
    "parse_failure", "provider_error", "context_blocked", "invalid_proposal",
})


@dataclass
class AutoProposer:
    """离线执行者替身：按变异器产出下一版提案。

    它**看不到任何效应量** —— 输入只有步数与上一轮的语义错配码。因此它跑出来的链
    是"搜索过程本身"的形状，而这正是零假设带要度量的东西。
    """

    target_name: str
    model_id: str = "deterministic_mutator"
    step_index: int = 0
    mismatch_codes: tuple[str, ...] = ()
    calls: list[str] = field(default_factory=list)

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        payload, plan = next_proposal(
            step_index=self.step_index,
            mismatch_codes=self.mismatch_codes,
            target_name=self.target_name,
            parent=self.step_index or None,
        )
        self.calls.append(plan.reason_code)
        self.step_index += 1
        return ProviderResponse(
            request_id=request.request_id, role=Role.PROPOSER,
            raw_text=payload, model_id=self.model_id,
        )


@dataclass
class ServiceResult:
    episodes: list[dict] = field(default_factory=list)
    stopped_because: str = ""
    rounds: int = 0
    distinct_features: int = 0
    #: 基础设施失败的轮数。与 distinct_features 分开报，因为它们意思相反：
    #: 一个说"问出了几个互异的问题"，一个说"有几轮根本没问成"。
    infrastructure_failures: int = 0

    def summary(self) -> dict:
        return {
            "service_version": SERVICE_VERSION,
            "episodes": len(self.episodes),
            "rounds": self.rounds,
            "distinct_features": self.distinct_features,
            "infrastructure_failures": self.infrastructure_failures,
            "stopped_because": self.stopped_because,
        }


def run_service(
    *,
    ledger: EvidenceLedger,
    queue: DurableQueue,
    provider: Any,
    family: str,
    owner: str,
    assemble: Any,
    build_evaluation: Any,
    audit_input: Any,
    seed_task: dict,
    contamination: Any = None,
    max_rounds: int = 40,
    calls_per_episode: int = 6,
    stall_rounds: int = 3,
    now: datetime | None = None,
) -> ServiceResult:
    """一轮接一轮地跑，直到到达外部边界或停滞。

    每一轮结束后由**上一轮的语义错配**决定下一版怎么变 —— 这是环真正闭上的地方：
    诊断是盲化的，因此这条反馈通路不构成在检验统计量上爬山。
    """
    result = ServiceResult()
    current = now or datetime.now(UTC)
    parent: str | None = None
    seen: set[str] = set()
    learned: tuple[str, ...] = ()
    stale = 0
    broken = 0
    index = 0

    while result.rounds < max_rounds:
        task_id = f"auto-task-{index}"
        study_id = f"auto-study-{index}"
        # 累积的错配码走**任务载荷**，不走 provider 属性。原实现是
        # `if hasattr(provider, "mismatch_codes")`，而那个属性只有确定性变异器有，
        # `ClaudeCliProvider` 没有 —— 于是诊断对真实模型被静默丢弃，实跑 8 轮里
        # 最后三轮连续撞在同一个 magnitude_vs_signed_label 上。载荷这条路对任何
        # provider 都成立，因为它最终进的是提示词。
        queue.enqueue(task_id, "study",
                      {**seed_task, "study_id": study_id, "parent_study_id": parent,
                       "learned_mismatches": list(learned)},
                      now=current)
        episode = run_episode(
            episode_id=f"auto-episode-{index}",
            queue=queue, ledger=ledger, provider=provider,
            budget=EpisodeBudget(max_calls=calls_per_episode),
            family=family, owner=owner, assemble=assemble,
            build_evaluation=build_evaluation, audit_input=audit_input,
            contamination=contamination, max_rounds=1, now=current,
        )
        result.episodes.append(episode.summary())
        result.rounds += len(episode.rounds)
        if not episode.rounds:
            result.stopped_because = "no_runnable_work"
            break

        outcome = episode.rounds[-1]
        if outcome.outcome in INFRASTRUCTURE_OUTCOMES:
            # 这一轮没走到提案，它对"还有没有新问题可问"不构成任何证据。
            # 既不清零 stale 也不累加，只单独计数：连续失败由 broken_rounds 判停。
            result.infrastructure_failures += 1
            broken += 1
            if broken >= stall_rounds:
                result.stopped_because = "provider_unusable"
                break
        else:
            broken = 0
            # 停滞判据只看内容身份，不看判决好坏：用「判决没改善」当停止条件，
            # 就是在用结果决定搜索何时停，那是另一种选择偏差
            novelty = outcome.feature_id or outcome.proposal_id
            if novelty and novelty not in seen:
                seen.add(novelty)
                stale = 0
            else:
                stale += 1
        if outcome.study_id:
            parent = outcome.study_id

        # 诊断累积，不是只看上一轮：一旦「幅度对方向」被指出来，之后就不该再退回
        # 幅度特征。只取上一轮的码会让链在两种机制之间来回震荡（实测 A/B/A/B）。
        codes = tuple(outcome.detail.get("codes", ())) if outcome.detail else ()
        learned = tuple(dict.fromkeys(learned + codes))
        if hasattr(provider, "mismatch_codes"):
            provider.mismatch_codes = learned

        if stale >= stall_rounds:
            result.stopped_because = "stalled"
            break
        index += 1
        current = current + timedelta(seconds=1)
    else:
        result.stopped_because = "max_rounds"

    result.distinct_features = len(seen)
    ledger.append("service_stopped", result.summary())
    # 两种停法都要人看，但它们要人做的判断不是一回事：一个问「还值不值得继续找」，
    # 一个说「执行者根本没产出可解析的东西」。混成一句话就会把工程缺陷读成研究结论。
    if result.stopped_because == "stalled":
        # 「该不该继续找」是人的判断，系统只负责如实报告它已经问不出新东西
        ledger.append("human_review_required", {
            "reason": "连续多轮没有产生新的提案内容；是否继续搜索由人决定",
            "distinct_features": result.distinct_features,
            "rounds": result.rounds,
        })
    elif result.stopped_because == "provider_unusable":
        ledger.append("human_review_required", {
            "reason": "连续多轮未能取得可解析的提案；这是执行通道的故障，"
                      "不构成关于该机制族的任何研究结论",
            "infrastructure_failures": result.infrastructure_failures,
            "rounds": result.rounds,
        })
    return result


def describe(result: ServiceResult) -> str:
    return json.dumps(result.summary(), ensure_ascii=False, indent=2)
