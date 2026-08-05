"""M2 合同测试的合成 tick 构造器。

不依赖来源仓库；用最小的人造 tick 覆盖夜盘跨零点、集合竞价、午休、
盘后快照行、累计量差分与倒退等情形。
"""

from __future__ import annotations

from datetime import date

import pyarrow as pa

TICK_FIELDS = [
    ("TradingDay", pa.int32()),
    ("InstrumentID", pa.string()),
    ("UpdateTime", pa.string()),
    ("UpdateMillisec", pa.int16()),
    ("LastPrice", pa.float64()),
    ("Volume", pa.int64()),
    ("BidPrice1", pa.float64()),
    ("BidVolume1", pa.int32()),
    ("AskPrice1", pa.float64()),
    ("AskVolume1", pa.int32()),
    ("AveragePrice", pa.float64()),
    ("Turnover", pa.float64()),
    ("OpenInterest", pa.float64()),
    ("UpperLimitPrice", pa.float64()),
    ("LowerLimitPrice", pa.float64()),
]

TICK_SCHEMA = pa.schema(TICK_FIELDS)


def make_ticks(
    trading_day: date,
    contract: str,
    rows: list[tuple[str, int, float, int, float]],
    *,
    open_interest: float = 1000.0,
    upper_limit: float = 900.0,
    lower_limit: float = 100.0,
) -> pa.Table:
    """rows: (UpdateTime, UpdateMillisec, LastPrice, cumulative Volume, cumulative Turnover)。"""
    td = int(trading_day.strftime("%Y%m%d"))
    cols: dict[str, list] = {name: [] for name, _ in TICK_FIELDS}
    for t, ms, price, vol, turnover in rows:
        cols["TradingDay"].append(td)
        cols["InstrumentID"].append(contract)
        cols["UpdateTime"].append(t)
        cols["UpdateMillisec"].append(ms)
        cols["LastPrice"].append(price)
        cols["Volume"].append(vol)
        cols["BidPrice1"].append(price - 0.1)
        cols["BidVolume1"].append(1)
        cols["AskPrice1"].append(price + 0.1)
        cols["AskVolume1"].append(1)
        cols["AveragePrice"].append(turnover / vol if vol else 0.0)
        cols["Turnover"].append(turnover)
        cols["OpenInterest"].append(open_interest)
        cols["UpperLimitPrice"].append(upper_limit)
        cols["LowerLimitPrice"].append(lower_limit)
    return pa.table(cols, schema=TICK_SCHEMA)


def hhmmss(sod: int) -> str:
    sod %= 86400
    return f"{sod // 3600:02d}:{sod % 3600 // 60:02d}:{sod % 60:02d}"


def ticks_from_points(
    points: list[tuple[int, float, int]],
    *,
    multiplier: float = 1000.0,
    vol0: int = 0,
    turnover0: float = 0.0,
    millisec: int = 0,
) -> list[tuple[str, int, float, int, float]]:
    """points: (seconds_of_day, price, delta_volume) → 累计量形式的 tick 行。"""
    rows = []
    vol, turnover = vol0, turnover0
    for sod, price, dvol in points:
        vol += dvol
        turnover += dvol * price * multiplier
        rows.append((hhmmss(sod), millisec, price, vol, turnover))
    return rows


def ramp(
    start_sod: int,
    n: int,
    *,
    step: int = 60,
    price0: float = 500.0,
    dprice: float = 0.1,
    vol0: int = 0,
    dvol: int = 10,
    multiplier: float = 1000.0,
) -> list[tuple[str, int, float, int, float]]:
    """从 start_sod 起每 step 秒一行，价格线性变动，成交量线性累计。"""
    out = []
    vol = vol0
    turnover = float(vol0) * price0 * multiplier
    for i in range(n):
        sod = (start_sod + i * step) % 86400
        price = price0 + dprice * i
        vol += dvol
        turnover += dvol * price * multiplier
        out.append((f"{sod // 3600:02d}:{sod % 3600 // 60:02d}:{sod % 60:02d}", 0, price, vol, turnover))
    return out
