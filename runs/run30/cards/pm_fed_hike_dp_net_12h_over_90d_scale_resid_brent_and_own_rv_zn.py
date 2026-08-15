"""pm_fed_hike_dp_net_12h_over_90d_scale_resid_brent_and_own_rv_zn

机制：s1 取 mech:FED_HIKE:dp 在决策时点前 43200 秒、不带偏移的区间内的求和。dp 是构成受控的分桶增量，窗口内求和在语义上等于该轴归一化概率在这 12 小时里的净变化，量纲为概率点，读作「加息发生的概率被净上修了多少」，有符号、以零为中性且零点是构造性的。窗口长度取 43200 秒是由决策网格几何定出的：日盘决策时点 08:59 与夜盘决策时点 20:59 相距 12 小时，该窗口把时间轴无重叠地分割，每个观测读到的恰是上一个可行动时刻之后新到达的那一段政策信息，相邻观测不共用任何分桶，机械自相关为零；不带偏移使与随后不可交易区间首尾相接的最新一段被完整包含。s2 取同一 source、同一 field 在决策时点前 7776000 秒内各分桶净变化的标准差（约 460 个桶），作为该轴自身的季度尺度。s3 为 ratio，inputs 顺序为分子在前、分母在后，输出无量纲、有符号、以零为中性，读作「自上一个决策时点以来的净鹰派重定价，以该轴自身季度单桶变化标准差为单位」。须记录一处量纲上的不精确：分子是约 2 至 3 个桶的和、分母是单桶尺度，两者相差一个与桶数平方根同量级的因子，故本读数不是严格的标准化统计量，而是以单桶尺度计量的净位移倍数；该因子恒正并随该族活动强度同向变动，只放大幅度不改变符号。s4 把 s3 对 brent 与 own_realised_volatility 两条已登记基线控制同时残差化，作用于特征一侧，标签仍是沪锌的名义下一时段收益，不构造任何超额收益标签；参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测，采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把 08:59 与 20:59 混入同一拟合样本 —— 两个相位下布伦特的活跃程度、沪锌对其的响应斜率与自身已实现波动水平差异很大，混相位拟合会得到一组对两者都不成立的平均斜率。输出为残差，不再取 rank_pct 或 zscore：s3 的零点是构造性的，符号是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的仓位映射读错方向，同时丢弃使排除界可以按经济量陈述的量纲。残差为正表示加息概率的净上修超出国际油价变动与沪锌自身波动状态两者共同所能解释的部分，按 direction=-1 对应更低的下一时段收益。

失败条件：本构造的语义假设有五条，任一条不成立都会使读数偏离所主张的经济量，届时结果与预期不符应归因于假设而非机制。第一，假定 mech:FED_HIKE:dp 是按「加息发生」极性同号化后的构成受控分桶增量，其窗口内求和等于该轴归一化概率的净变化；若同号化在某些成员上失效（例如降息档被错并入该轴），则符号被局部翻转，读数将向零收缩且在同号化失效集中的时期系统性偏离，此时否定读数不能归因于机制。第二，假定分桶时间戳按小时桶右端可用且早于决策时点；若某些桶的可用时刻晚于其标称右端，窗口会包含决策时点尚不可得的信息，此时正向读数不可信。第三，假定十二小时窗口内至少有一个有取值分桶，否则 s1 无定义、该决策时点进入排除清单；菜单给出该族 dp 在六小时窗口上的决策网格有定义比例为 0.5317，十二小时窗口应显著更高，若实测有定义比例低于 0.45，则样本已被截到本条预期之外，读数应按低功效对待而非按否定对待。第四，假定九十日窗口内的分桶标准差远离零；若在该族长时间静默的区段该标准差塌向零，比值发散，少数几个观测将同时支配残差回归的斜率与主回归，此时应先检查特征的极端分位再解释斜率。第五，假定 residualise 的两条控制在参考网格上互异且都不恒定、成对样本数充足；若沪锌自身已实现波动在某些区段近乎恒定或与布伦特高度共线，该步无定义或斜率不稳定，此时残差不再是「减掉基线之后的增量」。另需记录一条不是失败但会改变解释的性质：布伦特本身对美元与政策路径有暴露，对其残差化会把本机制的一部分真实传导一并减去，该偏误方向明确为向零收缩，因此本条的正向读数是保守的，而否定读数只针对油价与自身波动之外的增量传导，不否定经由油价的基线通道。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 2a4400cd32707b53d75d3458e188ca9e9a44d30da5722d92ee7db903865c9c93
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 180日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 15552000


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


def _at_fed_dp_net_12h_scaled(at: datetime, series: dict):
    """在任意过去时刻求 fed_dp_net_12h_scaled 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_net_12h = _agg("sum", _window(t, x, end, 43200))
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_scale_90d = _agg("std", _window(t, x, end, 7776000))
    v_fed_dp_net_12h_scaled = (v_fed_dp_net_12h / v_fed_dp_scale_90d) if _ok(v_fed_dp_net_12h) and _ok(v_fed_dp_scale_90d) and v_fed_dp_scale_90d != 0 else None
    return v_fed_dp_net_12h_scaled

def _solve_normal(css, ys):
    """正规方程 + 部分主元高斯消元；主元 < 1e-10 判奇异返回 None。"""
    n = len(ys)
    k = len(css)
    dim = k + 1
    rows = [[1.0, *(c[i] for c in css)] for i in range(n)]
    mat = [[math.fsum(r[a] * r[b] for r in rows) for b in range(dim)]
           for a in range(dim)]
    vec = [math.fsum(r[a] * y for r, y in zip(rows, ys, strict=True))
           for a in range(dim)]
    aug = [[*mat[a], vec[a]] for a in range(dim)]
    for col in range(dim):
        pivot = max(range(col, dim), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-10:
            return None
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for r in range(dim):
            if r == col:
                continue
            f = aug[r][col] / aug[col][col]
            for c2 in range(col, dim + 1):
                aug[r][c2] -= f * aug[col][c2]
    return [aug[a][dim] / aug[a][a] for a in range(dim)]


def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_fed_dp_net_12h, x_fed_dp_net_12h = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_net_12h = decision_time - timedelta(seconds=0)
    v_fed_dp_net_12h = _agg("sum", _window(t_fed_dp_net_12h, x_fed_dp_net_12h, end_fed_dp_net_12h, 43200))
    v_fed_dp_net_12h = v_fed_dp_net_12h if _ok(v_fed_dp_net_12h) else None
    if v_fed_dp_net_12h is not None and not math.isfinite(v_fed_dp_net_12h):
        v_fed_dp_net_12h = None
    t_fed_dp_scale_90d, x_fed_dp_scale_90d = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_scale_90d = decision_time - timedelta(seconds=0)
    v_fed_dp_scale_90d = _agg("std", _window(t_fed_dp_scale_90d, x_fed_dp_scale_90d, end_fed_dp_scale_90d, 7776000))
    v_fed_dp_scale_90d = v_fed_dp_scale_90d if _ok(v_fed_dp_scale_90d) else None
    if v_fed_dp_scale_90d is not None and not math.isfinite(v_fed_dp_scale_90d):
        v_fed_dp_scale_90d = None
    v_fed_dp_net_12h_scaled = (v_fed_dp_net_12h / v_fed_dp_scale_90d) if _ok(v_fed_dp_net_12h) and _ok(v_fed_dp_scale_90d) and v_fed_dp_scale_90d != 0 else None
    if v_fed_dp_net_12h_scaled is not None and not math.isfinite(v_fed_dp_net_12h_scaled):
        v_fed_dp_net_12h_scaled = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_fed_dp_net_12h_scaled_resid, xc0_fed_dp_net_12h_scaled_resid = series["intl_brent.brent"]
    tc1_fed_dp_net_12h_scaled_resid, xc1_fed_dp_net_12h_scaled_resid = series["commodity_bar.realised_volatility"]
    xs_fed_dp_net_12h_scaled_resid = []
    css_fed_dp_net_12h_scaled_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_fed_dp_net_12h_scaled(past, series)
        cvs = []
        cw = _window(tc0_fed_dp_net_12h_scaled_resid, xc0_fed_dp_net_12h_scaled_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_fed_dp_net_12h_scaled_resid, xc1_fed_dp_net_12h_scaled_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_fed_dp_net_12h_scaled_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_fed_dp_net_12h_scaled_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_fed_dp_net_12h_scaled_resid, xc0_fed_dp_net_12h_scaled_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_fed_dp_net_12h_scaled_resid, xc1_fed_dp_net_12h_scaled_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_fed_dp_net_12h_scaled) or not all(_ok(c) for c in c0s) or len(xs_fed_dp_net_12h_scaled_resid) < 40 or any(len(set(c)) < 2 for c in css_fed_dp_net_12h_scaled_resid)):
        v_fed_dp_net_12h_scaled_resid = None
    else:
        coefs = _solve_normal(css_fed_dp_net_12h_scaled_resid, xs_fed_dp_net_12h_scaled_resid)
        if coefs is None:
            v_fed_dp_net_12h_scaled_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_fed_dp_net_12h_scaled_resid = v_fed_dp_net_12h_scaled - pred
    if v_fed_dp_net_12h_scaled_resid is not None and not math.isfinite(v_fed_dp_net_12h_scaled_resid):
        v_fed_dp_net_12h_scaled_resid = None
    return v_fed_dp_net_12h_scaled_resid
