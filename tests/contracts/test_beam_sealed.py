"""Beam search、封闭段与组合的合同测试（M7）。

这一层的存在理由是：**加强优化器之前必须先改 reward**。若 reward 取评估段上的 |t|，
搜索越强观测到的最好值越高，即使底下什么都没有。因此测试盯的是自惩罚是否真的成立、
封条能否被揭第二次、以及组合会不会收敛成同一个想法的若干写法。
"""

from __future__ import annotations

import pytest

from arad.evaluation.sealed import (
    SealedAlreadyOpened,
    assert_unopened,
    open_sealed,
    seal_key,
)
from arad.evaluation.selection import expected_max_abs_z
from arad.harness.beam import Beam, Candidate, greedy_ensemble
from arad.memory.ledger import EvidenceLedger
from arad.registry.specs import TaxonomyContamination

CONTAMINATED = TaxonomyContamination(
    taxonomy_id="pm_candidate_families/0.1.0",
    taxonomy_freeze_at="2026-08-01",
    induction_corpus_max_date="2026-08-01",
    outcome_read_intervals=[("2025-01-02", "2025-12-31")],
)


@pytest.fixture
def ledger(tmp_path):
    with EvidenceLedger(str(tmp_path / "l.db")) as led:
        yield led


# ------------------------------------------------------------ reward 自惩罚


def test_the_same_statistic_earns_less_the_later_it_is_found():
    """这是整套东西的支点：多搜索不该自动提高 reward。"""
    early = Candidate("f", "s", value=2.0, tests_at_evaluation=1)
    middle = Candidate("f", "s", value=2.0, tests_at_evaluation=5)
    late = Candidate("f", "s", value=2.0, tests_at_evaluation=15)
    assert early.reward > middle.reward > late.reward
    # 第 15 次时 |t|=2.0 已在噪声地板之下，reward 为负
    assert late.reward < 0
    assert early.reward == pytest.approx(2.0 - expected_max_abs_z(1))


def test_the_beam_ranks_by_reward_not_by_the_raw_statistic():
    """按原始 |t| 排会让束的头部被「试得更多」这件事推高。"""
    beam = Beam(width=2)
    beam.offer(Candidate("late_big", "s1", value=2.4, tests_at_evaluation=40))
    beam.offer(Candidate("early_small", "s2", value=1.6, tests_at_evaluation=1))
    ids = [m["feature_id"] for m in beam.summary()["members"]]
    assert ids[0] == "early_small"          # |t| 更小，但地板更低


def test_an_undefined_candidate_never_enters_the_beam():
    beam = Beam(width=3)
    assert beam.offer(Candidate("nan", "s", value=None, tests_at_evaluation=3)) is False
    assert beam.members == []


# ------------------------------------------------------------ 封条只能揭一次


def test_the_seal_opens_exactly_once(ledger):
    """再看一眼，封闭段就变成第二个发现段了。"""
    open_sealed(ledger, feature_id="f1", segment="historical_validation",
                result={"effects": {"t_stat": 1.0}}, contamination=None)
    with pytest.raises(SealedAlreadyOpened, match="已经做过"):
        assert_unopened(ledger, "f1", "historical_validation")


def test_a_different_feature_or_segment_is_a_different_seal(ledger):
    open_sealed(ledger, feature_id="f1", segment="historical_validation",
                result={}, contamination=None)
    assert assert_unopened(ledger, "f2", "historical_validation")
    assert assert_unopened(ledger, "f1", "contaminated_audit")
    assert seal_key("f1", "a") != seal_key("f1", "b")


def test_out_of_sample_in_time_and_taxonomy_clean_are_recorded_separately(ledger):
    """把两者混为一谈，等于用一个仍被污染的段给出「已验证」的结论。"""
    clean = open_sealed(ledger, feature_id="price_only", segment="historical_validation",
                        result={}, contamination=None)
    dirty = open_sealed(ledger, feature_id="pm_family", segment="historical_validation",
                        result={}, contamination=CONTAMINATED)
    assert clean.out_of_sample_in_time is True and clean.taxonomy_clean is True
    # 归纳切点 2026-08-01 覆盖了 2025 全年，因此这一段对 PM 族并不干净
    assert dirty.out_of_sample_in_time is True and dirty.taxonomy_clean is False


def test_the_sealed_record_says_that_sealed_is_not_the_same_as_clean(ledger):
    v = open_sealed(ledger, feature_id="f", segment="historical_validation",
                    result={}, contamination=CONTAMINATED)
    assert "封闭不等于干净" in v.payload()["note"]


# ------------------------------------------------------------ 组合的低相关约束


def test_the_ensemble_refuses_a_second_writing_of_the_same_idea():
    base = [float(i % 17) for i in range(200)]
    signals = {
        "a": base,
        "a_again": [v + 0.001 * (i % 3) for i, v in enumerate(base)],   # 与 a 近乎共线
        "b": [float((i * 7) % 13) for i in range(200)],
    }
    labels = [0.4 * signals["a"][i] + 0.3 * signals["b"][i] for i in range(200)]
    out = greedy_ensemble(signals, labels, max_size=3, max_correlation=0.7)
    rejected = {r["feature_id"] for r in out["rejected_for_correlation"]}
    assert "a_again" in rejected
    assert "a_again" not in out["constituents"]


def test_the_ensemble_stops_when_nothing_adds_anything():
    signals = {"a": [float(i % 11) for i in range(120)],
               "b": [float(i % 11) for i in range(120)]}
    labels = [float(i % 11) for i in range(120)]
    out = greedy_ensemble(signals, labels, max_size=3)
    assert len(out["constituents"]) <= 2
    assert out["trajectory"]


def test_the_ensemble_says_which_segment_it_was_selected_on():
    """在封闭段上调它就等于把封条揭了，因此这句话必须跟着结果走。"""
    out = greedy_ensemble({"a": [1.0] * 40, "b": [2.0] * 40}, [1.0] * 40)
    assert "封条" in out["note"]
