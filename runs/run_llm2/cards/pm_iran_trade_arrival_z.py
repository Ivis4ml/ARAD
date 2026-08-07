"""pm_iran_trade_arrival_z

机制：以 cand:iran 族最近一日的成交笔数相对其一个月基线的异动，度量霍尔木兹与红海供给中断风险上的信息到达强度，再用近九十日的同类取值把该异动标准化，以消除该族成交规模在 2023 至 2024 年间的量级漂移。取值越高表示进入该风险市场的新信息越多，据混合分布假说应对应下一时段更高的已实现波动率。

失败条件：以下任一情形出现即认为该特征在该时点不可用或不成立：一，参考分布的互异取值少于 20 个（该族在 2023-01-09 之前无数据，序列起始的九十日内必然如此），此时不应产生取值；二，参考期内成交笔数近乎恒定使标准差趋近于零，导致 z 值被放大到与信息到达强度无关的量级；三，该族在某段时间内因市场集中到期而成交枯竭，此时异动反映的是市场生命周期而非外部信息到达。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 5d075ccab77331a8775384b952355704146a323beaf5175f594f70e1628886e1
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 120日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 10368000


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


def _at_iran_trade_burst(at: datetime, series: dict):
    """在任意过去时刻求 iran_trade_burst 的值。zscore 的参考分布要用它。"""
    t, x = series["pm_market.cand:iran:trades"]
    end = at - timedelta(seconds=0)
    v_iran_trade_burst = _agg("sum", _window(t, x, end, 86400))
    far = _agg("sum", _window(t, x, end, 2592000))
    v_iran_trade_burst = (v_iran_trade_burst - far) if _ok(v_iran_trade_burst) and _ok(far) else None
    return v_iran_trade_burst

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_iran_trade_burst, x_iran_trade_burst = series["pm_market.cand:iran:trades"]
    end_iran_trade_burst = decision_time - timedelta(seconds=0)
    v_iran_trade_burst = _agg("sum", _window(t_iran_trade_burst, x_iran_trade_burst, end_iran_trade_burst, 86400))
    far_iran_trade_burst = _agg("sum", _window(t_iran_trade_burst, x_iran_trade_burst, end_iran_trade_burst, 2592000))
    v_iran_trade_burst = (v_iran_trade_burst - far_iran_trade_burst) if _ok(v_iran_trade_burst) and _ok(far_iran_trade_burst) else None
    if v_iran_trade_burst is not None and not math.isfinite(v_iran_trade_burst):
        v_iran_trade_burst = None
    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去
    samples_iran_trade_burst_z = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_iran_trade_burst(past, series)
        if _ok(s):
            samples_iran_trade_burst_z.append(s)
    distinct_iran_trade_burst_z = len(set(samples_iran_trade_burst_z))
    if not _ok(v_iran_trade_burst) or distinct_iran_trade_burst_z < 20:
        v_iran_trade_burst_z = None
    else:
        mu = math.fsum(samples_iran_trade_burst_z) / len(samples_iran_trade_burst_z)
        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in samples_iran_trade_burst_z) / (len(samples_iran_trade_burst_z) - 1))
        v_iran_trade_burst_z = ((v_iran_trade_burst - mu) / sd) if sd > 0 else None
    if v_iran_trade_burst_z is not None and not math.isfinite(v_iran_trade_burst_z):
        v_iran_trade_burst_z = None
    return v_iran_trade_burst_z
