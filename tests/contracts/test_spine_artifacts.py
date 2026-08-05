"""M2 产物的合同测试（出口条件 1 与 2）。

出口条件 2 要求"随机 30 个时点可人工回放且无未来信息"。人工核对清单是给人看的，
真正的守卫是本文件：清单里的每一条 feature 的 availability_time 必须严格早于
决策时点，决策时点必须严格早于 label 窗口起点。清单产物已入 git，因此本测试
总是运行，不允许因为产物缺失而跳过。
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECKLIST = os.path.join(REPO, "artifacts", "manifests", "sc_replay_checklist.json")
SPINE_MANIFEST = os.path.join(REPO, "artifacts", "manifests", "sc_temporal_spine.json")
COMMODITY_MANIFEST = os.path.join(REPO, "artifacts", "manifests", "commodity_tick.json")
BARS_DAILY = os.path.join(REPO, "data", "spine", "sc", "bars_daily")
CURVE = "/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/intl/curve_daily.parquet"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    assert dt.tzinfo is not None, f"{value} 缺少时区"
    return dt


@pytest.fixture(scope="module")
def checklist():
    assert os.path.exists(CHECKLIST), (
        "缺少 artifacts/manifests/sc_replay_checklist.json；"
        "请运行 python -m arad.cli spine replay"
    )
    return load(CHECKLIST)


@pytest.fixture(scope="module")
def spine():
    assert os.path.exists(SPINE_MANIFEST), "缺少 artifacts/manifests/sc_temporal_spine.json"
    return load(SPINE_MANIFEST)


# ---------------------------------------------------------------- 回放清单


def test_checklist_has_thirty_seeded_entries(checklist):
    assert checklist["sample_size"] == 30
    assert len(checklist["entries"]) == 30
    assert isinstance(checklist["seed"], int)  # 无种子的抽样不可复现


def test_every_entry_has_a_decision_before_its_label_window(checklist):
    for e in checklist["entries"]:
        decision = parse(e["decision_time"])
        start = parse(e["label_start"])
        end = parse(e["label_end"])
        assert decision < start, e
        assert start < end, e


def test_no_feature_is_available_at_or_after_the_decision_time(checklist):
    """这是本票最重要的负向断言：任何一条越界都意味着 spine 有前视。"""
    for e in checklist["entries"]:
        decision = parse(e["decision_time"])
        start = parse(e["label_start"])
        assert e["features"], f"回放条目没有任何 feature: {e['index']}"
        for f in e["features"]:
            available = parse(f["availability_time"])
            assert available < decision, (e["index"], f)
            assert available < start, (e["index"], f)


def test_entries_carry_episode_and_contamination_tags(checklist):
    allowed = {"discovery", "historical_validation", "contaminated_audit", "forward_confirmation"}
    for e in checklist["entries"]:
        assert e["episode_id"]
        assert e["sample_segment"] in allowed


def test_sample_spans_more_than_one_historical_segment(checklist):
    segments = {e["sample_segment"] for e in checklist["entries"]}
    assert len(segments) >= 2, segments


def test_no_trade_entries_have_a_reason_and_a_null_value(checklist):
    for e in checklist["entries"]:
        if e["no_trade"]:
            assert e["target_value"] is None
            assert e["no_trade_reason"]
        else:
            assert e["target_value"] is not None
            assert not isinstance(e["target_value"], bool)
            assert math.isfinite(e["target_value"])


def test_checklist_references_the_spine_fingerprint(checklist, spine):
    assert checklist["spine_fingerprint"] == spine["fingerprint"]


# ---------------------------------------------------------------- spine manifest


def test_spine_manifest_pins_its_source_inputs(spine):
    """来源 manifest 指纹变化必须使 spine 指纹失效，否则产物无法追溯。"""
    commodity = load(COMMODITY_MANIFEST)
    assert spine["inputs"]["commodity_tick"]["fingerprint"] == commodity["fingerprint"]
    assert spine["inputs"]["commodity_tick"]["source_snapshot_digest"] == (
        commodity["source_snapshot"]["digest"]
    )
    assert spine["code_version"]
    assert spine["config_digest"]


def test_spine_fingerprint_recomputes_from_its_own_content(spine):
    from arad.temporal.manifest import SpineManifest

    manifest = SpineManifest.model_validate(spine)
    assert manifest.compute_fingerprint() == spine["fingerprint"]


def test_spine_manifest_records_target_specs_and_dominant_rule(spine):
    names = {t["name"] for t in spine["targets"]}
    assert "sc_rv_next_session" in names
    assert "sc_open_gap_absorption" in names
    diagnostic = next(t for t in spine["targets"] if t["name"] == "sc_open_gap_absorption")
    assert diagnostic["tradable_claim"] is False
    assert spine["dominant_rule"]["version"]


def test_spine_manifest_records_calendar_and_session_verification(spine):
    assert spine["calendar"]["trading_days"] > 0
    assert spine["calendar"]["fingerprint"]
    assert "session_table" in spine
    assert spine["session_table"]["reference"]


def test_spine_calendar_agrees_with_the_m1_commodity_manifest(spine):
    commodity = load(COMMODITY_MANIFEST)
    assert spine["calendar"]["trading_days"] == commodity["facts"]["trading_days"]
    assert spine["calendar"]["first_day"] == commodity["facts"]["first_day"]
    assert spine["calendar"]["last_day"] == commodity["facts"]["last_day"]


def test_control_sources_declare_availability_rules(spine):
    ids = {c["source_id"] for c in spine["control_contracts"]}
    assert {"cls_telegraph", "intl_brent", "pm_cn_registry_v3"} <= ids
    for c in spine["control_contracts"]:
        assert c["availability_rule"]


def test_registry_slice_bans_lookahead_and_unaudited_seed_fields(spine):
    reg = next(c for c in spine["control_contracts"] if c["source_id"] == "pm_cn_registry_v3")
    assert {"usdc_win", "n_win", "resolved_at", "sigma", "orientation", "exploratory"} <= set(
        reg["banned_fields"]
    )


def test_registry_contract_records_the_survivorship_caveat(spine):
    """admit_ts 只点时化了准入时刻；成员资格仍是全窗口筛选，该缺陷必须写进合同。"""
    reg = next(c for c in spine["control_contracts"] if c["source_id"] == "pm_cn_registry_v3")
    assert "幸存者偏差" in reg["availability_rule"]
    assert any("幸存者偏差" in b for b in spine["blockers"])


# ---------------------------------------------------------------- 独立交叉核对


@pytest.mark.skipif(not os.path.exists(BARS_DAILY), reason="需要先运行 spine build")
@pytest.mark.skipif(not os.path.exists(CURVE), reason="缺少 Alpha-Data 参照数据")
def test_daily_bars_agree_with_the_independent_curve_reference():
    """用与 tick 无关的日频参照（Alpha-Data curve_daily）独立核对派生日频 bar。

    curve_daily 只覆盖 2026-01-05 至 2026-07-13，因此仅作该窗口的等价性检查，
    不作为登记的控制数据源。
    """
    import pyarrow.compute as pc
    import pyarrow.dataset as ds
    import pyarrow.parquet as pq

    curve = pq.read_table(CURVE)
    curve = curve.filter(pc.equal(curve.column("product"), "SC")).to_pylist()
    ours = ds.dataset(BARS_DAILY, format="parquet").to_table().to_pylist()
    ours_by_key = {}
    for r in ours:
        day = str(r["trading_day"])
        key = (f"{day[:4]}-{day[4:6]}-{day[6:]}", r["contract"][2:])
        ours_by_key[key] = r

    compared = bad_volume = bad_oi = 0
    for c in curve:
        row = ours_by_key.get((c["trade_date"], c["delivery_month"]))
        # curve_daily 对部分近月合约留空，跳过无参照值的行
        if row is None or c["volume"] is None or c["oi"] is None:
            continue
        compared += 1
        if abs(row["volume"] - c["volume"]) > 0.5:
            bad_volume += 1
        if abs(row["open_interest_close"] - c["oi"]) > 0.5:
            bad_oi += 1
    assert compared > 500, f"可比样本过少：{compared}"
    assert bad_volume / compared < 0.02, f"{bad_volume}/{compared} 日频成交量与独立参照不符"
    assert bad_oi / compared < 0.02, f"{bad_oi}/{compared} 日频持仓与独立参照不符"


@pytest.mark.skipif(not os.path.exists(BARS_DAILY), reason="需要先运行 spine build")
def test_materialized_calendar_covers_the_full_manifest_range():
    import pyarrow.dataset as ds

    table = ds.dataset(BARS_DAILY, format="parquet").to_table(columns=["trading_day"])
    days = {int(d) for d in table.column("trading_day").to_pylist()}
    commodity = load(COMMODITY_MANIFEST)
    # 区间来自 manifest，不在测试里写死日期
    assert min(days) == int(commodity["facts"]["first_day"])
    assert max(days) == int(commodity["facts"]["last_day"])
    assert len(days) == commodity["facts"]["trading_days"]


def test_manifest_segment_breakdown_sums_to_the_reported_row_count(spine):
    for target in spine["targets"]:
        assert sum(target["sample_segments"].values()) == target["rows"], target["name"]
        assert (
            sum(target["sample_segments_valued"].values())
            == target["rows"] - sum(target["no_trade_reasons"].values())
        ), target["name"]


def test_verify_covers_every_materialised_dataset(spine):
    """指纹链必须覆盖分区数据集，否则 verify 的 MATCH 是以偏概全。"""
    names = {d["name"] for d in spine["datasets"]}
    assert {"bars_1min", "bars_daily"} <= names
    for d in spine["datasets"]:
        assert d["fingerprint"]
        assert d["rows"] > 0
