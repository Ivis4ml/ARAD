"""pm_iran_closure_p_innovation

机制：cand:iran 族在 SC 停市窗口（决策时点前六小时）内的平均概率，减去其此前三日的平均概率。度量的是停市期间伊朗局势信息使该族概率偏离自身近期水平的有符号幅度：为正表示停市期间风险概率被上修，为负表示被下修。

失败条件：该族在决策时点前六小时内没有任何小时桶时，短窗均值无定义，特征无定义，该决策点应被排除而不是记为零；决策时点减去回看深度早于 cand:iran 的覆盖起点 2023-01-09 时同样无定义，样本前段约两个月因此不可用。此外，若归一到 outcome_seq==1 一侧的概率在本族内并非对应「事件发生」，则该特征的符号与所声明的经济含义相反，此时即使斜率显著也不支持本机制。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 6ab8f5546c5f6099bebd4218201e7aa41c9e2b18a097ad9269a7e8c4f4b85bb8
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 3日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 259200


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
    t_iran_p_closure_innovation, x_iran_p_closure_innovation = series["pm_market.cand:iran:p"]
    end_iran_p_closure_innovation = decision_time - timedelta(seconds=0)
    v_iran_p_closure_innovation = _agg("mean", _window(t_iran_p_closure_innovation, x_iran_p_closure_innovation, end_iran_p_closure_innovation, 21600))
    far_iran_p_closure_innovation = _agg("mean", _window(t_iran_p_closure_innovation, x_iran_p_closure_innovation, end_iran_p_closure_innovation, 259200))
    v_iran_p_closure_innovation = (v_iran_p_closure_innovation - far_iran_p_closure_innovation) if _ok(v_iran_p_closure_innovation) and _ok(far_iran_p_closure_innovation) else None
    if v_iran_p_closure_innovation is not None and not math.isfinite(v_iran_p_closure_innovation):
        v_iran_p_closure_innovation = None
    return v_iran_p_closure_innovation
