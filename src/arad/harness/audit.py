"""语义审计员（M6 第一块）：在读取任何 outcome 之前，检查规格与目标是否说的是一回事。

**这个角色是盲化的，而且它的输入按白名单从类型化对象构造，绝不走 `read_events`。**
后者的教训是实测过的：提案器视图曾经把 `diagnostics.placebo.actual_slope` 除以
`two_way_cluster.se` 得到的带符号 t 值原样送出，逐位与评价机相同。

它能发现什么，是有边界的：只发现**规格与目标之间的语义错配**，例如「特征预测的是
幅度，而标签是有符号收益」。这类诊断不需要任何效应量 —— 本仓库实测过，
从盲化视图里就能推出来。发现错配的 Study 判 blocked 且**根本不读 outcome**，
因此不进统计分母：一个问错了的问题不该消耗多重检验预算。

审计在 `study_created` 之后、`record_outcome_read` 之前无条件进行。无条件是关键：
调用本身不携带任何结果信息，盲化由哈希链的 seq 顺序证明，而不是靠检查提示词。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..features.spec import FeatureSpec, Op, StepKind

AUDIT_VERSION = "0.1.0"

#: 封闭的错配词表。审计员只能从这里挑，不能自由写 —— 自由文本会成为一条把效应
#: 走私给下一版提案器的通道，而这正是本模块存在的理由。
SEMANTIC_MISMATCH_TAXONOMY: dict[str, str] = {
    "magnitude_vs_signed_label": (
        "特征度量的是幅度（标准差、绝对创新、已实现波动一类），"
        "而标签是有符号收益。sign_unit 仓位下被检验的是方向，两者不是一回事"
    ),
    "untradable_claim": (
        "提案声称可交易，而该 target 的记录里 tradable_claim 为假"
    ),
    "direction_undeclared": (
        "提案没有声明方向（direction 为零），却用有符号标签做检验：没有事前方向就无法证伪"
    ),
    "source_not_wired": (
        "特征引用的数据源尚未接入解释器，本轮不可能求值"
    ),
    "lookback_exceeds_coverage": (
        "特征要求的回看深度超过可见数据范围，绝大多数决策点将无定义"
    ),
}

#: 判定「这个特征在度量幅度」的算子与步骤。幅度类算子的输出与方向无关。
_MAGNITUDE_OPS = frozenset({Op.STD})
_MAGNITUDE_HINTS = ("volatility", "realised_volatility", "abs", "dispersion", "range")


@dataclass(frozen=True)
class SemanticMismatch:
    """一条错配。`code` 取自封闭词表，`slots` 只放规格与目标里已有的字段名与取值。"""

    code: str
    slots: dict = field(default_factory=dict)

    def render(self) -> str:
        return SEMANTIC_MISMATCH_TAXONOMY[self.code]

    def payload(self) -> dict:
        return {"code": self.code, "explanation": self.render(), "slots": self.slots}


@dataclass(frozen=True)
class AuditInput:
    """审计员**唯一**允许看到的东西。逐字段构造，不是过滤某个 payload。"""

    feature: FeatureSpec
    target_record: dict
    proposal_direction: int
    falsifiable_condition: str
    wired_sources: frozenset[str]
    visible_span_seconds: int | None = None


def _measures_magnitude(feature: FeatureSpec) -> bool:
    if any(s.op in _MAGNITUDE_OPS for s in feature.steps):
        return True
    haystack = " ".join(
        [feature.mechanism.lower(), feature.feature_id.lower()]
        + [(s.field or "").lower() for s in feature.steps]
    )
    return any(hint in haystack for hint in _MAGNITUDE_HINTS)


def audit(spec: AuditInput) -> list[SemanticMismatch]:
    """纯函数。同样的输入必然给出同样的错配列表，不调用任何模型。"""
    out: list[SemanticMismatch] = []
    label_is_return = bool(spec.target_record.get("label_is_return"))

    if label_is_return and _measures_magnitude(spec.feature):
        out.append(SemanticMismatch("magnitude_vs_signed_label", {
            "feature_id": spec.feature.feature_id,
            "target_name": spec.target_record.get("name"),
            "label_rule": spec.target_record.get("label_rule"),
        }))
    if label_is_return and spec.proposal_direction == 0:
        out.append(SemanticMismatch("direction_undeclared", {
            "target_name": spec.target_record.get("name"),
        }))
    if not spec.target_record.get("tradable_claim") and "可交易" in spec.falsifiable_condition:
        out.append(SemanticMismatch("untradable_claim", {
            "target_name": spec.target_record.get("name"),
        }))
    unwired = sorted(
        {s.source.value for s in spec.feature.steps if s.source is not None}
        - set(spec.wired_sources)
    )
    if unwired:
        out.append(SemanticMismatch("source_not_wired", {"sources": unwired}))
    if (
        spec.visible_span_seconds is not None
        and spec.feature.required_lookback_seconds >= spec.visible_span_seconds
    ):
        out.append(SemanticMismatch("lookback_exceeds_coverage", {
            "required_lookback_seconds": spec.feature.required_lookback_seconds,
            "visible_span_seconds": spec.visible_span_seconds,
        }))
    return out


def render_for_proposer(mismatches: list[SemanticMismatch]) -> list[dict]:
    """给下一版提案器看的形态：封闭词表的解释 + 规格里已有的字段名。

    这份东西会进提案器上下文，因此**不得含任何评价机产出的数字**。
    词表是封闭的，slots 只装规格与目标自身的字段，两者都与结果无关。
    """
    return [m.payload() for m in mismatches]


def unsupported_step_kinds(feature: FeatureSpec, implemented: frozenset[str]) -> list[str]:
    """规格里用到但解释器尚未实现的步骤类型。"""
    return sorted({s.kind.value for s in feature.steps} - set(implemented))


IMPLEMENTED_STEP_KINDS = frozenset(
    {StepKind.WINDOW.value, StepKind.INNOVATION.value, StepKind.RATIO.value,
     StepKind.DIFFERENCE.value, StepKind.ZSCORE.value}
)
