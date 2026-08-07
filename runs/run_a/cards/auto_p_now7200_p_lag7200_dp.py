"""auto_p_now7200_p_lag7200_dp

机制：闭市期间地缘族信念变化驱动开盘后的方向

失败条件：若该族信念变化与下一 session 收益无关，则本特征被证伪

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 402a32f74bc3db161e860de4be4dddc828d6eca01744768a5486a9a97aa1eb60
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 26时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 93600


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
    t_p_now, x_p_now = series["pm_market.cand:iran:p"]
    end_p_now = decision_time - timedelta(seconds=0)
    v_p_now = _agg("last", _window(t_p_now, x_p_now, end_p_now, 7200))
    v_p_now = v_p_now if _ok(v_p_now) else None
    if v_p_now is not None and not math.isfinite(v_p_now):
        v_p_now = None
    t_p_lag, x_p_lag = series["pm_market.cand:iran:p"]
    end_p_lag = decision_time - timedelta(seconds=86400)
    v_p_lag = _agg("last", _window(t_p_lag, x_p_lag, end_p_lag, 7200))
    v_p_lag = v_p_lag if _ok(v_p_lag) else None
    if v_p_lag is not None and not math.isfinite(v_p_lag):
        v_p_lag = None
    v_dp = (v_p_now - v_p_lag) if _ok(v_p_now) and _ok(v_p_lag) else None
    if v_dp is not None and not math.isfinite(v_dp):
        v_dp = None
    return v_dp
