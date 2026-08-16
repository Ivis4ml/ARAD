"""pm_us_election_tariff_dp_last_bucket_12h_over_90d_scale_resid_brent_and_own_rv_export_chain_panel

机制：s1 取 mech:US_ELECTION_2024:dp 在决策时点前 43200 秒、不带偏移的区间内最后一个有取值的小时桶的增量，量纲为概率点，有符号、以零为中性且零点是构造性的（该小时无净修正时取零），读作「最靠近开盘的那一小时里，对华关税更强硬的一方胜出的概率被净上修了多少」。s2 取同一 source、同一 field 在决策时点前 7776000 秒内各分桶净变化的标准差，作为该轴自身的季度单桶尺度；活跃期约每日 8 个桶，九十日内期望数百个桶，塌缩为零的概率极低。s3 为 ratio，inputs 顺序为 [elec_dp_last_bucket_12h, elec_dp_scale_90d]，分子与分母同为单桶增量量纲，故输出是严格标准化的单桶位移，无量纲、有符号、以零为中性；取比而非取差做归一，是因为该族成员规模与平台整体活跃度在样本期内整体漂移，该漂移对分子近似乘性，相除使其一阶抵消。s4 把 s3 对两条已登记的基线控制 brent 与 own_realised_volatility 同时做残差化，作用于特征一侧，标签仍是各成员品种的名义下一时段收益，本条不构造任何超额收益标签；参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测，采样步长取 86400 秒使拟合样本与决策时点同相位，不把 08:59 与 20:59 混入同一拟合样本。输出为残差，不再取 rank_pct 或 zscore：零点的构造性与符号是本特征的全部经济内容，rank_pct 会把中性点移到 0.5 而使基于符号的仓位映射读错方向，同时丢弃使排除界可以按经济量陈述的量纲。残差为正表示关税倾向在开盘前最后一次被净上修、且该上修超出国际油价变动与品种自身波动状态两者共同所能解释的部分，按 direction=-1 对应更低的下一交易时段收益。

失败条件：本构造的语义假设逐条列明，任一条不成立则结果的归因不再指向机制本身。一，极性假设：菜单声明 mech:US_ELECTION_2024:p 已同号化为「关税更强硬的一方胜出」，dp 是其分桶增量；若同号化方向与该声明相反，本特征的符号整体翻转，届时观测到的反号斜率是口径错误而非机制被否。二，聚合口径假设：last 取的是窗口内最后一个有取值的小时桶，桶时间戳取小时桶右端；该族并非每小时都有桶，因此在静默期最后一个活跃桶可能落在窗口起点附近、即距决策时点近 12 小时，本读数是「窗口内最近一次重定价」而不是「决策前一小时的重定价」，该时滞随该轴活跃度变化，静默期的稀释恒向零收缩而不制造符号。三，相位假设（语言层限制，本轮新记录）：决策时点有 08:59 与 20:59 两个相位，前者的 12 小时窗口覆盖美东白天、是本机制最干净的实例，后者覆盖美东夜间与欧洲上午、信息密度低得多；语言不提供按会话相位条件化的手段，也不存在能在两个相位上同时落在本地停市区间的固定秒数偏移，因此本条不主张两类观测同质，夜盘相位的观测对效应只做向零的稀释。同样的原因使任何「停市段减可交易段」的相位差构造在两个相位上的信息内容互为反号，本条因此不采用该形态。四，尺度假设：分母为九十日单桶增量标准差，若该轴在某段样本上桶数过少使标准差估计噪声主导，读数会被放大；90 日标度对选情由平静转入白热化的制度切换响应更慢，切换处读数系统性偏高，该效应恒正、只放大幅度不改变符号。五，控制假设：residualise 要求两条控制在同一网格上互异且都不恒定，否则该步无定义；min_samples 只约束控制侧，对特征侧的稀疏不提供任何保护。六，面板假设：五个成员的关税外需通道符号被假定一致；若其中某些成员实际由人民币贬值经进口原料成本主导，则面板内符号相消，读数向零收缩，此时观测到的不显著不足以否定单个品种上的机制。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 a16e9256b8b81f41b509c7cff7f36b4179f182b810553347c60080ef30c773f1
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


def _at_elec_last_repricing_scaled(at: datetime, series: dict):
    """在任意过去时刻求 elec_last_repricing_scaled 的值。参考分布要用它。"""
    t, x = series["pm_market.mech:US_ELECTION_2024:dp"]
    end = at - timedelta(seconds=0)
    v_elec_dp_last_bucket_12h = _agg("last", _window(t, x, end, 43200))
    t, x = series["pm_market.mech:US_ELECTION_2024:dp"]
    end = at - timedelta(seconds=0)
    v_elec_dp_scale_90d = _agg("std", _window(t, x, end, 7776000))
    v_elec_last_repricing_scaled = (v_elec_dp_last_bucket_12h / v_elec_dp_scale_90d) if _ok(v_elec_dp_last_bucket_12h) and _ok(v_elec_dp_scale_90d) and v_elec_dp_scale_90d != 0 else None
    return v_elec_last_repricing_scaled

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
    t_elec_dp_last_bucket_12h, x_elec_dp_last_bucket_12h = series["pm_market.mech:US_ELECTION_2024:dp"]
    end_elec_dp_last_bucket_12h = decision_time - timedelta(seconds=0)
    v_elec_dp_last_bucket_12h = _agg("last", _window(t_elec_dp_last_bucket_12h, x_elec_dp_last_bucket_12h, end_elec_dp_last_bucket_12h, 43200))
    v_elec_dp_last_bucket_12h = v_elec_dp_last_bucket_12h if _ok(v_elec_dp_last_bucket_12h) else None
    if v_elec_dp_last_bucket_12h is not None and not math.isfinite(v_elec_dp_last_bucket_12h):
        v_elec_dp_last_bucket_12h = None
    t_elec_dp_scale_90d, x_elec_dp_scale_90d = series["pm_market.mech:US_ELECTION_2024:dp"]
    end_elec_dp_scale_90d = decision_time - timedelta(seconds=0)
    v_elec_dp_scale_90d = _agg("std", _window(t_elec_dp_scale_90d, x_elec_dp_scale_90d, end_elec_dp_scale_90d, 7776000))
    v_elec_dp_scale_90d = v_elec_dp_scale_90d if _ok(v_elec_dp_scale_90d) else None
    if v_elec_dp_scale_90d is not None and not math.isfinite(v_elec_dp_scale_90d):
        v_elec_dp_scale_90d = None
    v_elec_last_repricing_scaled = (v_elec_dp_last_bucket_12h / v_elec_dp_scale_90d) if _ok(v_elec_dp_last_bucket_12h) and _ok(v_elec_dp_scale_90d) and v_elec_dp_scale_90d != 0 else None
    if v_elec_last_repricing_scaled is not None and not math.isfinite(v_elec_last_repricing_scaled):
        v_elec_last_repricing_scaled = None
    # residualise（多控制）：拟合样本严格取自决策时点之前
    tc0_elec_last_repricing_resid, xc0_elec_last_repricing_resid = series["intl_brent.brent"]
    tc1_elec_last_repricing_resid, xc1_elec_last_repricing_resid = series["commodity_bar.realised_volatility"]
    xs_elec_last_repricing_resid = []
    css_elec_last_repricing_resid = [[] for _ in range(2)]
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_elec_last_repricing_scaled(past, series)
        cvs = []
        cw = _window(tc0_elec_last_repricing_resid, xc0_elec_last_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        cw = _window(tc1_elec_last_repricing_resid, xc1_elec_last_repricing_resid, past, 7776000)
        cvs.append(cw[-1] if cw else None)
        if _ok(xv) and all(_ok(cv) for cv in cvs):
            xs_elec_last_repricing_resid.append(xv)
            for _j, _cv in enumerate(cvs):
                css_elec_last_repricing_resid[_j].append(_cv)
    c0s = []
    cw0 = _window(tc0_elec_last_repricing_resid, xc0_elec_last_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    cw0 = _window(tc1_elec_last_repricing_resid, xc1_elec_last_repricing_resid, decision_time, 7776000)
    c0s.append(cw0[-1] if cw0 else None)
    if (not _ok(v_elec_last_repricing_scaled) or not all(_ok(c) for c in c0s) or len(xs_elec_last_repricing_resid) < 40 or any(len(set(c)) < 2 for c in css_elec_last_repricing_resid)):
        v_elec_last_repricing_resid = None
    else:
        coefs = _solve_normal(css_elec_last_repricing_resid, xs_elec_last_repricing_resid)
        if coefs is None:
            v_elec_last_repricing_resid = None
        else:
            pred = coefs[0] + math.fsum(b * cv for b, cv in zip(coefs[1:], c0s, strict=True))
            v_elec_last_repricing_resid = v_elec_last_repricing_scaled - pred
    if v_elec_last_repricing_resid is not None and not math.isfinite(v_elec_last_repricing_resid):
        v_elec_last_repricing_resid = None
    return v_elec_last_repricing_resid
