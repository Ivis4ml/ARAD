"""pm_fed_hike_dp_3d_over_90d_scale_resid_brent_and_own_rv_panel

机制：决策时点之前三天，mech:FED_HIKE 机制轴上构成受控的净概率变化之和，即「美联储加息发生的概率在这三天里被净上修了多少个概率点」，除以该轴自身近九十天分桶变化的典型尺度，再对国际油价与各品种自身已实现波动两条已登记基线控制同时做残差化。取值有符号、以零为中性且零点是构造性的（三日内无净重定价时取零），量纲为「每一个季度分桶变化标准差单位」，为正表示加息路径被净上修的程度超出国际油价变动与该品种自身波动状态两者共同所能解释的部分。

失败条件：本构造的语义假设有六条，任一不成立时结果不可归因于机制。其一，极性假设：mech:FED_HIKE:p 已按机制极性同号化为「加息发生」的概率，dp 为其构成受控的分桶增量，故 dp 为正即鹰派方向；若该极性与菜单声明相反，斜率符号整体翻转，读到的将是一个显著为正的斜率而不是噪声。其二，可加性假设：dp 在窗口内求和等于该轴归一化概率的净变化；若 dp 实为已归一化的速率或含成员进出的残余跳变，则三日求和会随窗口内成员轮换次数系统性偏移，表现为特征在会议轮换日前后出现与信念无关的电平跳变。其三，ratio 的方向约定：inputs 顺序 [fed_dp_3d, fed_dp_scale_90d] 被解释为前者除以后者；若实现为后者除以前者，输出在分子过零处发散且符号含义反转，表现为极少数观测的绝对值远离其余分布并同时支配残差回归与主回归。其四，分母非退化假设：90 日窗口内约 440 个分桶使 std 稳定为正；若该族在某段时期整体静默使 std 塌向零，比值发散，且本构造不再取 rank_pct 做重尾保护，表现为少数观测的杠杆异常。其五，残差化的方向与时序假设：residualise 作用于特征一侧、标签保持为各品种名义收益，拟合样本严格取自决策时点之前的 90 个同相位日采样点；若实现为在全样本上拟合，残差含未来信息，表现为异常高的样本内显著性而置换检验同时判 placebo_failed。其六，面板同号假设：本机制在多数成员上符号一致、在内需定价成员上接近零；若实际上在两组成员上符号相反，合并斜率会自我抵消并读到接近零的效应，此时读数否定的是「共同因子」这一形态而不是机制本身，须由拆分子集的后续提案区分，本条不做该区分。此外记录三条已知的构造缺陷而非假设：三日窗口在相邻决策时点之间重叠六分之五，一阶自相关约 0.83，置换检验分辨力因此受限；分子是约 15 个桶上的和而分母是单桶尺度，两者相差一个约等于桶数平方根的正因子，故本读数不是严格标准化量，只使效应向零收缩或放大而不改变符号；三日窗口必然同时覆盖各品种的交易时段与停市时段，因此本条不隔离停市时段到达的信息，也不主张所读到的重定价完全未被境内价格看到，本条主张的只是数日尺度上的吸收不完全。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 423fd52a68d121b620de9d84b7ab6baa41cce6eb73fe7702ec3608c042e0bd5a
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


def _at_fed_repricing_stock_3d(at: datetime, series: dict):
    """在任意过去时刻求 fed_repricing_stock_3d 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_3d = _agg("sum", _window(t, x, end, 259200))
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_scale_90d = _agg("std", _window(t, x, end, 7776000))
    v_fed_repricing_stock_3d = (v_fed_dp_3d / v_fed_dp_scale_90d) if _ok(v_fed_dp_3d) and _ok(v_fed_dp_scale_90d) and v_fed_dp_scale_90d != 0 else None
    return v_fed_repricing_stock_3d

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
    t_fed_dp_3d, x_fed_dp_3d = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_3d = decision_time - timedelta(seconds=0)
    v_fed_dp_3d = _agg("sum", _window(t_fed_dp_3d, x_fed_dp_3d, end_fed_dp_3d, 259200))
    v_fed_dp_3d = v_fed_dp_3d if _ok(v_fed_dp_3d) else None
    if v_fed_dp_3d is not None and not math.isfinite(v_fed_dp_3d):
        v_fed_dp_3d = None
    t_fed_dp_scale_90d, x_fed_dp_scale_90d = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_scale_90d = decision_time - timedelta(seconds=0)
    v_fed_dp_scale_90d = _agg("std", _window(t_fed_dp_scale_90d, x_fed_dp_scale_90d, end_fed_dp_scale_90d, 7776000))
    v_fed_dp_scale_90d = v_fed_dp_scale_90d if _ok(v_fed_dp_scale_90d) else None
    if v_fed_dp_scale_90d is not None and not math.isfinite(v_fed_dp_scale_90d):
        v_fed_dp_scale_90d = None
    v_fed_repricing_stock_3d = (v_fed_dp_3d / v_fed_dp_scale_90d) if _ok(v_fed_dp_3d) and _ok(v_fed_dp_scale_90d) and v_fed_dp_scale_90d != 0 else None
    if v_fed_repricing_stock_3d is not None and not math.isfinite(v_fed_repricing_stock_3d):
        v_fed_repricing_stock_3d = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_fed_repricing_stock_resid, xc0_fed_repricing_stock_resid = series["intl_brent.brent"]
    tc1_fed_repricing_stock_resid, xc1_fed_repricing_stock_resid = series["commodity_bar.realised_volatility"]
    xs_fed_repricing_stock_resid = []
    css_fed_repricing_stock_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_fed_repricing_stock_3d(past, series)
        cvs = []
        cw = _window(tc0_fed_repricing_stock_resid, xc0_fed_repricing_stock_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_fed_repricing_stock_resid, xc1_fed_repricing_stock_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_fed_repricing_stock_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_fed_repricing_stock_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_fed_repricing_stock_resid, xc0_fed_repricing_stock_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_fed_repricing_stock_resid, xc1_fed_repricing_stock_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_fed_repricing_stock_3d) or not all(_ok(c) for c in c0s) or len(xs_fed_repricing_stock_resid) < 40 or any(len(set(c)) < 2 for c in css_fed_repricing_stock_resid)):
        v_fed_repricing_stock_resid = None
    else:
        coefs = _solve_normal(css_fed_repricing_stock_resid, xs_fed_repricing_stock_resid)
        if coefs is None:
            v_fed_repricing_stock_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_fed_repricing_stock_resid = v_fed_repricing_stock_3d - pred
    if v_fed_repricing_stock_resid is not None and not math.isfinite(v_fed_repricing_stock_resid):
        v_fed_repricing_stock_resid = None
    return v_fed_repricing_stock_resid
