"""特征规格解释器（M4 第四块；zscore 于 M4.1 补齐）。

把 `FeatureSpec` 在给定决策时点上算成一个数。**PIT 安全由构造保证**：
每个窗口的右端点是 `decision_time - offset_seconds`，左端点再往前
`window_seconds`，因此没有任何路径能读到决策时点之后的数据 ——
不是算完再检查，而是取数时就够不到。

本版只实现 `COMMODITY_BAR` 源（SC 的 1 分钟 bar）。其余源返回
`SourceNotImplemented`，它和 `UnsupportedMechanism` 一样是应被记录的缺口，
不是崩溃：提案器据此知道哪些源还不能用。

**求值是惰性递归的**：`zscore` 需要它的输入步骤在若干过去时刻上的取值，
因此步骤不能只在决策时点上算一次。`_value_of(name, t)` 按需求值并按 `(名字, 时刻)`
记忆化；记忆表在每次 `evaluate_spec` 内创建并显式传递，不放模块级 —— 序列一旦更换，
同一个键就对应另一个数。惰性求值的代价是够不到的步骤不再被执行，
因此 `FeatureSpec` 在语言层拒绝存在不可达步骤的规格。

**覆盖准入**：若 `decision_time - required_lookback_seconds` 早于序列的覆盖起点，
特征判为无定义。否则声明为"20 日均值"的东西在序列开头几天实际上是"能取到多少算多少"
的均值 —— 同一份规格在完整序列与其截断副本上会给出不同的数，而没有任何记录能看出
差别。加了这道准入之后，"可求值"就蕴含"值唯一"。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from .spec import FeatureSpec, Op, Source, Step, StepKind

#: 解释器语义版本。进入 `EvaluationRequest.digest()`：同一规格换一个解释器版本
#: 可能算出另一个数，证据必须能区分。
INTERPRETER_VERSION = "0.5.0"

#: 已接入的数据源。`pm_market` 的序列由 `arad pm-index series` 物化，字段名形如
#: `cand:iran:p` —— 族的选择是各 Study 冻结的经济假设，不是这里固化的映射表。
WIRED_SOURCES = frozenset({Source.COMMODITY_BAR, Source.PM_MARKET})

#: 已登记的 Baseline Control：控制名 → 序列键。**不认识的名字直接拒绝**，
#: 不退化为原样返回 —— 后者等于把未残差化的值当成已残差化的证据。
CONTROL_SERIES: dict[str, tuple[Source, str]] = {
    "brent": (Source.INTL, "brent"),
    #: 品种自身的已实现波动。实测最需要减掉的正是它：模型给出 |t| = 9.3 的特征，
    #: 分母是 `mean(realised_volatility)` 而目标就是已实现波动 ——
    #: 它重新发现了波动率聚集，是教科书级的 Baseline Control。
    "own_realised_volatility": (Source.COMMODITY_BAR, "realised_volatility"),
}


class NotInterpretable(RuntimeError):
    """解释器尚不能求值这条规格。这是缺口，应被记录并驱动扩展。"""


class SourceNotImplemented(NotInterpretable):
    """该数据源尚未接入解释器。"""


class StepNotImplemented(NotInterpretable):
    """该步骤类型在语言里可表达，但解释器还没实现它的语义。

    **绝不能退化为恒等映射。**把 zscore 当成"原样返回"会让评价机拿到的数不是规格
    声明的那个数，而结果照样被记成该规格的证据 —— 这正是评价机被建出来要拦的
    单位错误形态，只不过发生在解释器内部，没有任何检查能看见。宁可判 blocked。
    """


class FeatureUndefined(RuntimeError):
    """在该决策时点上特征无定义（窗口内无数据等）。返回 None 而非 0。"""


@dataclass(frozen=True)
class BarSeries:
    """按时间升序的 (available_time, value) 序列。available_time 是 bar 右端点。"""

    field: str
    times: list[datetime]
    values: list[float]
    #: 该序列的覆盖起点。默认取第一个观测时刻；数据实际开始得更早但本对象只装了
    #: 一段时，应显式声明，否则准入检查会把可用的决策点误判为无定义。
    #:
    #: **这是调用方的断言，解释器无法验证它。**声明得比实际数据早，准入就会放行一些
    #: 参考分布被截断的点，而完整序列与截断副本会在同一决策时点给出不同的数。
    #: 因此声明本身进证据（见 `evaluate_series` 的 `series_coverage`），
    #: 使"声明的覆盖宽于实际持有的数据"在快照上看得见，而不是只能靠信任。
    coverage_start: datetime | None = None

    def begins_at(self) -> datetime | None:
        if self.coverage_start is not None:
            return self.coverage_start
        return self.times[0] if self.times else None

    def window(self, end: datetime, seconds: int) -> list[float]:
        """取 [end - seconds, end) 内的值。**end 一律不含**，这是 PIT 的关键。"""
        start = end - timedelta(seconds=seconds)
        lo = bisect_left(self.times, start)
        hi = bisect_left(self.times, end)
        return self.values[lo:hi]


@dataclass
class ReferenceSampleCoverage:
    """一个采样类步骤（zscore / rank_pct）在一个决策时点上的参考样本统计。

    这三个数必须进证据：参考分布被假日截断时特征照样出数，而截断量既不改变
    content id 也不进入现有的 coverage，评价机的影响点闸门也看不见它。
    """

    step: str
    expected: int
    defined: int
    distinct: int


@dataclass
class EvalContext:
    """一次 `evaluate_spec` 调用的可变状态。不跨调用共享。"""

    series: dict[tuple[Source, str], BarSeries]
    memo: dict[tuple[str, datetime], float | None] = field(default_factory=dict)
    reference_sample_coverage: list[ReferenceSampleCoverage] = field(default_factory=list)


def _defined(value: float | None) -> bool:
    """非有限值一律当作无定义。

    NaN 传下去尤其危险：评价机的闸门都是比较式的，`nan > 上限` 恒为假，
    于是一个坏值会**全部闸门取假**地通过，而不是被拦下。
    """
    return value is not None and math.isfinite(value)


def _aggregate(op: Op, values: list[float]) -> float | None:
    if not values:
        return None
    if op is Op.LAST:
        return values[-1]
    if op is Op.MEAN:
        return math.fsum(values) / len(values)
    if op is Op.SUM:
        return math.fsum(values)
    if op is Op.COUNT:
        return float(len(values))
    if op is Op.MIN:
        return min(values)
    if op is Op.MAX:
        return max(values)
    if op is Op.STD:
        if len(values) < 2:
            return None
        return _sample_std(values)
    raise ValueError(f"未实现的算子 {op}")


def _sample_std(values: list[float]) -> float:
    mean = math.fsum(values) / len(values)
    return math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))


def evaluate_step(
    step: Step,
    decision_time: datetime,
    series: dict[tuple[Source, str], BarSeries],
    computed: dict[str, float | None],
) -> float | None:
    """求值单个**叶子**步骤（window / innovation）。

    派生步骤请走 `evaluate_spec`：它们的语义要求能在过去时刻重新求值输入，
    而这里拿到的 `computed` 只有当前时刻的结果。
    """
    if step.kind not in (StepKind.WINDOW, StepKind.INNOVATION):
        raise ValueError(
            f"{step.kind.value} 是派生步骤，必须经 evaluate_spec 求值；"
            "它需要在过去时刻重新求值输入，单点结果不够"
        )
    if step.source not in WIRED_SOURCES:
        raise SourceNotImplemented(
            f"解释器尚未接入数据源 {step.source.value!r}；"
            "这是原语缺口，应记录并驱动扩展，不是失败"
        )
    key = (step.source, step.field or "")
    if key not in series:
        raise SourceNotImplemented(f"没有为 {key} 提供数据序列")
    # 窗口右端点严格早于决策时点：offset 只能非负，语言层已保证
    end = decision_time - timedelta(seconds=step.offset_seconds)
    near = _aggregate(step.op, series[key].window(end, step.window_seconds or 0))
    if step.kind is StepKind.WINDOW:
        return near if _defined(near) else None
    far = _aggregate(step.op, series[key].window(end, step.baseline_seconds or 0))
    if not _defined(near) or not _defined(far):
        return None
    return near - far


def _value_of(
    spec: FeatureSpec, index: dict[str, Step], name: str, at: datetime, ctx: EvalContext
) -> float | None:
    key = (name, at)
    if key in ctx.memo:
        return ctx.memo[key]
    ctx.memo[key] = value = _evaluate(spec, index, index[name], at, ctx)
    return value


def _evaluate(
    spec: FeatureSpec, index: dict[str, Step], step: Step, at: datetime, ctx: EvalContext
) -> float | None:
    if step.kind in (StepKind.WINDOW, StepKind.INNOVATION):
        return evaluate_step(step, at, ctx.series, {})
    if step.kind is StepKind.RATIO:
        a = _value_of(spec, index, step.inputs[0], at, ctx)
        b = _value_of(spec, index, step.inputs[1], at, ctx)
        if not _defined(a) or not _defined(b) or b == 0:
            return None
        out = a / b
        return out if _defined(out) else None
    if step.kind is StepKind.DIFFERENCE:
        a = _value_of(spec, index, step.inputs[0], at, ctx)
        b = _value_of(spec, index, step.inputs[1], at, ctx)
        return a - b if _defined(a) and _defined(b) else None
    if step.kind is StepKind.ZSCORE:
        return _zscore(spec, index, step, at, ctx)
    if step.kind is StepKind.RANK_PCT:
        return _rank_pct(spec, index, step, at, ctx)
    if step.kind is StepKind.RESIDUALISE:
        return _residualise(spec, index, step, at, ctx)
    raise ValueError(f"未实现的步骤类型 {step.kind}")


def _solve_normal_equations(
    css: list[list[float]], ys: list[float]
) -> list[float] | None:
    """最小二乘 y ~ 1 + c1 + … + cK：正规方程 + 部分主元高斯消元。

    纯 Python（本仓不引 numpy）。主元绝对值低于 1e-10 判奇异（含共线控制），
    返回 None —— 不可识别时宁可无定义，与单控制路径同一条纪律。
    """
    n = len(ys)
    k = len(css)
    dim = k + 1
    rows = [[1.0, *(c[i] for c in css)] for i in range(n)]
    mat = [[math.fsum(r[a] * r[b] for r in rows) for b in range(dim)]
           for a in range(dim)]
    vec = [math.fsum(r[a] * y for r, y in zip(rows, ys, strict=True))
           for a in range(dim)]
    aug = [[*mat[a], vec[a]] for a in range(dim)]
    for col in range(dim):
        pivot = max(range(col, dim), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-10:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(dim):
            if r == col:
                continue
            f = aug[r][col] / aug[col][col]
            for c2 in range(col, dim + 1):
                aug[r][c2] -= f * aug[col][c2]
    return [aug[a][dim] / aug[a][a] for a in range(dim)]


def _residualise(
    spec: FeatureSpec, index: dict[str, Step], step: Step, at: datetime, ctx: EvalContext
) -> float | None:
    """把输入步骤对一个控制序列做残差化。**拟合样本严格取自决策时点之前。**

    在全样本上拟合再取残差，等于用未来数据定义了每个时点的残差 —— 那是最隐蔽的
    一种前视：残差看起来永远「干净」，而干净正是因为它见过未来。这里对每个决策时点
    单独拟合一次，样本取自 `at - k * sample_every_seconds`，与 zscore 同一张网格。

    存在的理由是实测的：真实模型在面板上给出 |t| = 9.3 的特征，分母是
    `mean(realised_volatility)` 而目标就是已实现波动 —— 它重新发现了波动率聚集，
    是教科书级的 Baseline Control，不是另类数据的 alpha。没有这一步，
    任何与波动相关的目标都会被这一层淹没。

    控制值取自控制序列在同一时刻的取值（`Source.CONTROL`）。控制序列本身带
    `available_time`，PIT 由序列构造保证。
    """
    source_name = step.inputs[0]
    controls = []
    for cname in step.controls:
        control_key = CONTROL_SERIES.get(cname)
        if control_key is None:
            raise SourceNotImplemented(
                f"未登记的控制项 {cname!r}；已登记 {sorted(CONTROL_SERIES)}"
            )
        if control_key not in ctx.series:
            raise SourceNotImplemented(
                f"没有为控制项 {cname!r} 提供序列；"
                "残差化不能在缺控制序列时退化为原样返回 —— 那等于把未残差化的值"
                "当成已残差化的证据"
            )
        controls.append(ctx.series[control_key])

    def control_at(control, t: datetime) -> float | None:
        # 取严格早于 t 的最后一个观测。窗口右端点一律不含，与其余原语同一条纪律。
        window = control.window(t, step.window_seconds or 0)
        return window[-1] if window else None

    current_x = _value_of(spec, index, source_name, at, ctx)
    current_cs = [control_at(c, at) for c in controls]
    expected = (step.window_seconds or 0) // (step.sample_every_seconds or 1)
    xs: list[float] = []
    css: list[list[float]] = [[] for _ in controls]
    for k in range(1, expected + 1):
        past = at - timedelta(seconds=k * (step.sample_every_seconds or 0))
        xv = _value_of(spec, index, source_name, past, ctx)
        cvs = [control_at(c, past) for c in controls]
        if _defined(xv) and all(_defined(cv) for cv in cvs):
            xs.append(xv)
            for j, cv in enumerate(cvs):
                css[j].append(cv)
    ctx.reference_sample_coverage.append(
        ReferenceSampleCoverage(step=step.name, expected=expected, defined=len(xs),
                               distinct=min((len(set(c)) for c in css), default=0))
    )
    if not _defined(current_x) or not all(_defined(cv) for cv in current_cs):
        return None
    if len(controls) == 1:
        # 单控制路径**逐位保持第一版算式**：账本里的冻结规格必须可复现。
        cs = css[0]
        # 门槛计**控制变量的互异取值**：控制恒定时斜率不可识别，此时残差就是
        # 去均值，那不是残差化。宁可判无定义。
        if len(set(cs)) < (step.min_samples or 0):
            return None
        cbar = math.fsum(cs) / len(cs)
        xbar = math.fsum(xs) / len(xs)
        scc = math.fsum((c - cbar) ** 2 for c in cs)
        if scc <= 0:
            return None
        slope = math.fsum(
            (c - cbar) * (x - xbar) for c, x in zip(cs, xs, strict=True)) / scc
        out = current_x - (xbar + slope * (current_cs[0] - cbar))
        return out if _defined(out) else None
    # 多控制（决定 0009 方向，评审第一梯队）：正规方程 + 高斯消元。
    # 门槛：成对样本数 ≥ min_samples，且每个控制各自非恒定；奇异（含共线）判 None。
    if len(xs) < (step.min_samples or 0):
        return None
    if any(len(set(c)) < 2 for c in css):
        return None
    coefs = _solve_normal_equations(css, xs)
    if coefs is None:
        return None
    pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], current_cs, strict=True))
    out = current_x - pred
    return out if _defined(out) else None


def _reference_samples(
    spec: FeatureSpec, index: dict[str, Step], step: Step, at: datetime, ctx: EvalContext
) -> tuple[float | None, list[float], int]:
    """取当前值与参考样本。zscore 与 rank_pct 共用，两者只在归一方式上不同。

    参考样本取自 `at - k * sample_every_seconds`，k = 1..window // sample_every。
    锚点就是 `at` 本身：派生步骤不接受 offset_seconds（语言层已拒绝），
    因此不存在"当前值取自 t-offset 而样本取自 t 附近"这种参考分布晚于被标准化观测
    的歧义。

    互异样本数单独返回：采样步长小于数据节奏时会反复读到同一批数据，
    重复样本既压低标准差也压缩分位排名的取值范围。
    """
    source_name = step.inputs[0]
    current = _value_of(spec, index, source_name, at, ctx)
    expected = (step.window_seconds or 0) // (step.sample_every_seconds or 1)
    samples: list[float] = []
    for k in range(1, expected + 1):
        past = at - timedelta(seconds=k * (step.sample_every_seconds or 0))
        value = _value_of(spec, index, source_name, past, ctx)
        if _defined(value):
            samples.append(value)
    distinct = len(set(samples))
    ctx.reference_sample_coverage.append(
        ReferenceSampleCoverage(step=step.name, expected=expected, defined=len(samples),
                       distinct=distinct)
    )
    return current, samples, distinct


def _rank_pct(
    spec: FeatureSpec, index: dict[str, Step], step: Step, at: datetime, ctx: EvalContext
) -> float | None:
    """当前值在其自身过去分布中的分位排名，取值 [0,1]。

    用中位秩的经验分布函数：`(#{s < x} + 0.5 * #{s == x}) / n`。平局各算一半，
    因此常量段不会被系统性地推向 0 或 1。

    存在的理由是实测的：一条真实特征的最大杠杆是 0.607，即单个观测占了回归元
    全部变异的六成，斜率因此由那一个点决定。分位排名有界于 [0,1]，
    无论输入的尾多重，任何单点的杠杆都受这个界约束。它换来的代价是丢掉幅度信息，
    因此它不是 zscore 的替代，是另一个假设。
    """
    current, samples, distinct = _reference_samples(spec, index, step, at, ctx)
    if not _defined(current) or distinct < (step.min_samples or 0):
        return None
    below = sum(1 for s in samples if s < current)
    tied = sum(1 for s in samples if s == current)
    return (below + 0.5 * tied) / len(samples)


def _zscore(
    spec: FeatureSpec, index: dict[str, Step], step: Step, at: datetime, ctx: EvalContext
) -> float | None:
    """相对输入步骤自身过去分布的标准化。参考样本的取法见 `_reference_samples`。"""
    current, samples, distinct = _reference_samples(spec, index, step, at, ctx)
    if not _defined(current) or distinct < (step.min_samples or 0):
        return None
    mean = math.fsum(samples) / len(samples)
    sd = _sample_std(samples)
    if not _defined(sd) or sd == 0:
        return None
    out = (current - mean) / sd
    return out if _defined(out) else None


def _admits(spec: FeatureSpec, at: datetime, ctx: EvalContext) -> bool:
    """回看深度必须整段落在序列覆盖范围内，否则无定义。

    否则"20 日均值"在序列开头几天实际上是"能取到多少算多少"的均值：
    同一份规格在完整序列与其截断副本上给出不同的数，且无从察觉。
    """
    earliest = at - timedelta(seconds=spec.required_lookback_seconds)
    for step in spec.steps:
        if step.source is None:
            continue
        series = ctx.series.get((step.source, step.field or ""))
        begins = series.begins_at() if series is not None else None
        if begins is not None and earliest < begins:
            return False
    return True


def evaluate_spec(
    spec: FeatureSpec,
    decision_time: datetime,
    series: dict[tuple[Source, str], BarSeries],
    *,
    context: EvalContext | None = None,
) -> float | None:
    """在一个决策时点上求值。无定义时返回 None，绝不返回 0。"""
    at = decision_time.astimezone(UTC) if decision_time.tzinfo else decision_time
    ctx = context or EvalContext(series=series)
    ctx.memo.clear()
    if not _admits(spec, at, ctx):
        return None
    index = {s.name: s for s in spec.steps}
    return _value_of(spec, index, spec.output_step, at, ctx)


def evaluate_series(
    spec: FeatureSpec,
    decision_times: list[datetime],
    series: dict[tuple[Source, str], BarSeries],
) -> tuple[list[float | None], dict]:
    """逐决策时点求值。返回 (值序列, 覆盖统计)。"""
    ctx = EvalContext(series=series)
    values = [evaluate_spec(spec, t, series, context=ctx) for t in decision_times]
    defined = [v for v in values if v is not None]
    coverage = {
        "decision_points": len(decision_times),
        "defined": len(defined),
        "undefined": len(values) - len(defined),
        "coverage": len(defined) / len(values) if values else 0.0,
        "constant": bool(defined) and max(defined) == min(defined),
        "required_lookback_seconds": spec.required_lookback_seconds,
        "interpreter_version": INTERPRETER_VERSION,
    }
    coverage["series_coverage"] = {
        f"{source.value}:{field_name}": {
            "declared_coverage_start": (
                bs.coverage_start.isoformat() if bs.coverage_start else None
            ),
            "first_observation": bs.times[0].isoformat() if bs.times else None,
            "observations": len(bs.times),
            "declared_wider_than_data": bool(
                bs.coverage_start is not None and bs.times
                and bs.coverage_start < bs.times[0]
            ),
        }
        for (source, field_name), bs in series.items()
    }
    if ctx.reference_sample_coverage:
        coverage["reference_samples"] = _summarise_reference_samples(ctx.reference_sample_coverage)
    return values, coverage


def _summarise_reference_samples(records: list[ReferenceSampleCoverage]) -> dict:
    """把逐点样本统计聚合进证据。逐点数组太长，聚合量足以审计截断。"""
    out: dict[str, dict] = {}
    for step in sorted({r.step for r in records}):
        rows = [r for r in records if r.step == step]
        defined = sorted(r.defined for r in rows)
        distinct = sorted(r.distinct for r in rows)
        expected = rows[0].expected
        out[step] = {
            "expected_per_point": expected,
            "points": len(rows),
            "points_truncated": sum(1 for r in rows if r.defined < expected),
            "defined_min": defined[0],
            "defined_median": defined[len(defined) // 2],
            "distinct_min": distinct[0],
            "distinct_median": distinct[len(distinct) // 2],
            "note": (
                "参考分布被假日或停牌截断的点计入 points_truncated；"
                "门槛计互异取值，重复读数不增加信息量"
            ),
        }
    return out
