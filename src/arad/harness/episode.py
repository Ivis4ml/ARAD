"""Search Episode 驱动（M4 第五块）—— 闭环。

一次 Episode = 一段有调用预算上限的循环。预算耗尽即结束 Episode 并把剩余预算
交回 Program；**Research Service 不因此停止**（Merge-Plan-2 §6）。

每一轮都走同一条路：
    认领任务 → 组装盲化上下文（入账）→ 调用模型 → 解析
    → **只要产出了提案内容就计入 proposal denominator**
    → 冻结两把锁 → 求特征 → 评价 → 判决入账 → 反馈

分母的边界要精确：**被预检挡下的提案与原语缺口声明都计入** proposal denominator，
因为它们都是真实发生过的提案；解析失败没有任何提案内容可供内容寻址，
它作为中止轮次单独入账（Atlas 单列一节），不计入分母。把它算进去等于虚构一个
从未被提出的假设，会同时污染分母与失败档案。

四种非正常产出都不是失败，而是被记录的证据：坏 JSON 降级为 `ParseFailure`、
原语缺口降级为 `UnsupportedMechanism`、上下文泄漏效果字段降级为 `context_blocked`、
特征恒定或覆盖不足由评价机拒绝。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator

from ..evaluation.kernel import evaluate
from ..features.interpreter import NotInterpretable
from ..features.spec import FeatureSpec, UnsupportedMechanism
from ..memory.ledger import EvidenceLedger
from ..orchestrator.queue import DurableQueue
from ..providers.base import (
    ContextLeak,
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
from .audit import AUDIT_VERSION, audit, render_for_proposer
from .context import ContextBundle, record_context
from .feedback import Feedback, format_feedback

EPISODE_VERSION = "0.1.0"

#: 方向的封闭同义词表。模型自然会写 "positive" 而不是 1，实测三次尝试都栽在这里。
#: 这不是宽容：映射是封闭的、确定的，账本里记下的仍是规范化后的整数。
#: **表外的词必须报错**——`direction` 为 None 时 `to_proposal()` 会写成 0，
#: 于是一条 falsifiable_condition 写着「为正」的提案会带着「无方向主张」通过，
#: 预注册就成了空的。宁可整条被拒。
_DIRECTION_WORDS: dict[str, int] = {
    "positive": 1, "negative": -1,
    "long": 1, "short": -1,
    "up": 1, "down": -1,
    "+1": 1, "-1": -1, "1": 1,
}


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
    change_summary: str = ""
    feature_spec: FeatureSpec | None = None
    unsupported_mechanism: UnsupportedMechanism | None = None

    @field_validator("direction", mode="before")
    @classmethod
    def _normalise_direction(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        word = value.strip().lower()
        if word not in _DIRECTION_WORDS:
            raise ValueError(
                f"direction 只接受整数 1 或 -1（或 {sorted(_DIRECTION_WORDS)} 中的词），"
                f"收到 {value!r}"
            )
        return _DIRECTION_WORDS[word]

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
    #: 特征规格的内容身份。**新颖性要按它算而不是按 proposal_id** ——
    #: ProposalSpec 不含 feature_spec，参数扫描的多个变体共用同一个 proposal_id，
    #: 用后者做停滞判据会把「一直在出新特征」误判成「问不出新东西」。
    feature_id: str | None = None
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
    audit_input: Any = None,
    contamination: Any = None,
    now: datetime | None = None,
) -> RoundOutcome | None:
    """跑一轮。没有可运行任务时返回 None（不是"完成"）。"""
    current = now or datetime.now(UTC)
    task = queue.claim(owner, now=current)
    if task is None:
        return None
    task_id = task["task_id"]

    study_id = task["payload"].get("study_id", task_id)
    try:
        bundle: ContextBundle = assemble(task)
    except ContextLeak as exc:
        # 菜单来自数据，token 里出现 alpha/beta/return 是迟早的事。
        # 组装器泄漏效果字段时调用已被拒绝，这一轮必须像其他异常产出一样降级为证据，
        # 而不是让未捕获的异常打断 Episode 并把任务卡在租约里。
        ledger.append("context_blocked", {"task_id": task_id, "error": str(exc)[:400]},
                      study_id=study_id)
        queue.fail(task_id, owner, "上下文组装泄漏效果字段，调用已拒绝", now=current)
        return RoundOutcome(task_id=task_id, outcome="context_blocked",
                            study_id=study_id, detail={"error": str(exc)[:200]})
    record_context(ledger, bundle, study_id)

    request = ProviderRequest(
        role=Role.PROPOSER, prompt=bundle.prompt, schema_name="ProposalOutput"
    )
    try:
        parsed, failure, responses = invoke_structured(
            provider, request, ProposalOutput, budget=budget
        )
    except ProviderError as exc:
        queue.fail(task_id, owner, f"provider 故障：{exc}", now=current)
        ledger.append("provider_error", {"task_id": task_id, "error": str(exc)[:400]})
        return RoundOutcome(task_id=task_id, outcome="provider_error",
                            detail={"error": str(exc)[:200]})

    if len(responses) > 1:
        # 模型第一次没产出合规 JSON 是关于**这份提示词**的研究信息，不是噪声。
        # 不记下来，就无法知道 schema 说明是否够清楚，也无法比较不同提示词的成本。
        ledger.append("provider_repair", {
            "task_id": task_id, "attempts": len(responses),
            "model_id": responses[-1].model_id,
        }, study_id=study_id)

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

    # 分类法污染（决定 0004）：归纳语料若覆盖本 Study 读 outcome 的区间，
    # 机制选择就发生在与结果相关的变量上，条件化之后选择偏差变成估计偏差。
    # 它必须在**冻结时**记进 Hypothesis Lock，事后补记就不是事前信息了。
    hypothesis = HypothesisLock(
        proposal_id=proposal.content_id, experiment_family=family,
        sample_segments=["discovery"],
        taxonomy_contamination=(
            contamination(parsed.feature_spec) if contamination is not None else None
        ),
    )
    confirmatory = ConfirmatoryLock(
        hypothesis_id=hypothesis.content_id,
        formula=f"target ~ {parsed.feature_spec.feature_id}",
        preregistered_diagnostics=["leakage", "influence", "placebo", "cost"],
        test_family=family,
    )
    study = StudySpec(study_id=study_id, proposal_id=proposal.content_id,
                      hypothesis_id=hypothesis.content_id,
                      confirmatory_id=confirmatory.content_id,
                      parent_study_id=task["payload"].get("parent_study_id"),
                      change_summary=parsed.change_summary)
    ledger.append("hypothesis_locked", hypothesis.payload(), study_id=study_id)
    ledger.append("confirmatory_locked", confirmatory.payload(), study_id=study_id)
    ledger.append("study_created", study.payload(), study_id=study_id)
    ledger.append("feature_spec_locked", parsed.feature_spec.describe(), study_id=study_id)

    # 语义审计：在 study_created 之后、读任何 outcome 之前，**无条件**进行。
    # 无条件是关键 —— 调用本身不携带任何结果信息，盲化由哈希链的 seq 顺序证明，
    # 而不是靠事后检查提示词。发现错配就判 blocked 且根本不读 outcome：
    # 一个问错了的问题不该消耗多重检验预算。
    mismatches = []
    if audit_input is not None:
        mismatches = audit(audit_input(parsed.feature_spec, proposal))
        ledger.append("semantic_audit", {
            "audit_version": AUDIT_VERSION,
            "mismatches": render_for_proposer(mismatches),
        }, study_id=study_id)
    if mismatches:
        verdict = StudyVerdict(
            study_id=study_id, verdict=Verdict.BLOCKED,
            next_action=NextAction.CREATE_NEW_VERSION,
            rationale="；".join(m.render() for m in mismatches),
        )
        ledger.append("visible_data_range", {"note": "语义审计未通过，未取数"},
                      study_id=study_id)
        ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)
        queue.complete(task_id, owner, {"verdict": verdict.verdict.value},
                       idempotency_key=f"{task_id}:verdict", now=current)
        return RoundOutcome(task_id=task_id, outcome="semantic_mismatch",
                            proposal_id=proposal.content_id,
                            feature_id=parsed.feature_spec.content_id, study_id=study_id,
                            verdict=verdict.verdict.value,
                            detail={"codes": [m.code for m in mismatches]})

    try:
        request_obj, labels, visible = build_evaluation(parsed.feature_spec, study_id)
    except NotInterpretable as exc:
        ledger.append("interpretation_gap", {"study_id": study_id, "error": str(exc)[:400]},
                      study_id=study_id)
        verdict = StudyVerdict(
            study_id=study_id, verdict=Verdict.BLOCKED,
            next_action=NextAction.REQUEST_HUMAN_REVIEW,
            rationale=f"解释器尚不能求值该规格：{exc}",
        )
        ledger.append("visible_data_range", {"note": "未取数"}, study_id=study_id)
        ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)
        queue.complete(task_id, owner, {"verdict": verdict.verdict.value},
                       idempotency_key=f"{task_id}:verdict", now=current)
        return RoundOutcome(task_id=task_id, outcome="interpretation_gap",
                            proposal_id=proposal.content_id,
                            feature_id=parsed.feature_spec.content_id, study_id=study_id,
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
                            proposal_id=proposal.content_id,
                            feature_id=parsed.feature_spec.content_id, study_id=study_id,
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
        feature_id=parsed.feature_spec.content_id, study_id=study_id, verdict=suggested,
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
    audit_input: Any = None,
    contamination: Any = None,
    schedule_next: Any = None,
    max_rounds: int = 50,
    now: datetime | None = None,
) -> EpisodeResult:
    """跑一次 Episode。预算耗尽或无可运行任务即结束 —— Service 不停。

    `schedule_next(outcome, queue, now)` 是判决之后的调度回调：它读 `next_action`
    决定要不要排下一版。这是环真正闭上的那一段 —— 没有它，每个 Study 都是孤立的
    一次性尝试，`NextAction.CREATE_NEW_VERSION` 写进账本却没有任何东西会去执行它，
    而"策略在迭代"这句话就没有事实支撑。
    """
    result = EpisodeResult(episode_id=episode_id)
    ledger.append("episode_started", {"episode_id": episode_id, "family": family,
                                      "budget": budget.describe()})
    for _ in range(max_rounds):
        try:
            outcome = run_round(
                queue=queue, ledger=ledger, provider=provider, budget=budget,
                family=family, owner=owner, assemble=assemble,
                build_evaluation=build_evaluation, audit_input=audit_input,
                contamination=contamination, now=now,
            )
        except EpisodeBudgetExhausted:
            result.ended_because = "budget_exhausted"
            break
        if outcome is None:
            result.ended_because = "no_runnable_work"
            break
        result.rounds.append(outcome)
        if schedule_next is not None:
            schedule_next(outcome, queue, now or datetime.now(UTC))
    else:
        result.ended_because = "max_rounds"
    result.budget = budget.describe()
    ledger.append("episode_ended", result.summary())
    return result
