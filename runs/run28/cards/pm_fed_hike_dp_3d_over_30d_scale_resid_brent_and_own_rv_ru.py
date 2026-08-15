"""pm_fed_hike_dp_3d_over_30d_scale_resid_brent_and_own_rv_ru

机制：决策时点之前三天，mech:FED_HIKE 机制轴上构成受控的净概率变化之和，即「美联储加息发生的概率在这三天里被净上修了多少个概率点」，除以该轴自身近三十天分桶变化的典型尺度，再对国际油价与沪胶自身已实现波动两条已登记基线控制同时做残差化。s1 取 dp 在 window_seconds=259200、offset_seconds=0 的区间内的求和：不带偏移使最靠近决策时点、与随后不可交易区间首尾相接的那一段被完整包含，而本机制主张的正是该段信息尚未被境内价格消化；三日窗口在 5.1 桶／日的密度下期望约 15 个桶，净和有足够互异取值，半日窗口只有约 2.5 个桶且大量取零。窗口几何须如实记录：三日窗口必然同时覆盖 ru 的交易时段（日盘 09:00 至 11:30 与 13:30 至 15:00、夜盘 21:00 至 23:00）与停市时段，因此本构造不隔离停市时段到达的信息，也不主张所读到的重定价完全未被境内价格看到；本条主张的是数日尺度上的吸收不完全。两个决策相位（08:59 与 20:59，相距约 12 小时）在三日窗口上覆盖的国际时段构成几乎相同，都含三个完整的日内周期，仅在两端相差半日，其残余的系统性差异只经由同相位残差回归的截距进入而不进入斜率。s2 取同一 source、同一 field 在决策时点前 2592000 秒内的标准差，约 153 个桶，对任一单桶不敏感、塌缩为零的概率低，且在相邻两个决策时点之间近乎常数，不随分子同向抖动，这是把它放进分母仍可接受的前提。s3 为 ratio，inputs 顺序为分子在前、分母在后，输出为三日净重定价除以该轴自身的月度分桶变化尺度，有符号、以零为中性且零点是构造性的（三日内无净重定价时取零），量纲为「每一个月度分桶变化标准差单位」。取比而非取差做归一：该轴的重定价幅度在议息与数据发布周同静默期相差一个数量级，且成员数与成交规模在样本期内整体漂移，这些成分对分子近似乘性，相除使其一阶抵消。须记录一处量纲上的不精确：分子是约 15 个桶上的和、分母是单桶尺度，两者相差一个约等于桶数平方根（约 3.9）的因子，故本读数不是严格的标准化统计量，而是以单桶尺度计量的净位移倍数；该因子恒正且随该轴活动强度同向变动，其后果是效应向零收缩或放大而不改变符号。不使用 innovation 承载本构造：sum 关于窗口长度单调，两个不等长窗口的 sum 不可比，而本构造需要的是短窗净位移相对长窗尺度的乘性归一，且分子分母必须用不同算子（sum 与 std），innovation 无法表达。s4 把 s3 对 brent 与 own_realised_volatility 同时残差化，这是增量主张的承重步骤：鹰派重定价同时压低原油，而原油经石脑油—丁二烯—合成胶这条替代链回到天然橡胶，属价格维度，由 brent 承担，减去它之后剩下的才是本机制主张的美元、全球需求与保税库存融资通道；议息与数据发布周同时是本品种的高波动期，波动状态与收益之间存在已被反复记录的杠杆关系，由 own_realised_volatility 承担。residualise 作用于特征一侧，标签仍是沪胶的名义下一时段收益，本条不构造超额收益标签。参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测；采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把 08:59 与 20:59 混入同一拟合样本，两个相位下布伦特的活跃程度、沪胶对其的响应斜率与自身已实现波动水平差异很大，混相位拟合会得到一组对两者都不成立的平均斜率。输出为残差，不再取 rank_pct 或 zscore：符号本身是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的仓位映射读错方向，同时丢弃使排除界可以按经济量陈述的量纲。

失败条件：本构造的语义假设有五条，任一条不成立都会使结果无法归因于机制本身。其一，dp 的符号约定为正表示「加息发生」的概率被上修；若该轴的极性同号化在某些时期反了，本特征的符号随之反转，读数会表现为方向与事前相反而非无效应。其二，dp 是构成受控的分桶增量、其窗口内求和等于该轴归一化概率在该窗口内的净变化；若成员轮换在 dp 上仍留下残余电平跳变，则三日净和会在会议轮换处被污染，表现为议息周附近的极端取值。其三，ratio 的 inputs 顺序为 [分子, 分母]；若求值端按相反顺序解释，本读数变为尺度除以位移，符号在位移为负时仍保留但幅度含义完全不同。其四，brent 控制项可能过度吸收：鹰派重定价本身压低油价，故 brent 与本特征的真实机制部分同向，残差化会把本机制的一部分一并减掉，本条因此是保守的 —— 若读到零效应，不能区分「机制不存在」与「机制已被 brent 吸收殆尽」，这一歧义在结论中必须显式保留。其五，own_realised_volatility 是非负量而本特征有符号，把后者投影到前者上预期只移除很小一部分变差，该控制主要承担排除「本读数只是高波动状态的重新包装」这条更简单解释的职能，不足以处理非线性的波动—收益关系。此外须声明两类可能的构造性失败：若 FED_HIKE 轴在三日窗口上的净位移高度集中于议息与数据发布周、其余时段近零，则互异取值可能不足而被事前功效筛拦下，此时不产生任何结论；若残差化步在参考网格上因长假造成成对样本塌缩至 min_samples 之下，该时点特征无定义并进入排除清单，而非取零。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 c710f3cdaa7264e3d12c93d5fcfc7e48fdb22a0c10e90d8b06403eaefffb3886
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


def _at_fed_repricing_scaled_3d(at: datetime, series: dict):
    """在任意过去时刻求 fed_repricing_scaled_3d 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_3d = _agg("sum", _window(t, x, end, 259200))
    t, x = series["pm_market.mech:FED_HIKE:dp"]
    end = at - timedelta(seconds=0)
    v_fed_dp_scale_30d = _agg("std", _window(t, x, end, 2592000))
    v_fed_repricing_scaled_3d = (v_fed_dp_3d / v_fed_dp_scale_30d) if _ok(v_fed_dp_3d) and _ok(v_fed_dp_scale_30d) and v_fed_dp_scale_30d != 0 else None
    return v_fed_repricing_scaled_3d

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
    t_fed_dp_scale_30d, x_fed_dp_scale_30d = series["pm_market.mech:FED_HIKE:dp"]
    end_fed_dp_scale_30d = decision_time - timedelta(seconds=0)
    v_fed_dp_scale_30d = _agg("std", _window(t_fed_dp_scale_30d, x_fed_dp_scale_30d, end_fed_dp_scale_30d, 2592000))
    v_fed_dp_scale_30d = v_fed_dp_scale_30d if _ok(v_fed_dp_scale_30d) else None
    if v_fed_dp_scale_30d is not None and not math.isfinite(v_fed_dp_scale_30d):
        v_fed_dp_scale_30d = None
    v_fed_repricing_scaled_3d = (v_fed_dp_3d / v_fed_dp_scale_30d) if _ok(v_fed_dp_3d) and _ok(v_fed_dp_scale_30d) and v_fed_dp_scale_30d != 0 else None
    if v_fed_repricing_scaled_3d is not None and not math.isfinite(v_fed_repricing_scaled_3d):
        v_fed_repricing_scaled_3d = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_fed_repricing_resid_ru, xc0_fed_repricing_resid_ru = series["intl_brent.brent"]
    tc1_fed_repricing_resid_ru, xc1_fed_repricing_resid_ru = series["commodity_bar.realised_volatility"]
    xs_fed_repricing_resid_ru = []
    css_fed_repricing_resid_ru = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_fed_repricing_scaled_3d(past, series)
        cvs = []
        cw = _window(tc0_fed_repricing_resid_ru, xc0_fed_repricing_resid_ru, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_fed_repricing_resid_ru, xc1_fed_repricing_resid_ru, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_fed_repricing_resid_ru.append(xv)
            for _j, _cv in enumerate(cvs):
                css_fed_repricing_resid_ru[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_fed_repricing_resid_ru, xc0_fed_repricing_resid_ru, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_fed_repricing_resid_ru, xc1_fed_repricing_resid_ru, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_fed_repricing_scaled_3d) or not all(_ok(c) for c in c0s) or len(xs_fed_repricing_resid_ru) < 40 or any(len(set(c)) < 2 for c in css_fed_repricing_resid_ru)):
        v_fed_repricing_resid_ru = None
    else:
        coefs = _solve_normal(css_fed_repricing_resid_ru, xs_fed_repricing_resid_ru)
        if coefs is None:
            v_fed_repricing_resid_ru = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_fed_repricing_resid_ru = v_fed_repricing_scaled_3d - pred
    if v_fed_repricing_resid_ru is not None and not math.isfinite(v_fed_repricing_resid_ru):
        v_fed_repricing_resid_ru = None
    return v_fed_repricing_resid_ru
