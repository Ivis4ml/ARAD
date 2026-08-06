"""分类法后见暴露与前向门扩展的合同测试（决定 0004）。"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta

import pytest

from arad.registry.specs import TaxonomyContamination, Verdict
from arad.temporal.episode import SampleSegment, classify_segment, forward_gate

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(REPO, "artifacts", "manifests", "pm_taxonomy_hindsight_audit.json")

T = datetime(2026, 1, 1, tzinfo=UTC)


def test_forward_gate_takes_the_max_of_every_freeze_stamp():
    gate = forward_gate(
        protocol_freeze_at=T,
        confirmatory_freeze_at=T + timedelta(days=10),
        source_snapshot_at=T + timedelta(days=5),
        taxonomy_freeze_at=T + timedelta(days=30),
        embargo=timedelta(days=1),
    )
    assert gate == T + timedelta(days=31)


def test_forward_gate_without_any_stamp_is_none():
    """没有完整的冻结记录就没有 forward。"""
    assert forward_gate() is None


def test_taxonomy_freeze_can_push_the_forward_gate_later():
    """分类法晚于 confirmatory 冻结时，前向起点必须推迟到分类法之后。"""
    early = forward_gate(confirmatory_freeze_at=T)
    late = forward_gate(confirmatory_freeze_at=T, taxonomy_freeze_at=T + timedelta(days=60))
    assert late > early


def test_segment_is_not_forward_before_the_taxonomy_freeze():
    start = T + timedelta(days=20)
    end = start + timedelta(hours=6)
    # 只看 confirmatory 冻结时已算 forward
    assert (
        classify_segment(start, end, freeze_at=T) is SampleSegment.FORWARD_CONFIRMATION
    )
    # 加入更晚的分类法冻结后不再是 forward
    assert (
        classify_segment(start, end, freeze_at=T, taxonomy_freeze_at=T + timedelta(days=60))
        is SampleSegment.CONTAMINATED_AUDIT
    )


def test_overlapping_induction_corpus_caps_the_verdict_at_candidate():
    """归纳语料覆盖裁决区间时 verdict 上限为 candidate（机器可检）。"""
    contaminated = TaxonomyContamination(
        taxonomy_id="t1",
        taxonomy_freeze_at="2026-08-05",
        induction_corpus_max_date="2026-07-14",
        outcome_read_intervals=[("2022-11-01", "2024-12-31")],
    )
    assert contaminated.overlaps_outcome_window is True
    assert contaminated.verdict_cap() is Verdict.CANDIDATE

    clean = TaxonomyContamination(
        taxonomy_id="t2",
        taxonomy_freeze_at="2025-01-01",
        induction_corpus_max_date="2024-12-31",
        outcome_read_intervals=[("2025-01-02", "2025-12-31")],
    )
    assert clean.overlaps_outcome_window is False
    assert clean.verdict_cap() is None


def test_taxonomy_contamination_is_frozen():
    from pydantic import ValidationError

    c = TaxonomyContamination(
        taxonomy_id="t", taxonomy_freeze_at="2026-08-05", induction_corpus_max_date="2026-07-14"
    )
    with pytest.raises(ValidationError):
        c.taxonomy_id = "other"


@pytest.mark.skipif(not os.path.exists(AUDIT), reason="需要先运行分类法后见审计")
def test_audit_quantifies_hindsight_exposure_and_outcome_adjacency():
    """检验 (a) 与 (b) 的结论必须是可复算的数，不是判断。"""
    with open(AUDIT, encoding="utf-8") as f:
        audit = json.load(f)
    em = audit["emergence"]
    assert 0.0 <= em["hindsight_exposure"] <= 1.0
    assert em["families_emerging_only_at_final_cutoff"] <= em["families"]

    adj = audit["outcome_adjacency"]
    assert adj["late_families"] > 0 and adj["early_families"] > 0
    assert adj["permutation_p_value"] <= 1.0
    # 记录的差值必须与两组均值一致
    assert adj["observed_difference"] == pytest.approx(
        adj["mean_top_share_late"] - adj["mean_top_share_early"], abs=1e-9
    )


@pytest.mark.skipif(not os.path.exists(AUDIT), reason="需要先运行分类法后见审计")
def test_late_emerging_families_are_more_outcome_adjacent():
    """决定 0004 的实证依据：晚涌现族更集中在大波动日上。

    这条若失败，说明该样本上检不出偏差通道，决定 0004 的论证需要重新审视。
    """
    with open(AUDIT, encoding="utf-8") as f:
        adj = json.load(f)["outcome_adjacency"]
    assert adj["observed_difference"] > 0
    assert adj["permutation_p_value"] < 0.05
