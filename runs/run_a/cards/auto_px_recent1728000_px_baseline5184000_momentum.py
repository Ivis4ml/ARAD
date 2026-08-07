"""auto_px_recent1728000_px_baseline5184000_momentum

机制：价格动量：短期累计收益相对长期基线为正时，下一 session 收益方向偏正

失败条件：若动量与下一 session 收益无关，则本特征被证伪

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 fe9b2983a7c608633b8a5c9f0ea9fefc57484065dbdd338e42d5e910d9ee7b91
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 60日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 5184000


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


def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_px_recent, x_px_recent = series["commodity_bar.log_return"]
    end_px_recent = decision_time - timedelta(seconds=0)
    v_px_recent = _agg("sum", _window(t_px_recent, x_px_recent, end_px_recent, 1728000))
    v_px_recent = v_px_recent if _ok(v_px_recent) else None
    if v_px_recent is not None and not math.isfinite(v_px_recent):
        v_px_recent = None
    t_px_baseline, x_px_baseline = series["commodity_bar.log_return"]
    end_px_baseline = decision_time - timedelta(seconds=0)
    v_px_baseline = _agg("sum", _window(t_px_baseline, x_px_baseline, end_px_baseline, 5184000))
    v_px_baseline = v_px_baseline if _ok(v_px_baseline) else None
    if v_px_baseline is not None and not math.isfinite(v_px_baseline):
        v_px_baseline = None
    v_momentum = (v_px_recent - v_px_baseline) if _ok(v_px_recent) and _ok(v_px_baseline) else None
    if v_momentum is not None and not math.isfinite(v_momentum):
        v_momentum = None
    return v_momentum
