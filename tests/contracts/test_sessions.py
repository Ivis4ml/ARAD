"""SC 品种时段表与交易日历的合同测试（M2 工作项 1）。

覆盖：夜盘跨零点归属、集合竞价窗口、午休不判为 session 中断、
盘后快照行判为 session 外、时段表与 tick 实测的一致性校验、
交易日历边界拒绝猜测。
"""

from __future__ import annotations

from datetime import date, time

import pytest

from arad.data_catalog.timeguard import natural_date_of_tick
from arad.temporal.calendar import CalendarBoundaryError, TradingCalendar
from arad.temporal.sessions import (
    PRODUCTS,
    SC,
    Placement,
    natural_date_for,
    verify_session_table,
)


def sod(h: int, m: int = 0, s: int = 0) -> int:
    return h * 3600 + m * 60 + s


# ---------------------------------------------------------------- 时段表结构


def test_sc_has_two_sessions_and_lunch_break_does_not_split_the_day_session():
    """午休是 session 内的 break，不是第三个 session。"""
    table = SC.sessions
    assert [s.name for s in table.sessions] == ["night", "day"]
    day = table.session("day")
    assert day.open == time(9, 0) and day.close == time(15, 0)
    # 三个连续竞价 segment，但仍是一个 session
    assert len(day.segments) == 3
    assert [(s.start, s.end) for s in day.segments] == [
        (time(9, 0), time(10, 15)),
        (time(10, 30), time(11, 30)),
        (time(13, 30), time(15, 0)),
    ]


def test_night_session_is_one_segment_crossing_midnight():
    night = SC.sessions.session("night")
    assert night.open == time(21, 0) and night.close == time(2, 30)
    assert night.close_next_day is True
    assert len(night.segments) == 1


def test_product_reference_declares_multiplier_and_tick_size():
    assert PRODUCTS["sc"] is SC
    assert SC.exchange == "INE"
    assert SC.multiplier == 1000.0
    assert SC.tick_size == 0.1
    assert SC.reference  # 版本化权威参照出处不得为空


# ---------------------------------------------------------------- 归类


@pytest.mark.parametrize(
    ("seconds", "session_name", "placement"),
    [
        (sod(20, 55), "night", Placement.AUCTION),
        (sod(20, 59), "night", Placement.AUCTION),
        (sod(21, 0), "night", Placement.SEGMENT),
        (sod(23, 59, 59), "night", Placement.SEGMENT),
        (sod(0, 0), "night", Placement.SEGMENT),
        (sod(2, 30), "night", Placement.SEGMENT),
        (sod(8, 55), "day", Placement.AUCTION),
        (sod(9, 0), "day", Placement.SEGMENT),
        (sod(10, 15), "day", Placement.SEGMENT),
        (sod(11, 30), "day", Placement.SEGMENT),
        (sod(15, 0), "day", Placement.SEGMENT),
    ],
)
def test_classify_in_session_points(seconds, session_name, placement):
    got = SC.sessions.classify(seconds)
    assert got.session_name == session_name
    assert got.placement is placement


@pytest.mark.parametrize("seconds", [sod(10, 20), sod(12, 0), sod(13, 0)])
def test_lunch_and_morning_breaks_are_breaks_not_outside(seconds):
    """午休/上午休息属于 day session 内部 break：不判中断，也不进 bar。"""
    got = SC.sessions.classify(seconds)
    assert got.session_name == "day"
    assert got.placement is Placement.BREAK


@pytest.mark.parametrize("seconds", [sod(15, 17, 23), sod(3, 0), sod(19, 0)])
def test_post_close_and_dead_zones_are_outside(seconds):
    """15:17 结算快照行必须判为 session 外，否则会污染日盘收盘价与 RV。"""
    got = SC.sessions.classify(seconds)
    assert got.placement is Placement.OUTSIDE


# ---------------------------------------------------------------- 自然日归属


def test_night_before_midnight_maps_to_previous_trading_day():
    nd = natural_date_for(
        SC.sessions, date(2026, 7, 30), sod(20, 59), prev_trading_day=date(2026, 7, 29)
    )
    assert nd == date(2026, 7, 29)


def test_night_after_midnight_maps_to_next_natural_day_of_previous_trading_day():
    # 周一交易日：夜盘在周五晚开始，跨零点后是周六凌晨
    nd = natural_date_for(
        SC.sessions, date(2026, 7, 27), sod(1, 0), prev_trading_day=date(2026, 7, 24)
    )
    assert nd == date(2026, 7, 25)


def test_day_session_maps_to_trading_day():
    nd = natural_date_for(
        SC.sessions, date(2026, 7, 30), sod(9, 30), prev_trading_day=date(2026, 7, 29)
    )
    assert nd == date(2026, 7, 30)


def test_session_table_windows_agree_with_timeguard_scalar_rule():
    """时段表驱动的归属必须与 M1 的 natural_date_of_tick 在其定义域上逐点一致。"""
    windows = SC.sessions.natural_date_windows()
    for h in list(range(8, 16)) + list(range(20, 24)) + [0, 1, 2]:
        tick = time(h, 5)
        expect = natural_date_of_tick(
            date(2026, 7, 30), tick, prev_trading_day=date(2026, 7, 29)
        )
        got = natural_date_of_tick(
            date(2026, 7, 30), tick, prev_trading_day=date(2026, 7, 29), windows=windows
        )
        assert got == expect, h


def test_timeguard_without_windows_still_refuses_unknown_window():
    from arad.data_catalog.timeguard import SessionAttributionError

    with pytest.raises(SessionAttributionError):
        natural_date_of_tick(date(2026, 7, 30), time(17, 30), prev_trading_day=date(2026, 7, 29))


# ---------------------------------------------------------------- session 窗口


def test_session_windows_are_timezone_aware_and_ordered():
    wins = SC.sessions.windows(date(2026, 7, 30), prev_trading_day=date(2026, 7, 29))
    assert [w.name for w in wins] == ["night", "day"]
    night, day = wins
    assert night.open.tzinfo is not None
    assert night.open.isoformat() == "2026-07-29T21:00:00+08:00"
    assert night.close.isoformat() == "2026-07-30T02:30:00+08:00"
    assert night.auction_start.isoformat() == "2026-07-29T20:55:00+08:00"
    assert day.open.isoformat() == "2026-07-30T09:00:00+08:00"
    assert day.close.isoformat() == "2026-07-30T15:00:00+08:00"
    assert night.close < day.open


def test_session_windows_over_a_weekend_use_the_calendar_predecessor():
    wins = SC.sessions.windows(date(2026, 7, 27), prev_trading_day=date(2026, 7, 24))
    night = wins[0]
    assert night.open.isoformat() == "2026-07-24T21:00:00+08:00"
    assert night.close.isoformat() == "2026-07-25T02:30:00+08:00"


# ---------------------------------------------------------------- 实测校验


def test_verify_session_table_flags_observed_ticks_outside_declared_windows():
    observed = {
        "night": (sod(20, 59), sod(2, 30)),
        "day": (sod(8, 59), sod(15, 17)),  # 15:17 盘后快照
    }
    findings = verify_session_table(SC.sessions, observed)
    codes = {f.code for f in findings}
    assert "sessions.observed_outside_declared" in codes


def test_verify_session_table_accepts_conforming_observation():
    observed = {"night": (sod(20, 59), sod(2, 30)), "day": (sod(8, 59), sod(15, 0))}
    assert verify_session_table(SC.sessions, observed) == []


# ---------------------------------------------------------------- 交易日历


def test_calendar_prev_and_next():
    cal = TradingCalendar([date(2026, 7, 24), date(2026, 7, 27), date(2026, 7, 28)], source="test")
    assert cal.prev(date(2026, 7, 27)) == date(2026, 7, 24)
    assert cal.next(date(2026, 7, 27)) == date(2026, 7, 28)


def test_calendar_refuses_to_guess_at_the_first_day():
    """首个归档日没有前一交易日：必须报错，不得猜一个自然日。"""
    cal = TradingCalendar([date(2022, 11, 1), date(2022, 11, 2)], source="test")
    with pytest.raises(CalendarBoundaryError):
        cal.prev(date(2022, 11, 1))


def test_calendar_unknown_day_is_rejected():
    cal = TradingCalendar([date(2026, 7, 27)], source="test")
    with pytest.raises(CalendarBoundaryError):
        cal.prev(date(2026, 7, 28))


def test_calendar_flags_night_session_across_an_unexplained_gap():
    """夜盘存在却跨越了非周末的长间隔：可能缺归档日，必须成为 finding。"""
    cal = TradingCalendar(
        [date(2026, 5, 1), date(2026, 5, 11), date(2026, 5, 12)], source="test"
    )
    findings = cal.night_gap_findings({date(2026, 5, 11), date(2026, 5, 12)})
    codes = {f.code for f in findings}
    assert "calendar.night_session_across_unexplained_gap" in codes
    # 5-12 的前一日 5-11 相邻，不应报告
    assert all(f.evidence.get("trading_day") != "2026-05-12" for f in findings)


def test_calendar_weekend_gap_is_not_flagged():
    cal = TradingCalendar([date(2026, 7, 24), date(2026, 7, 27)], source="test")
    assert cal.night_gap_findings({date(2026, 7, 27)}) == []


def test_calendar_fingerprint_is_deterministic_and_content_sensitive():
    a = TradingCalendar([date(2026, 7, 24), date(2026, 7, 27)], source="test")
    b = TradingCalendar([date(2026, 7, 24), date(2026, 7, 27)], source="test")
    c = TradingCalendar([date(2026, 7, 24), date(2026, 7, 28)], source="test")
    assert a.fingerprint == b.fingerprint
    assert a.fingerprint != c.fingerprint


# ---------------------------------------------------------------- 多品种（M8.1）


def test_every_commodity_product_shares_the_declared_day_geometry():
    """品种之间只差夜盘收盘。日盘几何沿用 SC 已按权威参照声明的那一套。

    实测依据（M8.1）：跨 2022 至 2026 采样 16 个交易日、88 个品种，
    每个 (品种, 日) 取该日最大的合约文件，按 tick 时刻的 5 分钟空档判分段，
    商品品种全部落在 09:00-10:15 / 10:30-11:30 / 13:30-15:00 上。
    """
    from arad.temporal.sessions import PRODUCTS

    reference = PRODUCTS["sc"].sessions.session("day")
    for name, product in PRODUCTS.items():
        day = product.sessions.session("day")
        assert day.open == reference.open, name
        assert day.close == reference.close, name
        assert day.auction_start == reference.auction_start, name
        assert [(s.start, s.end) for s in day.segments] == [
            (s.start, s.end) for s in reference.segments
        ], name


def test_night_close_partitions_the_products_into_the_measured_classes():
    from arad.temporal.sessions import NIGHT_CLASSES, PRODUCTS

    for night_close, products in NIGHT_CLASSES.items():
        for name in products:
            table = PRODUCTS[name].sessions
            names = [s.name for s in table.sessions]
            if not night_close:
                assert names == ["day"], name
                continue
            hh, mm = (int(x) for x in night_close.split(":"))
            night = table.session("night")
            assert (night.close.hour, night.close.minute) == (hh, mm), name
            assert night.open == time(21, 0), name
            assert night.close_next_day is (hh < 12), name


def test_a_derived_session_table_says_so_and_does_not_claim_an_exchange_source():
    """出处标注必须比 sc 弱，而且必须写明弱在哪。

    由数据归纳的时段表有一个结构性盲区：集合竞价窗口内没有 tick，
    因此实测首笔是竞价成交打印而不是开盘。工厂因此不用实测值定任何时刻，
    只用它判定品种属于哪一类。
    """
    from arad.temporal.sessions import PRODUCTS

    sc = PRODUCTS["sc"].sessions.reference
    cu = PRODUCTS["cu"].sessions.reference
    assert "未由数据反推" in sc
    assert "原始 tick 实测归纳" in cu
    assert "不是交易所公告" in cu
    assert "集合竞价窗口内没有 tick" in cu


def test_contract_regex_matches_the_same_letters_as_the_m1_scanner():
    """两处正则的字母类必须一致。

    `build.py` 原本写 `[a-z]`，因此 35 个大写前缀品种在这里一个文件都匹配不上，
    扫描返回 days=0 entries=0 而**不报错** —— 建出来的是一张空 spine。
    """
    from arad.data_catalog.commodity import _CONTRACT_RE as M1
    from arad.temporal.build import _CONTRACT_RE as SPINE

    for name in ("MA609_20260730.csv", "IF2608_20260730.csv",
                 "sc2601_20260730.csv", "a2601_20260730.csv"):
        assert bool(SPINE.match(name)) is bool(M1.search(name)), name
