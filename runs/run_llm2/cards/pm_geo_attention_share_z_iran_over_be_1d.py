"""pm_geo_attention_share_z_iran_over_be_1d

机制：地缘冲突族（cand:iran）相对娱乐基准族（cand:be）的日度名义成交额份额，经 90 日滚动标准化。份额而非绝对量，用以剔除平台整体活跃度增长与全平台性的新闻日抬升；标准化用以剔除份额的慢速漂移。取值越高，表示对中东供给中断风险的定价注意力越集中。

失败条件：以下任一情形出现，该特征在该时点无效：(1) be_notional_1d 在窗口内为零或缺失，导致比值无定义 —— cand:be 覆盖始于 2022-12-12，数据起点 2022-11-02 之前的约 6 周（约占 1040 行的 7%）必然无值；(2) cand:iran 覆盖始于 2023-01-09，此前 iran_notional_1d 恒为零，比值退化为常数零，标准化后无信息；(3) 90 日回看窗口内 geo_share 的互异取值少于 20 个，标准差被重复样本压低而放大 z 值。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 4dcef77d23f1f171da5ecccdb69469cf074e18e51089044a8ed79ee9e2343d4e
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 2185时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7866000


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


def _at_geo_share(at: datetime, series: dict):
    """在任意过去时刻求 geo_share 的值。zscore 的参考分布要用它。"""
    t, x = series["pm_market.cand:iran:notional"]
    end = at - timedelta(seconds=3600)
    v_iran_notional_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.cand:be:notional"]
    end = at - timedelta(seconds=3600)
    v_be_notional_1d = _agg("sum", _window(t, x, end, 86400))
    v_geo_share = (v_iran_notional_1d / v_be_notional_1d) if _ok(v_iran_notional_1d) and _ok(v_be_notional_1d) and v_be_notional_1d != 0 else None
    return v_geo_share

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
    t_be_notional_1d, x_be_notional_1d = series["pm_market.cand:be:notional"]
    end_be_notional_1d = decision_time - timedelta(seconds=3600)
    v_be_notional_1d = _agg("sum", _window(t_be_notional_1d, x_be_notional_1d, end_be_notional_1d, 86400))
    v_be_notional_1d = v_be_notional_1d if _ok(v_be_notional_1d) else None
    if v_be_notional_1d is not None and not math.isfinite(v_be_notional_1d):
        v_be_notional_1d = None
    v_geo_share = (v_iran_notional_1d / v_be_notional_1d) if _ok(v_iran_notional_1d) and _ok(v_be_notional_1d) and v_be_notional_1d != 0 else None
    if v_geo_share is not None and not math.isfinite(v_geo_share):
        v_geo_share = None
    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去
    samples_geo_share_z = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_geo_share(past, series)
        if _ok(s):
            samples_geo_share_z.append(s)
    distinct_geo_share_z = len(set(samples_geo_share_z))
    if not _ok(v_geo_share) or distinct_geo_share_z < 20:
        v_geo_share_z = None
    else:
        mu = math.fsum(samples_geo_share_z) / len(samples_geo_share_z)
        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in samples_geo_share_z) / (len(samples_geo_share_z) - 1))
        v_geo_share_z = ((v_geo_share - mu) / sd) if sd > 0 else None
    if v_geo_share_z is not None and not math.isfinite(v_geo_share_z):
        v_geo_share_z = None
    return v_geo_share_z
