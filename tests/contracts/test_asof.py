"""as-of join、Episode、purge/embargo 与样本段污染标签的合同测试
（M2 工作项 3 与 5）。

as-of join 是 PIT 硬边界：只返回 available_time 严格早于决策时点的观测，
并且沿用 M1 的字段合同（banned 字段无条件拒绝，provisional 字段默认拒绝）。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pyarrow as pa
import pytest

from arad.data_catalog.schema import (
    BannedFieldAccess,
    FieldAvailability,
    ProvisionalFieldAccess,
    SourceManifest,
    TimeSemantics,
)
from arad.temporal.asof import PitSeries, asof_last, asof_last_many
from arad.temporal.episode import (
    SampleSegment,
    classify_segment,
    episode_id,
    purge_embargo_mask,
)
from arad.temporal.errors import LookaheadError
from arad.temporal.sessions import SHANGHAI


def ts(h, m=0, *, day=30):
    return datetime(2026, 7, day, h, m, tzinfo=SHANGHAI)


def demo_manifest() -> SourceManifest:
    return SourceManifest(
        source_id="demo",
        root_uri="memory://demo",
        time_semantics=TimeSemantics(
            event_time="e", publication_time="p", availability_time="a",
            availability_rule="r", timezone="Asia/Shanghai",
        ),
        fields=[
            FieldAvailability(name="title", dtype="str", semantic="标题"),
            FieldAvailability(name="reads", dtype="int64", semantic="阅读数",
                              banned=True, banned_reason="抓取时刻快照，前视"),
            FieldAvailability(name="venue", dtype="str", semantic="场馆", provisional=True),
        ],
        partitions=[],
    )


def demo_series(**kw) -> PitSeries:
    table = pa.table(
        {
            "available_time": pa.array([ts(9), ts(10), ts(11)],
                                       pa.timestamp("us", tz="Asia/Shanghai")),
            "title": pa.array(["a", "b", "c"], pa.string()),
            "reads": pa.array([1, 2, 3], pa.int64()),
            "venue": pa.array(["x", "y", "z"], pa.string()),
        }
    )
    return PitSeries(name="demo", table=table, manifest=demo_manifest(), **kw)


# ---------------------------------------------------------------- as-of 严格性


def test_asof_returns_the_last_row_strictly_before_the_decision_time():
    got = asof_last(demo_series(), ts(10, 30), ["title"])
    assert got["title"] == "b"
    assert got["available_time"] == ts(10)


def test_a_row_exactly_at_the_decision_time_is_excluded():
    """并列时刻按不可用处理：歧义一律取保守方向。"""
    got = asof_last(demo_series(), ts(10), ["title"])
    assert got["title"] == "a"


def test_no_observation_before_the_decision_time_returns_none():
    assert asof_last(demo_series(), ts(8), ["title"]) is None


def test_asof_many_is_consistent_with_asof_last():
    series = demo_series()
    decisions = [ts(8), ts(9, 30), ts(12)]
    many = asof_last_many(series, decisions, ["title"])
    one = [asof_last(series, d, ["title"]) for d in decisions]
    assert many == one


def test_naive_decision_time_is_rejected():
    with pytest.raises(ValueError):
        asof_last(demo_series(), datetime(2026, 7, 30, 10, 30), ["title"])  # noqa: DTZ001


def test_unsorted_series_is_rejected():
    table = pa.table(
        {
            "available_time": pa.array([ts(11), ts(9)], pa.timestamp("us", tz="Asia/Shanghai")),
            "title": pa.array(["c", "a"], pa.string()),
        }
    )
    with pytest.raises(ValueError):
        PitSeries(name="bad", table=table)


def test_timezone_naive_series_is_rejected():
    table = pa.table(
        {
            "available_time": pa.array(
                [datetime(2026, 7, 30, 9)], pa.timestamp("us")  # noqa: DTZ001
            ),
            "title": pa.array(["a"], pa.string()),
        }
    )
    with pytest.raises(ValueError):
        PitSeries(name="naive", table=table)


# ---------------------------------------------------------------- 字段合同


def test_banned_field_cannot_be_joined():
    with pytest.raises(BannedFieldAccess):
        asof_last(demo_series(), ts(12), ["title", "reads"])


def test_provisional_field_is_blocked_without_an_audited_override():
    with pytest.raises(ProvisionalFieldAccess):
        asof_last(demo_series(), ts(12), ["venue"])


def test_provisional_field_passes_only_with_a_recorded_override():
    series = demo_series(allow_provisional={"venue"}, override_reason="M2 演示：口径待核实")
    got = asof_last(series, ts(12), ["venue"])
    assert got["venue"] == "z"


# ---------------------------------------------------------------- 前视守卫


def test_decision_time_must_precede_the_label_window():
    from arad.temporal.asof import assert_decision_precedes_label

    assert_decision_precedes_label(ts(20, 59), ts(21, 0))
    with pytest.raises(LookaheadError):
        assert_decision_precedes_label(ts(21, 0), ts(21, 0))
    with pytest.raises(LookaheadError):
        assert_decision_precedes_label(ts(21, 1), ts(21, 0))


# ---------------------------------------------------------------- Episode


def test_episode_groups_both_sessions_of_the_same_trading_day_by_default():
    a = episode_id("sc", date(2026, 7, 30), 0)
    b = episode_id("sc", date(2026, 7, 30), 1)
    c = episode_id("sc", date(2026, 7, 31), 0)
    assert a == b
    assert a != c


def test_session_grain_episode_separates_the_two_sessions():
    a = episode_id("sc", date(2026, 7, 30), 0, grain="session")
    b = episode_id("sc", date(2026, 7, 30), 1, grain="session")
    assert a != b


def test_unknown_episode_grain_is_rejected():
    with pytest.raises(ValueError):
        episode_id("sc", date(2026, 7, 30), 0, grain="whatever")


# ---------------------------------------------------------------- purge/embargo


def row(ep, dec, start, end):
    return {"episode_id": ep, "decision_time": dec, "label_start": start, "label_end": end}


def test_purge_drops_rows_whose_label_window_overlaps_a_test_row():
    test_rows = [row("e2", ts(20, 59), ts(21, 0), ts(2, 30, day=31))]
    candidates = [
        row("e1", ts(8, 59), ts(9, 0), ts(15, 0)),          # 不重叠，保留
        row("e3", ts(23, 0), ts(23, 30), ts(23, 45)),        # 重叠，purge
    ]
    mask = purge_embargo_mask(candidates, test_rows, embargo=timedelta(0))
    assert mask == [True, False]


def test_same_episode_is_always_purged():
    test_rows = [row("e1", ts(20, 59), ts(21, 0), ts(2, 30, day=31))]
    candidates = [row("e1", ts(8, 59), ts(9, 0), ts(15, 0))]
    assert purge_embargo_mask(candidates, test_rows, embargo=timedelta(0)) == [False]


def test_embargo_drops_rows_decided_shortly_after_the_test_label_ends():
    test_rows = [row("e1", ts(8, 59), ts(9, 0), ts(15, 0))]
    candidates = [
        row("e2", ts(16, 0), ts(16, 30), ts(17, 0)),   # embargo 内
        row("e3", ts(23, 0), ts(23, 30), ts(23, 45)),  # embargo 外
    ]
    mask = purge_embargo_mask(candidates, test_rows, embargo=timedelta(hours=4))
    assert mask == [False, True]


# ---------------------------------------------------------------- 污染标签


@pytest.mark.parametrize(
    ("end", "expect"),
    [
        (datetime(2022, 11, 2, 2, 30, tzinfo=SHANGHAI), SampleSegment.DISCOVERY),
        (datetime(2024, 12, 31, 15, 0, tzinfo=SHANGHAI), SampleSegment.DISCOVERY),
        (datetime(2025, 1, 2, 15, 0, tzinfo=SHANGHAI), SampleSegment.HISTORICAL_VALIDATION),
        (datetime(2025, 12, 31, 15, 0, tzinfo=SHANGHAI), SampleSegment.HISTORICAL_VALIDATION),
        (datetime(2026, 1, 5, 15, 0, tzinfo=SHANGHAI), SampleSegment.CONTAMINATED_AUDIT),
        (datetime(2026, 7, 30, 15, 0, tzinfo=SHANGHAI), SampleSegment.CONTAMINATED_AUDIT),
    ],
)
def test_historical_segments_follow_the_canonical_plan(end, expect):
    assert classify_segment(end - timedelta(hours=6), end) is expect


def test_label_spanning_the_new_year_is_tagged_by_its_outcome_end():
    """跨年样本按 label 结束时点归段：结果落在哪一段就属于哪一段。"""
    start = datetime(2024, 12, 31, 21, 0, tzinfo=SHANGHAI)
    end = datetime(2025, 1, 1, 2, 30, tzinfo=SHANGHAI)
    assert classify_segment(start, end) is SampleSegment.HISTORICAL_VALIDATION


def test_forward_requires_a_freeze_time_and_is_never_a_hardcoded_date():
    start = datetime(2026, 7, 30, 21, 0, tzinfo=SHANGHAI)
    end = datetime(2026, 7, 31, 2, 30, tzinfo=SHANGHAI)
    # 没有 freeze_at 就没有 forward
    assert classify_segment(start, end) is SampleSegment.CONTAMINATED_AUDIT
    freeze = datetime(2026, 7, 29, 0, 0, tzinfo=SHANGHAI)
    assert (
        classify_segment(start, end, freeze_at=freeze, embargo=timedelta(days=1))
        is SampleSegment.FORWARD_CONFIRMATION
    )
    # embargo 未过则仍不是 forward
    assert (
        classify_segment(start, end, freeze_at=freeze, embargo=timedelta(days=30))
        is SampleSegment.CONTAMINATED_AUDIT
    )
