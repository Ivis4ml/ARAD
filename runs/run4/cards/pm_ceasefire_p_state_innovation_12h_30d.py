"""pm_ceasefire_p_state_innovation_12h_30d

机制：cand:ceasefire 族归一概率在决策时点前十二小时的均值，减去同一算子在前三十日上的均值。十二小时的选择使相邻两个决策时点（SC 日盘 15:00 收盘与夜盘次日 02:30 收盘，间隔约 11.5 与 12.5 小时）的取数窗口几乎不重叠，避免由窗口重叠人为制造的序列相关；三十日基线吸收该族因市场组成更替与平台成交规模变化带来的慢速漂移，使取值表示「停火概率相对近一个月的水平偏离」。取值为正表示地缘风险状态在缓解，据本机制应对应下一 session 更低的已实现波动率。算子取均值而非 last：last 在长短两个窗口上会读到同一个最近取值，创新量恒为零。

失败条件：以下任一情形出现时该特征在该时点无定义，应排除该决策点而不是记为零：（一）决策时点前十二小时内该族没有任何小时桶，短窗均值无定义；（二）决策时点减去三十日早于该族覆盖起点 2023-01-16，因此 discovery 段（2022-11-02 至 2024-12-31，共 1040 行）中约前三分之一的行必然无值，可用行数约为 690，任何按 1040 行给出的显著性都是错的；（三）该族约 21264 个小时桶分布于三年半区间，存在稀疏段，若三十日基线窗口内的有效小时数过少，基线本身由少数几个桶决定，创新量反映的是市场生命周期而非停火预期的变化。以下情形使特征有定义但结论不可用：（四）该族聚合的 410 个市场若在某段时间内由单一停火事件主导，概率水平接近零或一并长期停滞，创新量趋近于零且方差塌缩；（五）归一到 outcome_seq==1 一侧的语义若与「停火达成或延续」不一致，特征符号与声明的经济含义相反。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 adcec46e4b2aa801d2465445f847afa5b7f274027f4e7ff6c4a07ec3968e4591
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 30日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 2592000


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
    t_ceasefire_p_state_innovation, x_ceasefire_p_state_innovation = series["pm_market.cand:ceasefire:p"]
    end_ceasefire_p_state_innovation = decision_time - timedelta(seconds=0)
    v_ceasefire_p_state_innovation = _agg("mean", _window(t_ceasefire_p_state_innovation, x_ceasefire_p_state_innovation, end_ceasefire_p_state_innovation, 43200))
    far_ceasefire_p_state_innovation = _agg("mean", _window(t_ceasefire_p_state_innovation, x_ceasefire_p_state_innovation, end_ceasefire_p_state_innovation, 2592000))
    v_ceasefire_p_state_innovation = (v_ceasefire_p_state_innovation - far_ceasefire_p_state_innovation) if _ok(v_ceasefire_p_state_innovation) and _ok(far_ceasefire_p_state_innovation) else None
    if v_ceasefire_p_state_innovation is not None and not math.isfinite(v_ceasefire_p_state_innovation):
        v_ceasefire_p_state_innovation = None
    return v_ceasefire_p_state_innovation
