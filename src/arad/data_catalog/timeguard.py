"""时间单位与时区的强制校验。

旧系统真实故障：微秒时间戳被按纳秒解析，导致新闻控制变量恒为零且无人察觉。
M1 合同：时间单位歧义必须立即失败，不允许自动猜测。
"""

from __future__ import annotations

from datetime import date, time

# epoch 秒的合理区间：2010-01-01 至 2040-01-01
_EPOCH_S_MIN = 1_262_304_000
_EPOCH_S_MAX = 2_208_988_800


class AmbiguousTimeUnit(ValueError):
    """时间戳数值与声明单位不符（疑似毫秒/微秒/纳秒混入秒级字段）。"""


def require_epoch_seconds(value: float, field: str = "") -> int:
    """断言数值是 epoch 秒。毫秒、微秒、纳秒量级一律抛 AmbiguousTimeUnit。"""
    v = float(value)
    if _EPOCH_S_MIN <= v <= _EPOCH_S_MAX:
        return int(v)
    for unit, factor in (("milliseconds", 1e3), ("microseconds", 1e6), ("nanoseconds", 1e9)):
        if _EPOCH_S_MIN <= v / factor <= _EPOCH_S_MAX:
            raise AmbiguousTimeUnit(
                f"{field or 'timestamp'}={value!r} looks like epoch {unit}, "
                "declared unit is seconds; refusing to guess"
            )
    raise AmbiguousTimeUnit(
        f"{field or 'timestamp'}={value!r} is outside plausible epoch-second range"
    )


class SessionAttributionError(ValueError):
    """交易日归属规则被违反或输入不足以归属。"""


# 缺省归属窗口：(起始秒, 结束秒（不含）, 锚点, 相对锚点的自然日偏移)
# 仅覆盖通用日盘与夜盘时段；品种级时段表通过 windows 参数传入更精确的定义。
DEFAULT_NATURAL_DATE_WINDOWS: tuple[tuple[int, int, str, int], ...] = (
    (8 * 3600, 16 * 3600, "trading_day", 0),
    (20 * 3600, 24 * 3600, "prev_trading_day", 0),
    (0, 3 * 3600, "prev_trading_day", 1),
)


def natural_date_of_tick(
    trading_day: date,
    tick_time: time,
    *,
    prev_trading_day: date,
    windows: tuple[tuple[int, int, str, int], ...] | None = None,
) -> date:
    """把 (TradingDay, UpdateTime) 归属到自然日。

    中国商品期货规则：夜盘（20:00 之后开始）归属下一交易日。因此
    TradingDay=T 的 tick 中，20:00 至 24:00 的时刻发生在 T 的前一交易日晚间，
    00:00 至 03:00 的时刻发生在前一交易日的次自然日凌晨（即 T 的前一自然日，
    当 T 前一交易日为周五时为周六凌晨）。日盘时刻（08:00 至 16:00）发生在 T 当日。

    prev_trading_day 必须由调用方从交易日历提供；本函数拒绝自行猜测。

    windows 允许品种级时段表覆盖缺省窗口（M2 扩展）：每项为
    `(起始秒, 结束秒（不含）, 锚点, 自然日偏移)`，锚点取 `trading_day`
    或 `prev_trading_day`。未落入任何窗口的时刻仍然报错，不做猜测。
    """
    from datetime import timedelta

    sod = tick_time.hour * 3600 + tick_time.minute * 60 + tick_time.second
    for lo, hi, anchor, offset in windows or DEFAULT_NATURAL_DATE_WINDOWS:
        if lo <= sod < hi:
            base = trading_day if anchor == "trading_day" else prev_trading_day
            return base + timedelta(days=offset)
    raise SessionAttributionError(
        f"tick time {tick_time} outside known session windows for trading day {trading_day}"
    )
