"""pm_ruua_ceasefire_dp_1d_over_30d_scale_resid_brent_and_own_rv_al

机制：停火机制轴上最近一个完整日内周期的构成受控净概率变化，除以该轴自身近一个月分桶变化的典型尺度，再对国际油价与本品种自身已实现波动两条基线控制做残差化。取值有符号、以零为中性，为正表示停火发生概率被净上修的程度超出这两条基线共同所能解释的部分。

失败条件：本构造的语义假设有五条，任一不成立时读数的含义随之改变。其一，dp 的符号方向依赖菜单声明的族极性同号化，即 p 是『停火发生』的概率、dp 是其构成受控的分桶变化；若某些成员市场的极性未被正确翻转，s1 的符号将是若干条相反方向问题的混合，斜率向零收缩。其二，ratio 的方向约定：本构造假定 inputs 为 [x, y] 时输出为 x 除以 y；若解释器约定相反，s3 变为月度尺度除以当日净重定价，取值在净重定价接近零时发散、符号仍随分子翻转，此时读到的是一个重尾的倒数量而非标准化位移，斜率不可按本条的量纲解读。其三，稀疏度：该族约每日 4.5 个分桶，若实际分桶密度低于此，24 小时窗口内 dp 求和将大量精确取零，特征在决策网格上互异取值不足，事前功效筛应当拦下；若未被拦下而大量零值混入，斜率主要由少数谈判日决定。其四，分母退化：若 30 日窗口内该族只有极少数活跃分桶，s2 的标准差可能塌缩到接近零，s3 发散并支配残差回归的斜率与主回归。其五，桶数依赖：s1 是若干个桶上的和而 s2 是单桶尺度，两者相差一个约等于窗口内桶数平方根的因子，该因子随该族活动强度上升，故本特征在谈判密集期系统性取到更大的绝对值；该因子恒正，只放大或收缩效应而不改变符号，但它使不同时期的读数不严格可比。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 0539453d5020b21f2a4223ee8fdb55a88dac5bb4c91008ec1e298af5e0fcc882
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


def _at_cf_repricing_scaled_1d(at: datetime, series: dict):
    """在任意过去时刻求 cf_repricing_scaled_1d 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end = at - timedelta(seconds=0)
    v_cf_dp_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end = at - timedelta(seconds=0)
    v_cf_dp_scale_30d = _agg("std", _window(t, x, end, 2592000))
    v_cf_repricing_scaled_1d = (v_cf_dp_1d / v_cf_dp_scale_30d) if _ok(v_cf_dp_1d) and _ok(v_cf_dp_scale_30d) and v_cf_dp_scale_30d != 0 else None
    return v_cf_repricing_scaled_1d

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
    t_cf_dp_1d, x_cf_dp_1d = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end_cf_dp_1d = decision_time - timedelta(seconds=0)
    v_cf_dp_1d = _agg("sum", _window(t_cf_dp_1d, x_cf_dp_1d, end_cf_dp_1d, 86400))
    v_cf_dp_1d = v_cf_dp_1d if _ok(v_cf_dp_1d) else None
    if v_cf_dp_1d is not None and not math.isfinite(v_cf_dp_1d):
        v_cf_dp_1d = None
    t_cf_dp_scale_30d, x_cf_dp_scale_30d = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end_cf_dp_scale_30d = decision_time - timedelta(seconds=0)
    v_cf_dp_scale_30d = _agg("std", _window(t_cf_dp_scale_30d, x_cf_dp_scale_30d, end_cf_dp_scale_30d, 2592000))
    v_cf_dp_scale_30d = v_cf_dp_scale_30d if _ok(v_cf_dp_scale_30d) else None
    if v_cf_dp_scale_30d is not None and not math.isfinite(v_cf_dp_scale_30d):
        v_cf_dp_scale_30d = None
    v_cf_repricing_scaled_1d = (v_cf_dp_1d / v_cf_dp_scale_30d) if _ok(v_cf_dp_1d) and _ok(v_cf_dp_scale_30d) and v_cf_dp_scale_30d != 0 else None
    if v_cf_repricing_scaled_1d is not None and not math.isfinite(v_cf_repricing_scaled_1d):
        v_cf_repricing_scaled_1d = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_cf_repricing_resid, xc0_cf_repricing_resid = series["intl_brent.brent"]
    tc1_cf_repricing_resid, xc1_cf_repricing_resid = series["commodity_bar.realised_volatility"]
    xs_cf_repricing_resid = []
    css_cf_repricing_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_cf_repricing_scaled_1d(past, series)
        cvs = []
        cw = _window(tc0_cf_repricing_resid, xc0_cf_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_cf_repricing_resid, xc1_cf_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_cf_repricing_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_cf_repricing_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_cf_repricing_resid, xc0_cf_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_cf_repricing_resid, xc1_cf_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_cf_repricing_scaled_1d) or not all(_ok(c) for c in c0s) or len(xs_cf_repricing_resid) < 40 or any(len(set(c)) < 2 for c in css_cf_repricing_resid)):
        v_cf_repricing_resid = None
    else:
        coefs = _solve_normal(css_cf_repricing_resid, xs_cf_repricing_resid)
        if coefs is None:
            v_cf_repricing_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_cf_repricing_resid = v_cf_repricing_scaled_1d - pred
    if v_cf_repricing_resid is not None and not math.isfinite(v_cf_repricing_resid):
        v_cf_repricing_resid = None
    return v_cf_repricing_resid
