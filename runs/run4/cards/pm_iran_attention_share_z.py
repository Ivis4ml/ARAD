"""pm_iran_attention_share_z

机制：cand:iran 族一日成交金额占其 30 日成交金额的比例，再对该比例做 60 个日频样本的标准化，度量地缘风险注意力相对自身常态的集中程度。

失败条件：以下任一情形出现时该特征无定义或不可用：（1）30 日窗口内 cand:iran 族成交金额为 0，比例的分母为零；（2）决策时点早于该族序列起点 2023-01-09，或标准化窗口内互异样本数不足 20；（3）该族在标准化窗口内成交金额近似恒定，样本标准差趋于 0，使 z 值被放大为伪信号。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 5d01f9d664aad6716565e5e70b3f79f1daf2aa7fd896a8a0d8f196c1c41ee6b8
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 2161时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7779600


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


def _at_iran_attention_share(at: datetime, series: dict):
    """在任意过去时刻求 iran_attention_share 的值。参考分布要用它。"""
    t, x = series["pm_market.cand:iran:notional"]
    end = at - timedelta(seconds=3600)
    v_iran_notional_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.cand:iran:notional"]
    end = at - timedelta(seconds=3600)
    v_iran_notional_30d = _agg("sum", _window(t, x, end, 2592000))
    v_iran_attention_share = (v_iran_notional_1d / v_iran_notional_30d) if _ok(v_iran_notional_1d) and _ok(v_iran_notional_30d) and v_iran_notional_30d != 0 else None
    return v_iran_attention_share

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_iran_notional_1d, x_iran_notional_1d = series["pm_market.cand:iran:notional"]
    end_iran_notional_1d = decision_time - timedelta(seconds=3600)
    v_iran_notional_1d = _agg("sum", _window(t_iran_notional_1d, x_iran_notional_1d, end_iran_notional_1d, 86400))
    v_iran_notional_1d = v_iran_notional_1d if _ok(v_iran_notional_1d) else None
    if v_iran_notional_1d is not None and not math.isfinite(v_iran_notional_1d):
        v_iran_notional_1d = None
    t_iran_notional_30d, x_iran_notional_30d = series["pm_market.cand:iran:notional"]
    end_iran_notional_30d = decision_time - timedelta(seconds=3600)
    v_iran_notional_30d = _agg("sum", _window(t_iran_notional_30d, x_iran_notional_30d, end_iran_notional_30d, 2592000))
    v_iran_notional_30d = v_iran_notional_30d if _ok(v_iran_notional_30d) else None
    if v_iran_notional_30d is not None and not math.isfinite(v_iran_notional_30d):
        v_iran_notional_30d = None
    v_iran_attention_share = (v_iran_notional_1d / v_iran_notional_30d) if _ok(v_iran_notional_1d) and _ok(v_iran_notional_30d) and v_iran_notional_30d != 0 else None
    if v_iran_attention_share is not None and not math.isfinite(v_iran_attention_share):
        v_iran_attention_share = None
    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去
    samples_iran_attention_share_z = []
    for k in range(1, 60 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_iran_attention_share(past, series)
        if _ok(s):
            samples_iran_attention_share_z.append(s)
    distinct_iran_attention_share_z = len(set(samples_iran_attention_share_z))
    if not _ok(v_iran_attention_share) or distinct_iran_attention_share_z < 20:
        v_iran_attention_share_z = None
    else:
        mu = math.fsum(samples_iran_attention_share_z) / len(samples_iran_attention_share_z)
        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in samples_iran_attention_share_z) / (len(samples_iran_attention_share_z) - 1))
        v_iran_attention_share_z = ((v_iran_attention_share - mu) / sd) if sd > 0 else None
    if v_iran_attention_share_z is not None and not math.isfinite(v_iran_attention_share_z):
        v_iran_attention_share_z = None
    return v_iran_attention_share_z
