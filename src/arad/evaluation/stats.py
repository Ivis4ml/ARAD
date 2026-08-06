"""评价机的统计原语（纯 Python，无 numpy 依赖）。

只实现 Merge-Plan-2 §5.4 要求同时报告的量：nominal n、双向 cluster、HAC、
序列相关与块长、Kish n_eff、对斜率的 top-k 影响点。

Kish n_eff **不能替代**双向 cluster、HAC 或 block bootstrap；它只描述权重集中度。
本模块把三者并列返回，正是为了防止只报一个就当作有效样本量。
"""

from __future__ import annotations

import math
import random
from collections import defaultdict


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def ols(y: list[float], x: list[float]) -> tuple[float, float, list[float]]:
    """一元最小二乘。返回 (截距, 斜率, 残差)。"""
    n = len(y)
    if n < 3:
        raise ValueError("最小二乘至少需要 3 个观测")
    if len(x) != n:
        raise ValueError("y 与 x 长度不一致")
    xbar, ybar = mean(x), mean(y)
    sxx = sum((xi - xbar) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("回归元没有变异：斜率不可识别")
    sxy = sum((xi - xbar) * (yi - ybar) for xi, yi in zip(x, y))
    slope = sxy / sxx
    intercept = ybar - slope * xbar
    resid = [yi - intercept - slope * xi for xi, yi in zip(x, y)]
    return intercept, slope, resid


def _meat_by_group(x: list[float], resid: list[float], groups: list) -> float:
    """按组求和的 score 平方和，即 cluster 稳健方差的"肉"部分。"""
    acc: dict = defaultdict(float)
    xbar = mean(x)
    for xi, ei, g in zip(x, resid, groups):
        acc[g] += (xi - xbar) * ei
    return sum(v * v for v in acc.values())


def two_way_cluster_se(
    x: list[float], resid: list[float], cluster_a: list, cluster_b: list
) -> dict:
    """Cameron-Gelbach-Miller 双向 cluster 标准误：V_a + V_b - V_ab。

    单向 cluster 会低估相关结构同时存在于两个维度时的方差。日期与品种
    （或日期与市场）都必须成为 cluster 维，不能只取一个。
    """
    xbar = mean(x)
    sxx = sum((xi - xbar) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("回归元没有变异")
    n_a, n_b = len(set(cluster_a)), len(set(cluster_b))
    v_a = _meat_by_group(x, resid, cluster_a) / (sxx * sxx)
    v_b = _meat_by_group(x, resid, cluster_b) / (sxx * sxx)
    # 某一维只有一组时双向估计量退化：OLS 一阶条件使全样本 score 和恒为零，
    # 于是 V_b == V_ab，双向方差恒等于零。此时必须降级为单向并显式声明，
    # 不能吐一个 NaN 让下游以为"算过了"。
    if n_a < 2 or n_b < 2:
        kept, name = (v_a, "cluster_a") if n_a >= 2 else (v_b, "cluster_b")
        return {
            "variance": kept,
            "se": math.sqrt(kept) if kept > 0 else float("nan"),
            "clusters_a": n_a,
            "clusters_b": n_b,
            "variance_negative": kept <= 0,
            "degenerate_dimension": "cluster_b" if n_b < 2 else "cluster_a",
            "fell_back_to": name,
            "note": (
                "该维只有一组，双向 cluster 退化为恒零；已降级为单向 cluster。"
                "推断的相关结构只覆盖一个维度，须在 Study 中显式声明"
            ),
        }
    both = list(zip(cluster_a, cluster_b))
    v_ab = _meat_by_group(x, resid, both) / (sxx * sxx)
    variance = v_a + v_b - v_ab
    return {
        "variance": variance,
        "se": math.sqrt(variance) if variance > 0 else float("nan"),
        "clusters_a": n_a,
        "clusters_b": n_b,
        "variance_negative": variance <= 0,
        "degenerate_dimension": None,
        "fell_back_to": None,
    }


def newey_west_se(x: list[float], resid: list[float], lag: int) -> dict:
    """Newey-West HAC 标准误。观测须按时间升序排列。"""
    n = len(x)
    if lag < 0:
        raise ValueError("lag 不能为负")
    xbar = mean(x)
    sxx = sum((xi - xbar) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("回归元没有变异")
    u = [(xi - xbar) * ei for xi, ei in zip(x, resid)]
    s = sum(ui * ui for ui in u)
    for k in range(1, min(lag, n - 1) + 1):
        w = 1.0 - k / (lag + 1)
        cov = sum(u[t] * u[t - k] for t in range(k, n))
        s += 2.0 * w * cov
    variance = s / (sxx * sxx)
    return {
        "variance": variance,
        "se": math.sqrt(variance) if variance > 0 else float("nan"),
        "lag": lag,
        "variance_negative": variance <= 0,
    }


def autocorrelation(values: list[float], lag: int = 1) -> float:
    n = len(values)
    if n <= lag:
        return 0.0
    m = mean(values)
    denom = sum((v - m) ** 2 for v in values)
    if denom <= 0:
        return 0.0
    num = sum((values[t] - m) * (values[t - lag] - m) for t in range(lag, n))
    return num / denom


def suggested_block_length(values: list[float]) -> int:
    """由一阶自相关给出的块自助块长建议：rho 越高块越长。"""
    rho = abs(autocorrelation(values, 1))
    rho = min(rho, 0.99)
    n = len(values)
    if rho <= 0:
        return 1
    return max(1, min(n // 2, round((n ** (1 / 3)) * (2 * rho / (1 - rho)) ** (2 / 3))))


def kish_n_eff(weights: list[float]) -> float:
    """Kish 有效样本量。只描述权重集中度，不替代 cluster 与 HAC。"""
    total = sum(weights)
    sq = sum(w * w for w in weights)
    return (total * total / sq) if sq > 0 else 0.0


def cluster_n_eff(groups: list) -> dict:
    """按 cluster 规模给出 nominal n、cluster 数与 Kish n_eff 的并列。"""
    sizes: dict = defaultdict(int)
    for g in groups:
        sizes[g] += 1
    counts = list(sizes.values())
    return {
        "nominal_n": len(groups),
        "clusters": len(counts),
        "kish_n_eff": kish_n_eff([float(c) for c in counts]),
        "largest_cluster_share": (max(counts) / len(groups)) if groups else 0.0,
    }


def influence_on_slope(x: list[float], resid: list[float], top_k: int = 5) -> dict:
    """一步删除对斜率的影响（DFBETA）。报告 top-k 与其占斜率的比例。"""
    n = len(x)
    xbar = mean(x)
    sxx = sum((xi - xbar) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("回归元没有变异")
    deltas = []
    for i in range(n):
        h = 1.0 / n + (x[i] - xbar) ** 2 / sxx
        denom = sxx * (1.0 - h)
        deltas.append(((x[i] - xbar) * resid[i] / denom) if denom > 0 else float("inf"))
    order = sorted(range(n), key=lambda i: -abs(deltas[i]))[:top_k]
    return {
        "top_k": top_k,
        "top_indices": order,
        "top_dfbeta": [deltas[i] for i in order],
        "max_abs_dfbeta": max((abs(d) for d in deltas), default=0.0),
    }


def placebo_slope_distribution(
    y: list[float], x: list[float], groups: list, *, draws: int, seed: int
) -> dict:
    """按 Episode 整块打乱标签的置换检验。

    在 Episode 内部打乱会保留组内相关结构而破坏跨组关系，得到过窄的零分布；
    因此这里整块置换 Episode 与标签的对应关系。
    """
    if draws <= 0:
        raise ValueError("draws 必须为正")
    _, actual, _ = ols(y, x)
    by_group: dict = defaultdict(list)
    for yi, g in zip(y, groups):
        by_group[g].append(yi)
    keys = sorted(by_group)
    rng = random.Random(seed)
    exceed = 0
    slopes = []
    for _ in range(draws):
        shuffled = keys[:]
        rng.shuffle(shuffled)
        mapping = dict(zip(keys, shuffled))
        pool = {k: list(by_group[k]) for k in keys}
        cursor: dict = defaultdict(int)
        y_star = []
        for g in groups:
            src = mapping[g]
            values = pool[src]
            y_star.append(values[cursor[src] % len(values)])
            cursor[src] += 1
        try:
            _, s, _ = ols(y_star, x)
        except ValueError:
            continue
        slopes.append(s)
        if abs(s) >= abs(actual):
            exceed += 1
    return {
        "draws": len(slopes),
        "seed": seed,
        "actual_slope": actual,
        "placebo_exceed_rate": (exceed / len(slopes)) if slopes else 1.0,
        "placebo_slope_sd": (
            math.sqrt(sum((s - mean(slopes)) ** 2 for s in slopes) / len(slopes))
            if len(slopes) > 1
            else 0.0
        ),
    }


def _ranks(values: list[float]) -> list[float]:
    """平均秩。并列取平均，否则并列会给相关系数带来虚假的确定性。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) < 2:
        return float("nan")
    mx, my = mean(x), mean(y)
    num = math.fsum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
    dx = math.sqrt(math.fsum((a - mx) ** 2 for a in x))
    dy = math.sqrt(math.fsum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(_ranks(x), _ranks(y))


def information_coefficient(prediction: list[float], label: list[float]) -> dict:
    """IC。**这是时序 IC，不是截面 IC。**

    截面 IC 要求同一时点上有多个标的可排序；本样本单品种单 session，
    横截面维度不存在（评价机的 product_clusters 会显示为 1）。把时序 IC 叫作 IC
    而不注明，读的人会按截面 IC 的直觉理解它的量级与显著性，那是误导。
    """
    n = len(prediction)
    return {
        "ic_spearman": spearman(prediction, label) if n >= 2 else float("nan"),
        "ic_pearson": pearson(prediction, label) if n >= 2 else float("nan"),
        "n": n,
        "kind": "time_series",
        "note": (
            "时序 IC：同一标的在时间上的秩相关。截面 IC 需要同一时点多个标的，"
            "本样本不具备该维度"
        ),
    }


def moments(values: list[float]) -> dict:
    """样本偏度与超额峰度。DSR 需要它们；正态假设在收益上通常不成立。"""
    n = len(values)
    if n < 4:
        return {"skew": float("nan"), "excess_kurtosis": float("nan"), "n": n}
    m = mean(values)
    var = math.fsum((v - m) ** 2 for v in values) / n
    if var <= 0:
        return {"skew": float("nan"), "excess_kurtosis": float("nan"), "n": n}
    sd = math.sqrt(var)
    skew = math.fsum(((v - m) / sd) ** 3 for v in values) / n
    kurt = math.fsum(((v - m) / sd) ** 4 for v in values) / n - 3.0
    return {"skew": skew, "excess_kurtosis": kurt, "n": n}


def sharpe(returns: list[float], *, periods_per_year: float) -> dict:
    """逐期 Sharpe 与年化。**输入必须是收益，不是任何别的量。**

    调用方要为"这确实是一条收益序列"负责：把已实现波动或吸收比例喂进来会得到一个
    数，但那个数不是 Sharpe。评价机因此把它挡在 `label_is_return` 声明之后。
    """
    n = len(returns)
    if n < 2:
        return {"sharpe": float("nan"), "sharpe_annualised": float("nan"), "n": n}
    m = mean(returns)
    sd = math.sqrt(math.fsum((r - m) ** 2 for r in returns) / (n - 1))
    if sd <= 0:
        return {"sharpe": float("nan"), "sharpe_annualised": float("nan"), "n": n}
    per_period = m / sd
    return {
        "sharpe": per_period,
        "sharpe_annualised": per_period * math.sqrt(periods_per_year),
        "periods_per_year": periods_per_year,
        "n": n,
        "note": "pre-cost：未扣交易成本与容量约束，不得据此声明可交易性",
    }
