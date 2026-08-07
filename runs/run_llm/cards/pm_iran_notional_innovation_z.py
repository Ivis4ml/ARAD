"""pm_iran_notional_innovation_z

机制：cand:iran 族名义成交量的日度异常，相对其 30 日基线取 innovation，再以过去 90 日的日度采样分布做标准化。取值越高表示对伊朗/航运/袭击类事件的资金关注度越偏离自身常态，代表一次尚未被商品盘面吸收的供给风险重估。

失败条件：以下任一情形出现时，本特征应判为无效而非弱有效：(1) 有效样本不足 —— cand:iran 序列起于 2023-01-09，叠加 30 日基线与 90 日 z 窗口的预热期，特征在 2023 年二季度之前无定义；相对 1040 行的特征范围，可用行数显著低于该数，若可用行数不足以支撑分位比较，结果应判为不确定而非否证。(2) 该族约 18787 个小时桶分布于三年半区间，存在稀疏段；若某日 24 小时名义成交量为零或近零，innovation 与其后的 z 值将由基线主导而非由真实关注度主导，此类样本应被识别并剔除。(3) 自相关混淆 —— 若该特征的预测力在控制商品自身已实现波动率的持续性之后消失，则其经济含义不成立；本轮无法直接检验（residualise 尚未实现），因此该检验须在后续提案中补足。(4) 反向因果 —— 若关注度跳升实际发生于商品盘面波动之后（预测市场在追随而非领先），则机制方向被推翻。

**本文件由 `arad.features.codegen` 从冻结规格确定性生成，请勿手改。**
规格内容身份 24f6c3935bdc84c71d8be4fe96eccae03a6c3bf7ab9e4d4f91ed3c81b397bfc2
生成器 0.1.0；改规格才能改代码，两者不可能不一致。

PIT：每个窗口的右端点一律**不含**决策时点，offset 只能非负。
无定义返回 None，绝不返回 0 —— 返回 0 会被下游当成「没有信号」，那是伪造。
本特征最早触及 2881时 前的数据；该深度未整段落在序列覆盖范围内时判为无定义。
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import datetime, timedelta

REQUIRED_LOOKBACK_SECONDS = 10371600


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


def _at_iran_notional_innov(at: datetime, series: dict):
    """在任意过去时刻求 iran_notional_innov 的值。zscore 的参考分布要用它。"""
    t, x = series["pm_market.cand:iran:notional"]
    end = at - timedelta(seconds=3600)
    v_iran_notional_innov = _agg("sum", _window(t, x, end, 86400))
    far = _agg("sum", _window(t, x, end, 2592000))
    v_iran_notional_innov = (v_iran_notional_innov - far) if _ok(v_iran_notional_innov) and _ok(far) else None
    return v_iran_notional_innov

def compute(decision_time: datetime, series: dict, coverage_start=None):
    """在一个决策时点上求值。无定义返回 None。"""
    # 覆盖准入：回看深度必须整段落在序列覆盖范围内，否则同一份规格在完整
    # 序列与其截断副本上会给出不同的数，而没有任何记录能看出差别
    if coverage_start is not None and (
        decision_time - timedelta(seconds=REQUIRED_LOOKBACK_SECONDS)
        < coverage_start
    ):
        return None
    t_iran_notional_innov, x_iran_notional_innov = series["pm_market.cand:iran:notional"]
    end_iran_notional_innov = decision_time - timedelta(seconds=3600)
    v_iran_notional_innov = _agg("sum", _window(t_iran_notional_innov, x_iran_notional_innov, end_iran_notional_innov, 86400))
    far_iran_notional_innov = _agg("sum", _window(t_iran_notional_innov, x_iran_notional_innov, end_iran_notional_innov, 2592000))
    v_iran_notional_innov = (v_iran_notional_innov - far_iran_notional_innov) if _ok(v_iran_notional_innov) and _ok(far_iran_notional_innov) else None
    if v_iran_notional_innov is not None and not math.isfinite(v_iran_notional_innov):
        v_iran_notional_innov = None
    # zscore：参考样本取自规格自己声明的采样网格，严格取自过去
    samples_iran_notional_innov_z = []
    for k in range(1, 90 + 1):
        past = decision_time - timedelta(seconds=k * 86400)
        s = _at_iran_notional_innov(past, series)
        if _ok(s):
            samples_iran_notional_innov_z.append(s)
    distinct_iran_notional_innov_z = len(set(samples_iran_notional_innov_z))
    if not _ok(v_iran_notional_innov) or distinct_iran_notional_innov_z < 30:
        v_iran_notional_innov_z = None
    else:
        mu = math.fsum(samples_iran_notional_innov_z) / len(samples_iran_notional_innov_z)
        sd = math.sqrt(math.fsum((s - mu) ** 2 for s in samples_iran_notional_innov_z) / (len(samples_iran_notional_innov_z) - 1))
        v_iran_notional_innov_z = ((v_iran_notional_innov - mu) / sd) if sd > 0 else None
    if v_iran_notional_innov_z is not None and not math.isfinite(v_iran_notional_innov_z):
        v_iran_notional_innov_z = None
    return v_iran_notional_innov_z
