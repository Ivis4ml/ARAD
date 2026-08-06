"""目标定义与可重复性的合同测试（M2 工作项 4，出口条件 1）。

primary target：决策 cutoff 后下一 SC session 的已实现波动。
diagnostic-only target：同期开盘跳空吸收，明确不作可交易 alpha 主张。

关键陷阱：跨 segment（10:15-10:30、11:30-13:30）的 bar 间收益不是 1 分钟收益，
计入 RV 会把两小时的价格变化当成一分钟波动；no-trade 必须是 NULL 加原因，
绝不能是 0.0。
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta

import pytest
from spine_fixtures import make_ticks, ticks_from_points

from arad.temporal.bars import bars_1min
from arad.temporal.errors import LookaheadError
from arad.temporal.sessions import SC, SHANGHAI
from arad.temporal.targets import (
    OPEN_GAP_ABSORPTION,
    RV_NEXT_SESSION,
    build_session_bars,
    open_gap_absorption,
    realized_volatility,
)
from arad.temporal.ticks import enrich

TD = date(2026, 7, 30)
PREV = date(2026, 7, 29)


def sod(h, m=0, s=0):
    return h * 3600 + m * 60 + s


def sessions_from(points, *, contract="sc2609", trading_day=TD, prev=PREV, **kw):
    rows = ticks_from_points(points)
    ticks, _ = enrich(
        make_ticks(trading_day, contract, rows, **kw),
        product=SC,
        trading_day=trading_day,
        prev_trading_day=prev,
    )
    return build_session_bars(bars_1min(ticks, product=SC), product=SC, prev_trading_day=prev)


def pick(sessions, name):
    return next(s for s in sessions if s.session_name == name)


# ---------------------------------------------------------------- spec 声明


def test_target_specs_declare_decision_time_execution_lag_and_claim():
    from arad.temporal.targets import RET_NEXT_SESSION

    assert RV_NEXT_SESSION.kind == "primary"
    # 已实现波动是一个正的量级，不是可捕获的收益，且本数据集没有波动率工具
    assert RV_NEXT_SESSION.tradable_claim is False
    assert RV_NEXT_SESSION.label_is_return is False
    assert OPEN_GAP_ABSORPTION.kind == "diagnostic_only"
    assert OPEN_GAP_ABSORPTION.tradable_claim is False
    assert "不作可交易" in OPEN_GAP_ABSORPTION.description
    assert RV_NEXT_SESSION.execution_lag_seconds > 0
    # 只有收益型规则才承载可交易主张，两者必须一致
    assert RET_NEXT_SESSION.label_is_return is True
    assert RET_NEXT_SESSION.tradable_claim is True


def test_decision_time_precedes_the_label_window_by_the_execution_lag():
    window = SC.sessions.windows(TD, prev_trading_day=PREV)[0]
    start, end = RV_NEXT_SESSION.label_window(window)
    decision = RV_NEXT_SESSION.decision_time(window)
    assert start == window.open and end == window.close
    assert decision == window.open - timedelta(seconds=RV_NEXT_SESSION.execution_lag_seconds)
    assert decision < start


def test_zero_execution_lag_is_rejected_because_decision_would_equal_label_start():
    from arad.temporal.targets import TargetSpec

    with pytest.raises(ValueError):
        TargetSpec(
            name="bad", kind="primary", description="d",
            execution_lag_seconds=0, tradable_claim=True, params={},
        )


# ---------------------------------------------------------------- RV


def test_realized_volatility_excludes_returns_spanning_a_session_break():
    """11:30 → 13:30 的 bar 间收益跨越午休，不得进入 1 分钟收益序列。"""
    points = (
        [(sod(11, 26), 500.0, 10), (sod(11, 27), 500.1, 10),
         (sod(11, 28), 500.2, 10), (sod(11, 29), 500.3, 10)]
        + [(sod(13, 30), 520.0, 10), (sod(13, 31), 520.1, 10), (sod(13, 32), 520.2, 10)]
    )
    day = pick(sessions_from(points), "day")
    rets = day.returns()
    assert len(rets) == 5  # 段内 3 + 段内 2，跨段那一根被排除
    assert max(abs(r) for r in rets) < 1e-3
    assert abs(math.log(520.0 / 500.3)) > 0.03  # 被排除的那根有多大
    value, reason, n = realized_volatility(day)
    assert reason is None and n == 5
    assert value == pytest.approx(math.sqrt(sum(r * r for r in rets)))


def test_lunch_break_does_not_split_the_day_session():
    """同一条测试的另一面：午休不产生第二个 day session。"""
    points = [(sod(9, 30), 500.0, 10), (sod(14, 0), 501.0, 10)]
    days = [s for s in sessions_from(points) if s.session_name == "day"]
    assert len(days) == 1
    assert len(days[0].segments) == 3


def test_realized_volatility_excludes_the_auction_bar():
    base = [(sod(21, 0), 500.0, 10), (sod(21, 1), 500.1, 10), (sod(21, 2), 500.2, 10)]
    without = pick(sessions_from(base), "night")
    with_auction = pick(sessions_from([(sod(20, 59), 480.0, 5)] + base), "night")
    assert with_auction.auction is not None
    a, _, na = realized_volatility(with_auction)
    b, _, nb = realized_volatility(without)
    assert na == nb
    assert a == pytest.approx(b)


def test_no_ticks_gives_null_with_a_reason_never_zero():
    """没有夜盘数据的交易日仍要产生一行 no-trade 记录，不能整段消失。"""
    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10), (sod(9, 32), 500.2, 10)]
    sess = sessions_from(points)
    assert {s.session_name for s in sess} == {"night", "day"}
    night = pick(sess, "night")
    value, reason, n = realized_volatility(night)
    assert value is None and reason == "no_ticks" and n == 0
    day = pick(sess, "day")
    assert realized_volatility(day)[0] is not None


def test_zero_volume_session_is_no_trade_not_zero_volatility():
    points = [(sod(9, 30), 500.0, 0), (sod(9, 31), 500.0, 0), (sod(9, 32), 500.0, 0)]
    day = pick(sessions_from(points), "day")
    value, reason, _ = realized_volatility(day)
    assert value is None
    assert reason == "zero_volume"


def test_single_return_session_is_underdetermined_not_zero():
    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10)]
    day = pick(sessions_from(points), "day")
    value, reason, n = realized_volatility(day)
    assert value is None and reason == "insufficient_returns" and n == 1


def test_limit_locked_session_is_no_trade():
    points = [(sod(9, 30), 900.0, 10), (sod(9, 31), 900.0, 10), (sod(9, 32), 900.0, 10)]
    day = pick(sessions_from(points, upper_limit=900.0), "day")
    value, reason, _ = realized_volatility(day)
    assert value is None and reason == "limit_locked"


# ---------------------------------------------------------------- 开盘跳空吸收


def _night_and_day(prev_close_price, open_price, later_price):
    """构造：夜盘收在 prev_close_price，日盘以 open_price 开出后走到 later_price。"""
    points = (
        [(sod(21, 0), prev_close_price, 10), (sod(21, 1), prev_close_price, 10)]
        + [(sod(9, 0), open_price, 10), (sod(9, 1), open_price, 10)]
        + [(sod(9, 28), later_price, 10), (sod(9, 29), later_price, 10)]
    )
    sess = sessions_from(points)
    return pick(sess, "night"), pick(sess, "day")


def test_gap_absorption_measures_the_reversed_fraction():
    # 跳空 +2%，随后回吸一半
    night, day = _night_and_day(500.0, 510.0, 505.0)
    value, reason, extra = open_gap_absorption(
        day, night, k_minutes=30, min_abs_gap=OPEN_GAP_ABSORPTION.params["min_abs_gap"]
    )
    assert reason is None
    assert extra["gap"] == pytest.approx(math.log(510.0 / 500.0))
    assert value == pytest.approx(-math.log(505.0 / 510.0) / math.log(510.0 / 500.0), rel=1e-9)
    assert 0 < value < 1


def test_gap_below_threshold_is_undefined_not_zero():
    night, day = _night_and_day(500.0, 500.01, 500.02)
    value, reason, _ = open_gap_absorption(
        day, night, k_minutes=30, min_abs_gap=OPEN_GAP_ABSORPTION.params["min_abs_gap"]
    )
    assert value is None and reason == "gap_below_threshold"


def test_gap_requires_a_previous_session_of_the_same_contract():
    _, day = _night_and_day(500.0, 510.0, 505.0)
    value, reason, _ = open_gap_absorption(day, None, k_minutes=30, min_abs_gap=1e-4)
    assert value is None and reason == "no_prev_session"


def test_gap_rejects_a_previous_session_of_a_different_contract():
    night, day = _night_and_day(500.0, 510.0, 505.0)
    other = pick(
        sessions_from([(sod(21, 0), 400.0, 10), (sod(21, 1), 400.0, 10)], contract="sc2610"),
        "night",
    )
    assert other.contract != day.contract
    value, reason, _ = open_gap_absorption(day, other, k_minutes=30, min_abs_gap=1e-4)
    assert value is None and reason == "prev_session_contract_mismatch"
    assert open_gap_absorption(day, night, k_minutes=30, min_abs_gap=1e-4)[1] is None


# ---------------------------------------------------------------- 可重复性


def test_target_table_fingerprint_is_reproducible_and_content_sensitive():
    from arad.temporal.manifest import fingerprint_table

    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10), (sod(9, 32), 500.2, 10)]
    a = sessions_from(points)
    b = sessions_from(points)
    from arad.temporal.targets import build_target_table

    ta = build_target_table(a, RV_NEXT_SESSION, product=SC)
    tb = build_target_table(b, RV_NEXT_SESSION, product=SC)
    assert fingerprint_table(ta) == fingerprint_table(tb)

    changed = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.5, 10), (sod(9, 32), 500.2, 10)]
    tc = build_target_table(sessions_from(changed), RV_NEXT_SESSION, product=SC)
    assert fingerprint_table(ta) != fingerprint_table(tc)


def test_target_rows_carry_pit_and_contamination_metadata():
    from arad.temporal.episode import SampleSegment
    from arad.temporal.targets import build_target_table

    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10), (sod(9, 32), 500.2, 10)]
    rows = build_target_table(sessions_from(points), RV_NEXT_SESSION, product=SC).to_pylist()
    assert len(rows) == 2  # night 与 day 各一行，夜盘为 no-trade
    r = next(x for x in rows if x["session_name"] == "day")
    assert r["decision_time"] < r["label_start"] < r["label_end"]
    assert r["episode_id"]
    assert r["sample_segment"] == SampleSegment.CONTAMINATED_AUDIT.value
    assert r["target_name"] == RV_NEXT_SESSION.name
    assert r["tradable_claim"] is False
    assert r["contract"] == "sc2609"


def test_build_target_table_refuses_a_session_whose_open_precedes_the_decision():
    """守卫：任何使 decision_time >= label_start 的配置都必须报错。"""
    from arad.temporal.targets import TargetSpec, build_target_table

    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10)]
    bad = TargetSpec(
        name="bad", kind="primary", description="d",
        execution_lag_seconds=60, tradable_claim=True, params={},
    )
    object.__setattr__(bad, "execution_lag_seconds", -60)  # 绕过构造校验，测第二道守卫
    with pytest.raises(LookaheadError):
        build_target_table(sessions_from(points), bad, product=SC)


def test_session_open_price_uses_the_auction_print_when_it_matched():
    night = pick(
        sessions_from([(sod(20, 59), 480.0, 5), (sod(21, 0), 500.0, 10), (sod(21, 1), 500.1, 10)]),
        "night",
    )
    assert night.open_price == 480.0


def test_session_open_price_falls_back_to_the_first_continuous_bar_without_a_match():
    night = pick(
        sessions_from([(sod(20, 59), 480.0, 0), (sod(21, 0), 500.0, 10), (sod(21, 1), 500.1, 10)]),
        "night",
    )
    assert night.open_price == 500.0


def test_session_windows_are_derived_from_the_trading_day_not_from_the_data():
    points = [(sod(9, 30), 500.0, 10)]
    day = pick(sessions_from(points), "day")
    assert day.window.open == datetime(2026, 7, 30, 9, 0, tzinfo=SHANGHAI)
    assert day.window.close == datetime(2026, 7, 30, 15, 0, tzinfo=SHANGHAI)


def test_segment_counts_cover_every_row_including_no_trade():
    """按样本段的计数必须等于总行数：用可空的 value 列计数会漏掉 no-trade 行。"""
    from arad.temporal.targets import build_target_table, no_trade_counts, segment_counts

    points = [(sod(9, 30), 500.0, 10), (sod(9, 31), 500.1, 10), (sod(9, 32), 500.2, 10)]
    table = build_target_table(sessions_from(points), RV_NEXT_SESSION, product=SC)
    counts = segment_counts(table)
    assert sum(counts.values()) == table.num_rows
    valued = segment_counts(table, valued_only=True)
    assert sum(valued.values()) == table.num_rows - sum(no_trade_counts(table).values())
    assert sum(valued.values()) < sum(counts.values())  # 该样例含一行 no-trade 夜盘


# ---------------------------------------------------------------- 收益型目标（M2.1）


def test_the_limit_guard_uses_a_tick_tolerance_not_float_equality():
    """交易所限价与成交价之间有浮点噪声：精确相等会把锁死的 session 当成正常成交。

    实测 sc2604 在 20260303 日盘整段 225 根 bar 收于 572.3，而限价字段是
    572.3000000000002，差 2.7e-13。原实现返回 False，于是那一天被物化成
    `value=0.0, no_trade=False` —— 一手都买不到的 session 记成一个真实的零。
    """
    from arad.temporal.targets import SessionBars

    window = SC.sessions.windows(TD, prev_trading_day=PREV)[1]
    bars = [{"close": 572.3, "open": 572.3, "volume": 1, "bar_end": window.open,
             "bar_start": window.open}]
    session = SessionBars(
        product="sc", contract="sc2604", trading_day=TD, session_seq=window.seq,
        session_name=window.name, window=window, auction=None, segments=[bars],
        upper_limit=572.3000000000002, lower_limit=449.6, tick_size=0.1,
    )
    assert session.at_price_limit(572.3) is True
    assert session.is_limit_locked() is True
    # 一个 tick 之外的价格不应被误判
    assert session.at_price_limit(572.1) is False


def test_the_return_target_excludes_the_opening_gap_and_names_its_entry():
    from arad.temporal.targets import RET_NEXT_SESSION

    window = SC.sessions.windows(TD, prev_trading_day=PREV)[1]
    start, end = RET_NEXT_SESSION.label_window(window)
    assert start == window.open + timedelta(minutes=1)
    assert end == window.close
    assert RET_NEXT_SESSION.execution_time(window) == start
    assert RET_NEXT_SESSION.decision_time(window) < start
    assert "开盘跳空不在本目标的主张之内" in RET_NEXT_SESSION.description


def test_a_return_is_undefined_when_entry_or_exit_sits_on_the_limit():
    """入场那一刻锁在涨停就买不进，收盘锁在跌停就卖不出。整段是否锁死与此无关。"""
    from arad.temporal.targets import SessionBars, entry_to_close_return

    window = SC.sessions.windows(TD, prev_trading_day=PREV)[1]

    def session(closes):
        bars = [
            {"close": c, "open": c, "volume": 5,
             "bar_start": window.open + timedelta(minutes=i),
             "bar_end": window.open + timedelta(minutes=i + 1)}
            for i, c in enumerate(closes)
        ]
        return SessionBars(
            product="sc", contract="sc2609", trading_day=TD, session_seq=window.seq,
            session_name=window.name, window=window, auction=None, segments=[bars],
            upper_limit=610.0, lower_limit=500.0, tick_size=0.1,
        )

    value, reason, _ = entry_to_close_return(session([610.0, 605.0, 600.0]),
                                             entry_offset_minutes=1)
    assert value is None and reason == "entry_at_price_limit"
    value, reason, _ = entry_to_close_return(session([550.0, 570.0, 610.0]),
                                             entry_offset_minutes=1)
    assert value is None and reason == "exit_at_price_limit"
    value, reason, extra = entry_to_close_return(session([550.0, 560.0, 561.0]),
                                                entry_offset_minutes=1)
    assert reason is None
    assert extra["entry_price"] == 550.0 and extra["exit_price"] == 561.0
    assert value == pytest.approx(math.log(561.0 / 550.0))


def test_an_unregistered_label_rule_cannot_silently_materialise_rv():
    """原实现是两分支 if/else 且 else 落在 RV 上：漏加分支会以新名字发出旧口径。"""
    from arad.temporal.targets import TargetSpec

    with pytest.raises(ValueError, match="未知的 label_rule"):
        TargetSpec(name="x", kind="primary", description="d", execution_lag_seconds=60,
                   tradable_claim=False, params={}, label_rule="not_a_rule")


def test_a_return_label_must_declare_a_tradable_claim():
    from arad.temporal.targets import TargetSpec

    with pytest.raises(ValueError, match="tradable_claim"):
        TargetSpec(name="x", kind="primary", description="d", execution_lag_seconds=60,
                   tradable_claim=False, params={"entry_offset_minutes": 1},
                   label_rule="entry_to_close")


# ---------------------------------------------------------------- 实测钉子（需 spine）

import os

_SPINE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "spine", "sc",
)
_RV = os.path.join(_SPINE, "target_sc_rv_next_session.parquet")
_RET = os.path.join(_SPINE, "target_sc_ret_next_session.parquet")


@pytest.mark.skipif(not os.path.exists(_RV), reason="需要先运行 spine build")
def test_the_float_gap_session_is_recorded_as_no_trade_not_as_a_real_zero():
    """钉住修复：全库扫描出的浮点缝隙只有两个 session，其中这一个进了主力视图。

    修复前它是 `value=0.0, no_trade=False` —— 一手都买不到的 session 记成真实的零。
    `spine verify` 抓不到这一类：它重建目标再与同一次运行写下的指纹比对，
    自洽但不校验语义。
    """
    import pyarrow.parquet as pq

    rows = pq.read_table(_RV).to_pylist()
    locked = [r for r in rows if r["no_trade_reason"] == "limit_locked"]
    assert len(locked) == 4
    hit = next(
        r for r in rows
        if (r["contract"], r["trading_day"], r["session_name"]) == ("sc2604", 20260303, "day")
    )
    assert hit["no_trade"] is True
    assert hit["no_trade_reason"] == "limit_locked"
    assert hit["value"] is None


@pytest.mark.skipif(not os.path.exists(_RET), reason="需要先运行 spine build")
def test_the_return_target_matches_its_measured_coverage():
    import pyarrow.parquet as pq

    rows = pq.read_table(_RET).to_pylist()
    reasons = {}
    for r in rows:
        if r["no_trade"]:
            reasons[r["no_trade_reason"]] = reasons.get(r["no_trade_reason"], 0) + 1
    assert len(rows) == 1816
    assert sum(1 for r in rows if not r["no_trade"]) == 1782
    assert reasons == {"no_ticks": 24, "entry_at_price_limit": 6, "exit_at_price_limit": 4}
    # 有取值就必须两个价都在，且取值确实是它们的对数比
    for r in rows:
        if not r["no_trade"]:
            assert r["entry_price"] > 0 and r["exit_price"] > 0
            assert abs(r["value"] - math.log(r["exit_price"] / r["entry_price"])) < 1e-12
            assert r["label_start"] == r["execution_time"]
