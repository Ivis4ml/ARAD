"""1 分钟与日频 bar 的物化。

bar 的 `available_time` 取 bar 的右端点（闭区间右端的成交发生在该分钟内，
整根 bar 在右端点才完整）。session 内部休息与时段表之外的行不进入 bar，
但在日频 bar 里保留计数，使异常可被审计而不是消失。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc

from .sessions import SHANGHAI, Placement, ProductReference, SessionWindow

_US = 1_000_000
_MINUTE_US = 60 * _US

BARS_1MIN_SCHEMA = pa.schema(
    [
        ("product", pa.string()),
        ("contract", pa.string()),
        ("trading_day", pa.int32()),
        ("session_seq", pa.int8()),
        ("session_name", pa.string()),
        ("segment_idx", pa.int8()),
        ("placement", pa.string()),
        ("bar_start", pa.timestamp("us", tz="Asia/Shanghai")),
        ("bar_end", pa.timestamp("us", tz="Asia/Shanghai")),
        ("available_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.int64()),
        ("turnover", pa.float64()),
        ("open_interest", pa.float64()),
        ("upper_limit", pa.float64()),
        ("lower_limit", pa.float64()),
        ("ticks", pa.int64()),
        ("n_negative_delta", pa.int64()),
    ]
)

BARS_DAILY_SCHEMA = pa.schema(
    [
        ("product", pa.string()),
        ("contract", pa.string()),
        ("trading_day", pa.int32()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.int64()),
        ("turnover", pa.float64()),
        ("open_interest_open", pa.float64()),
        ("open_interest_close", pa.float64()),
        ("upper_limit", pa.float64()),
        ("lower_limit", pa.float64()),
        ("first_tick_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("last_tick_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("available_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("night_present", pa.bool_()),
        ("day_present", pa.bool_()),
        ("night_first_sod", pa.int32()),
        ("night_last_sod", pa.int32()),
        ("day_first_sod", pa.int32()),
        ("day_last_sod", pa.int32()),
        ("n_ticks", pa.int64()),
        ("n_in_session", pa.int64()),
        ("n_out_of_session", pa.int64()),
        ("n_break", pa.int64()),
        ("n_quarantined", pa.int64()),
        ("n_negative_volume_delta", pa.int64()),
        ("n_negative_turnover_delta", pa.int64()),
    ]
)


def _meta(table: pa.Table) -> tuple[date, date | None]:
    meta = table.schema.metadata or {}
    td = meta.get(b"arad.trading_day", b"").decode()
    prev = meta.get(b"arad.prev_trading_day", b"").decode()
    if not td:
        raise ValueError("tick 表缺少 arad.trading_day 元数据；必须由 enrich 产生")
    trading_day = date(int(td[:4]), int(td[4:6]), int(td[6:]))
    prev_day = date.fromisoformat(prev) if prev else None
    return trading_day, prev_day


def _windows(table: pa.Table, product: ProductReference) -> tuple[SessionWindow, ...]:
    trading_day, prev_day = _meta(table)
    return product.sessions.windows(trading_day, prev_trading_day=prev_day)


def _usable(table: pa.Table) -> pa.Table:
    return table.filter(pc.invert(table.column("quarantined")))


def bars_1min(table: pa.Table, *, product: ProductReference) -> pa.Table:
    """把归一化 tick 聚合为 1 分钟 bar。

    段内最后一分钟包含该段收盘打印（例如 10:15:00 的打印归入 10:14 那根 bar），
    因此不会产生只含一条收盘 tick 的额外 bar。集合竞价单独成一根 bar 并标记，
    不与连续竞价混同。
    """
    windows = _windows(table, product)
    usable = _usable(table)
    keep = pc.is_in(
        usable.column("placement"),
        value_set=pa.array([Placement.SEGMENT.value, Placement.AUCTION.value]),
    )
    usable = usable.filter(keep)
    if usable.num_rows == 0:
        return BARS_1MIN_SCHEMA.empty_table()

    ts_us = pc.cast(usable.column("natural_ts").combine_chunks(), pa.int64())
    bar_start_us = pa.nulls(usable.num_rows, pa.int64())
    seq_col = usable.column("session_seq")
    seg_col = usable.column("segment_idx")
    place_col = usable.column("placement")

    for w in windows:
        in_session = pc.equal(seq_col, w.seq)
        for idx, (seg_start, seg_end) in enumerate(w.segments):
            mask = pc.and_(
                pc.and_(in_session, pc.equal(seg_col, idx)),
                pc.equal(place_col, Placement.SEGMENT.value),
            )
            s_us = int(seg_start.timestamp() * _US)
            e_us = int(seg_end.timestamp() * _US)
            n_bars = max(1, (e_us - s_us) // _MINUTE_US)
            k = pc.min_element_wise(
                pc.divide(pc.subtract(ts_us, s_us), _MINUTE_US), n_bars - 1
            )
            bar_start_us = pc.if_else(
                mask, pc.add(s_us, pc.multiply(k, _MINUTE_US)), bar_start_us
            )
        auction_mask = pc.and_(in_session, pc.equal(place_col, Placement.AUCTION.value))
        floored = pc.multiply(pc.divide(ts_us, _MINUTE_US), _MINUTE_US)
        bar_start_us = pc.if_else(auction_mask, floored, bar_start_us)

    usable = usable.append_column("bar_start_us", bar_start_us)
    usable = usable.append_column(
        "neg_flag", pc.cast(usable.column("volume_delta_negative"), pa.int32())
    )

    keys = [
        "InstrumentID",
        "TradingDay",
        "session_seq",
        "session_name",
        "segment_idx",
        "placement",
        "bar_start_us",
    ]
    grouped = pa.TableGroupBy(usable, keys, use_threads=False).aggregate(
        [
            ("LastPrice", "first"),
            ("LastPrice", "last"),
            ("LastPrice", "max"),
            ("LastPrice", "min"),
            ("volume_delta_nonneg", "sum"),
            ("turnover_delta_nonneg", "sum"),
            ("OpenInterest", "last"),
            ("UpperLimitPrice", "last"),
            ("LowerLimitPrice", "last"),
            ("neg_flag", "sum"),
            ("row_order", "count"),
        ]
    )
    grouped = grouped.sort_by([("bar_start_us", "ascending")])

    start = pc.cast(grouped.column("bar_start_us"), pa.timestamp("us", tz="Asia/Shanghai"))
    end = pc.cast(
        pc.add(grouped.column("bar_start_us"), _MINUTE_US),
        pa.timestamp("us", tz="Asia/Shanghai"),
    )
    out = pa.table(
        {
            "product": pa.array([product.product] * grouped.num_rows, pa.string()),
            "contract": grouped.column("InstrumentID"),
            "trading_day": pc.cast(grouped.column("TradingDay"), pa.int32()),
            "session_seq": grouped.column("session_seq"),
            "session_name": grouped.column("session_name"),
            "segment_idx": grouped.column("segment_idx"),
            "placement": grouped.column("placement"),
            "bar_start": start,
            "bar_end": end,
            "available_time": end,
            "open": grouped.column("LastPrice_first"),
            "high": grouped.column("LastPrice_max"),
            "low": grouped.column("LastPrice_min"),
            "close": grouped.column("LastPrice_last"),
            "volume": pc.cast(grouped.column("volume_delta_nonneg_sum"), pa.int64()),
            "turnover": pc.cast(grouped.column("turnover_delta_nonneg_sum"), pa.float64()),
            "open_interest": grouped.column("OpenInterest_last"),
            "upper_limit": grouped.column("UpperLimitPrice_last"),
            "lower_limit": grouped.column("LowerLimitPrice_last"),
            "ticks": pc.cast(grouped.column("row_order_count"), pa.int64()),
            "n_negative_delta": pc.cast(grouped.column("neg_flag_sum"), pa.int64()),
        },
        schema=BARS_1MIN_SCHEMA,
    )
    return out


def _sum_int(table: pa.Table, mask) -> int:
    return int(pc.sum(pc.cast(mask, pa.int32())).as_py() or 0)


def bars_daily(table: pa.Table, *, product: ProductReference) -> pa.Table:
    """把归一化 tick 聚合为日频 bar（每个合约每个交易日一行）。

    `volume`/`turnover` 取交易日内累计量的最大值（交易所口径的当日总量，
    对日内倒退稳健）；OHLC 只用时段表内的行，因此收盘后的结算快照不会成为收盘价。
    `available_time` 不早于日盘收盘，也不早于最后一条 tick。
    """
    trading_day, _ = _meta(table)
    windows = _windows(table, product)
    day_close = next(
        (w.close for w in windows if w.name == "day"),
        datetime.combine(trading_day, datetime.min.time(), tzinfo=SHANGHAI)
        + timedelta(hours=15),
    )
    usable = _usable(table)
    if usable.num_rows == 0:
        return BARS_DAILY_SCHEMA.empty_table()

    place = usable.column("placement")
    in_session_mask = pc.is_in(
        place, value_set=pa.array([Placement.SEGMENT.value, Placement.AUCTION.value])
    )
    in_session = usable.filter(in_session_mask)

    contracts = pc.unique(usable.column("InstrumentID")).to_pylist()
    rows = []
    for contract in sorted(contracts):
        sub = usable.filter(pc.equal(usable.column("InstrumentID"), contract))
        sub_in = in_session.filter(pc.equal(in_session.column("InstrumentID"), contract))
        row = {
            "product": product.product,
            "contract": contract,
            "trading_day": int(trading_day.strftime("%Y%m%d")),
            "volume": int(pc.max(sub.column("Volume")).as_py() or 0),
            "turnover": float(pc.max(sub.column("Turnover")).as_py() or 0.0),
            "open_interest_open": sub.column("OpenInterest")[0].as_py(),
            "open_interest_close": sub.column("OpenInterest")[-1].as_py(),
            "upper_limit": sub.column("UpperLimitPrice")[-1].as_py(),
            "lower_limit": sub.column("LowerLimitPrice")[-1].as_py(),
            "first_tick_time": sub.column("natural_ts")[0].as_py(),
            "last_tick_time": sub.column("natural_ts")[-1].as_py(),
            "n_ticks": sub.num_rows,
            "n_in_session": sub_in.num_rows,
            "n_out_of_session": _sum_int(
                sub, pc.equal(sub.column("placement"), Placement.OUTSIDE.value)
            ),
            "n_break": _sum_int(sub, pc.equal(sub.column("placement"), Placement.BREAK.value)),
            "n_quarantined": _sum_int(
                table.filter(pc.equal(table.column("InstrumentID"), contract)),
                table.filter(pc.equal(table.column("InstrumentID"), contract)).column(
                    "quarantined"
                ),
            ),
            "n_negative_volume_delta": _sum_int(sub, sub.column("volume_delta_negative")),
            "n_negative_turnover_delta": _sum_int(sub, sub.column("turnover_delta_negative")),
        }
        if sub_in.num_rows:
            row.update(
                {
                    "open": sub_in.column("LastPrice")[0].as_py(),
                    "high": pc.max(sub_in.column("LastPrice")).as_py(),
                    "low": pc.min(sub_in.column("LastPrice")).as_py(),
                    "close": sub_in.column("LastPrice")[-1].as_py(),
                }
            )
            last_in = sub_in.column("natural_ts")[-1].as_py()
        else:
            row.update({"open": None, "high": None, "low": None, "close": None})
            last_in = None
        row["available_time"] = max(day_close, last_in) if last_in else day_close
        for name, seq in (("night", 0), ("day", 1)):
            part = sub_in.filter(pc.equal(sub_in.column("session_seq"), seq))
            row[f"{name}_present"] = part.num_rows > 0
            row[f"{name}_first_sod"] = part.column("sod")[0].as_py() if part.num_rows else None
            row[f"{name}_last_sod"] = part.column("sod")[-1].as_py() if part.num_rows else None
        rows.append(row)
    return pa.Table.from_pylist(rows, schema=BARS_DAILY_SCHEMA)
