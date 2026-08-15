"""pm_iran_outstanding_resolution_mass_resid_own_rv_12h_90d

机制：s1 与 s2 是参数逐项相同的两个步骤，各取 cand:iran:p 在决策时点前 43200 秒内的均值 p。s3 为 ratio，inputs 为 [iran_p_mean_12h, iran_p_mean_12h_ref]，输出为前者除以后者，在 p 不为零时恒等于 1；原语中没有字面常数，这是取得常数 1 的唯一路径，用两个独立定义的窗口步骤而非把同一步骤填两次，是为了在解释器要求 inputs 互异时仍然成立。s4 为 difference，inputs 为 [unity, iran_p_mean_12h]，输出为前者减后者，即 1 减 p，取值域 [0,1]。s5 为 ratio，inputs 为 [unity, iran_p_complement_12h]，输出为 1 除以 (1 减 p)。s6 为 ratio，inputs 为 [iran_p_mean_12h, inv_complement_12h]，输出为 p 除以 (1 除以 (1 减 p))，代数上等于 p 乘以 (1 减 p)，即窗口均值处的伯努利方差，取值域 [0,0.25]，在 p 等于 0.5 处取到最大值，关于 0.5 对称。两次嵌套 ratio 是在没有乘法算子的前提下实现乘法的路径，与本族既有规格用同一手法实现平方一致。该量恒非负、无量纲，与该族的绝对成交规模、平台整体规模的增长都无关，度量的是决策时点上尚未被解决的概率质量。需要指明本构造得到的是窗口均值处的伯努利方差，而非各小时桶伯努利方差的窗口均值：两者之差恰好等于 p 在窗口内的方差，即同窗口 std 的平方，该二阶量已被本族多条翻覆类规格读过，取均值形式正是为了使本构造与之不重合。窗口取 43200 秒使相邻两个决策时点的取数区间几乎不重叠，且该族在 12 小时窗口内期望约 7.4 个小时桶，均值可估。算子取 mean 而非 last、max、min：本构造要的是窗口内的典型水平，last 受该桶内恰好写入哪几个并行合约的影响，极值只由单个桶决定并随桶数单调。不取 offset：不带偏移的窗口与本合约的收盘几何无关，使该特征在面板的每个品种上含义相同。s7 把 s6 对已登记的基线控制 own_realised_volatility 做残差化，控制取它而非 brent，因为标签是已实现波动率、属波动维度，与本特征要剥离的基线同构；只做一次残差化而不串联第二次，因为串联后的残差只与最后一个控制正交，并不给出对两个控制同时正交的量，却要多付一层预热。参考网格取 window_seconds=7776000、sample_every_seconds=86400，即严格位于决策时点之前的 90 个日采样点，拟合样本取自 t 减 k 倍采样步长，不使用同期或未来观测；采样步长取 86400 秒使拟合样本落在与决策时点相同的时钟相位上，不把日盘 15:00 收盘与夜盘 02:30 收盘混入同一拟合样本。min_samples 取 40，计控制变量的互异取值。输出为残差，不再取 rank_pct 或 zscore：输入被界在 [0,0.25] 内，不存在重尾，rank_pct 的保护没有对象；残差在拟合窗口上均值为零这一零点是构造性的，正号表示未解决质量超出本品种自身波动状态所能解释的部分。

失败条件：其一，常数构造依赖两项语义假设：解释器允许两个参数逐项相同的 window 步骤并列存在而不把它们折叠为同一步骤，且 ratio 接受这样两个步骤作为 inputs。若任一项不成立，本条被判 blocked；该 block 本身是关于原语语言无法引入字面常数的信息，应记为一条原语缺口。其二，difference 的方向约定：本条假定 inputs 为 [x, y] 时输出为前者减后者，据此 s4 等于 1 减 p。若解释器的约定相反，s4 等于 p 减 1、恒非正，s5 与 s6 随之反号，整个特征变为 p 乘以 (1 减 p) 的相反数，direction=1 会读错方向，属于需要回报的语义不匹配。其三，退化风险：若某个 12 小时窗口内该族没有任何小时桶，或全部打印为零，则 p 等于 0，s3 无定义；若 p 等于 1，则 s4 等于 0，s5 发散。该族约每日 14.7 个小时桶，12 小时窗口内期望约 7.4 个，桶数为零的窗口在清淡相位上仍可能出现；min_samples 只约束控制侧，对特征侧的这类退化不提供保护。其四，语义假设：假定 cand:iran:p 在小时桶上读到的是该桶内全族归一化概率的单一汇总值。若该字段实际是按合约展开后未加权拼接的结果，则窗口均值中混入的是合约之间的横截面平均而非族水平的代表值，p 乘以 (1 减 p) 度量的将是该平均值处的伯努利方差而非全族的未解决质量，两者在合约阈值分布偏斜时差异很大，机制的经济解释随之改变。其五，样本组成偏差：裁决区间之后才创建的市场其概率打印集中在 0 与 1 附近，会把族均值拖向两端并机械地压低本特征；该偏差在样本期内随平台市场创建强度变化而变化，属水平漂移而非噪声，若残差的预测力主要由该漂移承担，则本机制不被支持。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 e4b14c865d07814f9c2106428c914bea79feeab4c298441abaa98fbc0020ff0a
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 2172时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 7819200


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


def _at_iran_resolution_mass_12h(at: datetime, series: dict):
    """在任意过去时刻求 iran_resolution_mass_12h 的值。参考分布要用它。"""
    t, x = series["pm_market.cand:iran:p"]
    end = at - timedelta(seconds=0)
    v_iran_p_mean_12h = _agg("mean", _window(t, x, end, 43200))
    t, x = series["pm_market.cand:iran:p"]
    end = at - timedelta(seconds=0)
    v_iran_p_mean_12h_ref = _agg("mean", _window(t, x, end, 43200))
    v_unity = (v_iran_p_mean_12h / v_iran_p_mean_12h_ref) if _ok(v_iran_p_mean_12h) and _ok(v_iran_p_mean_12h_ref) and v_iran_p_mean_12h_ref != 0 else None
    v_iran_p_complement_12h = (v_unity - v_iran_p_mean_12h) if _ok(v_unity) and _ok(v_iran_p_mean_12h) else None
    v_inv_complement_12h = (v_unity / v_iran_p_complement_12h) if _ok(v_unity) and _ok(v_iran_p_complement_12h) and v_iran_p_complement_12h != 0 else None
    v_iran_resolution_mass_12h = (v_iran_p_mean_12h / v_inv_complement_12h) if _ok(v_iran_p_mean_12h) and _ok(v_inv_complement_12h) and v_inv_complement_12h != 0 else None
    return v_iran_resolution_mass_12h

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_iran_p_mean_12h, x_iran_p_mean_12h = series["pm_market.cand:iran:p"]
    end_iran_p_mean_12h = decision_time - timedelta(seconds=0)
    v_iran_p_mean_12h = _agg("mean", _window(t_iran_p_mean_12h, x_iran_p_mean_12h, end_iran_p_mean_12h, 43200))
    v_iran_p_mean_12h = v_iran_p_mean_12h if _ok(v_iran_p_mean_12h) else None
    if v_iran_p_mean_12h is not None and not math.isfinite(v_iran_p_mean_12h):
        v_iran_p_mean_12h = None
    t_iran_p_mean_12h_ref, x_iran_p_mean_12h_ref = series["pm_market.cand:iran:p"]
    end_iran_p_mean_12h_ref = decision_time - timedelta(seconds=0)
    v_iran_p_mean_12h_ref = _agg("mean", _window(t_iran_p_mean_12h_ref, x_iran_p_mean_12h_ref, end_iran_p_mean_12h_ref, 43200))
    v_iran_p_mean_12h_ref = v_iran_p_mean_12h_ref if _ok(v_iran_p_mean_12h_ref) else None
    if v_iran_p_mean_12h_ref is not None and not math.isfinite(v_iran_p_mean_12h_ref):
        v_iran_p_mean_12h_ref = None
    v_unity = (v_iran_p_mean_12h / v_iran_p_mean_12h_ref) if _ok(v_iran_p_mean_12h) and _ok(v_iran_p_mean_12h_ref) and v_iran_p_mean_12h_ref != 0 else None
    if v_unity is not None and not math.isfinite(v_unity):
        v_unity = None
    v_iran_p_complement_12h = (v_unity - v_iran_p_mean_12h) if _ok(v_unity) and _ok(v_iran_p_mean_12h) else None
    if v_iran_p_complement_12h is not None and not math.isfinite(v_iran_p_complement_12h):
        v_iran_p_complement_12h = None
    v_inv_complement_12h = (v_unity / v_iran_p_complement_12h) if _ok(v_unity) and _ok(v_iran_p_complement_12h) and v_iran_p_complement_12h != 0 else None
    if v_inv_complement_12h is not None and not math.isfinite(v_inv_complement_12h):
        v_inv_complement_12h = None
    v_iran_resolution_mass_12h = (v_iran_p_mean_12h / v_inv_complement_12h) if _ok(v_iran_p_mean_12h) and _ok(v_inv_complement_12h) and v_inv_complement_12h != 0 else None
    if v_iran_resolution_mass_12h is not None and not math.isfinite(v_iran_resolution_mass_12h):
        v_iran_resolution_mass_12h = None
    # residualise：拟合样本严格取自决策时点之前，逐点重拟合
    tc_iran_resolution_mass_resid, xc_iran_resolution_mass_resid = series["commodity_bar.realised_volatility"]
    xs_iran_resolution_mass_resid, cs_iran_resolution_mass_resid = [], []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        xv = _at_iran_resolution_mass_12h(past, series)
        cw = _window(tc_iran_resolution_mass_resid, xc_iran_resolution_mass_resid, past, 7776000)
        cv = cw[-1] if cw else None
        if _ok(xv) and _ok(cv):
            xs_iran_resolution_mass_resid.append(xv)
            cs_iran_resolution_mass_resid.append(cv)
    cw0 = _window(tc_iran_resolution_mass_resid, xc_iran_resolution_mass_resid, decision_time, 7776000)
    c0 = cw0[-1] if cw0 else None
    if not _ok(v_iran_resolution_mass_12h) or not _ok(c0) or len(set(cs_iran_resolution_mass_resid)) < 40:
        v_iran_resolution_mass_resid = None
    else:
        cbar = math.fsum(cs_iran_resolution_mass_resid) / len(cs_iran_resolution_mass_resid)
        xbar = math.fsum(xs_iran_resolution_mass_resid) / len(xs_iran_resolution_mass_resid)
        scc = math.fsum((c - cbar) ** 2 for c in cs_iran_resolution_mass_resid)
        if scc <= 0:
            v_iran_resolution_mass_resid = None
        else:
            b = math.fsum((c - cbar) * (x - xbar) for c, x in zip(cs_iran_resolution_mass_resid, xs_iran_resolution_mass_resid, strict=True)) / scc
            v_iran_resolution_mass_resid = v_iran_resolution_mass_12h - (xbar + b * (c0 - cbar))
    if v_iran_resolution_mass_resid is not None and not math.isfinite(v_iran_resolution_mass_resid):
        v_iran_resolution_mass_resid = None
    return v_iran_resolution_mass_resid
