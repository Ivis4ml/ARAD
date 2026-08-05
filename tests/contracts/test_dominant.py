"""t-1 信息主力合约选择的合同测试（M2 工作项 2）。

核心负向测试：主力规则只允许看前一交易日已知的成交量/持仓；
一旦把当日数据喂进选择器，必须立即报错而不是"顺手用一下"。
来源 `主力连续` 文件只作 QA 对照，不得成为依赖。
"""

from __future__ import annotations

from datetime import date

import pyarrow as pa
import pytest

from arad.temporal.dominant import (
    DominantRule,
    alias_agreement_finding,
    build_dominant_series,
    select_dominant,
)
from arad.temporal.errors import LookaheadError

RULE = DominantRule()


def panel(rows: list[tuple[str, str, int, float]]) -> pa.Table:
    """rows: (trading_day YYYYMMDD, contract, volume, open_interest)。"""
    return pa.table(
        {
            "trading_day": pa.array([int(r[0]) for r in rows], pa.int32()),
            "contract": pa.array([r[1] for r in rows], pa.string()),
            "volume": pa.array([r[2] for r in rows], pa.int64()),
            "open_interest": pa.array([r[3] for r in rows], pa.float64()),
        }
    )


# ---------------------------------------------------------------- 负向测试


def test_feeding_same_day_data_raises_lookahead():
    p = panel([("20260729", "sc2609", 100, 1.0), ("20260730", "sc2610", 999, 9.0)])
    with pytest.raises(LookaheadError):
        select_dominant(p, date(2026, 7, 30), rule=RULE)


def test_feeding_future_data_raises_lookahead():
    p = panel([("20260729", "sc2609", 100, 1.0), ("20260731", "sc2610", 999, 9.0)])
    with pytest.raises(LookaheadError):
        select_dominant(p, date(2026, 7, 30), rule=RULE)


def test_lookahead_error_names_the_offending_days():
    p = panel([("20260730", "sc2610", 999, 9.0)])
    with pytest.raises(LookaheadError) as exc:
        select_dominant(p, date(2026, 7, 30), rule=RULE)
    assert "20260730" in str(exc.value)


# ---------------------------------------------------------------- 选择规则


def test_selects_the_highest_volume_contract_of_the_previous_trading_day():
    p = panel(
        [
            ("20260728", "sc2609", 900, 5.0),
            ("20260729", "sc2609", 100, 5.0),
            ("20260729", "sc2610", 500, 3.0),
        ]
    )
    sel = select_dominant(p, date(2026, 7, 30), rule=RULE)
    assert sel.contract == "sc2610"
    assert sel.information_day == date(2026, 7, 29)
    assert sel.volume_tm1 == 500


def test_only_the_latest_available_day_is_used_as_information():
    p = panel([("20260720", "sc2608", 10_000, 9.0), ("20260729", "sc2610", 500, 3.0)])
    sel = select_dominant(p, date(2026, 7, 30), rule=RULE)
    assert sel.contract == "sc2610"
    assert sel.information_day == date(2026, 7, 29)


def test_ties_break_on_open_interest_then_contract_code():
    p = panel([("20260729", "sc2610", 500, 3.0), ("20260729", "sc2609", 500, 7.0)])
    sel = select_dominant(p, date(2026, 7, 30), rule=RULE)
    assert sel.contract == "sc2609"


def test_monotone_delivery_forbids_rolling_back_to_an_earlier_month():
    previous = select_dominant(
        panel([("20260728", "sc2610", 500, 3.0)]), date(2026, 7, 29), rule=RULE
    )
    p = panel([("20260729", "sc2609", 900, 9.0), ("20260729", "sc2610", 500, 3.0)])
    sel = select_dominant(p, date(2026, 7, 30), rule=RULE, previous=previous)
    assert sel.contract == "sc2610"
    assert "monotone" in sel.reason


def test_monotone_can_be_disabled_and_is_recorded_in_the_rule_version():
    rule = DominantRule(monotone_delivery=False)
    previous = select_dominant(
        panel([("20260728", "sc2610", 500, 3.0)]), date(2026, 7, 29), rule=rule
    )
    p = panel([("20260729", "sc2609", 900, 9.0), ("20260729", "sc2610", 500, 3.0)])
    sel = select_dominant(p, date(2026, 7, 30), rule=rule, previous=previous)
    assert sel.contract == "sc2609"
    assert rule.version != DominantRule().version


def test_empty_information_yields_no_selection_rather_than_a_guess():
    sel = select_dominant(panel([]), date(2026, 7, 30), rule=RULE)
    assert sel.contract is None
    assert sel.reason


# ---------------------------------------------------------------- 序列与换月


def _daily(rows):
    """rows: (trading_day, contract, volume, oi)。"""
    return panel(rows)


def test_build_series_marks_roll_days_and_missing_data_on_the_selected_day():
    daily = _daily(
        [
            ("20260727", "sc2609", 900, 9.0),
            ("20260727", "sc2610", 100, 1.0),
            ("20260728", "sc2609", 900, 9.0),
            ("20260728", "sc2610", 100, 1.0),
            ("20260729", "sc2610", 900, 9.0),
            ("20260729", "sc2609", 100, 1.0),
            # 20260730 当日 sc2610 无数据：不得静默换成别的合约
            ("20260730", "sc2611", 900, 9.0),
        ]
    )
    days = [date(2026, 7, 27), date(2026, 7, 28), date(2026, 7, 29), date(2026, 7, 30)]
    series, findings = build_dominant_series(daily, days, rule=RULE)
    by_day = {r["trading_day"]: r for r in series.to_pylist()}
    assert by_day[20260728]["contract"] == "sc2609"
    assert by_day[20260730]["contract"] == "sc2610"
    assert by_day[20260730]["has_data_on_day"] is False
    assert by_day[20260730]["is_roll"] is True
    assert by_day[20260729]["is_roll"] is False
    assert {f.code for f in findings} >= {"dominant.selected_contract_absent_on_day"}


def test_first_day_has_no_information_day_and_is_not_selected():
    daily = _daily([("20260727", "sc2609", 900, 9.0)])
    series, _ = build_dominant_series(daily, [date(2026, 7, 27)], rule=RULE)
    assert series.to_pylist()[0]["contract"] is None


# ---------------------------------------------------------------- 来源别名 QA


def test_alias_agreement_is_reported_but_never_used_as_a_dependency():
    series = pa.table(
        {
            "trading_day": pa.array([20260728, 20260729, 20260730], pa.int32()),
            "contract": pa.array(["sc2609", "sc2609", "sc2610"], pa.string()),
            "alias_contract": pa.array(["sc2609", "sc2610", "sc2610"], pa.string()),
        }
    )
    finding = alias_agreement_finding(series)
    assert finding.code == "dominant.alias_agreement"
    assert finding.evidence["agreement_rate"] == pytest.approx(2 / 3)
    assert finding.evidence["compared"] == 3
