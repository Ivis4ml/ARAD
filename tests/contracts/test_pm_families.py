"""候选机制族归纳与提案登记的合同测试（#12 第二层）。

这一层仍然不写任何分类法：族没有名字，只有 id、成员 token 与规模。
"""

from __future__ import annotations

import json
import os

import pyarrow as pa
import pytest

from arad.data_catalog.pm_entity_clusters import (
    ClusterSpec,
    connected_components,
    cooccurrence,
    mutual_knn_filter,
    pmi_edges,
)
from arad.data_catalog.pm_text_corpus import InductionSpec

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAMILIES = os.path.join(REPO, "artifacts", "manifests", "pm_candidate_families.json")

EARLY = 1_700_000_000


def spec(**kw) -> ClusterSpec:
    base = {
        "induction": InductionSpec("2024-01-01", min_markets_per_template=1),
        "max_tokens": 100,
        "min_cooccurrence": 1,
        "min_pmi": 0.5,
        "mutual_knn": 0,
    }
    base.update(kw)
    return ClusterSpec(**base)


def corpus(bases):
    return pa.table(
        {
            "condition_id": pa.array([f"c{i}" for i in range(len(bases))], pa.string()),
            "slug_base": pa.array(bases, pa.string()),
        }
    ), pa.table(
        {
            "condition_id": pa.array([f"c{i}" for i in range(len(bases))], pa.string()),
            "first_trade_ts": pa.array([EARLY] * len(bases), pa.int64()),
        }
    )


# ---------------------------------------------------------------- PMI


def test_pmi_downweights_tokens_that_cooccur_with_everything():
    """`will` 与所有东西共现，PMI 接近零；这就是不需要人写停用词表的原因。"""
    sets = [{"will", "oil", "opec"}, {"will", "nba", "lakers"}, {"will", "oil", "opec"}]
    counts = {"will": 3, "oil": 2, "opec": 2, "nba": 1, "lakers": 1}
    pairs = cooccurrence(sets)
    edges = pmi_edges(pairs, counts, len(sets), spec(min_pmi=0.1, mutual_knn=0))
    named = {(a, b): pmi for a, b, pmi, _ in edges}
    assert named[("oil", "opec")] > 0
    assert ("oil", "will") not in named and ("will", "oil") not in named


def test_edges_are_deterministic_and_sorted():
    sets = [{"a", "b"}, {"a", "b"}, {"c", "d"}, {"c", "d"}]
    counts = {"a": 2, "b": 2, "c": 2, "d": 2}
    pairs = cooccurrence(sets)
    first = pmi_edges(pairs, counts, 4, spec(mutual_knn=0))
    second = pmi_edges(pairs, counts, 4, spec(mutual_knn=0))
    assert first == second
    assert [e[2] for e in first] == sorted((e[2] for e in first), reverse=True)


# ---------------------------------------------------------------- 互为 top-k


def test_mutual_knn_cuts_hub_mediated_bridges():
    """枢纽把两个无关族接起来的桥接边必须被切断（实测的渗流问题）。"""
    edges = [
        ("a", "b", 9.0, 10), ("b", "c", 9.0, 10),      # 族一
        ("x", "y", 9.0, 10), ("y", "z", 9.0, 10),      # 族二
        ("c", "hub", 1.0, 5), ("hub", "x", 1.0, 5),    # 弱枢纽桥接
    ]
    kept = mutual_knn_filter(edges, k=1)
    names = {(a, b) for a, b, _, _ in kept}
    assert ("a", "b") in names or ("b", "c") in names
    assert ("c", "hub") not in names and ("hub", "x") not in names


def test_mutual_knn_zero_keeps_every_edge():
    edges = [("a", "b", 1.0, 1), ("c", "d", 1.0, 1)]
    assert mutual_knn_filter(edges, k=10) == edges


# ---------------------------------------------------------------- 分量


def test_components_are_deterministic_regardless_of_edge_order():
    counts = {"a": 3, "b": 2, "c": 1, "x": 3, "y": 2}
    edges = [("a", "b", 5.0, 3), ("b", "c", 4.0, 2), ("x", "y", 6.0, 3)]
    first = connected_components(edges, counts)
    second = connected_components(list(reversed(edges)), counts)
    assert [f["family_id"] for f in first] == [f["family_id"] for f in second]
    assert [f["tokens"] for f in first] == [f["tokens"] for f in second]


def test_families_carry_no_name_and_no_product_mapping():
    """族只有 id、成员与规模；命名与商品映射不在本层。"""
    counts = {"iran": 5, "israel": 4}
    families = connected_components([("iran", "israel", 6.0, 4)], counts)
    assert set(families[0]) == {
        "family_id", "tokens", "size", "markets_upper_bound", "head_tokens"
    }
    assert families[0]["family_id"].startswith("cand:")


def test_induction_only_uses_markets_inside_the_period():
    from arad.data_catalog.pm_entity_clusters import market_token_sets

    text, presence = corpus(["oil-opec", "nba-lakers"])
    presence = pa.table(
        {
            "condition_id": presence.column("condition_id"),
            "first_trade_ts": pa.array([EARLY, 1_900_000_000], pa.int64()),
        }
    )
    sets, counts = market_token_sets(text, presence, spec())
    assert len(sets) == 1
    assert "nba" not in counts


# ---------------------------------------------------------------- 提案登记


def test_every_family_is_recorded_in_the_proposal_denominator(tmp_path):
    from arad.data_catalog.pm_family_proposals import FAMILY_NAMESPACE, register_families
    from arad.memory.ledger import EvidenceLedger

    bases = ["oil-opec"] * 6 + ["nba-lakers"] * 6 + ["iran-israel"] * 2
    text, presence = corpus(bases)
    totals = pa.table(
        {
            "condition_id": text.column("condition_id"),
            "trades": pa.array([10] * len(bases), pa.int64()),
            "notional": pa.array([1.0] * len(bases), pa.float64()),
        }
    )
    with EvidenceLedger(str(tmp_path / "l.db")) as ledger:
        report = register_families(
            ledger, text, presence, totals, spec(min_pmi=0.1, mutual_knn=2), min_markets=5
        )
        d = ledger.denominators(FAMILY_NAMESPACE)
    assert report["families_registered"] == d["proposal_denominator"]
    # 规模不足的族照样进分母，只是标为被挡下
    assert report["families_screened_out"] == d["proposals_screened_out"]
    assert report["families_screened_out"] >= 1
    for family in report["families"]:
        if family["screened_out"]:
            assert family["markets"] < 5


def test_registration_is_label_blind_and_target_unbound(tmp_path):
    """族登记时不绑定 target：族→商品是经济假设，属各 Study 的 Hypothesis Lock。"""
    from arad.data_catalog.pm_family_proposals import register_families
    from arad.memory.ledger import EvidenceLedger, Role

    # 需要两个互不相交的组，PMI 才为正：单一组时 p(a,b)=p(a)=p(b)，PMI 为零
    bases = ["oil-opec"] * 6 + ["nba-lakers"] * 6
    text, presence = corpus(bases)
    totals = pa.table(
        {
            "condition_id": text.column("condition_id"),
            "trades": pa.array([1] * len(bases), pa.int64()),
            "notional": pa.array([1.0] * len(bases), pa.float64()),
        }
    )
    with EvidenceLedger(str(tmp_path / "l.db")) as ledger:
        register_families(ledger, text, presence, totals, spec(mutual_knn=2), min_markets=1)
        events = ledger.read_events(role=Role.EVALUATOR)
    locked = [e for e in events if e["event_type"] == "candidate_family_registered"]
    assert locked
    for event in locked:
        payload = event["payload"]
        assert "product" not in payload and "target" not in payload
        assert set(payload) == {
            "family_id", "proposal_id", "tokens", "head_tokens", "sizing", "screened_out"
        }
        # 规模统计只含市场数、成交与名义额，不含任何商品或标签信息
        assert set(payload["sizing"]) <= {
            "cutoff", "markets", "markets_share", "trades", "trades_share",
            "notional_provisional", "notional_share_provisional", "universe",
        }


# ---------------------------------------------------------------- 产物


@pytest.mark.skipif(not os.path.exists(FAMILIES), reason="需要先运行 pm-index families")
def test_artifact_records_families_without_naming_them():
    with open(FAMILIES, encoding="utf-8") as f:
        report = json.load(f)
    assert report["families_registered"] == report["denominators"]["proposal_denominator"]
    assert report["spec"]["mutual_knn"] >= 1
    for family in report["families"]:
        assert family["family_id"].startswith("cand:")
        assert "name" not in family and "product" not in family


# ---------------------------------------------------------------- 管线变体


def test_every_explored_pipeline_variant_enters_the_proposal_denominator(tmp_path):
    """超参数是在观察『商品族是否浮现』时调出的，被弃变体必须各计一条提案。"""
    from arad.data_catalog.pm_pipeline_variants import (
        EXPLORED_VARIANTS,
        VARIANT_NAMESPACE,
        register_variants,
    )
    from arad.memory.ledger import EvidenceLedger

    with EvidenceLedger(str(tmp_path / "l.db")) as ledger:
        report = register_variants(ledger)
        d = ledger.denominators(VARIANT_NAMESPACE)
    assert report["variants_recorded"] == len(EXPLORED_VARIANTS) == d["proposal_denominator"]
    assert report["variants_abandoned"] == d["proposals_screened_out"]
    assert report["variants_abandoned"] == len(EXPLORED_VARIANTS) - 1  # 只有一个被采纳


def test_every_abandoned_variant_states_why():
    from arad.data_catalog.pm_pipeline_variants import EXPLORED_VARIANTS

    for variant in EXPLORED_VARIANTS:
        assert variant.outcome, variant.variant_id
        if not variant.adopted:
            assert variant.abandoned_reason, variant.variant_id


def test_exactly_one_variant_is_adopted_and_matches_the_shipped_config():
    """记录的采纳变体必须与实际跑的配置一致，否则审计记录是假的。"""
    import yaml

    from arad.data_catalog.pm_pipeline_variants import EXPLORED_VARIANTS

    adopted = [v for v in EXPLORED_VARIANTS if v.adopted]
    assert len(adopted) == 1
    params = adopted[0].params
    with open(os.path.join(REPO, "configs", "pm_index.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)["families"]
    assert cfg["induction_cutoff"] == params["induction_cutoff"]
    assert cfg["max_tokens"] == params["max_tokens"]
    assert cfg["min_pmi"] == params["min_pmi"]
    assert cfg["mutual_knn"] == params["mutual_knn"]
    assert cfg["clustering"] == params["clustering"]
    assert cfg["resolution"] == params["resolution"]


def test_connected_components_variant_is_recorded_as_abandoned():
    """连通分量在近似树上会并成巨型分量，已被弃；记录必须留着。"""
    from arad.data_catalog.pm_pipeline_variants import EXPLORED_VARIANTS

    cc = [v for v in EXPLORED_VARIANTS if v.params.get("clustering") == "connected_components"]
    assert cc
    assert all(not v.adopted for v in cc)
    assert any("巨型分量" in v.abandoned_reason or "近似树" in v.abandoned_reason for v in cc)


def test_unknown_clustering_algorithm_is_rejected():
    import pyarrow as _pa

    from arad.data_catalog.pm_entity_clusters import induce_families

    text = _pa.table(
        {"condition_id": _pa.array(["a"]), "slug_base": _pa.array(["oil-opec"])}
    )
    pres = _pa.table(
        {"condition_id": _pa.array(["a"]), "first_trade_ts": _pa.array([EARLY], _pa.int64())}
    )
    with pytest.raises(ValueError, match="未知的聚类算法"):
        induce_families(text, pres, spec(clustering="whatever", mutual_knn=0))
