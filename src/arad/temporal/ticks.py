"""tick 归一化：自然日还原、时段归类、累计量差分。

三条不可妥协的规则：
1. 原始列一律保留，所有修正只以带 provenance 的派生列出现（Merge-Plan-2 §8.4）；
2. 累计量差分不跨交易日，倒退（郑商所口径的日内回退）只标记不修复；
3. 缺前一交易日时夜盘行进入 quarantine，不以自然日猜测归属。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc

from ..data_catalog.schema import QualityFinding, Severity
from .sessions import SHANGHAI, Placement, ProductReference

RAW_COLUMNS = (
    "TradingDay",
    "InstrumentID",
    "UpdateTime",
    "UpdateMillisec",
    "LastPrice",
    "Volume",
    "BidPrice1",
    "BidVolume1",
    "AskPrice1",
    "AskVolume1",
    "AveragePrice",
    "Turnover",
    "OpenInterest",
    "UpperLimitPrice",
    "LowerLimitPrice",
)

_US = 1_000_000


def _epoch_us(day: date, seconds: int = 0) -> int:
    dt = datetime.combine(day, datetime.min.time(), tzinfo=SHANGHAI) + timedelta(seconds=seconds)
    return int(dt.timestamp() * _US)


def _seconds_of_day(update_time: pa.Array) -> pa.Array:
    h = pc.cast(pc.utf8_slice_codeunits(update_time, 0, 2), pa.int32())
    m = pc.cast(pc.utf8_slice_codeunits(update_time, 3, 5), pa.int32())
    s = pc.cast(pc.utf8_slice_codeunits(update_time, 6, 8), pa.int32())
    return pc.add(pc.add(pc.multiply(h, 3600), pc.multiply(m, 60)), s)


def enrich(
    table: pa.Table,
    *,
    product: ProductReference,
    trading_day: date,
    prev_trading_day: date | None,
) -> tuple[pa.Table, list[QualityFinding]]:
    """把单个 (合约, 交易日) 的原始 tick 表归一化。

    返回 (归一化表, findings)。归一化表按自然时间升序，附带派生列：
    `sod`、`natural_ts`、`session_seq`/`session_name`/`segment_idx`/`placement`、
    `volume_delta`(可为负，保留原始差分)、`volume_delta_nonneg`、
    `turnover_delta`、`turnover_delta_nonneg`、`is_first_of_trading_day`、
    `quarantined`。
    """
    findings: list[QualityFinding] = []
    td_int = int(trading_day.strftime("%Y%m%d"))
    if table.num_rows:
        days = pc.unique(table.column("TradingDay")).to_pylist()
        if days != [td_int]:
            raise ValueError(
                f"tick 表的 TradingDay {days} 与声明的交易日 {td_int} 不一致；拒绝继续"
            )
    table = table.select(list(RAW_COLUMNS))
    if table.num_rows == 0:
        return _empty_enriched(table), findings

    sod = _seconds_of_day(table.column("UpdateTime").combine_chunks())
    windows = product.sessions.natural_date_windows()
    # 缺前一交易日时用自然前日仅作日内排序占位，相关行同时进入 quarantine
    anchor_prev = prev_trading_day or (trading_day - timedelta(days=1))

    base_us = pa.nulls(table.num_rows, pa.int64())
    needs_prev = pa.array([False] * table.num_rows, pa.bool_())
    for lo, hi, anchor, offset in windows:
        mask = pc.and_(pc.greater_equal(sod, lo), pc.less(sod, hi))
        anchor_day = trading_day if anchor == "trading_day" else anchor_prev
        value = pa.scalar(_epoch_us(anchor_day + timedelta(days=offset)), pa.int64())
        base_us = pc.if_else(mask, value, base_us)
        if anchor == "prev_trading_day":
            needs_prev = pc.or_(needs_prev, mask)

    natural_us = pc.add(
        base_us,
        pc.add(
            pc.multiply(pc.cast(sod, pa.int64()), _US),
            pc.multiply(pc.cast(table.column("UpdateMillisec"), pa.int64()), 1000),
        ),
    )
    natural_ts = pc.cast(natural_us, pa.timestamp("us", tz="Asia/Shanghai"))

    quarantined = (
        needs_prev if prev_trading_day is None else pa.array([False] * table.num_rows, pa.bool_())
    )
    if prev_trading_day is None and pc.any(needs_prev).as_py():
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="ticks.calendar_predecessor_missing",
                message=(
                    "该交易日没有前一交易日，夜盘行的自然日无法确定；相关行已隔离，"
                    "不进入 bar 与目标"
                ),
                evidence={
                    "trading_day": trading_day.isoformat(),
                    "quarantined_rows": int(pc.sum(pc.cast(needs_prev, pa.int32())).as_py() or 0),
                },
            )
        )

    seq, name, seg_idx, placement = _classify(sod, product)

    table = table.append_column("sod", sod)
    table = table.append_column("natural_ts", natural_ts)
    table = table.append_column("session_seq", seq)
    table = table.append_column("session_name", name)
    table = table.append_column("segment_idx", seg_idx)
    table = table.append_column("placement", placement)
    table = table.append_column("quarantined", quarantined)
    table = table.append_column(
        "row_order", pa.array(list(range(table.num_rows)), pa.int64())
    )

    order = pc.sort_indices(
        table, sort_keys=[("natural_ts", "ascending"), ("row_order", "ascending")]
    )
    table = table.take(order)

    table, delta_findings = _add_deltas(table, trading_day)
    findings.extend(delta_findings)

    n_outside = pc.sum(
        pc.cast(pc.equal(table.column("placement"), Placement.OUTSIDE.value), pa.int32())
    ).as_py()
    if n_outside:
        findings.append(
            QualityFinding(
                severity=Severity.INFO,
                code="ticks.out_of_session_rows",
                message="存在声明时段表之外的 tick（例如收盘后结算快照），已标记且不进入 bar",
                evidence={
                    "trading_day": trading_day.isoformat(),
                    "contract": table.column("InstrumentID")[0].as_py(),
                    "rows": int(n_outside),
                },
            )
        )

    meta = {
        b"arad.product": product.product.encode(),
        b"arad.trading_day": str(td_int).encode(),
        b"arad.prev_trading_day": (
            prev_trading_day.isoformat().encode() if prev_trading_day else b""
        ),
    }
    return table.replace_schema_metadata(meta), findings


def _classify(sod: pa.Array, product: ProductReference):
    n = len(sod)
    seq = pa.array([-1] * n, pa.int8())
    name = pa.array([""] * n, pa.string())
    seg = pa.array([-1] * n, pa.int8())
    placement = pa.array([Placement.OUTSIDE.value] * n, pa.string())
    for lo, hi, s_seq, s_name, s_idx, s_place in product.sessions.ranges():
        mask = pc.and_(pc.greater_equal(sod, lo), pc.less_equal(sod, hi))
        seq = pc.if_else(mask, pa.scalar(s_seq, pa.int8()), seq)
        name = pc.if_else(mask, pa.scalar(s_name, pa.string()), name)
        seg = pc.if_else(mask, pa.scalar(s_idx, pa.int8()), seg)
        placement = pc.if_else(mask, pa.scalar(s_place.value, pa.string()), placement)
    return seq, name, seg, placement


def _add_deltas(table: pa.Table, trading_day: date) -> tuple[pa.Table, list[QualityFinding]]:
    findings: list[QualityFinding] = []
    n = table.num_rows
    is_first = pa.array([i == 0 for i in range(n)], pa.bool_())
    table = table.append_column("is_first_of_trading_day", is_first)

    for raw, out in (("Volume", "volume_delta"), ("Turnover", "turnover_delta")):
        col = table.column(raw).combine_chunks()
        diff = pc.pairwise_diff(col, period=1)
        # 交易日起点从 0 累计：首行的 delta 就是首行的累计值
        delta = pc.if_else(is_first, col, diff)
        neg = pc.less(delta, pa.scalar(0, delta.type))
        nonneg = pc.if_else(neg, pa.scalar(0, delta.type), delta)
        table = table.append_column(out, delta)
        table = table.append_column(f"{out}_nonneg", nonneg)
        table = table.append_column(f"{out}_negative", neg)
        n_neg = pc.sum(pc.cast(neg, pa.int32())).as_py() or 0
        if n_neg:
            findings.append(
                QualityFinding(
                    severity=Severity.WARNING,
                    code="ticks.cumulative_rollback",
                    message=(
                        f"{raw} 为累计量却出现日内倒退；原值保留，派生列同时保留负差分"
                        "与置零版本，不做修复覆盖"
                    ),
                    evidence={
                        "trading_day": trading_day.isoformat(),
                        "contract": table.column("InstrumentID")[0].as_py(),
                        "field": raw,
                        "rows": int(n_neg),
                    },
                )
            )
    return table, findings


def _empty_enriched(table: pa.Table) -> pa.Table:
    extra = [
        ("sod", pa.int32()),
        ("natural_ts", pa.timestamp("us", tz="Asia/Shanghai")),
        ("session_seq", pa.int8()),
        ("session_name", pa.string()),
        ("segment_idx", pa.int8()),
        ("placement", pa.string()),
        ("quarantined", pa.bool_()),
        ("row_order", pa.int64()),
        ("is_first_of_trading_day", pa.bool_()),
        ("volume_delta", pa.int64()),
        ("volume_delta_nonneg", pa.int64()),
        ("volume_delta_negative", pa.bool_()),
        ("turnover_delta", pa.float64()),
        ("turnover_delta_nonneg", pa.float64()),
        ("turnover_delta_negative", pa.bool_()),
    ]
    for name, dtype in extra:
        table = table.append_column(name, pa.array([], dtype))
    return table
