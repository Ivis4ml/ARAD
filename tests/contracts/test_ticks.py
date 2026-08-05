"""tick 归一化与 bar 物化的合同测试（M2 工作项 1 与 3）。

覆盖：累计量差分、日界不跨差分、累计量倒退检测（保留原值不覆盖）、
集合竞价首行、session 外行不进 bar、夜盘跨零点排序、
1min/日频 bar 的 available_time 语义。
"""

from __future__ import annotations

from datetime import date, datetime

import pyarrow as pa
import pyarrow.compute as pc
import pytest
from spine_fixtures import make_ticks, ramp

from arad.temporal.bars import bars_1min, bars_daily
from arad.temporal.sessions import SC, SHANGHAI, Placement
from arad.temporal.ticks import enrich

TD = date(2026, 7, 30)
PREV = date(2026, 7, 29)


def _enrich(rows, contract="sc2609", trading_day=TD, prev=PREV, **kw):
    return enrich(
        make_ticks(trading_day, contract, rows, **kw),
        product=SC,
        trading_day=trading_day,
        prev_trading_day=prev,
    )


def col(table: pa.Table, name: str) -> list:
    return table.column(name).to_pylist()


# ---------------------------------------------------------------- 差分


def test_cumulative_volume_is_differenced_within_the_trading_day():
    rows = [
        ("21:00:00", 0, 500.0, 10, 5_000_000.0),
        ("21:00:01", 0, 500.1, 25, 12_502_500.0),
        ("21:00:02", 0, 500.2, 25, 12_502_500.0),
    ]
    table, findings = _enrich(rows)
    assert col(table, "volume_delta") == [10, 15, 0]
    assert findings == []


def test_first_row_of_the_trading_day_carries_its_own_cumulative_value():
    """交易日起点从 0 开始累计；首行的 delta 就是首行的累计值（集合竞价成交）。"""
    rows = [("20:59:00", 500, 560.0, 191, 106_960_000.0), ("21:00:00", 0, 560.0, 200, 111_000_000.0)]
    table, _ = _enrich(rows)
    assert col(table, "volume_delta")[0] == 191
    assert col(table, "is_first_of_trading_day") == [True, False]


def test_cumulative_rollback_is_flagged_and_raw_value_is_preserved():
    """郑商所式日内倒退：必须标记，不得静默修复或覆盖原值。"""
    rows = [
        ("21:00:00", 0, 500.0, 100, 50_000_000.0),
        ("21:00:01", 0, 500.0, 90, 45_000_000.0),
        ("21:00:02", 0, 500.0, 130, 65_000_000.0),
    ]
    table, findings = _enrich(rows)
    assert col(table, "Volume") == [100, 90, 130]  # 原值保留
    assert col(table, "volume_delta") == [100, -10, 40]  # 派生列保留负值
    assert col(table, "volume_delta_nonneg") == [100, 0, 40]
    assert {f.code for f in findings} >= {"ticks.cumulative_rollback"}


# ---------------------------------------------------------------- 归类与排序


def test_night_ticks_across_midnight_are_ordered_and_dated():
    rows = [
        ("23:59:59", 0, 500.0, 10, 5_000_000.0),
        ("00:00:01", 0, 500.5, 20, 10_010_000.0),
    ]
    table, _ = _enrich(rows)
    ts = col(table, "natural_ts")
    assert ts[0] == datetime(2026, 7, 29, 23, 59, 59, tzinfo=SHANGHAI)
    assert ts[1] == datetime(2026, 7, 30, 0, 0, 1, tzinfo=SHANGHAI)
    assert ts[0] < ts[1]


def test_rows_are_sorted_by_natural_time_even_when_file_order_is_lexicographic():
    rows = [
        ("00:00:01", 0, 500.5, 20, 10_010_000.0),
        ("23:59:59", 0, 500.0, 10, 5_000_000.0),
    ]
    table, _ = _enrich(rows)
    ts = col(table, "natural_ts")
    assert ts == sorted(ts)
    # 排序后差分才正确
    assert col(table, "volume_delta") == [10, 10]


def test_auction_rows_are_marked_and_kept_in_the_session():
    rows = [("20:59:00", 500, 560.0, 191, 1.0), ("21:00:00", 0, 560.0, 200, 2.0)]
    table, _ = _enrich(rows)
    assert col(table, "placement") == [Placement.AUCTION.value, Placement.SEGMENT.value]
    assert col(table, "session_name") == ["night", "night"]


def test_post_close_snapshot_row_is_tagged_outside():
    rows = [("14:59:00", 0, 575.0, 10, 1.0), ("15:17:23", 500, 575.0, 10, 1.0)]
    table, findings = _enrich(rows)
    assert col(table, "placement")[1] == Placement.OUTSIDE.value
    assert {f.code for f in findings} >= {"ticks.out_of_session_rows"}


def test_missing_predecessor_quarantines_night_rows_instead_of_guessing():
    """归档首日没有前一交易日：夜盘行必须被隔离并留 finding，不得猜自然日。"""
    rows = [("21:00:00", 0, 500.0, 10, 1.0), ("09:00:00", 0, 501.0, 20, 2.0)]
    table, findings = enrich(
        make_ticks(TD, "sc2609", rows),
        product=SC,
        trading_day=TD,
        prev_trading_day=None,
    )
    assert col(table, "quarantined") == [True, False]
    assert {f.code for f in findings} >= {"ticks.calendar_predecessor_missing"}


# ---------------------------------------------------------------- bar


def test_1min_bars_exclude_out_of_session_and_break_rows():
    rows = [
        ("09:00:00", 0, 500.0, 10, 1.0),
        ("09:00:30", 0, 501.0, 20, 2.0),
        ("12:00:00", 0, 502.0, 30, 3.0),  # 午休
        ("15:17:23", 0, 503.0, 40, 4.0),  # 盘后
    ]
    table, _ = _enrich(rows)
    bars = bars_1min(table, product=SC)
    assert bars.num_rows == 1
    assert col(bars, "placement") == [Placement.SEGMENT.value]
    assert col(bars, "open") == [500.0] and col(bars, "close") == [501.0]
    assert col(bars, "volume") == [20]  # 首行 delta 10 加次行 delta 10


def test_1min_bar_available_time_is_the_bar_end():
    rows = [("09:00:00", 0, 500.0, 10, 1.0), ("09:00:30", 0, 501.0, 20, 2.0)]
    table, _ = _enrich(rows)
    bars = bars_1min(table, product=SC)
    assert col(bars, "bar_start") == [datetime(2026, 7, 30, 9, 0, tzinfo=SHANGHAI)]
    assert col(bars, "available_time") == [datetime(2026, 7, 30, 9, 1, tzinfo=SHANGHAI)]


def test_segment_closing_print_folds_into_the_last_bar():
    """10:15:00 的收盘打印属于 10:14 这一分钟 bar，不额外生成一根 10:15 bar。"""
    rows = ramp(10 * 3600 + 13 * 60, 3, step=60)  # 10:13, 10:14, 10:15
    table, _ = _enrich(rows)
    bars = bars_1min(table, product=SC)
    starts = [b.strftime("%H:%M") for b in col(bars, "bar_start")]
    assert starts == ["10:13", "10:14"]


def test_auction_bar_is_separate_and_flagged():
    rows = [("20:59:00", 500, 560.0, 191, 1.0)] + ramp(21 * 3600, 2, step=60, vol0=191)
    table, _ = _enrich(rows)
    bars = bars_1min(table, product=SC)
    auction = bars.filter(pc.equal(bars.column("placement"), Placement.AUCTION.value))
    assert auction.num_rows == 1
    assert col(auction, "volume") == [191]


def test_daily_bar_reports_session_presence_and_quality_counters():
    rows = (
        [("20:59:00", 500, 560.0, 100, 1.0)]
        + ramp(21 * 3600, 3, step=60, vol0=100)
        + ramp(9 * 3600, 3, step=60, vol0=130)
        + [("15:17:23", 500, 561.0, 160, 9.0)]
    )
    table, _ = _enrich(rows)
    daily = bars_daily(table, product=SC)
    assert daily.num_rows == 1
    assert col(daily, "night_present") == [True]
    assert col(daily, "day_present") == [True]
    assert col(daily, "n_out_of_session") == [1]
    assert col(daily, "contract") == ["sc2609"]
    assert col(daily, "trading_day") == [20260730]


def test_daily_bar_available_time_is_not_earlier_than_the_day_session_close():
    rows = ramp(9 * 3600, 3, step=60)
    table, _ = _enrich(rows)
    daily = bars_daily(table, product=SC)
    assert col(daily, "available_time")[0] >= datetime(2026, 7, 30, 15, 0, tzinfo=SHANGHAI)


def test_enrich_rejects_a_table_whose_trading_day_disagrees_with_the_argument():
    with pytest.raises(ValueError):
        enrich(
            make_ticks(date(2026, 7, 29), "sc2609", ramp(9 * 3600, 2)),
            product=SC,
            trading_day=TD,
            prev_trading_day=PREV,
        )
