"""机制族构造之间的相关结构，以及它把解析地板抬高了多少（决定 0013 §六的更正）。

解析地板 `E₂(n)` 假设 n 次检验相互独立。实际不然：同一族的构造共用底层序列，
彼此相关，因此 n 次尝试的有效独立次数少于 n，真实的「纯噪声能给多好」低于 E₂(n)。

先前的一段论述给出「40 条构造、模拟最大 |z| 期望 2.291、对 E₂(40)=2.4511、
偏严约 0.16」。核对时发现两个问题，本脚本一并修掉：

1. 那些数字没有产出脚本，仓库里复算不出来；
2. 更要紧的是「40」的来历不明：40 是决定 0013 预注册的**回合预算**，
   不是被相关的构造数。拿回合预算去查 E₂ 表，对照的对象就错了。

因此本脚本不去还原「40」，改为把集合的界说清楚再算：**集合 = 机制先验族里
在决策网格上能重新求出信号序列的全部冻结构造**，n 由该集合的大小定，
模拟与对照一律用同一个 n。

方法与两处必须写明的限制：

- 信号序列不是回放存下的数字，而是用冻结规格在 SC 的 discovery 决策网格上
  **重新求值**得到，与作图脚本同一条路径。
- 由信号的相关矩阵推出统计量的相关矩阵，用的是「零假设下对同一个 y 回归不同
  的 x，所得 t 的相关约等于 x 的相关」这一近似。它在零假设下成立，本脚本的
  用途正是零假设参照，但它是近似而非恒等。
- 相关矩阵本身有抽样误差，**该误差没有传播进最终那个差值**。因此结论是一个
  点估计，不是一个带区间的量。

纪律：这段测量**不下调任何门槛**。它与肥尾那一侧（我们的读数比理论噪声更容易
碰出大值，使参照物偏松）方向相反，两者的净效应没有量化，因此现行地板照旧执行。
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import build_report  # 族归属与报告脚本共用一份运行清单

from arad.evaluation.selection import expected_max_abs_z

#: 模拟抽样次数。取到三位小数稳定。
_DRAWS = 20000
_SEED = 20260815


def _pairwise_corr(a: list[float], b: list[float]) -> tuple[float, int] | None:
    """两条序列在**共同有定义**的点上的 Pearson 相关，连同共同点数一并返回。

    共同点数必须随相关系数一起带出来：纯噪声下 |ρ| 的期望是 m 的函数
    （约 sqrt(2/π)/sqrt(m−1)），逐对的 m 差别很大。若拿全集合的最小 m 去定
    一条参照线，参照会被放大到实测之上，读出「实测相关比纯噪声还小」这种
    不可能的结论。参照必须逐对计算再汇总。
    """
    pairs = [(x, y) for x, y in zip(a, b)
             if not math.isnan(x) and not math.isnan(y)]
    if len(pairs) < 30:
        return None
    n = len(pairs)
    mx = sum(x for x, _ in pairs) / n
    my = sum(y for _, y in pairs) / n
    vx = sum((x - mx) ** 2 for x, _ in pairs)
    vy = sum((y - my) ** 2 for _, y in pairs)
    if vx <= 0 or vy <= 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    return cov / math.sqrt(vx * vy), n


def _symmetric_eigen(matrix: list[list[float]]) -> list[float]:
    """对称矩阵的特征值，用 Jacobi 旋转。避免为一个只读脚本引入 numpy 之外的依赖。"""
    import numpy as np

    return sorted(np.linalg.eigvalsh(np.array(matrix)), reverse=True)


def _simulate_max_abs(matrix: list[list[float]], draws: int, seed: int) -> dict:
    """在给定相关矩阵下模拟标准正态向量，返回最大绝对值的分布。

    相关矩阵由样本估计而来，可能有极小的负特征值；作 Cholesky 之前把特征值
    截到非负并重新标准化对角线。截断本身是一次近似，与上文的抽样误差同类。
    """
    import numpy as np

    arr = np.array(matrix, dtype=float)
    values, vectors = np.linalg.eigh(arr)
    clipped = np.clip(values, 1e-10, None)
    psd = vectors @ np.diag(clipped) @ vectors.T
    scale = np.sqrt(np.diag(psd))
    psd = psd / np.outer(scale, scale)
    factor = np.linalg.cholesky(psd + 1e-12 * np.eye(len(psd)))

    rng = np.random.default_rng(seed)
    maxima = np.empty(draws)
    block = 2000
    done = 0
    while done < draws:
        take = min(block, draws - done)
        z = rng.standard_normal((len(psd), take))
        maxima[done:done + take] = np.abs(factor @ z).max(axis=0)
        done += take
    maxima.sort()
    return {
        "expected_max_abs_z": float(maxima.mean()),
        "median_max_abs_z": float(maxima[draws // 2]),
        "p95_max_abs_z": float(maxima[int(draws * 0.95)]),
        "draws": draws,
        "seed": seed,
    }


def measure(ledger_path: str = "data/ledger/service.db") -> dict:
    from arad.harness import demo
    from arad.memory.ledger import EvidenceLedger, Role

    mech_runs = build_report.MECH_RUNS
    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))
        feature_of: dict[str, str] = {}
        for event in events:
            study = event.get("study_id") or ""
            if not study or event["event_type"] != "feature_spec_locked":
                continue
            if study.split("-study-")[0] in mech_runs:
                feature_of[study] = event["payload"].get("feature_id")
        wanted = {fid: sid for sid, fid in feature_of.items() if fid}

        rows, sc, _ = demo._load_sc(
            demo._product_target_path("sc", "sc_rv_next_session"), "discovery")
        signals = demo._signal_values(ledger, sc, rows, list(wanted))

    # 只保留在决策网格上真的取到值的构造。求不出序列的不进集合，
    # 也不假装它们独立：它们根本没有被这次测量覆盖，如实计数。
    usable = {wanted[fid]: values for fid, values in signals.items()
              if sum(1 for v in values if not math.isnan(v)) >= 30}
    studies = sorted(usable)
    n = len(studies)

    pairs = []
    common_counts = []
    matrix = [[1.0] * n for _ in range(n)]
    undefined_pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            got = _pairwise_corr(usable[studies[i]], usable[studies[j]])
            if got is None:
                undefined_pairs += 1
                rho = 0.0   # 共同定义点不足：记 0 并单独计数，不静默丢弃
            else:
                rho, common = got
                pairs.append(abs(rho))
                common_counts.append(common)
            matrix[i][j] = matrix[j][i] = rho

    # 纯噪声参照：逐对按该对自己的共同点数算，再按同一口径汇总
    # （均值对均值、中位对中位）。混着比会得出方向性错误的结论。
    null_means = [math.sqrt(2 / math.pi) / math.sqrt(m - 1) for m in common_counts]
    null_medians = [0.6745 / math.sqrt(m - 1) for m in common_counts]
    pairs.sort()
    eigen = _symmetric_eigen(matrix) if n else []
    simulated = _simulate_max_abs(matrix, _DRAWS, _SEED) if n else {}
    analytic = expected_max_abs_z(n) if n else float("nan")

    # 等价独立次数：使 E₂(k) 等于模拟期望的那个 k。
    equivalent_k = None
    if simulated:
        target = simulated["expected_max_abs_z"]
        for k in range(1, 4 * max(n, 1) + 1):
            if expected_max_abs_z(k) >= target:
                equivalent_k = k
                break

    common_sorted = sorted(common_counts)
    median_common = common_sorted[len(common_sorted) // 2] if common_sorted else 0

    return {
        "measurement": "construction-correlation/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "set_definition": (
            "机制先验族（运行前缀属 build_report.MECH_RUNS）中，"
            "冻结规格能在 SC 的 discovery 决策网格上重新求出至少 30 个有定义点的"
            "全部构造。模拟与解析对照使用同一个 n。"
        ),
        "n_constructions": n,
        "study_ids": studies,
        "undefined_pairs": undefined_pairs,
        "abs_rho": {
            "median": pairs[len(pairs) // 2] if pairs else None,
            "mean": (sum(pairs) / len(pairs)) if pairs else None,
            "share_above_0_5": (
                sum(1 for x in pairs if x > 0.5) / len(pairs)) if pairs else None,
            "n_pairs": len(pairs),
        },
        "pure_noise_reference": {
            "median_common_points": median_common,
            "min_common_points": common_sorted[0] if common_sorted else 0,
            "max_common_points": common_sorted[-1] if common_sorted else 0,
            "abs_rho_mean_under_null": (
                sum(null_means) / len(null_means)) if null_means else None,
            "abs_rho_median_under_null": (
                sorted(null_medians)[len(null_medians) // 2]
                if null_medians else None),
            "note": (
                "逐对按该对自己的共同点数算参照，再按同一口径汇总。"
                "同类比较：均值对均值、中位对中位"
            ),
        },
        "eigenvalues_top10": [float(v) for v in eigen[:10]],
        "n_eigenvalues_above_one": sum(1 for v in eigen if v > 1),
        "marchenko_pastur_upper": (
            (1 + math.sqrt(n / median_common)) ** 2
            if median_common and n else None),
        "simulated_null_max": simulated,
        "analytic_floor_same_n": analytic,
        "floor_over_strict_by": (
            analytic - simulated["expected_max_abs_z"] if simulated else None),
        "equivalent_independent_tests": equivalent_k,
        "caveats": [
            "由信号相关推出统计量相关是零假设下的近似，不是恒等式",
            "相关矩阵的抽样误差未传播进 floor_over_strict_by，该值是点估计",
            "本测量不下调任何门槛：它与肥尾那一侧方向相反，净效应未量化",
        ],
    }


def main() -> None:
    doc = measure()
    out = Path("artifacts/manifests/construction_correlation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    n = doc["n_constructions"]
    rho = doc["abs_rho"]
    ref = doc["pure_noise_reference"]
    print(f"集合：机制先验族中可在决策网格上重新求值的构造 {n} 条"
          f"（{rho['n_pairs']} 对；共同定义点不足的 {doc['undefined_pairs']} 对记 0）")
    print(f"  两两 |ρ|：中位 {rho['median']:.4f}，平均 {rho['mean']:.4f}，"
          f"超过 0.5 的占 {rho['share_above_0_5']:.1%}")
    print(f"  纯噪声参照（逐对按自己的共同点数算；共同点数中位 "
          f"{ref['median_common_points']}，范围 {ref['min_common_points']} 至 "
          f"{ref['max_common_points']}）："
          f"中位 {ref['abs_rho_median_under_null']:.4f}，"
          f"平均 {ref['abs_rho_mean_under_null']:.4f}")
    print(f"    → 中位之比 {rho['median'] / ref['abs_rho_median_under_null']:.2f} 倍，"
          f"平均之比 {rho['mean'] / ref['abs_rho_mean_under_null']:.2f} 倍")
    print(f"  相关矩阵最大特征值 {doc['eigenvalues_top10'][0]:.2f}，"
          f"大于 1 的 {doc['n_eigenvalues_above_one']} 个；"
          f"纯噪声上界（Marchenko-Pastur）约 {doc['marchenko_pastur_upper']:.2f}")
    sim = doc["simulated_null_max"]
    print(f"\n  模拟最大 |z| 期望 {sim['expected_max_abs_z']:.4f}"
          f"（{sim['draws']} 次，种子 {sim['seed']}）")
    print(f"  同一 n 的解析地板 E2({n}) = {doc['analytic_floor_same_n']:.4f}")
    print(f"  → 解析地板偏严 {doc['floor_over_strict_by']:.4f}；"
          f"{n} 次尝试等价于约 {doc['equivalent_independent_tests']} 次独立尝试")
    print("\n  限制：")
    for line in doc["caveats"]:
        print(f"    {line}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
