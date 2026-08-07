"""从冻结规格生成公式与可执行代码（M8）。

M4 票的裁决是「结构化规格为主，可执行代码为辅，但代码必须附带清楚的表达」，
并规定规格与代码不一致按缺陷处理。**因此代码由规格确定性生成，不由模型写** ——
生成式在构造上就不可能与规格不一致，而人写或模型写的代码只能靠事后比对。

生成的函数与解释器共用同一套语义：窗口右端点一律不含、offset 只能非负、
无定义返回 None 绝不返回 0、zscore 的参考样本取自规格自己声明的采样网格。
有一条合同测试钉死这一点：生成代码在同一批序列上的取值必须与解释器**逐位相同**。
"""

from __future__ import annotations

from .spec import SAMPLED_KINDS, FeatureSpec, Step, StepKind

CODEGEN_VERSION = "0.1.0"

_OP_TEXT = {
    "last": "最后值", "mean": "均值", "sum": "求和", "count": "计数",
    "std": "标准差", "min": "最小值", "max": "最大值",
}


def _dur(seconds: int | None) -> str:
    if not seconds:
        return "0"
    for unit, size in (("日", 86400), ("时", 3600), ("分", 60)):
        if seconds >= size and seconds % size == 0:
            return f"{seconds // size}{unit}"
    return f"{seconds}秒"


def _window_text(step: Step) -> str:
    span = _dur(step.window_seconds)
    if step.offset_seconds:
        return f"[t−{_dur(step.offset_seconds)}−{span}, t−{_dur(step.offset_seconds)})"
    return f"[t−{span}, t)"


def to_formula(spec: FeatureSpec) -> list[str]:
    """逐步的可读公式。每行一步，最后一行是输出步。"""
    lines: list[str] = []
    for step in spec.steps:
        if step.kind in (StepKind.WINDOW, StepKind.INNOVATION):
            base = (f"{step.name} = {_OP_TEXT.get((step.op or '').value if hasattr(step.op, 'value') else str(step.op), str(step.op))}"
                    f"( {step.source.value}.{step.field} , 窗口 {_window_text(step)} )")
            if step.kind is StepKind.INNOVATION:
                base += f" − 同算子(窗口 [t−{_dur(step.baseline_seconds)}, t) )"
            lines.append(base)
        elif step.kind is StepKind.RATIO:
            lines.append(f"{step.name} = {step.inputs[0]} ÷ {step.inputs[1]}")
        elif step.kind is StepKind.DIFFERENCE:
            lines.append(f"{step.name} = {step.inputs[0]} − {step.inputs[1]}")
        elif step.kind is StepKind.ZSCORE:
            lines.append(
                f"{step.name} = ( {step.inputs[0]}(t) − μ ) / σ，"
                f"其中 μ、σ 取自 {step.inputs[0]} 在 "
                f"t−k×{_dur(step.sample_every_seconds)}（k=1..{(step.window_seconds or 0) // (step.sample_every_seconds or 1)}）"
                f"上的取值，互异取值不足 {step.min_samples} 个则无定义"
            )
        elif step.kind is StepKind.RANK_PCT:
            lines.append(
                f"{step.name} = ( #{{s < {step.inputs[0]}(t)}} + ½·#{{s = {step.inputs[0]}(t)}} ) / n，"
                f"其中 s 取自 {step.inputs[0]} 在 "
                f"t−k×{_dur(step.sample_every_seconds)}（k=1..{(step.window_seconds or 0) // (step.sample_every_seconds or 1)}）"
                f"上的取值，互异取值不足 {step.min_samples} 个则无定义；取值域 [0,1]"
            )
        elif step.kind is StepKind.RESIDUALISE:
            lines.append(f"{step.name} = {step.inputs[0]} 对 {', '.join(step.controls)} 残差化")
    lines.append(f"输出 = {spec.output_step}")
    return lines


_HEADER = '''"""{feature_id}

机制：{mechanism}

失败条件：{failure_condition}

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 {content_id}
生成器 {codegen_version}；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 {lookback} 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = {lookback_seconds}


def _window(times, values, end, seconds):
    """取 [end - seconds, end) 内的值。**end 一律不含**，这是 PIT 的关键。"""
    lo = bisect_left(times, end - timedelta(seconds=seconds))
    hi = bisect_left(times, end)
    return values[lo:hi]


def _agg(op, xs):
    if not xs:
        return None
    if op == "last":
        return xs[-1]
    if op == "mean":
        return math.fsum(xs) / len(xs)
    if op == "sum":
        return math.fsum(xs)
    if op == "count":
        return float(len(xs))
    if op == "min":
        return min(xs)
    if op == "max":
        return max(xs)
    if op == "std":
        if len(xs) < 2:
            return None
        m = math.fsum(xs) / len(xs)
        return math.sqrt(math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1))
    raise ValueError(op)


def _ok(v):
    """非有限值一律当作无定义：NaN 传下去会让比较式的闸门全部取假地通过。"""
    return v is not None and math.isfinite(v)
'''


def to_python(spec: FeatureSpec) -> str:
    """生成一个自包含的求值函数。

    入参 `series` 是 `{{"来源.字段": (times, values)}}`，times 按升序，
    values 的可用时刻即 times[i]（右端点语义与解释器一致）。
    """
    body: list[str] = []
    body.append("")
    body.append("")
    body.append("def compute(decision_time: datetime, series: dict, coverage_start=None):")
    body.append('    """在一个决策时点上求值。无定义返回 None。"""')
    body.append("    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整")
    body.append("    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别")
    body.append("    if coverage_start is not None and (")
    body.append("        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)")
    body.append("        < coverage_start")
    body.append("    ):")
    body.append("        return None")
    for step in spec.steps:
        name = f"v_{step.name}"
        if step.kind in (StepKind.WINDOW, StepKind.INNOVATION):
            key = f"{step.source.value}.{step.field}"
            op = step.op.value if hasattr(step.op, "value") else str(step.op)
            body.append(f'    t_{step.name}, x_{step.name} = series["{key}"]')
            body.append(
                f"    end_{step.name} = decision_time - timedelta("
                f"seconds={step.offset_seconds})"
            )
            body.append(
                f'    {name} = _agg("{op}", _window(t_{step.name}, x_{step.name}, '
                f"end_{step.name}, {step.window_seconds}))"
            )
            if step.kind is StepKind.INNOVATION:
                body.append(
                    f'    far_{step.name} = _agg("{op}", _window(t_{step.name}, '
                    f"x_{step.name}, end_{step.name}, {step.baseline_seconds}))"
                )
                body.append(
                    f"    {name} = ({name} - far_{step.name}) "
                    f"if _ok({name}) and _ok(far_{step.name}) else None"
                )
            else:
                body.append(f"    {name} = {name} if _ok({name}) else None")
        elif step.kind is StepKind.RATIO:
            a, b = (f"v_{i}" for i in step.inputs)
            body.append(
                f"    {name} = ({a} / {b}) if _ok({a}) and _ok({b}) and {b} != 0 else None"
            )
        elif step.kind is StepKind.DIFFERENCE:
            a, b = (f"v_{i}" for i in step.inputs)
            body.append(f"    {name} = ({a} - {b}) if _ok({a}) and _ok({b}) else None")
        elif step.kind is StepKind.ZSCORE:
            src = step.inputs[0]
            k = (step.window_seconds or 0) // (step.sample_every_seconds or 1)
            body.append("    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去")
            body.append(f"    samples_{step.name} = []")
            body.append(f"    for k in range(1, {k} + 1):")
            body.append(
                f"        past = decision_time - timedelta("
                f"seconds=k * {step.sample_every_seconds})"
            )
            body.append(f"        s = _at_{src}(past, series)")
            body.append("        if _ok(s):")
            body.append(f"            samples_{step.name}.append(s)")
            body.append(f"    distinct_{step.name} = len(set(samples_{step.name}))")
            body.append(
                f"    if not _ok(v_{src}) or distinct_{step.name} < {step.min_samples}:"
            )
            body.append(f"        {name} = None")
            body.append("    else:")
            body.append(
                f"        mu = math.fsum(samples_{step.name}) / len(samples_{step.name})"
            )
            body.append(
                f"        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in "
                f"samples_{step.name}) / (len(samples_{step.name}) - 1))"
            )
            body.append(
                f"        {name} = ((v_{src} - mu) / sd) if sd > 0 else None"
            )
        elif step.kind is StepKind.RANK_PCT:
            src = step.inputs[0]
            k = (step.window_seconds or 0) // (step.sample_every_seconds or 1)
            body.append("    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同")
            body.append(f"    samples_{step.name} = []")
            body.append(f"    for k in range(1, {k} + 1):")
            body.append(
                f"        past = decision_time - timedelta("
                f"seconds=k * {step.sample_every_seconds})"
            )
            body.append(f"        s = _at_{src}(past, series)")
            body.append("        if _ok(s):")
            body.append(f"            samples_{step.name}.append(s)")
            body.append(f"    distinct_{step.name} = len(set(samples_{step.name}))")
            body.append(
                f"    if not _ok(v_{src}) or distinct_{step.name} < {step.min_samples}:"
            )
            body.append(f"        {name} = None")
            body.append("    else:")
            body.append(
                f"        below = sum(1 for s in samples_{step.name} if s < v_{src})"
            )
            body.append(
                f"        tied = sum(1 for s in samples_{step.name} if s == v_{src})"
            )
            body.append(
                f"        {name} = (below + 0.5 * tied) / len(samples_{step.name})"
            )
        elif step.kind is StepKind.RESIDUALISE:
            body.append(
                "    raise NotImplementedError('residualise 需要控制序列，"
                "原样返回输入等于把未残差化的值当成已残差化的证据')"
            )
        body.append(f"    if {name} is not None and not math.isfinite({name}):")
        body.append(f"        {name} = None")
    body.append(f"    return v_{spec.output_step}")

    helpers = _zscore_helpers(spec)
    header = _HEADER.format(
        feature_id=spec.feature_id,
        mechanism=spec.mechanism,
        failure_condition=spec.failure_condition,
        content_id=spec.content_id,
        codegen_version=CODEGEN_VERSION,
        lookback=_dur(spec.required_lookback_seconds),
        lookback_seconds=spec.required_lookback_seconds,
    )
    return header + helpers + "\n".join(body) + "\n"


def _zscore_helpers(spec: FeatureSpec) -> str:
    """zscore 需要把它的输入步骤在过去时刻重新求值，因此为该子链生成一个取值函数。"""
    index = {s.name: s for s in spec.steps}
    out: list[str] = []
    for step in spec.steps:
        if step.kind not in SAMPLED_KINDS:
            continue
        target = step.inputs[0]
        lines = [f"\n\ndef _at_{target}(at: datetime, series: dict):",
                 f'    """在任意过去时刻求 {target} 的值。参考分布要用它。"""']
        for name in _reachable(index, target):
            sub = index[name]
            var = f"v_{name}"
            if sub.kind in (StepKind.WINDOW, StepKind.INNOVATION):
                key = f"{sub.source.value}.{sub.field}"
                op = sub.op.value if hasattr(sub.op, "value") else str(sub.op)
                lines.append(f'    t, x = series["{key}"]')
                lines.append(f"    end = at - timedelta(seconds={sub.offset_seconds})")
                lines.append(f'    {var} = _agg("{op}", _window(t, x, end, {sub.window_seconds}))')
                if sub.kind is StepKind.INNOVATION:
                    lines.append(f'    far = _agg("{op}", _window(t, x, end, {sub.baseline_seconds}))')
                    lines.append(f"    {var} = ({var} - far) if _ok({var}) and _ok(far) else None")
            elif sub.kind is StepKind.RATIO:
                a, b = (f"v_{i}" for i in sub.inputs)
                lines.append(f"    {var} = ({a} / {b}) if _ok({a}) and _ok({b}) and {b} != 0 else None")
            elif sub.kind is StepKind.DIFFERENCE:
                a, b = (f"v_{i}" for i in sub.inputs)
                lines.append(f"    {var} = ({a} - {b}) if _ok({a}) and _ok({b}) else None")
        lines.append(f"    return v_{target}")
        out.append("\n".join(lines))
    return "".join(out)


def _reachable(index: dict[str, Step], name: str) -> list[str]:
    """从某步出发、按依赖顺序排出它需要的全部步骤。"""
    order: list[str] = []

    def visit(node: str) -> None:
        for dep in index[node].inputs:
            visit(dep)
        if node not in order:
            order.append(node)

    visit(name)
    return order
