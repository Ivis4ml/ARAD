"""pm_up_closed_window_arrival_rank_6h_off6h_90d

机制：cand:up 族在决策时点之前第二个六小时区间内的成交笔数之和，再取其在过去 90 个日历日、按 86400 秒采样得到的参考样本中的分位排名，取值域 [0,1]。窗口取 window_seconds=21600 且 offset_seconds=21600，使区间落在本面板停市的时段上（15:00 决策时点对应 03:00 至 09:00，02:30 决策时点对应前一日 14:30 至 20:30），并使相邻两个决策时点的区间互不重叠。算子取 sum 而非 mean：成交笔数是流量，同长度窗口之间求和可比，且 sum 直接对应信息到达的总次数。归一取 rank_pct 而非 zscore：预测市场成交笔数极重尾，且平台规模在 2023 至 2024 年间有数量级增长，标准化下单个事件日会获得不受约束的杠杆，分位排名把任一单个观测的影响界在 [0,1] 内并自动吸收慢速的规模漂移，代价是丢弃幅度信息，本机制只主张单调关系不主张幅度线性。采样步长取 86400 秒，使参考样本落在与决策时点相同的时钟相位上，不把日盘收盘对应的 03:00 至 09:00 区间与夜盘收盘对应的 14:30 至 20:30 区间混入同一个参考分布，这一点对本构造尤为重要，因为这两个区间分别对应美东晚间与欧洲上午，活动水平的日内差异很大。参考窗口取 90 日给出 90 个采样点，min_samples 取 40：该值必须计互异取值，而 cand:up 族约每日 13.1 个小时桶，六小时窗口内期望约 3.3 桶，清淡相位上参考样本中会出现零值并造成平局，取 40 是在预热损失与平局容忍之间的取舍。参考窗口的日采样点包含周末时刻，周末的采样值与工作日不完全同分布，这会给参考分布带来噪声，但不改变分位排名的符号方向。

失败条件：构造层面的失败有三种可判据的形态。第一，参考分布退化：若 90 个日采样点中互异取值不足 40，rank_pct 无法取值，相应决策时点被丢弃；若因此可取值的决策时点少于 600 个，该特征在本样本上功效不足，应判构造失败而非机制被检验。第二，特征退化为常数：若 cand:up:trades 在 03:00 至 09:00 或 14:30 至 20:30 这两个时钟相位上系统性为零，分位排名将大量塌缩到平局值，特征的互异取值数远小于行数，此时任何系数都不可解释。第三，方向约定被违反：本特征约定取值越高表示停市区间内的信息到达强度相对自身近 90 日同相位历史越高；若解释器对 rank_pct 的输出取的是降序分位，方向随之反转，属需要回报的语义不匹配。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 63f857330d91d566519e191709d4955c5679e9880ea7437c458cf90dbf7f5f3f
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 2172时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7819200


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


def _at_up_trades_closed_6h(at: datetime, series: dict):
    """在任意过去时刻求 up_trades_closed_6h 的值。参考分布要用它。"""
    t, x = series["pm_market.cand:up:trades"]
    end = at - timedelta(seconds=21600)
    v_up_trades_closed_6h = _agg("sum", _window(t, x, end, 21600))
    return v_up_trades_closed_6h

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_up_trades_closed_6h, x_up_trades_closed_6h = series["pm_market.cand:up:trades"]
    end_up_trades_closed_6h = decision_time - timedelta(seconds=21600)
    v_up_trades_closed_6h = _agg("sum", _window(t_up_trades_closed_6h, x_up_trades_closed_6h, end_up_trades_closed_6h, 21600))
    v_up_trades_closed_6h = v_up_trades_closed_6h if _ok(v_up_trades_closed_6h) else None
    if v_up_trades_closed_6h is not None and not math.isfinite(v_up_trades_closed_6h):
        v_up_trades_closed_6h = None
    # rank_pct：与 zscore 同一张采样网格，只是归一方式不同
    samples_closed_window_arrival_rank = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_up_trades_closed_6h(past, series)
        if _ok(s):
            samples_closed_window_arrival_rank.append(s)
    distinct_closed_window_arrival_rank = len(set(samples_closed_window_arrival_rank))
    if not _ok(v_up_trades_closed_6h) or distinct_closed_window_arrival_rank < 40:
        v_closed_window_arrival_rank = None
    else:
        below = sum(1 for s in samples_closed_window_arrival_rank if s < v_up_trades_closed_6h)
        tied = sum(1 for s in samples_closed_window_arrival_rank if s == v_up_trades_closed_6h)
        v_closed_window_arrival_rank = (below + 0.5 * tied) / len(samples_closed_window_arrival_rank)
    if v_closed_window_arrival_rank is not None and not math.isfinite(v_closed_window_arrival_rank):
        v_closed_window_arrival_rank = None
    return v_closed_window_arrival_rank
