"""pm_dip_barrier_pricing_closed_6h_over_norm_resid_own_rv_90d

机制：s1 取 cand:dip:p 在 window_seconds=21600 且 offset_seconds=21600 的区间内的均值，即决策时点之前第二个六小时区间内该族归一化概率的典型水平；该区间在本合约的两类收盘几何下分别为 03:00 至 09:00 与前一日 14:30 至 20:30，都落在停市时段内，且相邻两个决策时点的该区间互不重叠。算子取 mean 而非 last：该族在同一小时桶内含多个不同阈值的并行合约，last 只读到最后写入的那一个，取值将由合约写入次序而非定价决定；算子也不取 max 或 min：极值只由单个桶决定并随窗口内桶数单调，不是水平的稳健读数。该族约每日 13 个小时桶，六小时区间内期望约 3.3 个桶，mean 在该样本量上仍有定义，个别区间只有一个桶时 mean 退化为该桶的取值，属于噪声而非发散。s2 取同一字段在 window_seconds=2592000 内的均值，即该族障碍触及定价在近一个月内的常态水平，30 日窗口内约 390 个桶，均值对任一单桶不敏感，塌缩到零的风险可忽略。s3 为 ratio，inputs 为 [dip_p_closed_6h, dip_p_level_30d]，输出为前者除以后者，取值大于 1 表示停市区间的下行触及定价高于该族自身近一个月常态。取比值而非取差：该族由不同阈值的合约构成，阈值集合随标的价格水平推移而整体更替，这一更替对全族概率水平的影响近似乘性，比值使该成分一阶抵消，差分则不能；同时比值无量纲，与该族的绝对概率水平无关。不使用 innovation 承载本构造：innovation 给出的是同一算子在长短两窗口上的差，是加性归一，与此处需要的乘性归一不同，且其基线窗口嵌套于短窗口之外的设定无法表达「相对自身常态的倍数」。s4 把 s3 对已登记的基线控制 own_realised_volatility 做残差化。控制取 own_realised_volatility 而非 brent：标签是已实现波动率，其最强的基线解释是本品种自身的波动持续性，本特征要主张的正是相对该自回归基线的增量；brent 控制的是价格维度，与本特征所在的波动维度不同构。只做一次残差化而不串联第二次：串联后的残差只与最后一个控制正交，并不给出对两个控制同时正交的量，却要多付一层预热。参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测。采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把日盘 15:00 收盘与夜盘 02:30 收盘混入同一拟合样本：这两个相位对应的停市区间分别落在欧洲上午与美东白天到晚间，全球风险资产的活跃程度与本品种自身的已实现波动水平在两段上差异很大，混相位拟合会得到一个对两者都不成立的平均斜率。参考窗口取 90 日而非更短，是为了不让个别事件日主导斜率估计；取 90 日而非 180 日，是为了在 cand:dip 序列起于 2023-03-28 且还要先付 30 日窗口的前提下减少预热损失，该特征约自 2023 年 7 月下旬起可取值。min_samples 取 40，计控制变量的互异取值：已实现波动是连续量，90 个日采样点上互异取值通常远多于 40，该阈值主要用于排除序列起始处预热不足与长假造成的取值塌缩；该阈值只约束控制侧，对特征侧的取值退化不提供保护。输出为残差，不再取 rank_pct 或 zscore：残差在拟合窗口上均值为零，这个零点是构造性的，正号表示停市期间的下行触及定价超出本品种自身波动状态所能解释的部分，负号表示不足，符号本身是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的读法失效。

失败条件：一，特征侧退化：若 cand:dip 在某个停市六小时区间内没有任何小时桶，s1 无定义，该观测缺失；若只有一个桶，s1 等于该桶取值，比值的噪声显著上升。该族约每日 13 个小时桶，按此密度六小时区间为空的比例不高，但在该族清淡的月份会成批出现，若缺失或单桶观测超过全样本的四分之一，本特征的有效样本量不足以支撑越过 2.5376 的地板，应判为不可评价而非不成立。二，分母侧退化：若 s2 在某段时间接近零（该族全部合约的归一化概率同时贴近零），比值发散，单个观测会获得不受约束的杠杆；由于输出为残差而非分位排名，此处没有 [0,1] 的界作保护，若出现此情形应在诊断中报告并按剔除极端观测后的估计重读。三，语义不匹配：假定 cand:dip 族归一到 outcome_seq==1 一侧时对应的是「触及下行阈值」一侧。若该族的归一方向相反，本特征读到的实际是上行触及定价，direction=1 随之读错方向，属于需要回报的语义不匹配。四，族的语义连贯性：假定该族由 dip 与若干阈值价位词聚成，其成员确为下行阈值触及合约。若该族并入了与阈值触及无关但含同一词干的合约，则 s1 与 s2 度量的不再是障碍触及定价，机制的经济解释失效。五，控制侧不可识别：若 own_realised_volatility 在 90 个日采样点上的互异取值少于 40，斜率不可识别，该观测缺失。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 7c750b8d629526c8f08898457daf8558f17eb06909da954a44b45ae51f048fab
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


def _at_dip_p_closed_over_norm(at: datetime, series: dict):
    """在任意过去时刻求 dip_p_closed_over_norm 的值。参考分布要用它。"""
    t, x = series["pm_market.cand:dip:p"]
    end = at - timedelta(seconds=21600)
    v_dip_p_closed_6h = _agg("mean", _window(t, x, end, 21600))
    t, x = series["pm_market.cand:dip:p"]
    end = at - timedelta(seconds=0)
    v_dip_p_level_30d = _agg("mean", _window(t, x, end, 2592000))
    v_dip_p_closed_over_norm = (v_dip_p_closed_6h / v_dip_p_level_30d) if _ok(v_dip_p_closed_6h) and _ok(v_dip_p_level_30d) and v_dip_p_level_30d != 0 else None
    return v_dip_p_closed_over_norm

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_dip_p_closed_6h, x_dip_p_closed_6h = series["pm_market.cand:dip:p"]
    end_dip_p_closed_6h = decision_time - timedelta(seconds=21600)
    v_dip_p_closed_6h = _agg("mean", _window(t_dip_p_closed_6h, x_dip_p_closed_6h, end_dip_p_closed_6h, 21600))
    v_dip_p_closed_6h = v_dip_p_closed_6h if _ok(v_dip_p_closed_6h) else None
    if v_dip_p_closed_6h is not None and not math.isfinite(v_dip_p_closed_6h):
        v_dip_p_closed_6h = None
    t_dip_p_level_30d, x_dip_p_level_30d = series["pm_market.cand:dip:p"]
    end_dip_p_level_30d = decision_time - timedelta(seconds=0)
    v_dip_p_level_30d = _agg("mean", _window(t_dip_p_level_30d, x_dip_p_level_30d, end_dip_p_level_30d, 2592000))
    v_dip_p_level_30d = v_dip_p_level_30d if _ok(v_dip_p_level_30d) else None
    if v_dip_p_level_30d is not None and not math.isfinite(v_dip_p_level_30d):
        v_dip_p_level_30d = None
    v_dip_p_closed_over_norm = (v_dip_p_closed_6h / v_dip_p_level_30d) if _ok(v_dip_p_closed_6h) and _ok(v_dip_p_level_30d) and v_dip_p_level_30d != 0 else None
    if v_dip_p_closed_over_norm is not None and not math.isfinite(v_dip_p_closed_over_norm):
        v_dip_p_closed_over_norm = None
    # residualise：拟合样本严格取自决策时点之前，逐点重拟合
    tc_dip_barrier_pricing_resid_own_rv, xc_dip_barrier_pricing_resid_own_rv = series["commodity_bar.realised_volatility"]
    xs_dip_barrier_pricing_resid_own_rv, cs_dip_barrier_pricing_resid_own_rv = [], []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_dip_p_closed_over_norm(past, series)
        cw = _window(tc_dip_barrier_pricing_resid_own_rv, xc_dip_barrier_pricing_resid_own_rv, past, 7776000)
        cv = cw[-1] if cw else None
        if _ok(xv) and _ok(cv):
            xs_dip_barrier_pricing_resid_own_rv.append(xv)
            cs_dip_barrier_pricing_resid_own_rv.append(cv)
    cw0 = _window(tc_dip_barrier_pricing_resid_own_rv, xc_dip_barrier_pricing_resid_own_rv, decision_time, 7776000)
    c0 = cw0[-1] if cw0 else None
    if not _ok(v_dip_p_closed_over_norm) or not _ok(c0) or len(set(cs_dip_barrier_pricing_resid_own_rv)) < 40:
        v_dip_barrier_pricing_resid_own_rv = None
    else:
        cbar = math.fsum(cs_dip_barrier_pricing_resid_own_rv) / len(cs_dip_barrier_pricing_resid_own_rv)
        xbar = math.fsum(xs_dip_barrier_pricing_resid_own_rv) / len(xs_dip_barrier_pricing_resid_own_rv)
        scc = math.fsum((c - cbar) ** 2 for c in cs_dip_barrier_pricing_resid_own_rv)
        if scc <= 0:
            v_dip_barrier_pricing_resid_own_rv = None
        else:
            b = math.fsum((c - cbar) * (x - xbar) for c, x in zip(cs_dip_barrier_pricing_resid_own_rv, xs_dip_barrier_pricing_resid_own_rv, strict=True)) / scc
            v_dip_barrier_pricing_resid_own_rv = v_dip_p_closed_over_norm - (xbar + b * (c0 - cbar))
    if v_dip_barrier_pricing_resid_own_rv is not None and not math.isfinite(v_dip_barrier_pricing_resid_own_rv):
        v_dip_barrier_pricing_resid_own_rv = None
    return v_dip_barrier_pricing_resid_own_rv
