"""pm_ruua_ceasefire_dp_net_1d_x_arrival_mult_resid_brent_and_own_rv_y

机制：最近一日 mech:RU_UA_CEASEFIRE:dp 的分桶求和，即停火发生概率在这 24 小时里被净上修了多少个概率点（有符号，量纲为概率点），除以该轴近九十日各分桶净变化的标准差做尺度归一，再乘以该轴最近一日相对近三十日的单位活跃小时成交笔数倍数（乘法由 ratio(cf_net_scaled_1d, cf_arr_mult_inv) 实现，其中 cf_arr_mult_inv = ratio(cf_arr_30d, cf_arr_1d) 即到达倍数的倒数），得到一个有符号、以零为中性、零点为构造性的流量证实型净重定价读数：为正表示停火概率被净上修且该上修伴随高于自身常态的信息到达强度，为负表示被净下修。最后对 brent 与 own_realised_volatility 两条已登记基线控制同时做残差化，残差为正表示该流量证实型净上修超出国际油价变动与豆油自身波动持续性两者共同所能解释的部分。

失败条件：本构造的语义假设有五条，任一不成立时结果的解读都不是「机制不成立」而是「假设写错了」。第一，dp 的分桶求和等于该轴归一化概率在窗口内的净变化，且构成受控意味着成员进出不贡献位移；若实现中 dp 在成员到期或入族处仍留有残余跳变，则本读数在成员更替密集的时期含与信念无关的成分，其表现是特征在这些时期出现与谈判进程无关的大绝对值。第二，trades 的 mean 是按有取值的分桶取平均，即每活跃小时的成交笔数；若实现中 mean 按窗口内全部小时（含无成交的小时）取平均，则一日与三十日读数的分母口径不同，到达倍数会把活动覆盖率而非到达强度读进来，此时特征在清淡期系统性偏低。第三，到达倍数的倒数 cf_arr_mult_inv 不接近零；它接近零要求最近一日的每活跃小时成交笔数远高于三十日常态（约十倍以上），此时乘积被放大十倍以上，少数几个谈判日的观测会同时支配残差回归的斜率与主回归。这是本构造已知的重尾来源，恒正地放大方差而不改变符号，其后果是效应向零收缩或使置信区间变宽，而不是制造假阳性；若诊断显示特征的绝对值前 1% 观测贡献了残差回归斜率的绝大部分，本条的排除界应按去掉这些观测后的区间重述。第四，九十日分母标度非零且不与分子同向变动；约 396 个桶的标准差塌缩为零的概率极低，但若该族在某段时期完全停摆，该步无定义并使这些决策时点丢失。第五，残差化的两个控制在同一参考网格上互异且都不恒定，否则该步无定义；参考网格取严格早于决策时点的 90 个日采样点、采样步长 86400 秒，使拟合样本与决策时点落在相同的时钟相位（不把 08:59 与 20:59 混入同一拟合样本），两个相位下布伦特的活跃程度、豆油对其的响应斜率与自身已实现波动水平差异很大，混相位拟合会得到一组对两者都不成立的平均斜率。此外记录两处不精确：其一，分子是约 4 至 5 个桶上的和、分母是单桶尺度，两者相差一个与桶数平方根同量级的因子，故本读数不是严格的标准化统计量而是以单桶尺度计量的净位移倍数，该因子恒正且随该族活动强度同向变动；其二，本构造不隔离停市时段到达的信息，一日窗口对豆油必然同时覆盖交易时段与停市时段，因此若结果为否定，它否定的是「日尺度上吸收不完全」这一主张，而不是「停市段到达的信息完全未被消化」这一更强的主张。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 4c22c60a4f6496cab4bcaf3ef756ff64e4faac26ba4ffed3562c6fe9e6cdf3b5
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


def _at_cf_net_x_attention(at: datetime, series: dict):
    """在任意过去时刻求 cf_net_x_attention 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end = at - timedelta(seconds=0)
    v_cf_dp_net_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end = at - timedelta(seconds=0)
    v_cf_dp_scale_90d = _agg("std", _window(t, x, end, 7776000))
    v_cf_net_scaled_1d = (v_cf_dp_net_1d / v_cf_dp_scale_90d) if _ok(v_cf_dp_net_1d) and _ok(v_cf_dp_scale_90d) and v_cf_dp_scale_90d != 0 else None
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:trades"]
    end = at - timedelta(seconds=0)
    v_cf_arr_30d = _agg("mean", _window(t, x, end, 2592000))
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:trades"]
    end = at - timedelta(seconds=0)
    v_cf_arr_1d = _agg("mean", _window(t, x, end, 86400))
    v_cf_arr_mult_inv = (v_cf_arr_30d / v_cf_arr_1d) if _ok(v_cf_arr_30d) and _ok(v_cf_arr_1d) and v_cf_arr_1d != 0 else None
    v_cf_net_x_attention = (v_cf_net_scaled_1d / v_cf_arr_mult_inv) if _ok(v_cf_net_scaled_1d) and _ok(v_cf_arr_mult_inv) and v_cf_arr_mult_inv != 0 else None
    return v_cf_net_x_attention

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
    t_cf_dp_net_1d, x_cf_dp_net_1d = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end_cf_dp_net_1d = decision_time - timedelta(seconds=0)
    v_cf_dp_net_1d = _agg("sum", _window(t_cf_dp_net_1d, x_cf_dp_net_1d, end_cf_dp_net_1d, 86400))
    v_cf_dp_net_1d = v_cf_dp_net_1d if _ok(v_cf_dp_net_1d) else None
    if v_cf_dp_net_1d is not None and not math.isfinite(v_cf_dp_net_1d):
        v_cf_dp_net_1d = None
    t_cf_dp_scale_90d, x_cf_dp_scale_90d = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end_cf_dp_scale_90d = decision_time - timedelta(seconds=0)
    v_cf_dp_scale_90d = _agg("std", _window(t_cf_dp_scale_90d, x_cf_dp_scale_90d, end_cf_dp_scale_90d, 7776000))
    v_cf_dp_scale_90d = v_cf_dp_scale_90d if _ok(v_cf_dp_scale_90d) else None
    if v_cf_dp_scale_90d is not None and not math.isfinite(v_cf_dp_scale_90d):
        v_cf_dp_scale_90d = None
    v_cf_net_scaled_1d = (v_cf_dp_net_1d / v_cf_dp_scale_90d) if _ok(v_cf_dp_net_1d) and _ok(v_cf_dp_scale_90d) and v_cf_dp_scale_90d != 0 else None
    if v_cf_net_scaled_1d is not None and not math.isfinite(v_cf_net_scaled_1d):
        v_cf_net_scaled_1d = None
    t_cf_arr_1d, x_cf_arr_1d = series["pm_market.mech:RU_UA_CEASEFIRE:trades"]
    end_cf_arr_1d = decision_time - timedelta(seconds=0)
    v_cf_arr_1d = _agg("mean", _window(t_cf_arr_1d, x_cf_arr_1d, end_cf_arr_1d, 86400))
    v_cf_arr_1d = v_cf_arr_1d if _ok(v_cf_arr_1d) else None
    if v_cf_arr_1d is not None and not math.isfinite(v_cf_arr_1d):
        v_cf_arr_1d = None
    t_cf_arr_30d, x_cf_arr_30d = series["pm_market.mech:RU_UA_CEASEFIRE:trades"]
    end_cf_arr_30d = decision_time - timedelta(seconds=0)
    v_cf_arr_30d = _agg("mean", _window(t_cf_arr_30d, x_cf_arr_30d, end_cf_arr_30d, 2592000))
    v_cf_arr_30d = v_cf_arr_30d if _ok(v_cf_arr_30d) else None
    if v_cf_arr_30d is not None and not math.isfinite(v_cf_arr_30d):
        v_cf_arr_30d = None
    v_cf_arr_mult_inv = (v_cf_arr_30d / v_cf_arr_1d) if _ok(v_cf_arr_30d) and _ok(v_cf_arr_1d) and v_cf_arr_1d != 0 else None
    if v_cf_arr_mult_inv is not None and not math.isfinite(v_cf_arr_mult_inv):
        v_cf_arr_mult_inv = None
    v_cf_net_x_attention = (v_cf_net_scaled_1d / v_cf_arr_mult_inv) if _ok(v_cf_net_scaled_1d) and _ok(v_cf_arr_mult_inv) and v_cf_arr_mult_inv != 0 else None
    if v_cf_net_x_attention is not None and not math.isfinite(v_cf_net_x_attention):
        v_cf_net_x_attention = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_cf_flow_corroborated_net_repricing, xc0_cf_flow_corroborated_net_repricing = series["intl_brent.brent"]
    tc1_cf_flow_corroborated_net_repricing, xc1_cf_flow_corroborated_net_repricing = series["commodity_bar.realised_volatility"]
    xs_cf_flow_corroborated_net_repricing = []
    css_cf_flow_corroborated_net_repricing = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_cf_net_x_attention(past, series)
        cvs = []
        cw = _window(tc0_cf_flow_corroborated_net_repricing, xc0_cf_flow_corroborated_net_repricing, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_cf_flow_corroborated_net_repricing, xc1_cf_flow_corroborated_net_repricing, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_cf_flow_corroborated_net_repricing.append(xv)
            for _j, _cv in enumerate(cvs):
                css_cf_flow_corroborated_net_repricing[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_cf_flow_corroborated_net_repricing, xc0_cf_flow_corroborated_net_repricing, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_cf_flow_corroborated_net_repricing, xc1_cf_flow_corroborated_net_repricing, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_cf_net_x_attention) or not all(_ok(c) for c in c0s) or len(xs_cf_flow_corroborated_net_repricing) < 40 or any(len(set(c)) < 2 for c in css_cf_flow_corroborated_net_repricing)):
        v_cf_flow_corroborated_net_repricing = None
    else:
        coefs = _solve_normal(css_cf_flow_corroborated_net_repricing, xs_cf_flow_corroborated_net_repricing)
        if coefs is None:
            v_cf_flow_corroborated_net_repricing = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_cf_flow_corroborated_net_repricing = v_cf_net_x_attention - pred
    if v_cf_flow_corroborated_net_repricing is not None and not math.isfinite(v_cf_flow_corroborated_net_repricing):
        v_cf_flow_corroborated_net_repricing = None
    return v_cf_flow_corroborated_net_repricing
