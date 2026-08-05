"""时间单位与夜盘归属的负向测试。

对应旧系统真实故障：微秒时间戳被按纳秒解析导致控制变量恒为零；
夜盘 21:00 的 tick 属于下一交易日却被当作当日日盘。
"""

from datetime import date, time

import pytest

from arad.data_catalog.timeguard import (
    AmbiguousTimeUnit,
    SessionAttributionError,
    natural_date_of_tick,
    require_epoch_seconds,
)


def test_epoch_seconds_accepts_plausible_values():
    assert require_epoch_seconds(1_753_000_000) == 1_753_000_000


@pytest.mark.parametrize(
    "value",
    [
        1_753_000_000_000,          # 毫秒
        1_753_000_000_000_000,      # 微秒
        1_753_000_000_000_000_000,  # 纳秒
    ],
)
def test_epoch_unit_confusion_fails_loudly(value):
    with pytest.raises(AmbiguousTimeUnit):
        require_epoch_seconds(value, field="block_timestamp")


def test_epoch_garbage_fails():
    with pytest.raises(AmbiguousTimeUnit):
        require_epoch_seconds(42)


def test_night_session_belongs_to_previous_natural_day():
    # TradingDay=2026-07-30 的 20:59 tick 实际发生在 2026-07-29 晚间
    nd = natural_date_of_tick(
        date(2026, 7, 30), time(20, 59), prev_trading_day=date(2026, 7, 29)
    )
    assert nd == date(2026, 7, 29)


def test_after_midnight_night_session_maps_to_next_natural_day_of_prev_trading_day():
    # 周一交易日的 00:30 tick（贵金属夜盘）发生在周六凌晨：周五的下一自然日
    nd = natural_date_of_tick(
        date(2026, 7, 27), time(0, 30), prev_trading_day=date(2026, 7, 24)
    )
    assert nd == date(2026, 7, 25)


def test_day_session_is_same_day():
    nd = natural_date_of_tick(
        date(2026, 7, 30), time(9, 30), prev_trading_day=date(2026, 7, 29)
    )
    assert nd == date(2026, 7, 30)


def test_unknown_session_window_refuses_to_guess():
    with pytest.raises(SessionAttributionError):
        natural_date_of_tick(
            date(2026, 7, 30), time(17, 30), prev_trading_day=date(2026, 7, 29)
        )
