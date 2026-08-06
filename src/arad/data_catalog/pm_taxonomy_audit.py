"""分类法后见暴露的实证检验（决定 0004 的检验 a 与 b）。

不做判断，只把"全史归纳带来多少选择偏差"变成可计算的量。

- **(a) 族涌现日期曲线**：每个族在哪个归纳期切点首次出现。
- **(b) 结果相邻性检验**：族的历史活动落在 |SC 日收益| 顶部十分位日上的份额。
  这是直接测量偏差通道的主指标：若晚涌现的族系统性地更集中在大波动日上，
  就定量证明了全史归纳在与结果相关的通道上做了选择。
"""

from __future__ import annotations

import math
import random
from collections import defaultdict

import pyarrow as pa

from .pm_entity_clusters import ClusterSpec, induce_families
from .pm_text_corpus import InductionSpec


def _families_at(market_text, presence, spec: ClusterSpec) -> list[dict]:
    families, _ = induce_families(market_text, presence, spec)
    return families


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def emergence_curve(
    market_text: pa.Table,
    presence: pa.Table,
    base_spec: ClusterSpec,
    cutoffs: list[str],
    *,
    match_threshold: float = 0.5,
) -> dict:
    """检验 (a)：每个最终族最早在哪个切点出现（token 集 Jaccard 最优匹配）。"""
    final = _families_at(market_text, presence, base_spec)
    earlier = {}
    for cutoff in sorted(cutoffs):
        spec = ClusterSpec(
            induction=InductionSpec(
                cutoff, min_markets_per_template=base_spec.induction.min_markets_per_template
            ),
            max_tokens=base_spec.max_tokens,
            min_cooccurrence=base_spec.min_cooccurrence,
            min_pmi=base_spec.min_pmi,
            mutual_knn=base_spec.mutual_knn,
            clustering=base_spec.clustering,
            resolution=base_spec.resolution,
        )
        earlier[cutoff] = [set(f["tokens"]) for f in _families_at(market_text, presence, spec)]

    rows = []
    for family in final:
        tokens = set(family["tokens"])
        emergence = None
        for cutoff in sorted(cutoffs):
            if any(jaccard(tokens, other) >= match_threshold for other in earlier[cutoff]):
                emergence = cutoff
                break
        rows.append(
            {
                "family_id": family["family_id"],
                "size": family["size"],
                "head_tokens": family["head_tokens"],
                "emergence_cutoff": emergence or base_spec.induction.induction_cutoff,
                "emerged_only_at_final_cutoff": emergence is None,
            }
        )
    late = sum(1 for r in rows if r["emerged_only_at_final_cutoff"])
    return {
        "final_cutoff": base_spec.induction.induction_cutoff,
        "probe_cutoffs": sorted(cutoffs),
        "match_threshold": match_threshold,
        "families": len(rows),
        "families_emerging_only_at_final_cutoff": late,
        "hindsight_exposure": late / len(rows) if rows else 0.0,
        "detail": rows,
    }


def outcome_adjacency(
    market_text: pa.Table,
    market_day: pa.Table,
    families: list[dict],
    emergence: dict,
    daily_returns: dict[str, float],
    *,
    top_decile: float = 0.1,
    permutations: int = 500,
    seed: int = 20260805,
) -> dict:
    """检验 (b)：族活动在大波动日上的集中度，按涌现早晚分组比较。

    daily_returns 的键是 UTC 日期字符串，值是当日 SC 对数收益。
    不读取任何 Study 的 target，只用公开的日频价格构造"大波动日"集合。
    """
    ranked = sorted(daily_returns, key=lambda d: -abs(daily_returns[d]))
    n_top = max(1, int(len(ranked) * top_decile))
    top_days = set(ranked[:n_top])

    token_to_family: dict[str, str] = {}
    for family in families:
        for token in family["tokens"]:
            token_to_family.setdefault(token, family["family_id"])
    from .pm_text_corpus import slug_tokens

    market_family: dict[str, str] = {}
    for cid, base in zip(
        market_text.column("condition_id").to_pylist(),
        market_text.column("slug_base").to_pylist(),
    ):
        hits = {token_to_family[t] for t in slug_tokens(base) if t in token_to_family}
        if len(hits) == 1:
            market_family[cid] = next(iter(hits))

    activity: dict[str, dict[str, int]] = defaultdict(lambda: {"top": 0, "all": 0})
    for date_str, cid, trades in zip(
        market_day.column("date").to_pylist(),
        market_day.column("condition_id").to_pylist(),
        market_day.column("trades").to_pylist(),
    ):
        family = market_family.get(cid)
        if family is None or date_str not in daily_returns:
            continue
        activity[family]["all"] += trades
        if date_str in top_days:
            activity[family]["top"] += trades

    late = {r["family_id"] for r in emergence["detail"] if r["emerged_only_at_final_cutoff"]}
    groups: dict[str, list[float]] = {"late": [], "early": []}
    for family_id, acc in activity.items():
        if acc["all"] <= 0:
            continue
        share = acc["top"] / acc["all"]
        groups["late" if family_id in late else "early"].append(share)

    def mean(v: list[float]) -> float:
        return sum(v) / len(v) if v else 0.0

    observed = mean(groups["late"]) - mean(groups["early"])
    pooled = groups["late"] + groups["early"]
    n_late = len(groups["late"])
    rng = random.Random(seed)
    exceed = 0
    for _ in range(permutations):
        shuffled = pooled[:]
        rng.shuffle(shuffled)
        diff = mean(shuffled[:n_late]) - mean(shuffled[n_late:])
        if abs(diff) >= abs(observed):
            exceed += 1
    sd = (
        math.sqrt(sum((v - mean(pooled)) ** 2 for v in pooled) / len(pooled))
        if len(pooled) > 1
        else 0.0
    )
    return {
        "top_decile": top_decile,
        "top_days": len(top_days),
        "days_with_returns": len(daily_returns),
        "families_with_activity": len(activity),
        "late_families": n_late,
        "early_families": len(groups["early"]),
        "mean_top_share_late": mean(groups["late"]),
        "mean_top_share_early": mean(groups["early"]),
        "observed_difference": observed,
        "effect_size_in_sd": (observed / sd) if sd > 0 else 0.0,
        "permutations": permutations,
        "seed": seed,
        "permutation_p_value": exceed / permutations if permutations else 1.0,
        "interpretation": (
            "晚涌现族的活动若系统性更集中在大波动日上，即定量证明全史归纳"
            "在与结果相关的通道上做了选择；差值不显著则说明该通道的偏差在本样本上不可检出"
        ),
    }
