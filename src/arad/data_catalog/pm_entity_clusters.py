"""候选机制族的自下而上归纳（Decision Map #12 第二层）。

模板层被机器生成的系列淹没（90.6% 单例、加密涨跌梯队占 34%），因此归纳单元下沉到
**实体 token**。这一层仍然完全确定性、不使用任何模型、不写任何分类法：

1. 在归纳期内统计 token 两两共现；
2. 用 PMI 而不是原始共现次数建边 —— PMI 自动压低 `will`/`the`/`by` 这类与什么都
   共现的功能词，因此不需要人写停用词表（停用词表就是把先验固化成真值）；
3. 只在**互为 top-k 近邻**的 token 之间建边，再取连通分量作为候选机制族。
   实测：单靠 PMI 阈值建边会渗流 —— 即使 PMI 阈值提到 5.0，95% 的 token 仍被弱枢纽
   串进同一个巨型分量。互为 top-k 要求 b 在 a 的前 k 强邻居里、同时 a 也在 b 的前 k
   强邻居里，枢纽中介的长链因此被切断。

候选族没有名字，只有 id、成员 token 与规模。命名、金标与跨模型一致性审计是
后续阶段；每个候选族都必须作为**提案**计入 proposal denominator。

阈值不是判断题：`component_size_curve()` 实测不同 PMI 阈值下的分量规模分布，
把"阈值取多少"变成可测量的量，与归纳期切点的处理方式一致。
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict
from dataclasses import dataclass

import pyarrow as pa

from .pm_text_corpus import InductionSpec, _cutoff_epoch, slug_tokens

CLUSTER_VERSION = "0.1.0"


@dataclass(frozen=True)
class ClusterSpec:
    """冻结的聚类参数。任何一项变化都产生一个新的候选族版本。"""

    induction: InductionSpec
    max_tokens: int = 3000
    min_cooccurrence: int = 5
    min_pmi: float = 2.0
    mutual_knn: int = 5
    clustering: str = "modularity"
    resolution: float = 1.0
    version: str = CLUSTER_VERSION

    def describe(self) -> dict:
        return {
            "version": self.version,
            "induction": self.induction.describe(),
            "max_tokens": self.max_tokens,
            "min_cooccurrence": self.min_cooccurrence,
            "min_pmi": self.min_pmi,
            "mutual_knn": self.mutual_knn,
            "clustering": self.clustering,
            "resolution": self.resolution,
            "rule": (
                "只统计归纳期内、按市场数排前 max_tokens 的 token 的两两共现；"
                "PMI 不低于 min_pmi、共现不低于 min_cooccurrence，且两个 token 互为"
                "对方的前 mutual_knn 强邻居时才建边；再按 clustering 划分社区"
                "（缺省带权模块度；connected_components 在近似树上会并成巨型分量，"
                "已作为被弃变体记入分母）。候选族无名字、无语义判断"
            ),
        }


def market_token_sets(
    market_text: pa.Table, presence: pa.Table, spec: ClusterSpec
) -> tuple[list[set[str]], dict[str, int]]:
    """归纳期内每个市场的 token 集合，以及被保留的 token 的市场计数。"""
    cutoff = _cutoff_epoch(spec.induction.induction_cutoff)
    first = dict(
        zip(
            presence.column("condition_id").to_pylist(),
            presence.column("first_trade_ts").to_pylist(),
        )
    )
    raw: list[set[str]] = []
    counts: dict[str, int] = defaultdict(int)
    for cid, base in zip(
        market_text.column("condition_id").to_pylist(),
        market_text.column("slug_base").to_pylist(),
    ):
        ts = first.get(cid)
        if ts is None or ts >= cutoff:
            continue
        tokens = set(slug_tokens(base))
        raw.append(tokens)
        for t in tokens:
            counts[t] += 1
    kept = {
        t
        for t, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[: spec.max_tokens]
        if counts[t] >= spec.induction.min_markets_per_template
    }
    return [s & kept for s in raw], {t: counts[t] for t in kept}


def cooccurrence(sets: list[set[str]]) -> dict[tuple[str, str], int]:
    pairs: dict[tuple[str, str], int] = defaultdict(int)
    for tokens in sets:
        for a, b in itertools.combinations(sorted(tokens), 2):
            pairs[(a, b)] += 1
    return dict(pairs)


def pmi_edges(
    pairs: dict[tuple[str, str], int], counts: dict[str, int], n_markets: int, spec: ClusterSpec
) -> list[tuple[str, str, float, int]]:
    """按 PMI 建边。PMI 天然压低与什么都共现的功能词，无需停用词表。"""
    edges = []
    for (a, b), c in pairs.items():
        if c < spec.min_cooccurrence:
            continue
        p_ab = c / n_markets
        p_a = counts[a] / n_markets
        p_b = counts[b] / n_markets
        if p_a <= 0 or p_b <= 0 or p_ab <= 0:
            continue
        pmi = math.log(p_ab / (p_a * p_b))
        if pmi >= spec.min_pmi:
            edges.append((a, b, pmi, c))
    edges.sort(key=lambda e: (-e[2], e[0], e[1]))
    return mutual_knn_filter(edges, spec.mutual_knn) if spec.mutual_knn else edges


def mutual_knn_filter(
    edges: list[tuple[str, str, float, int]], k: int
) -> list[tuple[str, str, float, int]]:
    """只保留互为 top-k 强邻居的边，切断枢纽中介的长链。

    单靠 PMI 阈值会渗流：一个中等强度的枢纽 token 能把两个语义无关的族接起来。
    互为 top-k 要求双向都认可，这类桥接边会被去掉。
    """
    neighbours: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for a, b, pmi, _ in edges:
        neighbours[a].append((pmi, b))
        neighbours[b].append((pmi, a))
    top: dict[str, set[str]] = {}
    for token, items in neighbours.items():
        items.sort(key=lambda p: (-p[0], p[1]))
        top[token] = {name for _, name in items[:k]}
    return [e for e in edges if e[1] in top.get(e[0], ()) and e[0] in top.get(e[1], ())]


def modularity_communities(
    edges: list[tuple[str, str, float, int]], counts: dict[str, int], *, resolution: float = 1.0
) -> list[dict]:
    """带权模块度社区（Louvain 局部移动，确定性）。

    互为 top-k 之后图已接近一棵树（实测 648 个 token 只有 738 条边、平均度 2.28），
    连通分量必然把整条链并成一族。模块度按边权切断链上最弱的环节，
    因此能把局部强配对分开。

    确定性来源：节点按 (度降序, 名字) 固定顺序遍历，增益相同时取社区标签最小者。
    """
    adj: dict[str, dict[str, float]] = defaultdict(dict)
    for a, b, pmi, _ in edges:
        w = max(pmi, 0.0)
        if w <= 0 or a == b:
            continue
        adj[a][b] = adj[a].get(b, 0.0) + w
        adj[b][a] = adj[b].get(a, 0.0) + w
    if not adj:
        return []
    degree = {n: sum(w.values()) for n, w in adj.items()}
    m = sum(degree.values()) / 2.0
    if m <= 0:
        return []
    community = {n: n for n in adj}
    tot = dict(degree)
    order = sorted(adj, key=lambda n: (-degree[n], n))

    for _ in range(50):
        moved = False
        for node in order:
            current = community[node]
            tot[current] -= degree[node]
            weights: dict[str, float] = defaultdict(float)
            weights[current] += 0.0
            for nb, w in adj[node].items():
                weights[community[nb]] += w
            best, best_gain = current, None
            for cand in sorted(weights):
                gain = weights[cand] / m - resolution * degree[node] * tot.get(cand, 0.0) / (
                    2.0 * m * m
                )
                if best_gain is None or gain > best_gain + 1e-12:
                    best, best_gain = cand, gain
            community[node] = best
            tot[best] = tot.get(best, 0.0) + degree[node]
            if best != current:
                moved = True
        if not moved:
            break

    groups: dict[str, list[str]] = defaultdict(list)
    for node, comm in community.items():
        groups[comm].append(node)
    return _as_families(groups.values(), counts)


def _as_families(groups, counts: dict[str, int]) -> list[dict]:
    out = []
    for members in groups:
        members = sorted(members, key=lambda t: (-counts.get(t, 0), t))
        out.append(
            {
                "family_id": f"cand:{members[0]}",
                "tokens": members,
                "size": len(members),
                "markets_upper_bound": sum(counts.get(t, 0) for t in members),
                "head_tokens": members[:8],
            }
        )
    out.sort(key=lambda g: (-g["markets_upper_bound"], g["family_id"]))
    return out


def connected_components(
    edges: list[tuple[str, str, float, int]], counts: dict[str, int]
) -> list[dict]:
    """确定性连通分量。分量 id 由成员集合的排序决定，不依赖遍历顺序。"""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[max(rx, ry)] = min(rx, ry)

    for a, b, _, _ in edges:
        union(a, b)
    groups: dict[str, list[str]] = defaultdict(list)
    for token in parent:
        groups[find(token)].append(token)
    return _as_families(groups.values(), counts)


def induce_families(
    market_text: pa.Table, presence: pa.Table, spec: ClusterSpec
) -> tuple[list[dict], dict]:
    sets, counts = market_token_sets(market_text, presence, spec)
    pairs = cooccurrence(sets)
    edges = pmi_edges(pairs, counts, max(1, len(sets)), spec)
    if spec.clustering == "modularity":
        families = modularity_communities(edges, counts, resolution=spec.resolution)
    elif spec.clustering == "connected_components":
        families = connected_components(edges, counts)
    else:
        raise ValueError(f"未知的聚类算法 {spec.clustering!r}")
    stats = {
        "spec": spec.describe(),
        "markets_in_induction_period": len(sets),
        "tokens_kept": len(counts),
        "distinct_pairs": len(pairs),
        "edges": len(edges),
        "families": len(families),
        "largest_family_tokens": families[0]["size"] if families else 0,
        "tokens_in_families": sum(f["size"] for f in families),
        "isolated_tokens": len(counts) - sum(f["size"] for f in families),
    }
    return families, stats


def component_size_curve(
    market_text: pa.Table, presence: pa.Table, spec: ClusterSpec, thresholds: list[float]
) -> list[dict]:
    """不同 PMI 阈值下的分量结构。把阈值选择变成可测量的量。"""
    sets, counts = market_token_sets(market_text, presence, spec)
    pairs = cooccurrence(sets)
    n = max(1, len(sets))
    out = []
    for threshold in thresholds:
        trial = ClusterSpec(
            induction=spec.induction,
            max_tokens=spec.max_tokens,
            min_cooccurrence=spec.min_cooccurrence,
            min_pmi=threshold,
        )
        edges = pmi_edges(pairs, counts, n, trial)
        families = connected_components(edges, counts)
        largest = families[0]["size"] if families else 0
        out.append(
            {
                "min_pmi": threshold,
                "edges": len(edges),
                "families": len(families),
                "largest_family_tokens": largest,
                "largest_family_share": (
                    largest / sum(f["size"] for f in families) if families else 0.0
                ),
                "tokens_in_families": sum(f["size"] for f in families),
            }
        )
    return out
