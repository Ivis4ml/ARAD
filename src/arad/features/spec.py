"""特征规格语言（M4 第一块）。

这是 LLM 作为 research worker 的**表达**。规格是一等工件：进冻结锁、进账本、
进 Atlas，是被审计的对象；代码只是它的实现，两者不一致按缺陷处理。

**PIT 安全是结构性的，不是检查出来的。**语言层没有任何原语能引用决策时点之后的
数据：所有窗口都定义为"结束于决策时点之前"，`offset` 只能非负（向过去），
窗口长度只能为正。因此"写出一个前视特征"在这门语言里无法表达，
而不是写出来之后被评价机拦下。

原语集合刻意窄。窄不是缺陷 —— 它是可审计性的来源。当 LLM 判断现有原语无法表达
某个机制时，那本身是一条应当被记录的证据（见 `UnsupportedMechanism`），
而不是绕过语言去写代码。
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..registry.specs import content_id

FEATURE_SPEC_VERSION = "0.1.0"


class Source(str, Enum):
    """允许的数据来源。每个都有 M1 或声明式的可用时间合同。"""

    COMMODITY_BAR = "commodity_bar"
    PM_MARKET = "pm_market"
    CLS = "cls_telegraph"
    INTL = "intl_brent"


class Op(str, Enum):
    """聚合算子。全部作用在"结束于决策时点之前"的窗口上。"""

    LAST = "last"
    MEAN = "mean"
    SUM = "sum"
    COUNT = "count"
    STD = "std"
    MIN = "min"
    MAX = "max"


class StepKind(str, Enum):
    WINDOW = "window"              # 在过去窗口上聚合一个字段
    INNOVATION = "innovation"      # 相对更长基线窗口的创新量
    RATIO = "ratio"                # 两个已算步骤之比
    DIFFERENCE = "difference"      # 两个已算步骤之差
    ZSCORE = "zscore"              # 相对过去窗口的标准化
    RESIDUALISE = "residualise"    # 对已声明控制项残差化


class UnsupportedMechanism(BaseModel):
    """LLM 声明现有原语无法表达某机制。这是证据，不是失败。

    记入 proposal denominator 并进入失败档案：原语集合的缺口本身是研究信息，
    应当驱动下一轮扩展，而不是被绕过。
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    mechanism: str
    missing_primitive: str
    why_existing_primitives_insufficient: str


class Step(BaseModel):
    """一个计算步骤。窗口语义由构造保证不越过决策时点。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    kind: StepKind
    source: Source | None = None
    field: str | None = None
    op: Op | None = None
    #: 窗口长度（秒）。必须为正。
    window_seconds: int | None = None
    #: 窗口右端点相对决策时点的**回退**秒数。必须非负 —— 负值即前视，语言层禁止。
    offset_seconds: int = 0
    #: INNOVATION 用的基线窗口长度（秒），必须长于 window_seconds。
    baseline_seconds: int | None = None
    #: RATIO / DIFFERENCE / ZSCORE / RESIDUALISE 引用的已算步骤名。
    inputs: list[str] = Field(default_factory=list)
    #: RESIDUALISE 的控制项（必须是已登记的 Baseline Control）。
    controls: list[str] = Field(default_factory=list)

    @field_validator("offset_seconds")
    @classmethod
    def _no_negative_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError(
                "offset_seconds 不能为负：负偏移意味着引用决策时点之后的数据。"
                "本语言在结构上不允许表达前视"
            )
        return v

    @field_validator("window_seconds", "baseline_seconds")
    @classmethod
    def _positive_window(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("窗口长度必须为正")
        return v

    @field_validator("name")
    @classmethod
    def _named(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("每个步骤必须有名字，否则规格无法被引用与审计")
        return v

    @model_validator(mode="after")
    def _kind_requirements(self) -> Step:
        if self.kind in (StepKind.WINDOW, StepKind.INNOVATION):
            if self.source is None or not self.field or self.op is None:
                raise ValueError(f"{self.kind.value} 步骤必须声明 source、field 与 op")
            if self.window_seconds is None:
                raise ValueError(f"{self.kind.value} 步骤必须声明 window_seconds")
            if self.inputs:
                raise ValueError(f"{self.kind.value} 步骤不引用其他步骤")
        if self.kind is StepKind.INNOVATION:
            if self.baseline_seconds is None:
                raise ValueError("innovation 必须声明 baseline_seconds")
            if self.baseline_seconds <= (self.window_seconds or 0):
                raise ValueError("innovation 的基线窗口必须长于观测窗口")
        if self.kind in (StepKind.RATIO, StepKind.DIFFERENCE) and len(self.inputs) != 2:
            raise ValueError(f"{self.kind.value} 需要恰好两个输入步骤")
        if self.kind is StepKind.ZSCORE and (
            len(self.inputs) != 1 or self.window_seconds is None
        ):
            raise ValueError("zscore 需要一个输入步骤与一个窗口长度")
        if self.kind is StepKind.RESIDUALISE and (len(self.inputs) != 1 or not self.controls):
            raise ValueError("residualise 需要一个输入步骤与至少一个控制项")
        return self

    @property
    def earliest_lookback_seconds(self) -> int:
        """该步骤最远回看多少秒。用于声明数据需求，不影响 PIT 安全。"""
        span = max(self.window_seconds or 0, self.baseline_seconds or 0)
        return self.offset_seconds + span


class FeatureSpec(BaseModel):
    """一个可审计的特征表达。内容寻址；同一内容必然同 id。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    feature_id: str
    mechanism: str
    steps: list[Step]
    output_step: str
    failure_condition: str
    authored_by: str
    code_artifact_id: str | None = None
    spec_version: str = FEATURE_SPEC_VERSION

    @field_validator("mechanism", "failure_condition", "authored_by")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("特征必须声明经济含义、失败条件与作者")
        return v

    @model_validator(mode="after")
    def _dag_is_valid(self) -> FeatureSpec:
        if not self.steps:
            raise ValueError("特征至少需要一个步骤")
        seen: set[str] = set()
        for step in self.steps:
            if step.name in seen:
                raise ValueError(f"步骤名 {step.name!r} 重复")
            missing = [i for i in step.inputs if i not in seen]
            if missing:
                raise ValueError(
                    f"步骤 {step.name!r} 引用了尚未定义的步骤 {missing}；"
                    "步骤必须按依赖顺序排列，且不允许环"
                )
            seen.add(step.name)
        if self.output_step not in seen:
            raise ValueError(f"output_step {self.output_step!r} 不在步骤列表中")
        return self

    @property
    def content_id(self) -> str:
        return content_id({"kind": "FeatureSpec", **self.model_dump(mode="json")})

    @property
    def sources(self) -> set[Source]:
        return {s.source for s in self.steps if s.source is not None}

    @property
    def required_lookback_seconds(self) -> int:
        return max((s.earliest_lookback_seconds for s in self.steps), default=0)

    def declares_code(self) -> bool:
        return self.code_artifact_id is not None

    def describe(self) -> dict:
        """给账本与 Atlas 的机器可读摘要。"""
        return {
            "feature_id": self.feature_id,
            "content_id": self.content_id,
            "mechanism": self.mechanism,
            "sources": sorted(s.value for s in self.sources),
            # 步骤必须无损：账本里存的就是这份摘要，规格若不能从证据里重建，
            # 快照就不是自包含的（决定 0003）。省略 source/field/inputs 曾使
            # 快照里的 ratio 步骤看不出它引用了哪两步。
            "steps": [s.model_dump(mode="json") for s in self.steps],
            "output_step": self.output_step,
            "required_lookback_seconds": self.required_lookback_seconds,
            "failure_condition": self.failure_condition,
            "code_artifact_id": self.code_artifact_id,
            "spec_version": self.spec_version,
        }
