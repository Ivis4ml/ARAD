"""市场文本元数据 PIT 可证性审计的合同测试（Decision Map #12 取证阶段）。

本审计不做语义分类，只回答"哪些文本在历史时点确实可见"。两条实测结论必须被
测试固定住：扩展段完全没有 category；slug 会在两次抓取之间增长消歧数字段。
"""

from __future__ import annotations

import json
import os

import pytest

from arad.data_catalog.pm_metadata_audit import (
    ASSET_FIELDS,
    MARKET_FIELDS,
    normalize_slug,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(REPO, "artifacts", "manifests", "pm_metadata_audit.json")


@pytest.fixture(scope="module")
def audit():
    assert os.path.exists(MANIFEST), "缺少 artifacts/manifests/pm_metadata_audit.json"
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- slug 归一化


@pytest.mark.parametrize(
    ("raw", "expect"),
    [
        ("will-crude-oil-cl-hit-low-47-by-end-of-june", "will-crude-oil-cl-hit-low-47-by-end-of-june"),
        ("will-crude-oil-cl-hit-low-47-by-end-of-june-796-981-212",
         "will-crude-oil-cl-hit-low-47-by-end-of-june"),
        ("base-fdv-above-12b-one-day-after-launch-383", "base-fdv-above-12b-one-day-after-launch"),
        (None, None),
    ],
)
def test_normalize_slug_strips_disambiguation_suffixes(raw, expect):
    assert normalize_slug(raw) == expect


def test_normalize_slug_is_idempotent():
    once = normalize_slug("will-gpt-6-be-released-by-september-30-2026-543-325-933-952")
    assert normalize_slug(once) == once


@pytest.mark.parametrize("raw", ["-1", "-123-456", "0"])
def test_normalize_slug_never_returns_empty(raw):
    """归一化后不能变成空串，否则会把多个市场折叠成同一个键。"""
    assert normalize_slug(raw)


# ---------------------------------------------------------------- 键的正确性


def test_market_and_asset_fields_are_keyed_separately():
    """outcome_label 是 asset 级字段：按市场级归并会把 YES/NO 当成同一实体的漂移。"""
    assert "outcome_label" in ASSET_FIELDS
    assert "outcome_label" not in MARKET_FIELDS
    assert set(MARKET_FIELDS) & set(ASSET_FIELDS) == set()


def test_audit_keys_asset_fields_by_asset_id(audit):
    for finding in audit["findings"]:
        if finding["code"] == "pm_metadata.intra_segment_drift":
            assert finding["evidence"]["keys"]["asset_fields"] == "asset_id"
            # 按正确的键归并后，outcome_label 不应有漂移
            assert finding["evidence"]["entities_with_multiple_values"]["outcome_label"] == 0


# ---------------------------------------------------------------- 实测结论


def test_extension_segment_has_no_category_metadata(audit):
    """扩展段完全没有 category：任何依赖它的语义映射在 87.9% 的成交上不可用。"""
    fill = audit["coverage"]["coverage"]["ext"]["fill_rate"]
    assert fill["category"] == 0.0
    assert fill["category_refined"] == 0.0
    assert fill["market_slug"] == 1.0
    finding = next(
        f for f in audit["findings"] if f["code"] == "pm_metadata.field_absent_in_segment"
    )
    assert finding["severity"] == "error"
    assert set(finding["evidence"]["fields"]) >= {"category", "category_refined"}


def test_slug_mutates_across_scrapes_but_normalises_to_a_stable_base(audit):
    """slug 在两次抓取之间会增长；归一化后必须完全一致，否则规则无效。"""
    cross = audit["coverage"]["cross_segment"]
    assert cross["differs"].get("market_slug", 0) > 0
    assert cross["differs_after_normalisation"].get("market_slug", 0) == 0


def test_outcome_label_is_stable_across_scrapes(audit):
    cross = audit["coverage"]["cross_segment"]
    assert cross["comparable_assets"] > 0
    assert cross["differs"].get("outcome_label", 0) == 0


def test_audit_blocks_the_quality_gate_until_12_resolves_it(audit):
    """文本不可证即 Study 只能 blocked：审计必须以 error 级 finding 阻断闸门。"""
    errors = {f["code"] for f in audit["findings"] if f["severity"] == "error"}
    assert "pm_metadata.mutable_across_scrapes" in errors
    assert "pm_metadata.field_absent_in_segment" in errors


def test_audit_makes_no_semantic_claim(audit):
    """取证阶段不得产生任何分类结论。"""
    blob = json.dumps(audit, ensure_ascii=False)
    for word in ("mideast", "oil_price", "geopolit", "taxonomy"):
        assert word not in blob.lower()
