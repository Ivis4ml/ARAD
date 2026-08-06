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

#: 0.2.0：zscore 由"未实现"变为可求值，Step 新增 sample_every_seconds 与 min_samples，
#: 派生步骤的 offset_seconds 由静默忽略改为拒绝。新增字段进入 model_dump，因此
#: **全部 content id 随之改变** —— 这正是要的：旧证据与新证据不共用 id。
FEATURE_SPEC_VERSION = "0.2.0"

#: zscore 参考样本的硬约束。写死在语言层而不是解释器里：它们决定规格是否可能有定义。
MIN_SAMPLE_STEP_SECONDS = 60
MIN_REFERENCE_SAMPLES = 3
MAX_REFERENCE_SAMPLES = 512


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


#: 引用其他步骤的种类。它们没有自己的取数窗口，因此也没有 offset 的确定语义。
DERIVED_KINDS = frozenset(
    {StepKind.RATIO, StepKind.DIFFERENCE, StepKind.ZSCORE, StepKind.RESIDUALISE}
)


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
    #: ZSCORE 的参考样本步长（秒）。参考分布取自输入步骤在
    #: `t - k * sample_every_seconds`（k = 1..window_seconds // sample_every_seconds）
    #: 上的取值。**采样网格由规格自己定义**，不由调用方请求了哪些决策时点决定 ——
    #: 否则同一个 content id 会因调用方不同而得到不同的数。
    sample_every_seconds: int | None = None
    #: ZSCORE 的最小互异样本数。参考分布被假日或停牌截断时，特征判为无定义。
    #: 门槛计**互异取值**而不是样本个数：采样步长小于数据节奏时会反复读到同一批 bar，
    #: 重复样本压低标准差并系统性放大 z，而样本个数对此完全无感。
    min_samples: int | None = None

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
        if self.kind is StepKind.RESIDUALISE and (len(self.inputs) != 1 or not self.controls):
            raise ValueError("residualise 需要一个输入步骤与至少一个控制项")
        if self.kind is not StepKind.ZSCORE and (
            self.sample_every_seconds is not None or self.min_samples is not None
        ):
            raise ValueError("sample_every_seconds 与 min_samples 只属于 zscore 步骤")
        if self.kind is StepKind.ZSCORE:
            self._zscore_requirements()
        if self.kind in DERIVED_KINDS and self.offset_seconds:
            # 派生步骤此前**静默忽略** offset_seconds。让它生效会使同一个 content id
            # 算出另一个数，违反"同内容必同语义"；因此改为拒绝。滞后写在叶子 window 上。
            raise ValueError(
                f"{self.kind.value} 步骤不接受 offset_seconds："
                "滞后应当写在被引用的 window/innovation 步骤上，那里它有确定语义"
            )
        return self

    def _zscore_requirements(self) -> None:
        if len(self.inputs) != 1 or self.window_seconds is None:
            raise ValueError("zscore 需要一个输入步骤与一个窗口长度")
        if self.sample_every_seconds is None or self.min_samples is None:
            raise ValueError(
                "zscore 必须声明 sample_every_seconds 与 min_samples："
                "参考分布的采样网格与最小互异样本数都是规格的一部分，不能由实现替它决定"
            )
        if self.sample_every_seconds < MIN_SAMPLE_STEP_SECONDS:
            raise ValueError(
                f"sample_every_seconds 不得小于 {MIN_SAMPLE_STEP_SECONDS} 秒"
            )
        if self.min_samples < MIN_REFERENCE_SAMPLES:
            raise ValueError(
                f"min_samples 不得小于 {MIN_REFERENCE_SAMPLES}：样本过少时标准差本身不可用"
            )
        planned = self.window_seconds // self.sample_every_seconds
        if planned > MAX_REFERENCE_SAMPLES:
            raise ValueError(
                f"参考样本数 {planned} 超过上限 {MAX_REFERENCE_SAMPLES}；"
                "请加大 sample_every_seconds 或缩短 window_seconds"
            )
        if planned < self.min_samples:
            raise ValueError(
                f"窗口内最多只能取到 {planned} 个样本，低于声明的 min_samples "
                f"{self.min_samples}：该 zscore 在任何数据上都不可能有定义"
            )

    @property
    def own_lookback_seconds(self) -> int:
        """**本步骤自身**向过去伸出多远（秒），不含其输入的回看。

        跨步累计必须由 `FeatureSpec` 沿 DAG 求解：步骤只知道输入的名字，
        看不到输入的回看深度。
        """
        if self.kind is StepKind.ZSCORE:
            return self.window_seconds or 0
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
        self._all_steps_reachable()
        self._no_nested_zscore()
        return self

    def _index(self) -> dict[str, Step]:
        return {s.name: s for s in self.steps}

    def _reachable_from(self, name: str) -> set[str]:
        index, stack, seen = self._index(), [name], set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(index[current].inputs)
        return seen

    def _all_steps_reachable(self) -> None:
        """从 output_step 够不到的步骤一律拒绝。

        求值是惰性的：够不到的步骤根本不会被执行。而 `describe()` 仍会把它的
        source 写进账本，于是证据声称本特征用了某个数据源，实际那个数与它无关 ——
        一个够不到的 residualise 步骤更会让快照声称"已残差化"，而评价机拿到的
        是未残差化的数。这属于本项目定义的最坏失败形态，必须在语言层拒绝。
        """
        dead = sorted({s.name for s in self.steps} - self._reachable_from(self.output_step))
        if dead:
            raise ValueError(
                f"步骤 {dead} 从 output_step 不可达。求值不会执行它们，但规格摘要仍会"
                "声称本特征用了它们的数据源；请删除，或把它们接进输出链路"
            )

    def _no_nested_zscore(self) -> None:
        index = self._index()
        for step in self.steps:
            if step.kind is not StepKind.ZSCORE:
                continue
            nested = sorted(
                n for n in self._reachable_from(step.name) - {step.name}
                if index[n].kind is StepKind.ZSCORE
            )
            if nested:
                raise ValueError(
                    f"zscore 步骤 {step.name!r} 的输入链上还有 zscore {nested}。"
                    "对已标准化的量再标准化没有确定含义，且求值代价随嵌套深度指数增长。"
                    "这是第一版的保守选择，若出现真实需求可重新审议"
                )

    @property
    def content_id(self) -> str:
        return content_id({"kind": "FeatureSpec", **self.model_dump(mode="json")})

    @property
    def sources(self) -> set[Source]:
        return {s.source for s in self.steps if s.source is not None}

    @property
    def required_lookback_seconds(self) -> int:
        """本特征最早触及多久以前的数据（秒）。沿 DAG **累加**，不是逐步取 max。

        zscore 的参考样本本身取自 `t - window_seconds`，而每个样本又要把输入步骤
        的窗口再往前推一次，两者相加才是真实深度。逐步取 max 会把这个数写小，
        而它经 `describe()` 进入账本，是审计记录的一部分，也是判断历史数据是否
        足够的依据 —— 写小了就是账本里的一句假话。
        """
        index, depth = self._index(), {}

        def solve(name: str) -> int:
            if name in depth:
                return depth[name]
            step = index[name]
            inputs = max((solve(i) for i in step.inputs), default=0)
            depth[name] = step.own_lookback_seconds + inputs
            return depth[name]

        return solve(self.output_step)

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
