"""选择校正：把"看了多少次"变成图上的一条线（M9.1）。

一条随迭代上升的指标曲线，正是选择在纯噪声上必然产出的形状。旧系统的实测就摆在
那里：81 次爬山选出的最好 Sharpe 是 2.40，而同一套搜索过程在零假设下的期望是 2.63 ——
曲线在涨，实际比噪声还差。只画"每次尝试"与"running best"两条线的 app 会系统性地骗人。

因此本模块只做一件事：给定**这一族看过多少次 outcome**，算出零假设下同样次数的搜索
所能达到的水平，作为曲线上的一条带。次数取自账本的 statistical denominator ——
它只增不减，正是为此存在。

三条边界：

1. **只读账本，不重算任何统计量。**每个 Study 的 |t|、IC 来自评价机存下的
   `evaluation_result`，这里只做跨 Study 的聚合与阈值计算。
2. **阈值是"期望最大值"，不是显著性检验。**它回答的是"如果全是噪声，看这么多次
   最好的一次大概能有多好"，用于读图，不构成判决。判决仍由评价机出具。
3. **不做多重检验校正后的 p 值。**那需要检验之间的相关结构，而同一族里的变体高度
   相关，独立性假设会把阈值算得过严。这里给的是独立情形下的上界，图上如实标注。
"""

from __future__ import annotations

import math

#: 欧拉常数。Bailey & López de Prado 的期望最大值近似要用到它。
_EULER = 0.5772156649015329


def _inv_norm_cdf(p: float) -> float:
    """标准正态分位数（Acklam 近似）。不引入 scipy 依赖。"""
    if not 0.0 < p < 1.0:
        return float("nan")
    a = (-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00)
    b = (-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00)
    lo, hi = 0.02425, 1 - 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > hi:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _expected_max(n_trials: int, *, tail: float) -> float:
    """n 次独立标准正态抽样的最大值期望（Bailey & López de Prado 近似）。

    `tail` 是单次抽样落在阈值之外的概率份额：单侧取 1，双侧取 2。
    """
    if n_trials < 1:
        return float("nan")
    n = float(n_trials)
    return (1 - _EULER) * _inv_norm_cdf(1 - 1 / (tail * n)) + _EULER * _inv_norm_cdf(
        1 - 1 / (tail * n * math.e)
    )


def expected_max_z(n_trials: int) -> float:
    """n 次独立试验下**有符号**统计量最大值的期望。

    用于 Sharpe 这类只朝一个方向挑选的量：搜索留下的是 Sharpe 最大的那个，
    不是 |Sharpe| 最大的那个。用双侧形式会把零假设水平抬高约 1.5 倍。
    """
    if n_trials == 1:
        return 0.0                          # 单次抽样的期望就是均值
    return _expected_max(n_trials, tail=1.0)


def expected_max_abs_z(n_trials: int) -> float:
    """n 次独立检验下 **|z|** 最大值的期望（近似）。

    这是 |t| 曲线上那条带：如果全是噪声，看 n 次，最好的一次大概能到多高。
    用双侧是因为搜索接受任一方向的显著结果。

    独立假设使它偏严 —— 同一族里的变体高度相关，真实的期望最大值更低。
    图上必须标注这一点，否则读的人会把"没越过带"误读成"确定无效"。
    """
    if n_trials < 1:
        return float("nan")
    if n_trials == 1:
        return math.sqrt(2 / math.pi)      # 半正态的均值
    return _expected_max(n_trials, tail=2.0)


def expected_max_sharpe(n_trials: int, sharpe_sd_across_trials: float) -> float:
    """n 次试验下 Sharpe 最大值的期望（Bailey & López de Prado）。

    `sharpe_sd_across_trials` 是**同一族内各次试验 Sharpe 的标准差** ——
    它衡量这套搜索过程本身的噪声幅度，只能从实际试过的那些试验里估，
    不能假设。族内不足两次试验时无定义。
    """
    if n_trials < 2 or not math.isfinite(sharpe_sd_across_trials) or \
            sharpe_sd_across_trials <= 0:
        return float("nan")
    return sharpe_sd_across_trials * expected_max_z(n_trials)


def deflated_sharpe(
    observed_sharpe: float,
    *,
    benchmark_sharpe: float,
    n_periods: int,
    skew: float = 0.0,
    excess_kurtosis: float = 0.0,
) -> float:
    """紧缩 Sharpe：观测 Sharpe 真正超过选择基准的概率。

    `benchmark_sharpe` 应取 `expected_max_sharpe`，即同样搜索次数下噪声的期望上限。
    偏度与超额峰度进入方差修正：肥尾与负偏会让 Sharpe 的估计误差变大。
    """
    if not all(math.isfinite(v) for v in (observed_sharpe, benchmark_sharpe)) \
            or n_periods < 2:
        return float("nan")
    variance = (
        1.0 - skew * observed_sharpe
        + (excess_kurtosis / 4.0) * observed_sharpe ** 2
    )
    if variance <= 0:
        return float("nan")
    z = (observed_sharpe - benchmark_sharpe) * math.sqrt(n_periods - 1) / math.sqrt(variance)
    return _norm_cdf(z)


def selection_band(points: list[dict], *, metric: str = "abs_t") -> list[dict]:
    """把一串按顺序发生的试验变成曲线数据：每点的值、running best、零假设带。

    `points` 每项至少含 `value`（该次试验的指标）与 `counts_toward_denominator`
    （这次是否读过 outcome）。带的高度只随**读过 outcome 的次数**上升 ——
    被预检挡下、判 blocked 而未读 outcome 的轮次不抬高多重检验负担，但它们仍留在
    图上，因为它们是提案分母的一部分。
    """
    out: list[dict] = []
    looked = 0
    best = float("-inf")
    for i, point in enumerate(points):
        if point.get("counts_toward_denominator"):
            looked += 1
        value = point.get("value")
        if value is not None and math.isfinite(value) and value > best:
            best = value
        threshold = (
            expected_max_abs_z(looked) if metric == "abs_t" and looked >= 1 else None
        )
        out.append(
            {
                **point,
                "index": i,
                "tests_so_far": looked,
                "running_best": best if math.isfinite(best) else None,
                "null_threshold": threshold,
            }
        )
    return out
