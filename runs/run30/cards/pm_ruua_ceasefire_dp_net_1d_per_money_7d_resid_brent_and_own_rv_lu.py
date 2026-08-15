"""pm_ruua_ceasefire_dp_net_1d_per_money_7d_resid_brent_and_own_rv_lu

机制：s1 取 mech:RU_UA_CEASEFIRE:dp 在决策时点前 86400 秒、不带偏移的区间内的求和，即最近 24 小时该机制轴上构成受控的净概率变化。由于 dp 是构成受控的分桶增量，其窗口内求和在语义上等于该轴归一化概率在这 24 小时里的净变化，量纲为概率点，可按经济量陈述。字段取 dp 而非 p：菜单已声明 p 的电平不可跨时期比较，本族成员达五百余个且随战事与谈判进程整体更替，成员到期与新成员入族会在 p 上制造与信念无关的电平跳变。字段不取 conditions：它是当桶活跃成员市场数，直接度量市场被开出与到期，而菜单已声明归纳语料有 83.7% 的市场创建于其自身裁决区间之后，以它为信号等于把平台侧的建市行为读成信念。算子取 sum 而非 mean：dp 的经济含义可加，一段时间内的净重定价就是各桶增量之和，取 mean 会把有取值的桶数放进分母，使一次由少数几小时的剧烈跳变构成的重定价与一次铺开的同等总位移读数不同，而本条要读的正是净位移。算子不取 std：离散度是幅度，而标签是有符号收益，那正是已登记的 magnitude_vs_signed_label 错配；不取 max、min 或 last：极值只由单个桶决定且其期望随窗口内有取值桶数单调，last 只读到最后写入的那一个。窗口取 86400 秒有三条理由。其一是可估性与覆盖率：该族约每日 4.4 个分桶（5426 桶分布在约 1240 天上），菜单给出其 dp 在六小时窗口上的决策网格有定义比例仅 0.4433，一日窗口的覆盖率显著更高，因此『停市段与可交易段的相位对比』这一更直接的构造在该族密度下无法可靠成立，这一点记录为窗口长度的下界约束而不是没有想到。其二是机制节奏：航线重排、运费报价与调和料流向的调整以日为单位推进，半日窗口读到的是单条新闻而非本条主张的存量。其三是功效：LU 的两个决策时点为日盘开盘前 08:59 与夜盘开盘前 20:59，相距约 12 小时，一日窗口在相邻观测之间重叠一半，一阶自相关约 0.5，按有效独立观测折算后应远超事前功效筛的下限，整块置换检验对本条保有分辨力；取两日会把自相关推到 0.75，这是不取更长窗口的原因。窗口不带偏移使最靠近决策时点、与随后不可交易区间首尾相接的那一段被完整包含，任何非零偏移都会把它排除，而本机制主张的正是该段信息尚未被境内价格消化。窗口几何须如实记录：LU 日盘 09:00 至 11:30 与 13:30 至 15:00、夜盘 21:00 至 23:00，一日窗口必然同时覆盖交易时段与停市时段，因此本构造不隔离停市时段到达的信息，也不主张所读到的重定价完全未被境内价格看到；本条主张的是日尺度上吸收不完全。两个决策相位在一日窗口上都覆盖一个完整的日内周期，仅在两端相差半日，其残余的系统性差异只经由同相位残差回归的截距进入而不进入斜率。s2 取同一 source 的 mech:RU_UA_CEASEFIRE:notional 在决策时点前 604800 秒内的求和，即该轴成员市场在最近七日内的总成交金额，恒非负、量纲为美元。s3 为 ratio，inputs 顺序为 [cf_dp_net_1d, cf_notional_7d]，输出为『每单位周度常态资金规模所推动的净概率变化』，有符号、以零为中性且零点是构造性的（24 小时内无净重定价时取零，其中也包含无活动的情形）。取该分母而非本族此前一律使用的自身 dp 标准差，有三层理由。其一是标度职能：该族的成员数与成交规模在样本期内整体漂移，不归一时样本后段的观测在残差回归中具有远大的杠杆，而成交金额是这一漂移的直接度量。其二是经济读法：同等幅度的净上修，若是在很小的资金规模上完成，更像是共识性的信息更新而非仓位驱动的推挤，本读数把这一维度显式地放进特征。其三是退化风险：该族活动按谈判回合成簇，以自身近期离散度为分母的构造在静默期会遇到分母塌向零而使比值发散；七日总成交金额是一个跨越完整周内循环的累计量，塌缩为零的概率远低，且七日恰为一个整周，工作日与周末的构成被固定，不会随决策时点漂移把日历效应读进比值。代价如实记录：分母仍会随该轴热度与分子同向变动，热点期的读数因此被系统性压缩，这一乘性收缩恒正、只改变幅度不改变符号，其后果是效应向零收缩而非制造假阳性；此外该比值的绝对数量级很小（概率点每美元），这只影响斜率的数值表述而不影响 |t| 与置信区间按特征标准差归一后的陈述。不使用 innovation 承载本构造：innovation 在长短两个嵌套窗口之间比较同一算子并给出加性差，而本条需要的是分子与分母使用不同字段、不同算子（dp 的 sum 与 notional 的 sum）的乘性归一，innovation 无法表达。s4 把 s3 对两个已登记的基线控制 brent 与 own_realised_volatility 同时做残差化，这是本条增量主张的承重步骤，也是本条与更简单解释的分界。标签是有符号收益，其最强的两条基线解释分处两个维度：停火重定价同时压低国际油价，而 LU 作为原油下游馏分与布伦特高度同向，属价格维度，由 brent 承担 —— 不减掉它，本读数几乎必然只是『停火压低原油、原油压低 LU』的转述，而那条通道不含任何另类数据的增量，因此该步在本条上尤其承重，减掉之后剩下的才是本机制主张的吨海里与调和料通道，它作用于燃油相对原油的溢价；谈判密集期同时是本品种的高波动期，而波动状态与收益之间存在已被反复记录的杠杆关系，属波动维度，由 own_realised_volatility 承担，菜单已声明晚涌现族在大波动日的活动份额高出 10.4 个百分点，不减去这一条则无法排除本读数只是高波动状态的重新包装。须如实记录：本特征是有符号量，把它投影到一条非负的波动状态上预期只移除很小一部分变差，第二个控制在此主要承担排除上述更简单解释的职能，其代价是该步在参考网格上需要成对样本并多付一层退化风险。residualise 作用于特征一侧，标签仍是 LU 的名义下一时段收益，本条不构造任何超额收益标签。参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测；采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把 08:59 与 20:59 混入同一拟合样本，两个相位下布伦特的活跃程度、LU 对其的响应斜率与自身已实现波动水平差异很大，混相位拟合会得到一组对两者都不成立的平均斜率。参考窗口取 90 日而非更短，是为了不让个别谈判周主导斜率估计；取 90 日而非 180 日，是为了减少预热损失：该族序列起于 2023-02-20，先付 7 日的分母窗口再付 90 个日采样点，本特征约自 2023 年 5 月下旬起可取值，而 discovery 段止于 2024-12-31。min_samples 取 40：多控制时它计成对样本数，90 个日采样点上通常远多于 40，该阈值主要用于排除序列起始处预热不足与长假造成的样本塌缩；两个控制在同一网格上必须互异且都不恒定，否则该步无定义。该阈值只约束控制侧，对特征侧的退化不提供任何保护，特征侧的退化在 failure_condition 中单独声明。输出为残差，不再取 rank_pct 或 zscore：s3 的零点是构造性的，符号本身是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的仓位映射读错方向，同时丢弃使排除界可以按经济量陈述的量纲，而本轮唯一可交付的产出正是带界的否定；残差在拟合窗口上均值为零，正号表示停火概率的净上修超出国际油价变动与 LU 自身波动状态两者共同所能解释的部分，按 direction=-1 对应更低的下一时段收益。序列相关：分子在相邻两个决策时点之间重叠一半，七日分母重叠十四分之十三，特征方差由快分量支配；残余的序列相关来自谈判回合内重定价成簇出现，由推断阶段的时间维 cluster 承担，品种维 cluster 在单品种下退化为一组，这一退化按失效表使 candidate 失效而不使 null 失效。

失败条件：本构造的语义假设有五条，逐条写下以便结果与预期不符时能分清是机制不成立还是假设写错。其一，方向约定：mech:RU_UA_CEASEFIRE:p 已按机制极性同号化为『停火发生』的概率，故 dp 的正值即停火概率被上修；若该同号化在实现上是反的，本读数的符号将整体翻转，届时应表现为斜率显著为正且幅度可观，而非近零 —— 这一形态可与『机制不成立』区分开，因为后者预期给出的是近零而非显著反号的斜率。其二，字段口径：notional 是该轴成员市场在分桶内的成交金额，其成员集合与 dp 一致；若两者的成员口径不一致（例如 notional 含已被 dp 排除的成员），比值的经济读法失效，而这一点在读结果之前无法从菜单核实，明确记录为未验证的假设。其三，聚合口径：dp 的窗口内求和等于该轴归一化概率在窗口上的净变化，这依赖于『构成受控』在分桶层面成立；若成员轮换仍在 dp 上留下残余跳变，本读数会混入与信念无关的成分，其形态是若干孤立的大绝对值观测支配回归。其四，窗口几何：一日窗口同时覆盖 LU 的交易时段与停市时段，本构造不隔离停市段到达的信息，因此一个显著的负斜率也不能被读成『该信息完全未被境内价格看到』，只能读成日尺度上吸收不完全。其五，通道归属：本条主张增量来自燃油相对原油的溢价；若残差化前后特征几乎不变（即该特征与 brent 近乎正交，而斜率仍显著），则通道未必是吨海里与调和料，也可能是本条未识别的第三条路径，此时结论应限于『存在增量』而不认领本条给出的具体通道。退化情形另记：若 s2 的七日成交金额在某些决策时点为零或缺失，s3 在该点无定义，这些点进入样本缺失而非取零；若本特征在决策网格上的互异取值少于 10 或按一阶自相关折算的有效独立观测少于 30，事前功效筛会在读取任何 outcome 之前拦下本条，此时不产生结论也不消耗检验预算，那属于规格问题而非机制被否定。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 f55e839e1a7d5e5d24599d7de1f15652c4e469ad31eecc04219dc0f382ef6637
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 97日 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 8380800


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


def _at_cf_net_repricing_per_money(at: datetime, series: dict):
    """在任意过去时刻求 cf_net_repricing_per_money 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:dp"]
    end = at - timedelta(seconds=0)
    v_cf_dp_net_1d = _agg("sum", _window(t, x, end, 86400))
    t, x = series["pm_market.mech:RU_UA_CEASEFIRE:notional"]
    end = at - timedelta(seconds=0)
    v_cf_notional_7d = _agg("sum", _window(t, x, end, 604800))
    v_cf_net_repricing_per_money = (v_cf_dp_net_1d / v_cf_notional_7d) if _ok(v_cf_dp_net_1d) and _ok(v_cf_notional_7d) and v_cf_notional_7d != 0 else None
    return v_cf_net_repricing_per_money

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
    t_cf_notional_7d, x_cf_notional_7d = series["pm_market.mech:RU_UA_CEASEFIRE:notional"]
    end_cf_notional_7d = decision_time - timedelta(seconds=0)
    v_cf_notional_7d = _agg("sum", _window(t_cf_notional_7d, x_cf_notional_7d, end_cf_notional_7d, 604800))
    v_cf_notional_7d = v_cf_notional_7d if _ok(v_cf_notional_7d) else None
    if v_cf_notional_7d is not None and not math.isfinite(v_cf_notional_7d):
        v_cf_notional_7d = None
    v_cf_net_repricing_per_money = (v_cf_dp_net_1d / v_cf_notional_7d) if _ok(v_cf_dp_net_1d) and _ok(v_cf_notional_7d) and v_cf_notional_7d != 0 else None
    if v_cf_net_repricing_per_money is not None and not math.isfinite(v_cf_net_repricing_per_money):
        v_cf_net_repricing_per_money = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_cf_net_repricing_per_money_resid, xc0_cf_net_repricing_per_money_resid = series["intl_brent.brent"]
    tc1_cf_net_repricing_per_money_resid, xc1_cf_net_repricing_per_money_resid = series["commodity_bar.realised_volatility"]
    xs_cf_net_repricing_per_money_resid = []
    css_cf_net_repricing_per_money_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_cf_net_repricing_per_money(past, series)
        cvs = []
        cw = _window(tc0_cf_net_repricing_per_money_resid, xc0_cf_net_repricing_per_money_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_cf_net_repricing_per_money_resid, xc1_cf_net_repricing_per_money_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_cf_net_repricing_per_money_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_cf_net_repricing_per_money_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_cf_net_repricing_per_money_resid, xc0_cf_net_repricing_per_money_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_cf_net_repricing_per_money_resid, xc1_cf_net_repricing_per_money_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_cf_net_repricing_per_money) or not all(_ok(c) for c in c0s) or len(xs_cf_net_repricing_per_money_resid) < 40 or any(len(set(c)) < 2 for c in css_cf_net_repricing_per_money_resid)):
        v_cf_net_repricing_per_money_resid = None
    else:
        coefs = _solve_normal(css_cf_net_repricing_per_money_resid, xs_cf_net_repricing_per_money_resid)
        if coefs is None:
            v_cf_net_repricing_per_money_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_cf_net_repricing_per_money_resid = v_cf_net_repricing_per_money - pred
    if v_cf_net_repricing_per_money_resid is not None and not math.isfinite(v_cf_net_repricing_per_money_resid):
        v_cf_net_repricing_per_money_resid = None
    return v_cf_net_repricing_per_money_resid
