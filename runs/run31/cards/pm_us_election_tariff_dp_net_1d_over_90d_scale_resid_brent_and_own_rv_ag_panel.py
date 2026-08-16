"""pm_us_election_tariff_dp_net_1d_over_90d_scale_resid_brent_and_own_rv_ag_panel

机制：s1 取 mech:US_ELECTION_2024:dp 在决策时点前 86400 秒、不带偏移的区间内的分桶求和。dp 是构成受控的分桶增量，窗口内求和在语义上等于该轴归一化概率在这 24 小时里的净变化，量纲为概率点，有符号、以零为中性且零点是构造性的（无任何净修正时取零），读作「对华关税更强硬的一方胜出的概率被净上修了多少」。字段取 dp 而非 p：菜单已声明 p 的电平不可跨时期比较，该族成员随选情推进被大量新开（归纳语料有 83.7% 的后见建市暴露），成员进出会在 p 上制造与信念无关的电平跳变；不取 conditions，它是当桶活跃成员市场数、直接度量市场被开出与到期，以它为信号等于把平台侧的建市行为读成信息到达；不取 notional 或 trades，那是参与强度而非关税预期的位移方向，且与有符号的收益标签配对会落入已登记的 magnitude_vs_signed_label 错配。算子取 sum 而非 mean：dp 的经济含义可加，一段时间内的净重定价就是各桶增量之和，取 mean 会把有取值的桶数放进分母，使同等净位移在活跃日与静默日读数不同；不取 std、max、min，那些是幅度或极值，是非负量，与有符号收益标签配对同样落入 magnitude_vs_signed_label；不取 last，它只读到最后写入的那一个桶。s2 取同一 source、同一 field 在决策时点前 7776000 秒内各分桶净变化的标准差，作为该轴自身的季度单桶尺度（该族 5911 个分桶集中在选情区间内，九十日窗口内期望有数百个桶）。分母取 90 日而非 30 日有两条理由：其一，选情事件按辩论、初选、党代会、投票日成簇，30 日标度会与分子在同一批事件周内同向抬升，恰好把携带信息的那些观测过度归一；其二，本构造输出不再取分位保护，分母近零会使少数几个观测同时支配残差回归与主回归，而数百个桶的标准差塌缩为零的概率极低。代价如实记录：90 日标度对选情由平静转入白热化的制度切换响应更慢，切换处的读数会系统性偏低，该效应恒正地作用于幅度而不改变符号。s3 为 ratio，inputs 顺序为分子在前、分母在后，输出无量纲、有符号、以零为中性，读作「最近一日的关税倾向净上修相当于该轴季度常态单桶变化的几倍」。须记录一处量纲上的不精确：分子是若干个桶的和、分母是单桶尺度，两者相差一个与桶数平方根同量级的因子，故本读数不是严格的标准化统计量，而是以单桶尺度计量的净位移倍数；该因子恒正并随该族活动强度同向变动，只放大幅度不改变符号。窗口取 86400 秒有三条理由：其一是可估性，菜单给出该轴 dp 在六小时窗口上的决策网格有定义比例仅 0.3904，六小时窗口会使近六成决策时点无定义，因此「停市段与可交易段的相位对比」这一更贴合美东事件时钟的构造在该族密度下无法可靠成立，这一点记录为窗口长度的下界约束而不是没有想到更短的相位窗口；其二是信息节奏，辩论、初选之夜与计票之夜都是单点事件而其消化以小时计，一日窗口既完整覆盖事件及其消化尾巴，又不把上一日已有交易时段可供吸收的旧消息拖进来；其三是功效，两个决策时点为日盘开盘前 08:59 与夜盘开盘前 20:59，相距约 12 小时，一日窗口在相邻观测之间重叠一半、一阶自相关约 0.5，而 90 日分母在相邻观测之间近乎常数，故特征方差由快分量支配，按有效独立观测折算后应远超事前功效筛的下限；取两日会把自相关推到 0.75，这是不取更长窗口的原因。窗口不带偏移使最靠近决策时点、与随后不可交易区间首尾相接的那一段被完整包含，任何非零偏移都会把它排除，而本机制主张的正是该段信息尚未被境内价格消化。窗口几何须如实记录：面板六个成员的日盘为 09:00 至 11:30 与 13:30 至 15:00、夜盘为 21:00 至 23:00，24 小时窗口对任何成员都必然同时覆盖交易时段与停市时段，因此本构造不隔离停市时段到达的信息，也不主张所读到的重定价完全未被境内价格看到；本条主张的是日尺度上吸收不完全、其残余在下一时段以同号收益完成。同一次事件会同时进入日盘决策点与其后 12 小时的夜盘决策点的窗口，而在后者上它已被当日交易过一轮，这一稀释恒向零收缩效应而不制造符号。s4 把 s3 对两条已登记的基线控制 brent 与 own_realised_volatility 同时做残差化，这是本条增量主张的承重步骤：国际油价既经生物柴油与能源成本通道直接作用于豆油与玉米，也在宏观动荡期与政治重定价活动同向变动，属价格维度，不减掉它本读数完全可能只是「宏观动荡推高油价、油价带动油脂与饲料」的转述，而那条通道不含任何另类数据的增量；已实现波动高度持续，且菜单已声明晚涌现族在大波动日的活动份额高出 10.4 个百分点、即分类法与结果并非独立，不减去 own_realised_volatility 则无法排除本读数只是自身波动状态的重新包装，这是本条最强的竞争假设。residualise 作用于特征一侧，标签仍是各品种的名义下一时段收益，本条不构造任何超额收益标签。参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测；采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把 08:59 与 20:59 混入同一拟合样本 —— 两个相位下布伦特的活跃程度、各品种对其的响应斜率与自身已实现波动水平差异很大，混相位拟合会得到一组对两者都不成立的平均斜率。min_samples 取 40：多控制时它计成对样本数，90 个日采样点上通常远多于 40，该阈值主要用于排除序列起始处预热不足与长假造成的样本塌缩；两个控制在同一网格上必须互异且都不恒定，否则该步无定义；该阈值只约束控制侧，对特征侧的退化不提供任何保护。输出为残差，不再取 rank_pct 或 zscore：s3 的零点是构造性的，符号是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的仓位映射读错方向，同时丢弃使排除界可以按经济量陈述的量纲。残差为正表示关税倾向的净上修超出国际油价变动与品种自身波动状态两者共同所能解释的部分，按 direction=1 对应更高的下一时段收益。

失败条件：本构造的语义假设有五条，任一条不成立都会使结果不能归因于机制本身。第一，极性约定：假设 mech:US_ELECTION_2024:p 确如菜单声明已按机制极性同号化为「对华关税更强硬的一方胜出」的概率，因而 dp 的正值就是关税风险上升。若该同号化在实现上被反向登记，本特征的符号整体翻转，读到的负斜率将是机制成立而约定写反，而非通道被否定；这一条无法在读取结果之前从菜单侧证实，因此记为本条最主要的可归因风险。第二，族内容假设：假设该族 5911 个分桶所聚合的成员确以关税与对华贸易政策为内容，而非仅仅是「谁赢」的通用胜选概率。若成员实际以通用胜选问题为主，本读数度量的是选情本身而不是关税倾向，此时的零读数否定的是这一工具的关税含量，而不是进口平价通道；菜单已声明该族有 65 个正向与 12 个反向成员并按极性折叠，但成员的关税内容浓度不可见。第三，时间与解析口径：假设分桶可用时刻取小时桶右端（比撮合时刻的保守下界还晚一档），故 24 小时窗口内不含决策时点之后的任何信息；这一点由语言保证，不需要额外保护。第四，聚合口径：假设 dp 的窗口求和确实等于该窗口内归一化概率的净变化，即新成员入族不贡献电平跳变；若 dp 的构成控制在成员大规模新开的那些日子（2024 年选情白热化期）不完全，则那段区间的读数会混入建市造成的伪位移，其符号与真实信念位移不必相关，向零收缩而非制造系统性同号。第五，样本区间的结构性问题：大选于 2024 年 11 月裁决，而 discovery 段止于 2024-12-31，故样本末端约两个月内该轴几乎无新分桶，本特征在那一段或无定义、或读数近零；这会压低末端的互异取值密度并使有效样本集中在选举年区间内，若事前功效筛因此以互异取值不足或有效独立观测不足拦下本构造，被否定的是该轴在本决策网格上的可测性而非通道本身。此外，若面板六个成员中某些品种的下一时段收益完全由国内产业政策与库存周期主导，本条也可能读到被稀释的近零斜率；但六个成员按同一条进口平价与替代采购通道选出且预期符号一致，该稀释向零收缩而不制造反号，因此反号仍应按机制未被支持处理。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 8b0f06c6bcd5efb816dfa1f9767a62c4e5c702bd46cd25fbfc4ff4890ee01dc0
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


def _at_elec_net_scaled_1d(at: datetime, series: dict):
    """在任意过去时刻求 elec_net_scaled_1d 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:US_ELECTION_2024:dp"]
    end = at - timedelta(seconds=0)
    v_elec_dp_net_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.mech:US_ELECTION_2024:dp"]
    end = at - timedelta(seconds=0)
    v_elec_dp_scale_90d = _agg("std", _window(t, x, end, 7776000))
    v_elec_net_scaled_1d = (v_elec_dp_net_1d / v_elec_dp_scale_90d) if _ok(v_elec_dp_net_1d) and _ok(v_elec_dp_scale_90d) and v_elec_dp_scale_90d != 0 else None
    return v_elec_net_scaled_1d

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
    t_elec_dp_net_1d, x_elec_dp_net_1d = series["pm_market.mech:US_ELECTION_2024:dp"]
    end_elec_dp_net_1d = decision_time - timedelta(seconds=0)
    v_elec_dp_net_1d = _agg("sum", _window(t_elec_dp_net_1d, x_elec_dp_net_1d, end_elec_dp_net_1d, 86400))
    v_elec_dp_net_1d = v_elec_dp_net_1d if _ok(v_elec_dp_net_1d) else None
    if v_elec_dp_net_1d is not None and not math.isfinite(v_elec_dp_net_1d):
        v_elec_dp_net_1d = None
    t_elec_dp_scale_90d, x_elec_dp_scale_90d = series["pm_market.mech:US_ELECTION_2024:dp"]
    end_elec_dp_scale_90d = decision_time - timedelta(seconds=0)
    v_elec_dp_scale_90d = _agg("std", _window(t_elec_dp_scale_90d, x_elec_dp_scale_90d, end_elec_dp_scale_90d, 7776000))
    v_elec_dp_scale_90d = v_elec_dp_scale_90d if _ok(v_elec_dp_scale_90d) else None
    if v_elec_dp_scale_90d is not None and not math.isfinite(v_elec_dp_scale_90d):
        v_elec_dp_scale_90d = None
    v_elec_net_scaled_1d = (v_elec_dp_net_1d / v_elec_dp_scale_90d) if _ok(v_elec_dp_net_1d) and _ok(v_elec_dp_scale_90d) and v_elec_dp_scale_90d != 0 else None
    if v_elec_net_scaled_1d is not None and not math.isfinite(v_elec_net_scaled_1d):
        v_elec_net_scaled_1d = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_elec_tariff_repricing_1d, xc0_elec_tariff_repricing_1d = series["intl_brent.brent"]
    tc1_elec_tariff_repricing_1d, xc1_elec_tariff_repricing_1d = series["commodity_bar.realised_volatility"]
    xs_elec_tariff_repricing_1d = []
    css_elec_tariff_repricing_1d = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_elec_net_scaled_1d(past, series)
        cvs = []
        cw = _window(tc0_elec_tariff_repricing_1d, xc0_elec_tariff_repricing_1d, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_elec_tariff_repricing_1d, xc1_elec_tariff_repricing_1d, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_elec_tariff_repricing_1d.append(xv)
            for _j, _cv in enumerate(cvs):
                css_elec_tariff_repricing_1d[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_elec_tariff_repricing_1d, xc0_elec_tariff_repricing_1d, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_elec_tariff_repricing_1d, xc1_elec_tariff_repricing_1d, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_elec_net_scaled_1d) or not all(_ok(c) for c in c0s) or len(xs_elec_tariff_repricing_1d) < 40 or any(len(set(c)) < 2 for c in css_elec_tariff_repricing_1d)):
        v_elec_tariff_repricing_1d = None
    else:
        coefs = _solve_normal(css_elec_tariff_repricing_1d, xs_elec_tariff_repricing_1d)
        if coefs is None:
            v_elec_tariff_repricing_1d = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_elec_tariff_repricing_1d = v_elec_net_scaled_1d - pred
    if v_elec_tariff_repricing_1d is not None and not math.isfinite(v_elec_tariff_repricing_1d):
        v_elec_tariff_repricing_1d = None
    return v_elec_tariff_repricing_1d
