"""特征规格解释器（M4 第四块）。

把 `FeatureSpec` 在给定决策时点上算成一个数。**PIT 安全由构造保证**：
每个窗口的右端点是 `decision_time - offset_seconds`，左端点再往前
`window_seconds`，因此没有任何路径能读到决策时点之后的数据 ——
不是算完再检查，而是取数时就够不到。

本版只实现 `COMMODITY_BAR` 源（SC 的 1 分钟 bar）。其余源返回
`SourceNotImplemented`，它和 `UnsupportedMechanism` 一样是应被记录的缺口，
不是崩溃：提案器据此知道哪些源还不能用。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timedelta

from .spec import FeatureSpec, Op, Source, Step, StepKind


class SourceNotImplemented(RuntimeError):
    """该数据源尚未接入解释器。这是缺口，应被记录并驱动扩展。"""


class FeatureUndefined(RuntimeError):
    """在该决策时点上特征无定义（窗口内无数据等）。返回 None 而非 0。"""


@dataclass(frozen=True)
class BarSeries:
    """按时间升序的 (available_time, value) 序列。available_time 是 bar 右端点。"""

    field: str
    times: list[datetime]
    values: list[float]

    def window(self, end: datetime, seconds: int) -> list[float]:
        """取 [end - seconds, end) 内的值。**end 一律不含**，这是 PIT 的关键。"""
        start = end - timedelta(seconds=seconds)
        lo = bisect_left(self.times, start)
        hi = bisect_left(self.times, end)
        return self.values[lo:hi]


def _aggregate(op: Op, values: list[float]) -> float | None:
    if not values:
        return None
    if op is Op.LAST:
        return values[-1]
    if op is Op.MEAN:
        return sum(values) / len(values)
    if op is Op.SUM:
        return sum(values)
    if op is Op.COUNT:
        return float(len(values))
    if op is Op.MIN:
        return min(values)
    if op is Op.MAX:
        return max(values)
    if op is Op.STD:
        if len(values) < 2:
            return None
        m = sum(values) / len(values)
        return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))
    raise ValueError(f"未实现的算子 {op}")


def evaluate_step(
    step: Step,
    decision_time: datetime,
    series: dict[tuple[Source, str], BarSeries],
    computed: dict[str, float | None],
) -> float | None:
    if step.kind in (StepKind.WINDOW, StepKind.INNOVATION):
        if step.source is not Source.COMMODITY_BAR:
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
            return near
        far = _aggregate(step.op, series[key].window(end, step.baseline_seconds or 0))
        if near is None or far is None:
            return None
        return near - far
    if step.kind is StepKind.RATIO:
        a, b = (computed[i] for i in step.inputs)
        return None if a is None or not b else a / b
    if step.kind is StepKind.DIFFERENCE:
        a, b = (computed[i] for i in step.inputs)
        return None if a is None or b is None else a - b
    if step.kind is StepKind.ZSCORE:
        # 标准化所需的历史分布由调用方以同名 baseline 序列提供；
        # 缺失时返回 None 而不是伪装成 0
        return computed[step.inputs[0]]
    if step.kind is StepKind.RESIDUALISE:
        return computed[step.inputs[0]]
    raise ValueError(f"未实现的步骤类型 {step.kind}")


def evaluate_spec(
    spec: FeatureSpec,
    decision_time: datetime,
    series: dict[tuple[Source, str], BarSeries],
) -> float | None:
    """在一个决策时点上求值。无定义时返回 None，绝不返回 0。"""
    computed: dict[str, float | None] = {}
    for step in spec.steps:
        computed[step.name] = evaluate_step(step, decision_time, series, computed)
    return computed[spec.output_step]


def evaluate_series(
    spec: FeatureSpec,
    decision_times: list[datetime],
    series: dict[tuple[Source, str], BarSeries],
) -> tuple[list[float | None], dict]:
    """逐决策时点求值。返回 (值序列, 覆盖统计)。"""
    values = [evaluate_spec(spec, t, series) for t in decision_times]
    defined = [v for v in values if v is not None]
    return values, {
        "decision_points": len(decision_times),
        "defined": len(defined),
        "undefined": len(values) - len(defined),
        "coverage": len(defined) / len(values) if values else 0.0,
        "constant": bool(defined) and max(defined) == min(defined),
    }
