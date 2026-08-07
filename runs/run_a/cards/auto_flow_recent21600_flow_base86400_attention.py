"""auto_flow_recent21600_flow_base86400_attention

机制：资金关注度：地缘族成交额相对自身基线抬升时，下一 session 方向可预测

失败条件：若关注度与下一 session 收益无关，则本特征被证伪

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 2c138cd3cdacbe827a4b55b41ce0b9982444f54250fbd424f5d4db819b5c5f35
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 1日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 86400


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
    t_flow_recent, x_flow_recent = series["pm_market.cand:israel:notional"]
    end_flow_recent = decision_time - timedelta(seconds=0)
    v_flow_recent = _agg("sum", _window(t_flow_recent, x_flow_recent, end_flow_recent, 21600))
    v_flow_recent = v_flow_recent if _ok(v_flow_recent) else None
    if v_flow_recent is not None and not math.isfinite(v_flow_recent):
        v_flow_recent = None
    t_flow_base, x_flow_base = series["pm_market.cand:israel:notional"]
    end_flow_base = decision_time - timedelta(seconds=0)
    v_flow_base = _agg("sum", _window(t_flow_base, x_flow_base, end_flow_base, 86400))
    v_flow_base = v_flow_base if _ok(v_flow_base) else None
    if v_flow_base is not None and not math.isfinite(v_flow_base):
        v_flow_base = None
    v_attention = (v_flow_recent / v_flow_base) if _ok(v_flow_recent) and _ok(v_flow_base) and v_flow_base != 0 else None
    if v_attention is not None and not math.isfinite(v_attention):
        v_attention = None
    return v_attention
