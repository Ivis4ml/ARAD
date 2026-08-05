"""PIT Market Index 与 label-blind 普查的合同测试（M2.5）。

最重要的一条是 prefix-invariance：向 tape 追加未来成交后，任意历史 cutoff 的
市场成员与滚动指标必须完全不变。它同时守住两件事 —— 成员资格不含幸存者偏差，
滚动指标不含前视。
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pytest

from arad.data_catalog.pm_census import (
    CENSUS_COLUMNS,
    DEDUP_COLUMNS,
    MARKET_DAY_SCHEMA,
    OUTCOME_COLUMNS,
    OutcomeColumnAccess,
    census_partition,
    require_label_blind,
)
from arad.temporal.pm_market_index import (
    OrphanCensusPartition,
    PitMarketIndex,
    PitMarketIndexConfig,
    complete_days_before,
    kish_n_eff,
)

HF = "/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/polymarket/daily_aligned"


def day_epoch(date_str: str) -> int:
    return int(datetime.fromisoformat(date_str).replace(tzinfo=UTC).timestamp())


def utc(date_str: str, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    d = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
    return d + timedelta(hours=hour, minutes=minute, seconds=second)


def md(rows: list[tuple]) -> pa.Table:
    """rows: (date, condition_id, trades, notional, offset_first_s, offset_last_s)。"""
    cols = {k: [] for k in MARKET_DAY_SCHEMA.names}
    for date_str, cid, trades, notional, off_first, off_last in rows:
        base = day_epoch(date_str)
        cols["date"].append(date_str)
        cols["condition_id"].append(cid)
        cols["trades"].append(trades)
        cols["notional"].append(notional)
        cols["first_ts"].append(base + off_first)
        cols["last_ts"].append(base + off_last)
        cols["active_seconds"].append(trades)
        cols["price_changes"].append(max(0, trades - 1))
        cols["max_gap_seconds"].append(max(0, off_last - off_first))
        cols["assets"].append(2)
        cols["neg_risk"].append(False)
    return pa.table(cols, schema=MARKET_DAY_SCHEMA)


BASE = [
    ("2024-01-01", "m_early", 10, 1000.0, 3600, 7200),
    ("2024-01-02", "m_early", 5, 500.0, 100, 200),
    ("2024-01-02", "m_mid", 200, 900_000.0, 50, 86_000),
    ("2024-01-03", "m_mid", 3, 30.0, 10, 20),
]

FUTURE = [
    ("2024-01-04", "m_early", 999, 9_999_999.0, 10, 20),
    ("2024-01-04", "m_late", 5000, 5_000_000.0, 5, 80_000),
    ("2024-01-05", "m_late", 1, 1.0, 5, 5),
]


def index(rows, **kw) -> PitMarketIndex:
    return PitMarketIndex(md(rows), config=PitMarketIndexConfig(**kw))


# ---------------------------------------------------------------- 存在性


def test_market_does_not_exist_before_its_first_public_trade():
    idx = index(BASE)
    before = idx.present_at(utc("2024-01-02"))
    assert set(before.column("condition_id").to_pylist()) == {"m_early"}
    after = idx.present_at(utc("2024-01-03"))
    assert set(after.column("condition_id").to_pylist()) == {"m_early", "m_mid"}


def test_a_trade_at_exactly_the_cutoff_second_does_not_make_the_market_exist():
    """同秒边界：eligible_from 等于 cutoff 时按不可用处理，与 as-of 的口径一致。"""
    idx = index(BASE)
    exact = utc("2024-01-01", 1)  # m_early 首笔恰在此秒
    assert idx.present_at(exact).num_rows == 0
    assert idx.present_at(exact + timedelta(seconds=1)).num_rows == 1


def test_frozen_availability_delay_shifts_existence():
    idx = index(BASE, availability_delay_seconds=120)
    assert idx.present_at(utc("2024-01-01", 1, 1)).num_rows == 0
    assert idx.present_at(utc("2024-01-01", 1, 2, 1)).num_rows == 1


def test_naive_cutoff_is_rejected():
    idx = index(BASE)
    with pytest.raises(ValueError):
        idx.present_at(datetime(2024, 1, 3))  # noqa: DTZ001


# ---------------------------------------------------------------- prefix-invariance


@pytest.mark.parametrize("hours", [24, 48, 60, 72])
def test_appending_future_trades_never_changes_a_historical_cutoff(hours):
    """向 tape 追加未来成交后，历史 cutoff 的成员与滚动指标必须逐位相同。"""
    cutoff = utc("2024-01-01") + timedelta(hours=hours)
    short = index(BASE)
    long = index(BASE + FUTURE)
    assert short.present_at(cutoff).to_pylist() == long.present_at(cutoff).to_pylist()
    assert (
        short.eligibility_at(cutoff, lookback_days=30).to_pylist()
        == long.eligibility_at(cutoff, lookback_days=30).to_pylist()
    )


def test_a_market_that_only_appears_later_is_invisible_to_earlier_cutoffs():
    long = index(BASE + FUTURE)
    ids = set(long.present_at(utc("2024-01-04")).column("condition_id").to_pylist())
    assert "m_late" not in ids
    ids_after = set(long.present_at(utc("2024-01-05")).column("condition_id").to_pylist())
    assert "m_late" in ids_after


# ---------------------------------------------------------------- 滚动资格


def test_incomplete_current_day_is_excluded_from_the_rolling_window():
    """当日未结束就不能计入：否则滚动指标含有 cutoff 之后的成交。

    同时演示存在性与流动性分离：m_mid 当日 00:00:50 已首笔成交，因此在 12:00 的
    cutoff 上**已经存在**；但 01-02 这一天尚未结束，它的滚动指标仍是 0。
    """
    idx = index(BASE)
    mid_day = utc("2024-01-02", 12)
    by_id = {
        r["condition_id"]: r for r in idx.eligibility_at(mid_day, lookback_days=30).to_pylist()
    }
    assert by_id["m_early"]["rolling_trades"] == 10  # 只含已完整结束的 01-01
    assert by_id["m_mid"]["rolling_trades"] == 0
    assert by_id["m_mid"]["rolling_active_days"] == 0


def test_rolling_window_expires_but_the_market_stays_present():
    """低流动性市场不能被从历史中抹掉：滚动指标归零，存在性不变。"""
    idx = index(BASE)
    late = utc("2024-02-01")
    rolling = {
        r["condition_id"]: r for r in idx.eligibility_at(late, lookback_days=3).to_pylist()
    }
    assert set(rolling) == {"m_early", "m_mid"}
    assert rolling["m_early"]["rolling_trades"] == 0
    assert rolling["m_early"]["rolling_active_days"] == 0


def test_membership_is_not_defined_by_rolling_notional():
    """成员资格只看首笔可见成交；名义额再大也不能让尚未存在的市场提前出现。"""
    idx = index(BASE + FUTURE)
    cutoff = utc("2024-01-04")
    rolling = {
        r["condition_id"]: r for r in idx.eligibility_at(cutoff, lookback_days=30).to_pylist()
    }
    assert "m_late" not in rolling  # 名义额 500 万，但首笔在 cutoff 之后
    assert rolling["m_mid"]["rolling_notional_provisional"] > 0
    assert "m_early" in rolling  # 名义额很小，但存在，且不被抹掉


def test_rolling_notional_is_named_provisional():
    """relay/venue 去重不可执行，名义额必须在列名上就标明 provisional。"""
    idx = index(BASE)
    cols = idx.eligibility_at(utc("2024-01-03"), lookback_days=30).column_names
    assert "rolling_notional_provisional" in cols
    assert not any(c == "rolling_notional" for c in cols)


def test_no_global_quality_market_table_is_produced():
    """索引不做门槛判定：输出里没有任何 admit/eligible 布尔列。"""
    idx = index(BASE)
    cols = idx.eligibility_at(utc("2024-01-03"), lookback_days=30).column_names
    assert not [c for c in cols if c in ("admitted", "eligible", "is_quality", "selected")]


def test_lookback_must_be_positive():
    idx = index(BASE)
    with pytest.raises(ValueError):
        idx.eligibility_at(utc("2024-01-03"), lookback_days=0)


# ---------------------------------------------------------------- label-blind


def test_census_never_reads_outcome_columns():
    assert set(CENSUS_COLUMNS) & OUTCOME_COLUMNS == set()
    assert set(DEDUP_COLUMNS) & OUTCOME_COLUMNS == set()


@pytest.mark.parametrize(
    "column", ["resolution_status", "winning_outcome_label", "resolved_at", "winners"]
)
def test_requesting_an_outcome_column_fails_before_reading_data(column):
    with pytest.raises(OutcomeColumnAccess):
        require_label_blind([*CENSUS_COLUMNS, column])


# ---------------------------------------------------------------- 确定性


def test_index_is_deterministic_across_rebuilds():
    a = index(BASE + FUTURE)
    b = index(BASE + FUTURE)
    assert a.presence.to_pylist() == b.presence.to_pylist()
    cutoff = utc("2024-01-04")
    assert (
        a.eligibility_at(cutoff, lookback_days=7).to_pylist()
        == b.eligibility_at(cutoff, lookback_days=7).to_pylist()
    )


def test_row_order_of_the_input_does_not_change_the_index():
    a = index(BASE)
    b = index(list(reversed(BASE)))
    assert a.presence.to_pylist() == b.presence.to_pylist()


def test_seam_day_present_in_both_segments_is_collapsed_once():
    """接缝日在两段各有一个分区；同一 (日, 市场) 必须合并为一行再计入活跃天数。"""
    rows = [
        ("2026-04-28", "m", 10, 100.0, 10, 20),
        ("2026-04-28", "m", 5, 50.0, 30, 40),
    ]
    idx = index(rows)
    rolling = idx.eligibility_at(utc("2026-04-30"), lookback_days=30).to_pylist()[0]
    assert rolling["rolling_active_days"] == 1
    assert rolling["rolling_trades"] == 15


# ---------------------------------------------------------------- n_eff


def test_kish_n_eff_penalises_concentration():
    assert kish_n_eff([1.0] * 10) == pytest.approx(10.0)
    assert kish_n_eff([100.0, 1.0, 1.0]) < 2.0
    assert kish_n_eff([]) == 0.0


# ---------------------------------------------------------------- 真实分区


@pytest.mark.skipif(not os.path.exists(HF), reason="缺少 Polymarket 来源数据")
def test_real_partition_census_is_deterministic_and_label_blind():
    path = os.path.join(HF, "2024-06-03.parquet")
    a_assets, a_markets = census_partition(path, "2024-06-03")
    b_assets, b_markets = census_partition(path, "2024-06-03")
    assert a_assets.to_pylist() == b_assets.to_pylist()
    assert a_markets.to_pylist() == b_markets.to_pylist()
    assert a_markets.num_rows > 0
    assert a_assets.num_rows >= a_markets.num_rows  # 每个市场至少一个 outcome token
    assert set(a_markets.column_names) & OUTCOME_COLUMNS == set()
    assert set(a_assets.column_names) & OUTCOME_COLUMNS == set()
    assert min(a_markets.column("trades").to_pylist()) >= 1
    assert min(a_markets.column("active_seconds").to_pylist()) >= 1


# ---------------------------------------------------------------- 审计产物


MANIFEST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "artifacts",
    "manifests",
    "pm_market_index.json",
)


@pytest.fixture(scope="module")
def pm_manifest():
    import json

    assert os.path.exists(MANIFEST), "缺少 artifacts/manifests/pm_market_index.json"
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def test_manifest_records_that_venue_and_relay_columns_are_absent(pm_manifest):
    """缺列必须被报告成缺列，不能让下游以为 relay 审计做过了。"""
    finding = next(
        f for f in pm_manifest["findings"] if f["code"] == "pm_census.venue_columns_absent"
    )
    assert all(v == [] for v in finding["evidence"]["present_columns"].values())


def test_manifest_records_the_negrisk_and_duplicate_leg_audits(pm_manifest):
    codes = {f["code"] for f in pm_manifest["findings"]}
    assert "pm_census.neg_risk_absent_in_both_segments" in codes
    assert "pm_census.duplicate_legs_provisional" in codes


def test_manifest_reports_concentration_and_disclaims_effective_sample_size(pm_manifest):
    """集中度不是统计有效样本量，产物里必须写明，不能被当成功效分母。"""
    conc = pm_manifest["coverage"]["trade_concentration"]
    assert conc["is_effective_sample_size"] is False
    assert "不是" in conc["note"]
    assert conc["nominal_trades"] > conc["kish_concentration_equivalent_over_markets"]
    assert conc["kish_concentration_equivalent_over_days"] < conc["distinct_utc_days"]


def test_manifest_does_not_alter_the_canonical_sample_split(pm_manifest):
    """普查只报告分布，不重划样本段；2026 仍是 contaminated audit。"""
    segments = pm_manifest["coverage"]["segments"]
    assert set(segments) <= {"discovery", "historical_validation", "contaminated_audit"}
    assert segments["contaminated_audit"]["trade_share"] > 0.8


def test_census_coverage_reports_the_true_date_range(pm_manifest):
    finding = next(f for f in pm_manifest["findings"] if f["code"] == "pm_census.coverage")
    assert finding["evidence"]["first"] < finding["evidence"]["last"]


# ---------------------------------------------------------------- 缓存与孤儿

import shutil


def _tiny_tape(path, ts_values, price=0.5, cid="0xc", asset="a1", prices=None):
    import pyarrow.parquet as pq

    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(ts_values)
    pq.write_table(
        pa.table(
            {
                "condition_id": pa.array([cid] * n, pa.string()),
                "asset_id": pa.array([asset] * n, pa.string()),
                "outcome_seq": pa.array([0] * n, pa.int64()),
                "block_timestamp": pa.array(ts_values, pa.int64()),
                "price": pa.array(prices or [price] * n, pa.float64()),
                "usdc_amount": pa.array([10.0] * n, pa.float64()),
                "neg_risk": pa.array([False] * n, pa.bool_()),
            }
        ),
        path,
    )


def test_equal_length_content_rewrite_changes_the_partition_digest(tmp_path):
    """等长内容改写必须被检出，否则会错误复用 sidecar 与派生产物。"""
    from arad.data_catalog.pm_census import partition_digest

    p = str(tmp_path / "hf" / "2024-01-01.parquet")
    _tiny_tape(p, [1_704_070_800, 1_704_070_900])
    before = partition_digest(p)
    _tiny_tape(p, [1_704_070_800, 1_704_070_900], price=0.9)  # 行数与列数完全相同
    after = partition_digest(p)
    assert before != after


def test_rebuild_after_equal_length_rewrite_updates_the_census(tmp_path):
    from arad.data_catalog.pm_census import build_census

    root = str(tmp_path / "hf")
    out = str(tmp_path / "out")
    p = os.path.join(root, "2024-01-01.parquet")
    _tiny_tape(p, [1_704_070_800, 1_704_070_900], prices=[0.5, 0.5])
    first, _ = build_census({"hf": root}, out, workers=1)
    # 行数、列数、文件结构完全相同，只改一个价格：派生的 price_changes 由 0 变 1
    _tiny_tape(p, [1_704_070_800, 1_704_070_900], prices=[0.5, 0.9])
    second, _ = build_census({"hf": root}, out, workers=1)
    assert first[0]["source_digest"] != second[0]["source_digest"]
    assert first[0]["fingerprint_market_day"] != second[0]["fingerprint_market_day"]
    assert second[0]["fingerprint_market_day"]


def test_deleting_a_source_partition_prunes_its_census_output(tmp_path):
    from arad.data_catalog.pm_census import build_census

    root, out = str(tmp_path / "hf"), str(tmp_path / "out")
    _tiny_tape(os.path.join(root, "2024-01-01.parquet"), [1_704_070_800])
    _tiny_tape(os.path.join(root, "2024-01-02.parquet"), [1_704_157_200])
    build_census({"hf": root}, out, workers=1)
    assert len(os.listdir(os.path.join(out, "market_day"))) == 2
    os.remove(os.path.join(root, "2024-01-02.parquet"))
    summaries, findings = build_census({"hf": root}, out, workers=1)
    assert len(summaries) == 1
    assert len(os.listdir(os.path.join(out, "market_day"))) == 1
    assert findings[0].evidence["pruned_orphan_count"] == 3


def test_index_refuses_to_load_orphan_partitions(tmp_path):
    from arad.data_catalog.pm_census import build_census

    root, out = str(tmp_path / "hf"), str(tmp_path / "out")
    _tiny_tape(os.path.join(root, "2024-01-01.parquet"), [1_704_070_800])
    summaries, _ = build_census({"hf": root}, out, workers=1)
    shutil.copy(
        os.path.join(out, "market_day", "hf_2024-01-01.parquet"),
        os.path.join(out, "market_day", "hf_2099-01-01.parquet"),
    )
    with pytest.raises(OrphanCensusPartition):
        PitMarketIndex.from_census_dir(out, expected_keys={s["key"] for s in summaries})


def test_census_verify_detects_tampered_output(tmp_path):
    from arad.data_catalog.pm_census import build_census, verify_census

    root, out = str(tmp_path / "hf"), str(tmp_path / "out")
    _tiny_tape(os.path.join(root, "2024-01-01.parquet"), [1_704_070_800])
    build_census({"hf": root}, out, workers=1)
    checked, bad = verify_census(out)
    assert checked == 1 and bad == []
    os.remove(os.path.join(out, "market_day", "hf_2024-01-01.parquet"))
    checked, bad = verify_census(out)
    assert bad == ["hf_2024-01-01"]


# ---------------------------------------------------------------- 滚窗口径


def test_complete_days_before_is_the_single_window_definition():
    """非午夜 cutoff 也必须给满 N 个已完整结束的日；两处口径共用本函数。"""
    days = complete_days_before(utc("2024-01-10", 12, 59), 7)
    assert days == [f"2024-01-0{d}" for d in range(3, 10)]
    assert len(days) == 7
    midnight = complete_days_before(utc("2024-01-10"), 7)
    assert midnight == [f"2024-01-0{d}" for d in range(3, 10)]


def test_rolling_window_covers_exactly_lookback_complete_days():
    rows = [(f"2024-01-{d:02d}", "m", 1, 1.0, 10, 20) for d in range(1, 11)]
    idx = index(rows)
    got = idx.eligibility_at(utc("2024-01-10", 12, 59), lookback_days=7).to_pylist()[0]
    assert got["rolling_active_days"] == 7


# ---------------------------------------------------------------- asset 级


def test_asset_level_presence_is_available(tmp_path):
    from arad.data_catalog.pm_census import build_census

    root, out = str(tmp_path / "hf"), str(tmp_path / "out")
    _tiny_tape(os.path.join(root, "2024-01-01.parquet"), [1_704_070_800], asset="yes")
    _tiny_tape(os.path.join(root, "2024-01-02.parquet"), [1_704_157_200], asset="no")
    build_census({"hf": root}, out, workers=1)
    idx = PitMarketIndex.from_census_dir(out)
    assert set(idx.asset_presence.column("asset_id").to_pylist()) == {"yes", "no"}
    early = idx.assets_present_at(utc("2024-01-02"))
    assert early.column("asset_id").to_pylist() == ["yes"]


def test_price_changes_are_computed_per_asset_not_per_market(tmp_path):
    """同一 condition 下 YES/NO 价格不同；混算会制造伪跳变。"""
    import pyarrow.parquet as pq

    from arad.data_catalog.pm_census import census_partition

    path = str(tmp_path / "2024-01-01.parquet")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 两个 token 交替成交，各自价格恒定：真实价格变化数应为 0
    pq.write_table(
        pa.table(
            {
                "condition_id": pa.array(["0xc"] * 6, pa.string()),
                "asset_id": pa.array(["yes", "no"] * 3, pa.string()),
                "outcome_seq": pa.array([0, 1] * 3, pa.int64()),
                "block_timestamp": pa.array(
                    [1_704_070_800 + i for i in range(6)], pa.int64()
                ),
                "price": pa.array([0.7, 0.3] * 3, pa.float64()),
                "usdc_amount": pa.array([1.0] * 6, pa.float64()),
                "neg_risk": pa.array([False] * 6, pa.bool_()),
            }
        ),
        path,
    )
    asset_tbl, market_tbl = census_partition(path, "2024-01-01")
    assert sorted(asset_tbl.column("price_changes").to_pylist()) == [0, 0]
    assert market_tbl.column("price_changes").to_pylist() == [0]
    assert market_tbl.column("assets").to_pylist() == [2]
    assert market_tbl.column("active_seconds").to_pylist() == [6]
