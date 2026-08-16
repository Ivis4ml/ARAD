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
    """一步删除对斜率的影响（DFBETA）。报告 top-k、最大杠杆与最大 DFBETA。

    同时给出**只依赖回归元的**最大杠杆 `max_leverage`。它是 DFBETA 里不含残差
    的那一半，因此在读标签之前就可算：一个点的杠杆接近 1，意味着回归元的全部变异
    几乎都来自这一个点，无论标签是什么，斜率都由它决定。
    实测三条真实特征的最大杠杆为 0.022 / 0.607 / 0.119，量级差别很大。

    这里**不给出 DFBETA 与斜率的比值**：`|DFBETA| / |β̂|` 在 β̂ → 0 时发散，
    因此它在「根本没有效应」时最大，而那时并不存在任何被单点主导的结论。
    标准化要用斜率的标准误（Belsley-Kuh-Welsch 的 DFBETAS），由调用方给出标准误后计算。
    """
    n = len(x)
    xbar = mean(x)
    sxx = sum((xi - xbar) ** 2 for xi in x)
    if sxx <= 0:
        raise ValueError("回归元没有变异")
    deltas = []
    leverage = []
    for i in range(n):
        h = 1.0 / n + (x[i] - xbar) ** 2 / sxx
        leverage.append(h)
        denom = sxx * (1.0 - h)
        deltas.append(((x[i] - xbar) * resid[i] / denom) if denom > 0 else float("inf"))
    order = sorted(range(n), key=lambda i: -abs(deltas[i]))[:top_k]
    return {
        "top_k": top_k,
        "top_indices": order,
        "top_dfbeta": [deltas[i] for i in order],
        "max_abs_dfbeta": max((abs(d) for d in deltas), default=0.0),
        "max_leverage": max(leverage, default=0.0),
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


def decoy_slope_distribution(
    y: list[float], x: list[float], *, draws: int, seed: int, min_shift: int = 1
) -> dict:
    """仿冒因子（decoy）的零分布：切断**因子那一侧**的对应关系。

    与 `placebo_slope_distribution` 切的是同一条链的两端，两者互补：

    - 置换检验打乱**标签**，保留真实的因子序列。它的零分布条件于真实的 x，
      但 y 侧的序列结构、体制与肥尾被打乱破坏，零分布可能过窄。
    - 本函数循环平移**因子**，保留真实的标签序列（肥尾、体制、序列相关全在），
      也逐点保留因子自身的边际分布与自相关（平移不改变这两者），
      只破坏 x 与 y 的配对。

    为什么用循环平移而不是打乱因子：打乱会毁掉因子的自相关，而自相关正是
    构造伪迹的主要来源之一（实测：族概率日度变化的九成方差来自构成移动，
    这类结构在打乱后就不存在了，零分布会因此过窄）。平移把它原样保留。

    这条零分布**不依赖「试了多少次」**，因此在单次确认（封存段）上同样成立 ——
    那里没有搜索次数可数，解析地板塌回单次临界值，而本分布仍然给出标尺。
    """
    if draws <= 0:
        raise ValueError("draws 必须为正")
    n = len(x)
    if n != len(y):
        raise ValueError("x 与 y 长度不一致")
    _, actual, _ = ols(y, x)
    rng = random.Random(seed)
    usable = n - 2 * min_shift
    if usable <= 1:
        return {"draws": 0, "seed": seed, "actual_slope": actual,
                "decoy_exceed_rate": 1.0, "note": "样本太短，平移无定义"}
    slopes = []
    exceed = 0
    for _ in range(draws):
        shift = rng.randrange(min_shift, n - min_shift)
        x_star = x[shift:] + x[:shift]
        try:
            _, s, _ = ols(y, x_star)
        except ValueError:
            continue
        slopes.append(s)
        if abs(s) >= abs(actual):
            exceed += 1
    return {
        "draws": len(slopes),
        "seed": seed,
        "min_shift": min_shift,
        "actual_slope": actual,
        # 经验分位：伪因子里有多大比例跑出不小于实际值的 |斜率|。
        # 与 placebo_exceed_rate 同向读：越小越说明实际值不是伪迹能给出的。
        "decoy_exceed_rate": (exceed / len(slopes)) if slopes else 1.0,
        "decoy_slope_sd": (
            math.sqrt(sum((s - mean(slopes)) ** 2 for s in slopes) / len(slopes))
            if len(slopes) > 1 else 0.0
        ),
        "decoy_max_abs_slope": max((abs(s) for s in slopes), default=0.0),
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


def quantile_portfolio(
    prediction: list[float],
    label: list[float],
    *,
    top: float = 0.05,
    bottom: float = 0.05,
) -> dict:
    """分位组合：信号最高的一段做多、最低的一段做空，其余不持仓。

    **与 sign_unit 的区别不是口味问题。**sign_unit 对信号的符号下注，因此它度量的是
    「符号是否指对方向」；分位组合只在信号最极端的两端下注，度量的是「排在最前和最后
    的那些时点是否真的不同」。后者才是因子研究里说的多空组合，也才谈得上超额收益。

    单品种时序上，「超额」的参照是**同期全样本均值**（等权持有一切时点的收益），
    不是无风险利率：本仓库没有资金成本模型，把它当零会高估。
    全部 pre-cost：换手与冲击都不在其中。
    """
    n = len(prediction)
    if n < 20 or not 0 < top <= 0.5 or not 0 < bottom <= 0.5:
        return {"defined": False, "reason": "观测过少或分位设定非法", "n": n}
    order = sorted(range(n), key=lambda i: prediction[i])
    k_bottom = max(1, int(n * bottom))
    k_top = max(1, int(n * top))
    shorts = order[:k_bottom]
    longs = order[-k_top:]
    if set(longs) & set(shorts):
        return {"defined": False, "reason": "多空两端重叠：观测太少或信号取值过于集中",
                "n": n}
    long_ret = mean([label[i] for i in longs])
    short_ret = mean([label[i] for i in shorts])
    benchmark = mean(label)
    spread = long_ret - short_ret
    # 逐期的多空组合收益序列：只有被选中的时点有暴露，其余为零
    weights = [0.0] * n
    for i in longs:
        weights[i] = 1.0 / len(longs)
    for i in shorts:
        weights[i] = -1.0 / len(shorts)
    leg = [w * label[i] * (len(longs) + len(shorts)) / 2 for i, w in enumerate(weights)]
    active = [v for v, w in zip(leg, weights, strict=True) if w != 0.0]
    return {
        "defined": True,
        "n": n,
        "top_quantile": top,
        "bottom_quantile": bottom,
        "n_long": len(longs),
        "n_short": len(shorts),
        "long_mean": long_ret,
        "short_mean": short_ret,
        "benchmark_mean": benchmark,
        "long_short_spread": spread,
        "long_excess": long_ret - benchmark,
        "short_excess": benchmark - short_ret,
        "active_returns": active,
        "note": (
            "pre-cost 多空分位组合。超额的参照是同期全样本均值，不是无风险利率 —— "
            "本仓库没有资金成本模型，把它当零会高估"
        ),
    }


def correlation_matrix(series: dict[str, list[float]], *, method: str = "spearman") -> dict:
    """一组信号两两之间的相关系数。

    因子研究里这张表回答的是「这些想法是不是同一个想法」。同族变体高度相关时，
    多重检验的独立性假设最不成立，而零假设带正是按独立算的 —— 这张表就是那条
    「它偏严」的告诫的量化形式。
    """
    names = sorted(series)
    fn = spearman if method == "spearman" else pearson
    rows = []
    for a in names:
        row = []
        for b in names:
            xs, ys = series[a], series[b]
            pairs = [(x, y) for x, y in zip(xs, ys, strict=False)
                     if math.isfinite(x) and math.isfinite(y)]
            row.append(fn([p[0] for p in pairs], [p[1] for p in pairs])
                       if len(pairs) >= 3 else float("nan"))
        rows.append(row)
    off = [rows[i][j] for i in range(len(names)) for j in range(len(names))
           if i != j and math.isfinite(rows[i][j])]
    return {
        "method": method,
        "names": names,
        "matrix": rows,
        "mean_abs_offdiagonal": mean([abs(v) for v in off]) if off else float("nan"),
        "note": (
            "同族变体高度相关时，零假设带的独立性假设最不成立。"
            "这张表是「带偏严」那句告诫的量化形式"
        ),
    }


def _jacobi_eigenvalues(matrix: list[list[float]], sweeps: int = 60) -> list[float]:
    """对称矩阵的特征值（Jacobi 旋转）。纯 Python，不引 numpy。"""
    n = len(matrix)
    a = [row[:] for row in matrix]
    for _ in range(sweeps):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < 1e-12:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-15:
                    continue
                theta = (a[q][q] - a[p][p]) / (2 * a[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return sorted((a[i][i] for i in range(n)), reverse=True)


def effective_independent_signals(matrix: list[list[float]]) -> dict:
    """一组相关信号相当于多少个**独立信号**。

    用参与率（特征谱的有效模数）：`n_eff = (Σλ)² / Σλ²`。
    完全独立时等于 n，完全共线时等于 1，两个 ρ=0.99 的信号给出 1.01。

    **先试过 Li & Ji 的特征值法，自检没通过就换掉了**：那个估计量对两个 ρ=0.99 的
    信号给出 2.00，也就是把高度相关的两个信号仍当作两次独立检验 —— 它**低估**相关性
    问题，而这里需要的恰恰是不低估。（它为 SNP 那种高维场景设计，低维下行为不同。）

    **这是关于「信号」的陈述，不是关于「检验次数」的陈述。**零假设带按检验独立绘制
    因而偏严；但特征与检验并非一一对应（同一个特征可能被检验多次），把两者混为一谈
    会把带压得过低。因此这里只给出这个数并说明它的含义，不据此重绘任何东西。
    """
    n = len(matrix)
    if n < 2:
        return {"defined": False, "reason": "少于两个信号", "n_signals": n}
    clean = [[v if math.isfinite(v) else (1.0 if i == j else 0.0)
              for j, v in enumerate(row)] for i, row in enumerate(matrix)]
    eig = [max(0.0, v) for v in _jacobi_eigenvalues(clean)]
    total = math.fsum(eig)
    sq = math.fsum(v * v for v in eig)
    if sq <= 0:
        return {"defined": False, "reason": "特征谱退化", "n_signals": n}
    n_eff = (total * total) / sq
    return {
        "defined": True,
        "n_signals": n,
        "effective_independent_signals": min(float(n), max(1.0, n_eff)),
        "eigenvalues_top": [round(v, 4) for v in eig[:5]],
        "method": "participation ratio of the correlation eigenspectrum",
        "note": (
            "这是关于**信号**的陈述，不是关于检验次数的陈述。零假设带按检验独立绘制"
            "因而偏严，但特征与检验并非一一对应，不得据此重绘那条带"
        ),
    }
