"""机制族的合同测试（M16）。

这一层要防的四类错误都属于「错了也照样出数」，评审看不出来，只能由测试钉住：

1. 极性判错 —— 反向提问不折成同号，同一机制的两侧在族内相互抵消；
2. 规则盲区被静默吞掉 —— 落在实体门内却无人认领的市场如果不报错，
   规则的覆盖不全会伪装成「族里没有这种市场」；
3. 构成移动冒充信念移动 —— 新成员入族造成的电平跳变如果计进 dp，
   测的就是「今天谁在成交」而不是「市场怎么想」；
4. 规则改了而族名没改 —— 序列与结论会跨版本混用。
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from arad.data_catalog.pm_mechanism_families import (
    MechanismRule,
    MechanismRuleError,
    MechanismStage,
    classify,
    compile_membership,
    rules_content_id,
)
from arad.data_catalog.pm_series import build_mechanism_series

DISCOVERY_END = date(2024, 12, 31)
VALIDATION_END = date(2025, 12, 31)


def _rule(**overrides) -> MechanismRule:
    base = {
        "family_id": "TEST_FAM",
        "name_cn": "测试族",
        "driver_channel": "地缘-航运",
        "mechanism_cn": "封锁发生抬升运费",
        "match_field": "slug_base",
        "scope": r"canal",
        "stages": (
            MechanismStage(kind="exclude", name="noise", pattern=r"-say-", reason="noise"),
            MechanismStage(kind="member", name="reopen", pattern=r"reopen", sign=-1),
            MechanismStage(kind="member", name="close", pattern=r"close", sign=1),
        ),
    }
    base.update(overrides)
    return MechanismRule(**base)


def test_stage_order_decides_membership_and_polarity():
    """先判的段先赢：既含 reopen 又含 close 的提问归反向，不是正向。"""
    rule = _rule()
    assert classify(rule, "will-the-canal-close-in-june").sign == 1
    assert classify(rule, "will-the-canal-reopen-after-the-close").sign == -1
    assert classify(rule, "will-trump-say-canal-today").outcome == "excluded"
    assert classify(rule, "will-the-strait-close").outcome == "out_of_scope"


def test_a_market_inside_the_gate_that_no_stage_claims_is_reported_not_dropped():
    rule = _rule()
    got = classify(rule, "canal-toll-increase-in-june")
    assert got.outcome == "unmatched"
    assert got.reason == "no_stage_matched"


def test_member_stage_without_sign_is_refused():
    with pytest.raises(MechanismRuleError):
        MechanismStage(kind="member", name="x", pattern=r"a")


def test_rules_content_id_changes_with_any_pattern_edit():
    before = rules_content_id({"TEST_FAM": _rule()})
    after = rules_content_id({"TEST_FAM": _rule(scope=r"canals?")})
    assert before != after


def _write_market_tables(tmp_path, rows):
    text = pa.table({
        "condition_id": [r[0] for r in rows],
        "slug_base": [r[1] for r in rows],
        "slug_raw": [r[1] for r in rows],
    })
    presence = pa.table(
        {
            "condition_id": [r[0] for r in rows],
            "first_trade_ts": [r[2] for r in rows],
            "eligible_from": pa.array([None] * len(rows), pa.timestamp("us", tz="UTC")),
        }
    )
    text_path = tmp_path / "market_text.parquet"
    presence_path = tmp_path / "market_presence.parquet"
    pq.write_table(text, text_path)
    pq.write_table(presence, presence_path)
    return str(text_path), str(presence_path)


#: 2024-06-01 与 2025-06-01 的 epoch 秒，分属 discovery 与封存段。
IN_DISCOVERY = 1_717_200_000
IN_VALIDATION = 1_748_736_000


def test_discovery_blind_spot_fails_the_build(tmp_path):
    text, presence = _write_market_tables(tmp_path, [
        ("c1", "will-the-canal-close-in-june", IN_DISCOVERY),
        ("c2", "canal-toll-increase-in-june", IN_DISCOVERY),
    ])
    with pytest.raises(MechanismRuleError, match="无法归类"):
        compile_membership(text, presence, {"TEST_FAM": _rule()},
                           discovery_end=DISCOVERY_END, validation_end=VALIDATION_END,
                           strict_unmatched_segment="discovery")


def test_blind_spot_outside_the_calibrated_segment_is_recorded_not_fatal(tmp_path):
    text, presence = _write_market_tables(tmp_path, [
        ("c1", "will-the-canal-close-in-june", IN_DISCOVERY),
        ("c2", "canal-toll-increase-in-june", IN_VALIDATION),
    ])
    result = compile_membership(
        text, presence, {"TEST_FAM": _rule(expected_discovery_markets=1)},
        discovery_end=DISCOVERY_END, validation_end=VALIDATION_END,
        strict_unmatched_segment="discovery")
    assert result.membership.num_rows == 1
    reasons = result.excluded.column("reason").to_pylist()
    assert "no_stage_matched" in reasons


def test_discovery_anchor_mismatch_fails_the_build(tmp_path):
    text, presence = _write_market_tables(tmp_path, [
        ("c1", "will-the-canal-close-in-june", IN_DISCOVERY),
    ])
    with pytest.raises(MechanismRuleError, match="自检锚点"):
        compile_membership(text, presence,
                           {"TEST_FAM": _rule(expected_discovery_markets=2)},
                           discovery_end=DISCOVERY_END, validation_end=VALIDATION_END,
                           strict_unmatched_segment=None)


def _write_tape(tmp_path, trades):
    table = pa.table({
        "condition_id": pa.array([t[0] for t in trades], pa.large_string()),
        "outcome_seq": pa.array([t[1] for t in trades], pa.int64()),
        "price": pa.array([t[2] for t in trades], pa.float64()),
        "usdc_amount": pa.array([t[3] for t in trades], pa.float64()),
        "block_timestamp": pa.array([t[4] for t in trades], pa.int64()),
    })
    root = tmp_path / "tape"
    root.mkdir()
    pq.write_table(table, root / "2024-06-01.parquet")
    return {"tape": str(root)}


HOUR = 3600
T0 = 1_717_200_000  # 整点，便于逐桶核对


def test_reverse_polarity_member_is_folded_and_does_not_collapse_to_half():
    """一条 p=0.9 的正向与一条 p=0.1 的反向，折同号后是 0.9，不是 0.5。"""
    with tempfile.TemporaryDirectory() as tmp:
        roots = _write_tape(Path(tmp), [
            ("pos", 1, 0.9, 100.0, T0 + 10),
            ("neg", 1, 0.1, 100.0, T0 + 20),
        ])
        folded = build_mechanism_series(
            roots, {"mech:X": {"pos": 1, "neg": -1}})
        naive = build_mechanism_series(
            roots, {"mech:X": {"pos": 1, "neg": 1}})
    assert folded.column("p").to_pylist() == [pytest.approx(0.9)]
    assert naive.column("p").to_pylist() == [pytest.approx(0.5)]


def test_dp_excludes_the_level_jump_caused_by_a_new_member():
    """第二桶新进一个 p=0.1 的成员：电平被拉低，但没有人改变信念，dp 应为 0。"""
    with tempfile.TemporaryDirectory() as tmp:
        roots = _write_tape(Path(tmp), [
            ("a", 1, 0.8, 100.0, T0 + 10),
            ("a", 1, 0.8, 100.0, T0 + HOUR + 10),
            ("b", 1, 0.1, 100.0, T0 + HOUR + 20),
        ])
        series = build_mechanism_series(roots, {"mech:X": {"a": 1, "b": 1}})
    p = series.column("p").to_pylist()
    dp = series.column("dp").to_pylist()
    assert p[0] == pytest.approx(0.8)
    assert p[1] == pytest.approx(0.45)   # 电平被新成员拉低
    assert dp[1] == pytest.approx(0.0)   # 但没有任何成员重定价
    assert dp[0] is None                 # 首桶无前一桶，无定义


def test_dp_is_null_when_the_gap_exceeds_the_staleness_cap():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _write_tape(Path(tmp), [
            ("a", 1, 0.8, 100.0, T0 + 10),
            ("a", 1, 0.4, 100.0, T0 + 5 * HOUR + 10),
        ])
        series = build_mechanism_series(
            roots, {"mech:X": {"a": 1}}, max_stale_seconds=2 * HOUR)
    assert series.column("dp").to_pylist() == [None, None]


def test_dp_reports_the_repricing_of_a_shared_member():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _write_tape(Path(tmp), [
            ("a", 1, 0.4, 100.0, T0 + 10),
            ("a", 1, 0.6, 100.0, T0 + HOUR + 10),
        ])
        series = build_mechanism_series(roots, {"mech:X": {"a": 1}})
    assert series.column("dp").to_pylist()[1] == pytest.approx(0.2)


def test_outcome_seq_two_is_normalised_before_polarity_is_applied():
    """seq 2 先归一到 Yes 侧，再按极性折；两步顺序颠倒会得到 1−(1−p) 的假同号。"""
    with tempfile.TemporaryDirectory() as tmp:
        roots = _write_tape(Path(tmp), [("a", 2, 0.3, 100.0, T0 + 10)])
        series = build_mechanism_series(roots, {"mech:X": {"a": -1}})
    # seq2 价 0.3 → Yes 侧 0.7 → 反向折 → 0.3
    assert series.column("p").to_pylist() == [pytest.approx(0.3)]
