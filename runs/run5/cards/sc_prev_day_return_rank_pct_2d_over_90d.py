"""sc_prev_day_return_rank_pct_2d_over_90d

机制：上一交易日累计对数收益在其自身过去 90 天分布中的分位排名，度量近期已完成的同向定价冲击的相对强度

失败条件：若 172800 秒回看窗口内没有任何已结束的 session，该决策时点无定义；若参考样本被长假截断到少于 40 个互异取值，该点同样无定义。以上两种无定义只取决于特征与历史数据，与标签无关。若分位排名与下一 session 的对数收益之间不存在负向关系，则本特征被证伪。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 69f87bfde2959951d73cf2bd765bb0689ffd620152b3cbf57e8e5f61b9d54a7b
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 92日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7948800


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


def _at_ret_prev_day(at: datetime, series: dict):
    """在任意过去时刻求 ret_prev_day 的值。参考分布要用它。"""
    t, x = series["commodity_bar.log_return"]
    end = at - timedelta(seconds=0)
    v_ret_prev_day = _agg("sum", _window(t, x, end, 172800))
    return v_ret_prev_day

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_ret_prev_day, x_ret_prev_day = series["commodity_bar.log_return"]
    end_ret_prev_day = decision_time - timedelta(seconds=0)
    v_ret_prev_day = _agg("sum", _window(t_ret_prev_day, x_ret_prev_day, end_ret_prev_day, 172800))
    v_ret_prev_day = v_ret_prev_day if _ok(v_ret_prev_day) else None
    if v_ret_prev_day is not None and not math.isfinite(v_ret_prev_day):
        v_ret_prev_day = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_ret_prev_day_rank = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_ret_prev_day(past, series)
        if _ok(s):
            samples_ret_prev_day_rank.append(s)
    distinct_ret_prev_day_rank = len(set(samples_ret_prev_day_rank))
    if not _ok(v_ret_prev_day) or distinct_ret_prev_day_rank < 40:
        v_ret_prev_day_rank = None
    else:
        below = sum(1 for s in samples_ret_prev_day_rank if s < v_ret_prev_day)
        tied = sum(1 for s in samples_ret_prev_day_rank if s == v_ret_prev_day)
        v_ret_prev_day_rank = (below + 0.5 * tied) / len(samples_ret_prev_day_rank)
    if v_ret_prev_day_rank is not None and not math.isfinite(v_ret_prev_day_rank):
        v_ret_prev_day_rank = None
    return v_ret_prev_day_rank
