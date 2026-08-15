"""pm_fed_hike_dp_per_unit_flow_12h_over_1d_resid_brent_and_own_rv_bc

机制：mech:FED_HIKE:dp 在决策时点前 12 小时内的构成受控净概率变化，除以该族在决策时点前 24 小时内的成交笔数总量，得到单位流量所推动的加息发生概率净位移；再对国际油价与本品种自身已实现波动两条基线控制做残差化。取值有符号、以零为中性，为正表示加息发生概率被净上修且该上修只用了很少的下单决策即完成。

失败条件：本构造的语义假设有五条，任一不成立时读数的含义即改变：(1) dp 的符号约定，即 p 为『加息发生』的概率、dp 为其构成受控的分桶增量；若该族的极性同号化与此相反，本条读到的方向整体反号，表现为一个与预注册方向相反且量级相当的斜率。(2) ratio 的方向约定为 inputs 首项除以次项；若解释器约定为后者除以前者，本步读到的是每单位净重定价所需的成交笔数，量纲与经济含义都不同，且在 dp 接近零时发散，届时结果将由少数几个观测支配，表现为一个重尾输入上的不稳定斜率。(3) 分母在 24 小时窗口内为零时该步无定义，相应行被丢弃；该族约每日 5.2 个分桶，此类行占比很低，但样本前段更稀疏。(4) 若 dp 在某些分桶上并非构成受控（例如新成员入族仍贡献了电平跳变），分子将含与信念无关的成分，读数向噪声收缩而非改变符号。(5) residualise 的两个控制在参考网格上必须互异且都不恒定，否则该步无定义。另有一条已知且不在构造内部解决的机械依赖：分子的窗口内桶数与该族活动强度同向，分母亦然，故本比值在政策周系统性地被压缩；因分母恒为正，该通道只能使效应向零收缩，不可能制造出与预注册方向相反的符号。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 ae3014f2cd8c3e3e2369cd70fb40b7cf9d55f03d34c3f5ef6ab627cb5095a530
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 91日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7862400


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


def _at_fed_dp_per_unit_flow(at: datetime, series: dict):
    """在任意过去时刻求 fed_dp_per_unit_flow 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_12h = _agg("sum", _window(t, x, end, 43200))
    t, x = series["pm_market.mech:FED_HIKE:trades"]
    end = at - timedelta(seconds=0)
    v_fed_trades_1d = _agg("sum", _window(t, x, end, 86400))
    v_fed_dp_per_unit_flow = (v_fed_dp_12h / v_fed_trades_1d) if _ok(v_fed_dp_12h) and _ok(v_fed_trades_1d) and v_fed_trades_1d != 0 else None
    return v_fed_dp_per_unit_flow

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
    t_fed_dp_12h, x_fed_dp_12h = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_12h = decision_time - timedelta(seconds=0)
    v_fed_dp_12h = _agg("sum", _window(t_fed_dp_12h, x_fed_dp_12h, end_fed_dp_12h, 43200))
    v_fed_dp_12h = v_fed_dp_12h if _ok(v_fed_dp_12h) else None
    if v_fed_dp_12h is not None and not math.isfinite(v_fed_dp_12h):
        v_fed_dp_12h = None
    t_fed_trades_1d, x_fed_trades_1d = series["pm_market.mech:FED_HIKE:trades"]
    end_fed_trades_1d = decision_time - timedelta(seconds=0)
    v_fed_trades_1d = _agg("sum", _window(t_fed_trades_1d, x_fed_trades_1d, end_fed_trades_1d, 86400))
    v_fed_trades_1d = v_fed_trades_1d if _ok(v_fed_trades_1d) else None
    if v_fed_trades_1d is not None and not math.isfinite(v_fed_trades_1d):
        v_fed_trades_1d = None
    v_fed_dp_per_unit_flow = (v_fed_dp_12h / v_fed_trades_1d) if _ok(v_fed_dp_12h) and _ok(v_fed_trades_1d) and v_fed_trades_1d != 0 else None
    if v_fed_dp_per_unit_flow is not None and not math.isfinite(v_fed_dp_per_unit_flow):
        v_fed_dp_per_unit_flow = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_fed_informed_repricing_resid, xc0_fed_informed_repricing_resid = series["intl_brent.brent"]
    tc1_fed_informed_repricing_resid, xc1_fed_informed_repricing_resid = series["commodity_bar.realised_volatility"]
    xs_fed_informed_repricing_resid = []
    css_fed_informed_repricing_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_fed_dp_per_unit_flow(past, series)
        cvs = []
        cw = _window(tc0_fed_informed_repricing_resid, xc0_fed_informed_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_fed_informed_repricing_resid, xc1_fed_informed_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_fed_informed_repricing_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_fed_informed_repricing_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_fed_informed_repricing_resid, xc0_fed_informed_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_fed_informed_repricing_resid, xc1_fed_informed_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_fed_dp_per_unit_flow) or not all(_ok(c) for c in c0s) or len(xs_fed_informed_repricing_resid) < 40 or any(len(set(c)) < 2 for c in css_fed_informed_repricing_resid)):
        v_fed_informed_repricing_resid = None
    else:
        coefs = _solve_normal(css_fed_informed_repricing_resid, xs_fed_informed_repricing_resid)
        if coefs is None:
            v_fed_informed_repricing_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_fed_informed_repricing_resid = v_fed_dp_per_unit_flow - pred
    if v_fed_informed_repricing_resid is not None and not math.isfinite(v_fed_informed_repricing_resid):
        v_fed_informed_repricing_resid = None
    return v_fed_informed_repricing_resid
