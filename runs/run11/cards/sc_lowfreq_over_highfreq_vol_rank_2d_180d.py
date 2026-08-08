"""sc_lowfreq_over_highfreq_vol_rank_2d_180d

机制：过去两日 log_return 的标准差（低频价格离散度）除以同一两日窗口内 realised_volatility 的均值（高频波动读数），得到一个在 realised_volatility 为逐 bar 波动读数这一前提下无量纲的比值，度量 bar 收益的自相关方向与强度：比值高对应正自相关即信息缓慢扩散，比值低对应负自相关即暂时性报价噪声。再取该比值在过去 180 个日历日、按 86400 秒采样得到的参考样本中的分位排名，取值域 [0,1]。取分位而非 z 分数，是因为该比值在分母接近零的清淡时段发散且尾部极重，分位排名把任一单个观测的杠杆约束在 [0,1] 内，代价是丢弃幅度信息，本机制只主张单调关系而不主张幅度线性，因此这一代价可以接受。两个窗口同取 172800 秒而非 86400 秒，是为了保证决策时点落在周末或长假之后时窗口内仍有足够的 bar 使标准差可估；两侧同步加宽不改变量纲的相消关系。

失败条件：该特征在以下情形下无意义或需要按语义不匹配回报：其一，realised_volatility 若为方差量纲或时段累积量而非逐 bar 波动读数，则比值不再无量纲，退化为波动水平的倒数，声明的 direction 随之反转，此时应回报语义不匹配而非机制被否定；其二，ratio 若不按 inputs 的先后顺序取前者除以后者，则比值取倒数，方向反转；其三，若过去 180 日采样网格上该比值的互异取值数不足 60，rank_pct 无法给出稳定分位，特征取值不可用。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 ca6c23e54c3cd2dc189407d0cb69d26481eb73a0162d1c1835e115cf1e3c5f48
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 182日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 15724800


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


def _at_lowfreq_over_highfreq(at: datetime, series: dict):
    """在任意过去时刻求 lowfreq_over_highfreq 的值。参考分布要用它。"""
    t, x = series["commodity_bar.log_return"]
    end = at - timedelta(seconds=0)
    v_r_std_2d = _agg("std", _window(t, x, end, 172800))
    t, x = series["commodity_bar.realised_volatility"]
    end = at - timedelta(seconds=0)
    v_rv_mean_2d = _agg("mean", _window(t, x, end, 172800))
    v_lowfreq_over_highfreq = (v_r_std_2d / v_rv_mean_2d) if _ok(v_r_std_2d) and _ok(v_rv_mean_2d) and v_rv_mean_2d != 0 else None
    return v_lowfreq_over_highfreq

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_r_std_2d, x_r_std_2d = series["commodity_bar.log_return"]
    end_r_std_2d = decision_time - timedelta(seconds=0)
    v_r_std_2d = _agg("std", _window(t_r_std_2d, x_r_std_2d, end_r_std_2d, 172800))
    v_r_std_2d = v_r_std_2d if _ok(v_r_std_2d) else None
    if v_r_std_2d is not None and not math.isfinite(v_r_std_2d):
        v_r_std_2d = None
    t_rv_mean_2d, x_rv_mean_2d = series["commodity_bar.realised_volatility"]
    end_rv_mean_2d = decision_time - timedelta(seconds=0)
    v_rv_mean_2d = _agg("mean", _window(t_rv_mean_2d, x_rv_mean_2d, end_rv_mean_2d, 172800))
    v_rv_mean_2d = v_rv_mean_2d if _ok(v_rv_mean_2d) else None
    if v_rv_mean_2d is not None and not math.isfinite(v_rv_mean_2d):
        v_rv_mean_2d = None
    v_lowfreq_over_highfreq = (v_r_std_2d / v_rv_mean_2d) if _ok(v_r_std_2d) and _ok(v_rv_mean_2d) and v_rv_mean_2d != 0 else None
    if v_lowfreq_over_highfreq is not None and not math.isfinite(v_lowfreq_over_highfreq):
        v_lowfreq_over_highfreq = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_diffusion_speed_rank = []
    for k in range(1, 180 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_lowfreq_over_highfreq(past, series)
        if _ok(s):
            samples_diffusion_speed_rank.append(s)
    distinct_diffusion_speed_rank = len(set(samples_diffusion_speed_rank))
    if not _ok(v_lowfreq_over_highfreq) or distinct_diffusion_speed_rank < 60:
        v_diffusion_speed_rank = None
    else:
        below = sum(1 for s in samples_diffusion_speed_rank if s < v_lowfreq_over_highfreq)
        tied = sum(1 for s in samples_diffusion_speed_rank if s == v_lowfreq_over_highfreq)
        v_diffusion_speed_rank = (below + 0.5 * tied) / len(samples_diffusion_speed_rank)
    if v_diffusion_speed_rank is not None and not math.isfinite(v_diffusion_speed_rank):
        v_diffusion_speed_rank = None
    return v_diffusion_speed_rank
