"""确定性文本语料与模板归纳的合同测试（#12 自下而上第一层）。

裁决：机制族从数据自下而上归纳，不沿用旧系统的 8 个主题。本层必须完全确定性、
不使用任何模型，且归纳期切点是冻结参数 —— 用全史文本归纳分类法等于用后见的
市场宇宙定义分组。
"""

from __future__ import annotations

import json
import os

import pyarrow as pa
import pytest

from arad.data_catalog.pm_text_corpus import (
    InductionSpec,
    induce_templates,
    slug_template,
)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(REPO, "artifacts", "manifests", "pm_text_corpus.json")


@pytest.fixture(scope="module")
def corpus():
    assert os.path.exists(MANIFEST), "缺少 artifacts/manifests/pm_text_corpus.json"
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 模板


@pytest.mark.parametrize(
    ("base", "expect"),
    [
        ("will-crude-oil-cl-hit-low-47-by-end-of-june",
         "will-crude-oil-cl-hit-low-<N>-by-end-of-<MONTH>"),
        ("btc-updown-1770000000", "btc-updown-<N>"),
        ("will-gpt-6-be-released-by-september-30-2026",
         "will-gpt-<N>-be-released-by-<MONTH>-<N>-<YEAR>"),
        ("bitcoin-above-120k-on-may", "bitcoin-above-<N>-on-<MONTH>"),
        (None, None),
        ("", ""),
    ],
)
def test_slug_template_replaces_numbers_years_and_months(base, expect):
    assert slug_template(base) == expect


def test_year_takes_precedence_over_plain_number():
    """2026 既是四位数也是年份；作为年份更有信息量，否则模板会丢掉时间维。"""
    assert slug_template("event-2026") == "event-<YEAR>"
    assert slug_template("event-2026-47") == "event-<YEAR>-<N>"


def test_template_is_deterministic_and_case_insensitive():
    assert slug_template("Will-Crude-JUNE-47") == slug_template("will-crude-june-47")


# ---------------------------------------------------------------- 归纳期


def _text(rows):
    """rows: (condition_id, template)。"""
    return pa.table(
        {
            "condition_id": pa.array([r[0] for r in rows], pa.string()),
            "template": pa.array([r[1] for r in rows], pa.string()),
        }
    )


def _presence(rows):
    """rows: (condition_id, first_trade_ts)。"""
    return pa.table(
        {
            "condition_id": pa.array([r[0] for r in rows], pa.string()),
            "first_trade_ts": pa.array([r[1] for r in rows], pa.int64()),
        }
    )


EARLY = 1_700_000_000  # 2023-11
LATE = 1_760_000_000   # 2025-10


def test_only_markets_inside_the_induction_period_produce_templates():
    text = _text([("a", "t1"), ("b", "t1"), ("c", "t2"), ("d", "t3")])
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", EARLY), ("d", LATE)])
    table, stats = induce_templates(
        text, presence, InductionSpec("2024-01-01", min_markets_per_template=1)
    )
    assert set(table.column("template").to_pylist()) == {"t1", "t2"}
    assert "t3" not in table.column("template").to_pylist()
    assert stats["markets_in_induction_period"] == 3
    assert stats["markets_after_cutoff"] == 1


def test_min_markets_per_template_filters_the_singleton_tail():
    text = _text([("a", "t1"), ("b", "t1"), ("c", "t2")])
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", EARLY)])
    table, stats = induce_templates(
        text, presence, InductionSpec("2024-01-01", min_markets_per_template=2)
    )
    assert table.column("template").to_pylist() == ["t1"]
    assert stats["singleton_templates"] == 1


def test_out_of_period_coverage_is_measured_not_assumed():
    text = _text([("a", "t1"), ("b", "t1"), ("c", "t1"), ("d", "t9")])
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", LATE), ("d", LATE)])
    _, stats = induce_templates(
        text, presence, InductionSpec("2024-01-01", min_markets_per_template=1)
    )
    assert stats["markets_after_cutoff"] == 2
    assert stats["markets_after_cutoff_covered"] == 1  # 只有 t1 被期内模板覆盖
    assert stats["coverage_after_cutoff"] == pytest.approx(0.5)


def test_induction_spec_is_frozen_and_self_describing():
    spec = InductionSpec("2025-01-01", min_markets_per_template=5)
    described = spec.describe()
    assert described["induction_cutoff"] == "2025-01-01"
    assert described["min_markets_per_template"] == 5
    assert "不参与归纳" in described["rule"]
    with pytest.raises(AttributeError):
        spec.induction_cutoff = "2026-01-01"  # frozen dataclass


# ---------------------------------------------------------------- 产物


def test_coverage_curve_is_monotone_in_the_cutoff(corpus):
    """归纳期越晚，期外覆盖率不应下降；否则说明归纳或计数有误。"""
    curve = corpus["coverage"]["coverage_curve"]
    assert len(curve) >= 2
    values = [c["coverage_after_cutoff"] for c in curve]
    assert values == sorted(values)
    assert [c["markets_in_period"] for c in curve] == sorted(
        c["markets_in_period"] for c in curve
    )


def test_manifest_records_the_bottom_up_decision_and_makes_no_semantic_claim(corpus):
    blob = json.dumps(corpus, ensure_ascii=False)
    assert "自下而上" in blob
    assert "不沿用旧系统的 8 个主题" in blob
    # 取证与归纳阶段不得出现任何机制族命名
    for word in ("mideast_conflict", "oil_price", "russia_ukraine", "taiwan_risk"):
        assert word not in blob
    assert any("机制族尚未命名" in b for b in corpus["blockers"])


def test_low_coverage_is_reported_as_a_finding(corpus):
    codes = {f["code"] for f in corpus["findings"]}
    assert "pm_text.template_induction" in codes
    assert "pm_text.low_out_of_period_coverage" in codes
