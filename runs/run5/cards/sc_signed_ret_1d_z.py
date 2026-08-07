"""sc_signed_ret_1d_z

机制：截至决策时点前一日的有符号累计对数收益，用同一采样网格上的历史分布做 zscore 归一。取值为正表示近一日净上行，为负表示净下行；归一只改变量纲，不改变符号，因此该特征在 sign_unit 仓位下有可检验的方向。

失败条件：若参考网格上的互异取值数不足 min_samples（长假停市或主力合约换月造成的空窗、以及采样点落在非交易日导致的重复读数），该时点不产出特征值，不得以零、前值或截面均值填充；若填充，标准差被压低而 z 被放大，检验到的将是采样伪影而非机制。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 85c3737c256a58fcf201e634e87775d502e5ac36da008cf7e1548479f0dfbcd2
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 251日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 21686400


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


def _at_ret_1d(at: datetime, series: dict):
    """在任意过去时刻求 ret_1d 的值。参考分布要用它。"""
    t, x = series["commodity_bar.log_return"]
    end = at - timedelta(seconds=0)
    v_ret_1d = _agg("sum", _window(t, x, end, 86400))
    return v_ret_1d

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_ret_1d, x_ret_1d = series["commodity_bar.log_return"]
    end_ret_1d = decision_time - timedelta(seconds=0)
    v_ret_1d = _agg("sum", _window(t_ret_1d, x_ret_1d, end_ret_1d, 86400))
    v_ret_1d = v_ret_1d if _ok(v_ret_1d) else None
    if v_ret_1d is not None and not math.isfinite(v_ret_1d):
        v_ret_1d = None
    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去
    samples_ret_1d_z = []
    for k in range(1, 250 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_ret_1d(past, series)
        if _ok(s):
            samples_ret_1d_z.append(s)
    distinct_ret_1d_z = len(set(samples_ret_1d_z))
    if not _ok(v_ret_1d) or distinct_ret_1d_z < 100:
        v_ret_1d_z = None
    else:
        mu = math.fsum(samples_ret_1d_z) / len(samples_ret_1d_z)
        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in samples_ret_1d_z) / (len(samples_ret_1d_z) - 1))
        v_ret_1d_z = ((v_ret_1d - mu) / sd) if sd > 0 else None
    if v_ret_1d_z is not None and not math.isfinite(v_ret_1d_z):
        v_ret_1d_z = None
    return v_ret_1d_z
