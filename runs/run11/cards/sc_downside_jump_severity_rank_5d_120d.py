"""sc_downside_jump_severity_rank_5d_120d

机制：过去 5 个日历日内 log_return 的最小值（最不利单根 bar 的有符号位移）除以同窗口 realised_volatility 的均值（扩散波动尺度），得到无量纲的下行尾部严重度；再取其在过去 120 个日历日、按 86400 秒采样的参考样本中的分位排名，取值域 [0,1]。分子只取极小值而非求和，度量的是离散跳跃而非累积漂移；分母只提供正的尺度，不改变符号次序。采样步长取 86400 秒，使参考样本落在与决策时点相同的时段相位上，不把日盘收盘与夜盘收盘混入同一参考分布。取分位而非 zscore：分母在清淡时段接近零时比值发散，标准化下单个清淡日会获得不受约束的杠杆，分位排名把任一观测的影响界在 [0,1] 内，代价是丢弃幅度信息，本机制只主张单调关系不主张幅度线性。参考窗口取 120 日而非 180 日，以减少面板上逐品种重复支付的预热损失。

失败条件：rv_scale_5d 在停市、涨跌停封板或极端清淡的窗口上取到零或接近零，使 downside_jump_norm 发散或不可计算；或参考窗口内 downside_jump_norm 的互异取值少于 40 个（品种上市未满 120 日、或窗口内多数采样点读到同一批 bar 而塌缩成重复值），此时 rank_pct 无定义，该观测应被剔除而非以边界值填充。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 5b2fb648e479b8f074ce4a67dceab33d98e18db55cf6bfa15a26596a23f75aaf
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 125日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 10800000


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


def _at_downside_jump_norm(at: datetime, series: dict):
    """在任意过去时刻求 downside_jump_norm 的值。参考分布要用它。"""
    t, x = series["commodity_bar.log_return"]
    end = at - timedelta(seconds=0)
    v_min_ret_5d = _agg("min", _window(t, x, end, 432000))
    t, x = series["commodity_bar.realised_volatility"]
    end = at - timedelta(seconds=0)
    v_rv_scale_5d = _agg("mean", _window(t, x, end, 432000))
    v_downside_jump_norm = (v_min_ret_5d / v_rv_scale_5d) if _ok(v_min_ret_5d) and _ok(v_rv_scale_5d) and v_rv_scale_5d != 0 else None
    return v_downside_jump_norm

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_min_ret_5d, x_min_ret_5d = series["commodity_bar.log_return"]
    end_min_ret_5d = decision_time - timedelta(seconds=0)
    v_min_ret_5d = _agg("min", _window(t_min_ret_5d, x_min_ret_5d, end_min_ret_5d, 432000))
    v_min_ret_5d = v_min_ret_5d if _ok(v_min_ret_5d) else None
    if v_min_ret_5d is not None and not math.isfinite(v_min_ret_5d):
        v_min_ret_5d = None
    t_rv_scale_5d, x_rv_scale_5d = series["commodity_bar.realised_volatility"]
    end_rv_scale_5d = decision_time - timedelta(seconds=0)
    v_rv_scale_5d = _agg("mean", _window(t_rv_scale_5d, x_rv_scale_5d, end_rv_scale_5d, 432000))
    v_rv_scale_5d = v_rv_scale_5d if _ok(v_rv_scale_5d) else None
    if v_rv_scale_5d is not None and not math.isfinite(v_rv_scale_5d):
        v_rv_scale_5d = None
    v_downside_jump_norm = (v_min_ret_5d / v_rv_scale_5d) if _ok(v_min_ret_5d) and _ok(v_rv_scale_5d) and v_rv_scale_5d != 0 else None
    if v_downside_jump_norm is not None and not math.isfinite(v_downside_jump_norm):
        v_downside_jump_norm = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_downside_jump_severity = []
    for k in range(1, 120 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_downside_jump_norm(past, series)
        if _ok(s):
            samples_downside_jump_severity.append(s)
    distinct_downside_jump_severity = len(set(samples_downside_jump_severity))
    if not _ok(v_downside_jump_norm) or distinct_downside_jump_severity < 40:
        v_downside_jump_severity = None
    else:
        below = sum(1 for s in samples_downside_jump_severity if s < v_downside_jump_norm)
        tied = sum(1 for s in samples_downside_jump_severity if s == v_downside_jump_norm)
        v_downside_jump_severity = (below + 0.5 * tied) / len(samples_downside_jump_severity)
    if v_downside_jump_severity is not None and not math.isfinite(v_downside_jump_severity):
        v_downside_jump_severity = None
    return v_downside_jump_severity
