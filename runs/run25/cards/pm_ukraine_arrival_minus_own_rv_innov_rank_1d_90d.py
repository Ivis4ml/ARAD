"""pm_ukraine_arrival_minus_own_rv_innov_rank_1d_90d

机制：cand:ukraine 族最近 24 小时成交笔数的小时桶均值减去其前 30 日的同算子均值，得到外生供给中断信息到达强度相对自身常态的创新；取其在过去 90 个日历日、按 86400 秒采样的参考样本中的分位排名，得到有界的到达强度相对位置。对该品种的 realised_volatility 做完全相同的处理（1 日均值减 30 日基线均值，同一 90 日网格上取分位排名），得到该品种波动状态相对自身常态的相对位置。两个排名相减，度量外生信息到达超前于本品种价格吸收的程度。算子取 mean 而非 sum：innovation 在长短两个窗口上比较同一算子的取值，只有 mean 在两个不等长窗口间可比，sum 会把窗口长度差异误读为创新。采样步长取 86400 秒，使参考样本落在与决策时点相同的时段相位上，不把日盘收盘与夜盘收盘混入同一参考分布；90 个采样点满足分位排名对样本量的要求，同时相对 120 或 180 日的窗口减少预热损失 —— cand:ukraine 序列起于 2023-03-09，30 日基线加 90 日参考窗口意味着该特征约自 2023 年 7 月起可取值。两项均取 rank_pct 而非 zscore：预测市场成交笔数与商品已实现波动的创新都极重尾，标准化下单个事件日会获得不受约束的杠杆，分位排名把任一观测的影响界在 [0,1] 内，代价是丢弃幅度信息，本机制只主张单调关系不主张幅度线性。方向约定：difference 的 inputs 为 [ukr_arrival_rank, own_rv_rank] 时输出为前者减后者，取值高表示信息到达强度的相对上升超过本品种波动状态的相对上升。

失败条件：以下任一情形出现时该特征应判为无定义并置缺，而不是取零值或前值：（一）决策时点前 24 小时内 cand:ukraine 无成交桶，或前 30 日的桶数不足以估计基线，此时 ukr_arrival_innov 无定义；（二）任一 rank_pct 步骤在 90 日网格上的互异取值数少于 45，此时分位排名会因重复样本而塌缩到少数几个离散值；（三）该品种在窗口内因停市或主力换月缺少 bar，own_rv_innov 无定义。此外有一条语义依赖需回报：本规格假定 difference 的 inputs 为 [ukr_arrival_rank, own_rv_rank] 时输出为前者减后者；若解释器约定相反，特征符号整体反转，direction 应随之取 -1，这属于需要回报的语义不匹配而非机制被证伪。另假定 realised_volatility 是逐 bar 的波动读数，故用 mean 作为窗口内的波动水平；若该字段是时段累积量，则 mean 与窗口内 bar 数量相关，两个不等长窗口间的创新含义改变，同属需要回报的语义不匹配。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 dae2b9b6a7cf56839e3c5cad68a12eeee553578ad03fae9a87e6b4622d50ca7d
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


def _at_ukr_arrival_innov(at: datetime, series: dict):
    """在任意过去时刻求 ukr_arrival_innov 的值。参考分布要用它。"""
    t, x = series["pm_market.cand:ukraine:trades"]
    end = at - timedelta(seconds=0)
    v_ukr_arrival_innov = _agg("mean", _window(t, x, end, 86400))
    far = _agg("mean", _window(t, x, end, 2592000))
    v_ukr_arrival_innov = (v_ukr_arrival_innov - far) if _ok(v_ukr_arrival_innov) and _ok(far) else None
    return v_ukr_arrival_innov

def _at_own_rv_innov(at: datetime, series: dict):
    """在任意过去时刻求 own_rv_innov 的值。参考分布要用它。"""
    t, x = series["commodity_bar.realised_volatility"]
    end = at - timedelta(seconds=0)
    v_own_rv_innov = _agg("mean", _window(t, x, end, 86400))
    far = _agg("mean", _window(t, x, end, 2592000))
    v_own_rv_innov = (v_own_rv_innov - far) if _ok(v_own_rv_innov) and _ok(far) else None
    return v_own_rv_innov

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_ukr_arrival_innov, x_ukr_arrival_innov = series["pm_market.cand:ukraine:trades"]
    end_ukr_arrival_innov = decision_time - timedelta(seconds=0)
    v_ukr_arrival_innov = _agg("mean", _window(t_ukr_arrival_innov, x_ukr_arrival_innov, end_ukr_arrival_innov, 86400))
    far_ukr_arrival_innov = _agg("mean", _window(t_ukr_arrival_innov, x_ukr_arrival_innov, end_ukr_arrival_innov, 2592000))
    v_ukr_arrival_innov = (v_ukr_arrival_innov - far_ukr_arrival_innov) if _ok(v_ukr_arrival_innov) and _ok(far_ukr_arrival_innov) else None
    if v_ukr_arrival_innov is not None and not math.isfinite(v_ukr_arrival_innov):
        v_ukr_arrival_innov = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_ukr_arrival_rank = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_ukr_arrival_innov(past, series)
        if _ok(s):
            samples_ukr_arrival_rank.append(s)
    distinct_ukr_arrival_rank = len(set(samples_ukr_arrival_rank))
    if not _ok(v_ukr_arrival_innov) or distinct_ukr_arrival_rank < 45:
        v_ukr_arrival_rank = None
    else:
        below = sum(1 for s in samples_ukr_arrival_rank if s < v_ukr_arrival_innov)
        tied = sum(1 for s in samples_ukr_arrival_rank if s == v_ukr_arrival_innov)
        v_ukr_arrival_rank = (below + 0.5 * tied) / len(samples_ukr_arrival_rank)
    if v_ukr_arrival_rank is not None and not math.isfinite(v_ukr_arrival_rank):
        v_ukr_arrival_rank = None
    t_own_rv_innov, x_own_rv_innov = series["commodity_bar.realised_volatility"]
    end_own_rv_innov = decision_time - timedelta(seconds=0)
    v_own_rv_innov = _agg("mean", _window(t_own_rv_innov, x_own_rv_innov, end_own_rv_innov, 86400))
    far_own_rv_innov = _agg("mean", _window(t_own_rv_innov, x_own_rv_innov, end_own_rv_innov, 2592000))
    v_own_rv_innov = (v_own_rv_innov - far_own_rv_innov) if _ok(v_own_rv_innov) and _ok(far_own_rv_innov) else None
    if v_own_rv_innov is not None and not math.isfinite(v_own_rv_innov):
        v_own_rv_innov = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_own_rv_rank = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_own_rv_innov(past, series)
        if _ok(s):
            samples_own_rv_rank.append(s)
    distinct_own_rv_rank = len(set(samples_own_rv_rank))
    if not _ok(v_own_rv_innov) or distinct_own_rv_rank < 45:
        v_own_rv_rank = None
    else:
        below = sum(1 for s in samples_own_rv_rank if s < v_own_rv_innov)
        tied = sum(1 for s in samples_own_rv_rank if s == v_own_rv_innov)
        v_own_rv_rank = (below + 0.5 * tied) / len(samples_own_rv_rank)
    if v_own_rv_rank is not None and not math.isfinite(v_own_rv_rank):
        v_own_rv_rank = None
    v_arrival_absorption_gap = (v_ukr_arrival_rank - v_own_rv_rank) if _ok(v_ukr_arrival_rank) and _ok(v_own_rv_rank) else None
    if v_arrival_absorption_gap is not None and not math.isfinite(v_arrival_absorption_gap):
        v_arrival_absorption_gap = None
    return v_arrival_absorption_gap
