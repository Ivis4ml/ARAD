"""不可变研究规格与判决词表（M3 第一块）。

所有规格内容寻址：`content_id` 是规范化 JSON 的 sha256。同一内容必然同 id，
任何字段变化都产生新 id，因此"原地改冻结规格"在数据结构层就不可能 —— 改了
就是另一个对象，旧 id 仍指向旧内容。

Verdict 只描述证据状态，不描述调度动作。`SHIP / ITERATE / KILL / ARCHIVE`
不是 Verdict（Merge-Plan-2 §5.3）；尤其禁止用 KILL 删除代码或证据。
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Verdict(str, Enum):
    """Study 的终态。五个值，全部是合法完整产出。"""

    CANDIDATE = "candidate"
    NULL = "null"
    UNDERPOWERED = "underpowered"
    BLOCKED = "blocked"
    ERROR = "error"


class NextAction(str, Enum):
    """调度动作。与 Verdict 分开存放，避免把证据状态和流程状态混为一谈。"""

    QUEUE_FORWARD = "queue_forward"
    CREATE_NEW_VERSION = "create_new_version"
    ARCHIVE_EVIDENCE = "archive_evidence"
    WAIT_FOR_DATA = "wait_for_data"
    RETRY_INFRASTRUCTURE = "retry_infrastructure"
    REQUEST_HUMAN_REVIEW = "request_human_review"


class LockStage(str, Enum):
    """两次冻结。看过 outcome 之后的变体属于 outcome-exposed discovery family。"""

    HYPOTHESIS = "hypothesis"
    CONFIRMATORY = "confirmatory"


#: 效果字段：proposer 角色一律不可见（Merge-Plan-2 §7.2、§13.10）。
#:
#: 名单必须覆盖**评价机实际输出的字段名**，不能只覆盖教科书叫法。M9 渲染快照时
#: 才发现原名单漏了 `slope` 与 `intercept` —— 评价机出具的一元回归斜率就是效应量，
#: 换个名字并不改变它是效应量这件事。只按名字挡是脆的，因此另加前缀规则与容器规则。
EFFECT_FIELDS = frozenset(
    {
        "beta", "t_stat", "p_value", "ic", "sharpe", "return", "pnl",
        "effect_size", "correlation", "alpha", "information_ratio",
        "slope", "intercept", "t_value", "z_stat", "r_squared", "hit_rate",
    }
)

#: 前缀规则：标准误与最小可检测效应同样泄漏量级（`se_two_way_cluster`、`mde_at_2p8_se`）。
EFFECT_FIELD_PREFIXES = ("se_", "mde_", "beta_", "ic_", "slope_", "sharpe_")

#: 容器规则：整个子对象都是效果，逐字段挡不住新增的统计量。
EFFECT_CONTAINERS = frozenset({"effects"})


def is_effect_field(name: str) -> bool:
    lowered = name.lower()
    return lowered in EFFECT_FIELDS or lowered.startswith(EFFECT_FIELD_PREFIXES)


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      default=str)


def content_id(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class FrozenSpec(BaseModel):
    """内容寻址的冻结规格基类。字段不可变；改内容即新对象。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    def payload(self) -> dict:
        return self.model_dump(exclude={"content_id_cache"}, mode="json")

    @property
    def content_id(self) -> str:
        return content_id({"kind": type(self).__name__, **self.payload()})


class ProposalSpec(FrozenSpec):
    """一个研究提案。**无论是否通过预检都要计入 proposal denominator。**

    被语义、数据或功效预检挡下的想法同样是研究产出的一部分；
    把它们排除在分母之外会低估搜索空间并掩盖选择偏差。
    """

    mechanism: str
    source: str
    target: str
    horizon: str
    universe: str
    direction: int
    falsifiable_condition: str
    proposed_by: str
    rationale: str = ""

    @field_validator("direction")
    @classmethod
    def _direction(cls, v: int) -> int:
        if v not in (-1, 0, 1):
            raise ValueError("direction 只能是 -1、0 或 1")
        return v

    @field_validator("mechanism", "source", "target", "horizon", "universe",
                     "falsifiable_condition", "proposed_by")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("提案的机制、来源、目标、时域、样本、可证伪条件与提出者都不能为空")
        return v


class TaxonomyContamination(BaseModel):
    """分类法归纳语料与本 Study 裁决区间的重叠情况（决定 0004）。

    市场宇宙不是外生文本：创建哪些市场对真实事件内生，而这些事件正是推动商品
    价格的事件。因此归纳语料若覆盖 Study 读取 outcome 的任何区间，机制选择就
    发生在与结果相关的变量上，条件化之后选择偏差变成估计偏差。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    taxonomy_id: str
    taxonomy_freeze_at: str
    induction_corpus_max_date: str
    outcome_read_intervals: list[tuple[str, str]] = Field(default_factory=list)

    @property
    def overlaps_outcome_window(self) -> bool:
        return any(
            start <= self.induction_corpus_max_date for start, _ in self.outcome_read_intervals
        )

    def verdict_cap(self) -> Verdict | None:
        """重叠时 verdict 上限为 candidate：历史段结论本就以 Candidate 封顶。"""
        return Verdict.CANDIDATE if self.overlaps_outcome_window else None


class HypothesisLock(FrozenSpec):
    """第一次冻结：在读取任何相关目标结果**之前**。"""

    proposal_id: str
    experiment_family: str
    controls: list[str] = Field(default_factory=list)
    sample_segments: list[str] = Field(default_factory=list)
    taxonomy_contamination: TaxonomyContamination | None = None
    locked_at: str = Field(default_factory=utc_now)
    stage: LockStage = LockStage.HYPOTHESIS


class ConfirmatoryLock(FrozenSpec):
    """第二次冻结：discovery 完成、validation 开始之前。

    预注册的对抗诊断必须在此列出。看到 validation 之后提出的新检验只能解释
    已有证据，或创建新 Study 在新数据上裁决（Merge-Plan-2 §5.5）。
    """

    hypothesis_id: str
    formula: str
    transforms: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    statistics: list[str] = Field(default_factory=list)
    preregistered_diagnostics: list[str] = Field(default_factory=list)
    cost_model: str = ""
    economic_bound: str = ""
    test_family: str = ""
    locked_at: str = Field(default_factory=utc_now)
    stage: LockStage = LockStage.CONFIRMATORY

    @field_validator("preregistered_diagnostics")
    @classmethod
    def _needs_diagnostics(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError(
                "Confirmatory Lock 必须预注册对抗诊断（泄漏、伪重复、极端点、"
                "传统因子代理、单一情景、成本）；事后补检验不算 confirmatory"
            )
        return v


class StudySpec(FrozenSpec):
    """把两次冻结绑成一个可审计的研究单元。"""

    study_id: str
    proposal_id: str
    hypothesis_id: str
    confirmatory_id: str | None = None
    created_at: str = Field(default_factory=utc_now)


class StudyVerdict(FrozenSpec):
    """Study 的终态记录。Verdict 与调度动作分开。"""

    study_id: str
    verdict: Verdict
    next_action: NextAction
    rationale: str
    evidence_refs: list[str] = Field(default_factory=list)
    decided_at: str = Field(default_factory=utc_now)

    @field_validator("rationale")
    @classmethod
    def _needs_rationale(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Verdict 必须给出理由；null 与 underpowered 同样要说明依据")
        return v
