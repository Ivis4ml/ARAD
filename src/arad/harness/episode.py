"""Search Episode 驱动（M4 第五块）—— 闭环。

一次 Episode = 一段有调用预算上限的循环。预算耗尽即结束 Episode 并把剩余预算
交回 Program；**Research Service 不因此停止**（Merge-Plan-2 §6）。

每一轮都走同一条路：
    认领任务 → 组装盲化上下文（入账）→ 调用模型 → 解析
    → **无论结果如何都计入 proposal denominator**
    → 冻结两把锁 → 求特征 → 评价 → 判决入账 → 反馈

三种非正常产出都不是失败，而是被记录的证据：
坏 JSON 降级为 `ParseFailure`、原语缺口降级为 `UnsupportedMechanism`、
特征恒定或覆盖不足由评价机拒绝。它们都进分母，因为它们都是这一轮真实发生的提案。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from ..evaluation.kernel import evaluate
from ..features.interpreter import SourceNotImplemented
from ..features.spec import FeatureSpec, UnsupportedMechanism
from ..memory.ledger import EvidenceLedger
from ..orchestrator.queue import DurableQueue
from ..providers.base import (
    EpisodeBudget,
    EpisodeBudgetExhausted,
    Provider,
    ProviderError,
    ProviderRequest,
    Role,
    invoke_structured,
)
from ..registry.specs import (
    ConfirmatoryLock,
    HypothesisLock,
    NextAction,
    ProposalSpec,
    StudySpec,
    StudyVerdict,
    Verdict,
)
from .context import ContextBundle, record_context
from .feedback import Feedback, format_feedback

EPISODE_VERSION = "0.1.0"


class ProposalOutput(BaseModel):
    """提案器的结构化产出。要么是一个完整提案，要么是一条原语缺口声明。"""

    mechanism: str | None = None
    source: str | None = None
    target: str | None = None
    horizon: str | None = None
    universe: str | None = None
    direction: int | None = None
    falsifiable_condition: str | None = None
    rationale: str = ""
    feature_spec: FeatureSpec | None = None
    unsupported_mechanism: UnsupportedMechanism | None = None

    def is_gap(self) -> bool:
        return self.unsupported_mechanism is not None

    def to_proposal(self) -> ProposalSpec:
        return ProposalSpec(
            mechanism=self.mechanism or "",
            source=self.source or "",
            target=self.target or "",
            horizon=self.horizon or "",
            universe=self.universe or "",
            direction=self.direction if self.direction is not None else 0,
            falsifiable_condition=self.falsifiable_condition or "",
            proposed_by="llm_proposer",
            rationale=self.rationale,
        )


@dataclass
class RoundOutcome:
    """一轮的结局。全部字段都进账本。"""

    task_id: str
    outcome: str
    proposal_id: str | None = None
    study_id: str | None = None
    verdict: str | None = None
    feedback: Feedback | None = None
    detail: dict = field(default_factory=dict)


@dataclass
class EpisodeResult:
    episode_id: str
    rounds: list[RoundOutcome] = field(default_factory=list)
    ended_because: str = ""
    budget: dict = field(default_factory=dict)

    def summary(self) -> dict:
        counts: dict[str, int] = {}
        for r in self.rounds:
            counts[r.outcome] = counts.get(r.outcome, 0) + 1
        return {
            "episode_id": self.episode_id,
            "rounds": len(self.rounds),
            "outcomes": counts,
            "ended_because": self.ended_because,
            "budget": self.budget,
            "episode_version": EPISODE_VERSION,
        }


def _record_gap(ledger: EvidenceLedger, family: str, output: ProposalOutput) -> str:
    gap = output.unsupported_mechanism
    proposal = ProposalSpec(
        mechanism=gap.mechanism,
        source="polymarket",
        target="unbound",
        horizon="unbound",
        universe="primitive_gap",
        direction=0,
        falsifiable_condition="补上该原语后若仍无法表达该机制，则本声明被证伪",
        proposed_by="llm_proposer",
        rationale=gap.why_existing_primitives_insufficient,
    )
    ledger.record_proposal(
        proposal.content_id, family, screened_out=True,
        reason=f"原语缺口：缺 {gap.missing_primitive}",
    )
    ledger.append("primitive_gap_declared", gap.model_dump(mode="json"))
    return proposal.content_id


def run_round(
    *,
    queue: DurableQueue,
    ledger: EvidenceLedger,
    provider: Provider,
    budget: EpisodeBudget,
    family: str,
    owner: str,
    assemble: Any,
    build_evaluation: Any,
    now: datetime | None = None,
) -> RoundOutcome | None:
    """跑一轮。没有可运行任务时返回 None（不是"完成"）。"""
    current = now or datetime.now(UTC)
    task = queue.claim(owner, now=current)
    if task is None:
        return None
    task_id = task["task_id"]

    bundle: ContextBundle = assemble(task)
    study_id = task["payload"].get("study_id", task_id)
    record_context(ledger, bundle, study_id)

    request = ProviderRequest(
        role=Role.PROPOSER, prompt=bundle.prompt, schema_name="ProposalOutput"
    )
    try:
        parsed, failure, _ = invoke_structured(
            provider, request, ProposalOutput, budget=budget
        )
    except ProviderError as exc:
        queue.fail(task_id, owner, f"provider 故障：{exc}", now=current)
        ledger.append("provider_error", {"task_id": task_id, "error": str(exc)[:400]})
        return RoundOutcome(task_id=task_id, outcome="provider_error",
                            detail={"error": str(exc)[:200]})

    if failure is not None:
        ledger.append("parse_failure", failure.model_dump(mode="json"), study_id=study_id)
        queue.fail(task_id, owner, "输出无法解析为结构化提案", now=current)
        return RoundOutcome(task_id=task_id, outcome="parse_failure",
                            detail={"attempts": failure.attempts})

    if parsed.is_gap():
        proposal_id = _record_gap(ledger, family, parsed)
        queue.complete(task_id, owner, {"gap": True},
                       idempotency_key=f"{task_id}:gap", now=current)
        return RoundOutcome(task_id=task_id, outcome="primitive_gap",
                            proposal_id=proposal_id)

    try:
        proposal = parsed.to_proposal()
    except ValidationError as exc:
        ledger.append("invalid_proposal", {"task_id": task_id, "error": str(exc)[:400]})
        queue.fail(task_id, owner, "提案缺必填字段", now=current)
        return RoundOutcome(task_id=task_id, outcome="invalid_proposal")

    ledger.record_proposal(proposal.content_id, family)
    ledger.append("proposal_locked", proposal.payload(), study_id=study_id)

    hypothesis = HypothesisLock(
        proposal_id=proposal.content_id, experiment_family=family,
        sample_segments=["discovery"],
    )
    confirmatory = ConfirmatoryLock(
        hypothesis_id=hypothesis.content_id,
        formula=f"target ~ {parsed.feature_spec.feature_id}",
        preregistered_diagnostics=["leakage", "influence", "placebo", "cost"],
        test_family=family,
    )
    study = StudySpec(study_id=study_id, proposal_id=proposal.content_id,
                      hypothesis_id=hypothesis.content_id,
                      confirmatory_id=confirmatory.content_id)
    ledger.append("hypothesis_locked", hypothesis.payload(), study_id=study_id)
    ledger.append("confirmatory_locked", confirmatory.payload(), study_id=study_id)
    ledger.append("study_created", study.payload(), study_id=study_id)
    ledger.append("feature_spec_locked", parsed.feature_spec.describe(), study_id=study_id)

    try:
        request_obj, labels, visible = build_evaluation(parsed.feature_spec, study_id)
    except SourceNotImplemented as exc:
        ledger.append("source_gap", {"study_id": study_id, "error": str(exc)[:400]},
                      study_id=study_id)
        verdict = StudyVerdict(
            study_id=study_id, verdict=Verdict.BLOCKED,
            next_action=NextAction.REQUEST_HUMAN_REVIEW,
            rationale=f"特征所需数据源尚未接入解释器：{exc}",
        )
        ledger.append("visible_data_range", {"note": "未取数"}, study_id=study_id)
        ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)
        queue.complete(task_id, owner, {"verdict": verdict.verdict.value},
                       idempotency_key=f"{task_id}:verdict", now=current)
        return RoundOutcome(task_id=task_id, outcome="source_gap",
                            proposal_id=proposal.content_id, study_id=study_id,
                            verdict=verdict.verdict.value)

    ledger.append("visible_data_range", visible, study_id=study_id)
    if request_obj is None:
        verdict = StudyVerdict(
            study_id=study_id, verdict=Verdict.UNDERPOWERED,
            next_action=NextAction.QUEUE_FORWARD,
            rationale="该特征在可用样本上定义点过少，无法评价",
        )
        ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)
        queue.complete(task_id, owner, {"verdict": verdict.verdict.value},
                       idempotency_key=f"{task_id}:verdict", now=current)
        return RoundOutcome(task_id=task_id, outcome="underpowered",
                            proposal_id=proposal.content_id, study_id=study_id,
                            verdict=verdict.verdict.value)

    for test_id in [f"{study_id}:main"]:
        ledger.record_outcome_read(test_id, family, study_id)
    result = evaluate(request_obj, labels, role="evaluator")
    ledger.append("evaluation_result", result, study_id=study_id)

    suggested = result["suggested_verdict"]
    verdict = StudyVerdict(
        study_id=study_id, verdict=Verdict(suggested),
        next_action=(
            NextAction.QUEUE_FORWARD if suggested == Verdict.CANDIDATE.value
            else NextAction.ARCHIVE_EVIDENCE
        ),
        rationale="；".join(result["blocked_reasons"]) or "全部预注册闸门通过",
        evidence_refs=[result["result_digest"]],
    )
    ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)
    queue.complete(task_id, owner, {"verdict": suggested},
                   idempotency_key=f"{task_id}:verdict", now=current)
    return RoundOutcome(
        task_id=task_id, outcome="evaluated", proposal_id=proposal.content_id,
        study_id=study_id, verdict=suggested,
        feedback=format_feedback(result, suggested),
    )


def run_episode(
    *,
    episode_id: str,
    queue: DurableQueue,
    ledger: EvidenceLedger,
    provider: Provider,
    budget: EpisodeBudget,
    family: str,
    owner: str,
    assemble: Any,
    build_evaluation: Any,
    max_rounds: int = 50,
    now: datetime | None = None,
) -> EpisodeResult:
    """跑一次 Episode。预算耗尽或无可运行任务即结束 —— Service 不停。"""
    result = EpisodeResult(episode_id=episode_id)
    ledger.append("episode_started", {"episode_id": episode_id, "family": family,
                                      "budget": budget.describe()})
    for _ in range(max_rounds):
        try:
            outcome = run_round(
                queue=queue, ledger=ledger, provider=provider, budget=budget,
                family=family, owner=owner, assemble=assemble,
                build_evaluation=build_evaluation, now=now,
            )
        except EpisodeBudgetExhausted:
            result.ended_because = "budget_exhausted"
            break
        if outcome is None:
            result.ended_because = "no_runnable_work"
            break
        result.rounds.append(outcome)
    else:
        result.ended_because = "max_rounds"
    result.budget = budget.describe()
    ledger.append("episode_ended", result.summary())
    return result
