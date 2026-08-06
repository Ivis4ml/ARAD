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


# ---------------------------------------------------------------- 词表与规模


def test_slug_tokens_drops_only_numbers_years_and_months():
    from arad.data_catalog.pm_text_corpus import slug_tokens

    assert slug_tokens("will-crude-oil-hit-47-by-june-2026") == [
        "will", "crude", "oil", "hit", "by",
    ]
    assert slug_tokens(None) == []
    assert slug_tokens("") == []


def test_slug_tokens_has_no_builtin_stopword_list():
    """停用词是人写的先验。把它写进代码等于把『什么算实体』固化成真值。"""
    from arad.data_catalog.pm_text_corpus import slug_tokens

    # 功能词必须原样保留，由调用方以提案形式决定是否排除
    assert "will" in slug_tokens("will-trump-say-hello")
    assert "the" in slug_tokens("the-fed-cuts")


def test_entity_vocabulary_comes_from_document_frequency_not_a_curated_list():
    from arad.data_catalog.pm_text_corpus import entity_vocabulary

    text = pa.table(
        {
            "condition_id": pa.array(["a", "b", "c", "d"], pa.string()),
            "slug_base": pa.array(
                ["oil-up", "oil-down", "oil-flat", "gold-up"], pa.string()
            ),
            "template": pa.array(["oil-up", "oil-down", "oil-flat", "gold-up"], pa.string()),
        }
    )
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", EARLY), ("d", EARLY)])
    vocab = entity_vocabulary(
        text, presence, InductionSpec("2024-01-01", min_markets_per_template=2)
    )
    rows = {r["token"]: r for r in vocab.to_pylist()}
    assert rows["oil"]["markets"] == 3
    assert rows["oil"]["templates"] == 3
    assert rows["oil"]["share_of_markets"] == pytest.approx(0.75)
    assert "gold" not in rows  # 只出现在 1 个市场，被 min_markets 过滤
    # 按市场数降序，词表顺序是确定的
    assert vocab.column("token").to_pylist() == sorted(
        rows, key=lambda t: (-rows[t]["markets"], t)
    )


def test_entity_vocabulary_only_uses_markets_inside_the_induction_period():
    from arad.data_catalog.pm_text_corpus import entity_vocabulary

    text = pa.table(
        {
            "condition_id": pa.array(["a", "b", "c"], pa.string()),
            "slug_base": pa.array(["oil-up", "oil-down", "gold-up"], pa.string()),
            "template": pa.array(["oil-up", "oil-down", "gold-up"], pa.string()),
        }
    )
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", LATE)])
    vocab = entity_vocabulary(
        text, presence, InductionSpec("2024-01-01", min_markets_per_template=1)
    )
    assert "gold" not in vocab.column("token").to_pylist()


def _totals(rows):
    return pa.table(
        {
            "condition_id": pa.array([r[0] for r in rows], pa.string()),
            "trades": pa.array([r[1] for r in rows], pa.int64()),
            "notional": pa.array([r[2] for r in rows], pa.float64()),
        }
    )


def test_size_entity_proposal_takes_the_token_set_as_input_not_as_truth():
    """实体集合是提案：函数不内置任何清单，换一个提案就得到另一组规模。"""
    from arad.data_catalog.pm_text_corpus import size_entity_proposal

    text = pa.table(
        {
            "condition_id": pa.array(["a", "b", "c"], pa.string()),
            "slug_base": pa.array(["oil-up", "gold-up", "nba-game"], pa.string()),
        }
    )
    presence = _presence([("a", EARLY), ("b", EARLY), ("c", EARLY)])
    totals = _totals([("a", 100, 1000.0), ("b", 10, 100.0), ("c", 1000, 10000.0)])

    oil = size_entity_proposal(text, presence, totals, ["oil"])
    assert oil["markets"] == 1 and oil["trades"] == 100
    assert oil["markets_share"] == pytest.approx(1 / 3)
    assert oil["trades_share"] == pytest.approx(100 / 1110)

    both = size_entity_proposal(text, presence, totals, ["OIL", "gold"])
    assert both["markets"] == 2  # 大小写无关
    assert both["proposal_tokens"] == ["gold", "oil"]


def test_size_entity_proposal_respects_the_cutoff():
    from arad.data_catalog.pm_text_corpus import size_entity_proposal

    text = pa.table(
        {
            "condition_id": pa.array(["a", "b"], pa.string()),
            "slug_base": pa.array(["oil-up", "oil-down"], pa.string()),
        }
    )
    presence = _presence([("a", EARLY), ("b", LATE)])
    totals = _totals([("a", 5, 50.0), ("b", 500, 5000.0)])
    early = size_entity_proposal(text, presence, totals, ["oil"], cutoff="2024-01-01")
    assert early["markets"] == 1 and early["trades"] == 5
    assert early["universe"]["markets"] == 1


def test_size_entity_proposal_marks_notional_provisional():
    """relay 去重不可执行，名义额必须在字段名上就标明 provisional。"""
    from arad.data_catalog.pm_text_corpus import size_entity_proposal

    text = pa.table(
        {"condition_id": pa.array(["a"], pa.string()),
         "slug_base": pa.array(["oil-up"], pa.string())}
    )
    result = size_entity_proposal(
        text, _presence([("a", EARLY)]), _totals([("a", 1, 1.0)]), ["oil"]
    )
    assert "notional_provisional" in result
    assert "notional_share_provisional" in result
    assert "notional" not in result
