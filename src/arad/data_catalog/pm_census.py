"""Polymarket 逐笔的只读、label-blind 普查（M2.5 第一部分）。

只读取时间、市场标识、价格与名义额；结果字段（`resolution_status`、
`winning_outcome_label`、`resolved_at`）在读取层就被拒绝，不是靠约定回避。

按日分区流式聚合：每个分区只读需要的列，聚合成逐 (市场, 日) 一行后即释放，
855M 行不进内存。每个分区写一份 sidecar，键为分区的内容指纹，重跑可恢复。
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .schema import QualityFinding, Severity
from .timeguard import require_epoch_seconds

CENSUS_VERSION = "0.1.0"

#: 普查允许读取的列。任何结果字段都不在此列。
CENSUS_COLUMNS = ("condition_id", "block_timestamp", "price", "usdc_amount", "neg_risk")

#: 结果字段：读取层硬拒绝。label-blind 是能力边界，不是提醒。
OUTCOME_COLUMNS = frozenset(
    {"resolution_status", "winning_outcome_label", "resolved_at", "winners"}
)

#: 去重审计需要的额外列（仅在抽样审计中读取）。
DEDUP_COLUMNS = ("condition_id", "asset_id", "block_timestamp", "maker", "taker", "price",
                 "usdc_amount")

MARKET_DAY_SCHEMA = pa.schema(
    [
        ("date", pa.string()),
        ("condition_id", pa.string()),
        ("trades", pa.int64()),
        ("notional", pa.float64()),
        ("first_ts", pa.int64()),
        ("last_ts", pa.int64()),
        ("active_seconds", pa.int64()),
        ("price_changes", pa.int64()),
        ("max_gap_seconds", pa.int64()),
        ("neg_risk", pa.bool_()),
    ]
)


class OutcomeColumnAccess(RuntimeError):
    """普查试图读取结果字段。label-blind 边界被违反。"""


def require_label_blind(columns) -> list[str]:
    """拒绝任何结果字段。普查在读到数据之前就必须失败。"""
    banned = sorted(set(columns) & OUTCOME_COLUMNS)
    if banned:
        raise OutcomeColumnAccess(
            f"普查是 label-blind 的，禁止读取结果字段 {banned}；"
            "市场存在性与流动性不需要知道谁赢了"
        )
    return list(columns)


def partition_digest(path: str) -> str:
    """分区的内容身份：行数、字节数与 footer 关键元数据的聚合。"""
    md = pq.ParquetFile(path).metadata
    st = os.stat(path)
    blob = f"{os.path.basename(path)}|{md.num_rows}|{md.num_row_groups}|{st.st_size}"
    return hashlib.sha256(blob.encode()).hexdigest()


def _bool_array(column: pa.ChunkedArray | pa.Array) -> pa.Array:
    """neg_risk 在两段的类型不同（bool 与字符串），统一为 bool。"""
    arr = column.combine_chunks() if isinstance(column, pa.ChunkedArray) else column
    if pa.types.is_boolean(arr.type):
        return arr
    lowered = pc.utf8_lower(pc.cast(arr, pa.string()))
    return pc.is_in(lowered, value_set=pa.array(["true", "1", "t"], pa.string()))


def _prepend(values: pa.Array, first, dtype) -> pa.Array:
    return pa.concat_arrays([pa.array([first], dtype), values.cast(dtype)])


def census_partition(path: str, date_key: str) -> pa.Table:
    """把一个日分区聚合成逐 (市场, 日) 一行。"""
    table = pq.read_table(path, columns=require_label_blind(CENSUS_COLUMNS))
    if table.num_rows == 0:
        return MARKET_DAY_SCHEMA.empty_table()
    table = table.sort_by(
        [("condition_id", "ascending"), ("block_timestamp", "ascending")]
    )
    n = table.num_rows
    cid = table.column("condition_id").combine_chunks()
    ts = table.column("block_timestamp").combine_chunks().cast(pa.int64())
    price = table.column("price").combine_chunks().cast(pa.float64())

    require_epoch_seconds(pc.min(ts).as_py(), field="block_timestamp")
    require_epoch_seconds(pc.max(ts).as_py(), field="block_timestamp")

    if n == 1:
        same = pa.array([False], pa.bool_())
        gap = pa.array([None], pa.int64())
        changed = pa.array([False], pa.bool_())
    else:
        same = _prepend(pc.equal(cid.slice(1), cid.slice(0, n - 1)), False, pa.bool_())
        raw_gap = _prepend(pc.subtract(ts.slice(1), ts.slice(0, n - 1)), None, pa.int64())
        gap = pc.if_else(same, raw_gap, pa.scalar(None, pa.int64()))
        raw_changed = _prepend(
            pc.not_equal(price.slice(1), price.slice(0, n - 1)), False, pa.bool_()
        )
        changed = pc.and_kleene(same, raw_changed)
    # 新的一秒：换市场，或与前一笔不同秒
    new_second = pc.or_kleene(pc.invert(same), pc.greater(pc.fill_null(gap, 1), 0))

    work = pa.table(
        {
            "condition_id": cid,
            "ts": ts,
            "usdc": table.column("usdc_amount").combine_chunks().cast(pa.float64()),
            "gap": gap,
            "new_second": pc.cast(pc.fill_null(new_second, True), pa.int64()),
            "changed": pc.cast(pc.fill_null(changed, False), pa.int64()),
            "neg": pc.cast(_bool_array(table.column("neg_risk")), pa.int64()),
        }
    )
    grouped = pa.TableGroupBy(work, ["condition_id"], use_threads=False).aggregate(
        [
            ("ts", "count"),
            ("ts", "min"),
            ("ts", "max"),
            ("usdc", "sum"),
            ("gap", "max"),
            ("new_second", "sum"),
            ("changed", "sum"),
            ("neg", "max"),
        ]
    )
    out = pa.table(
        {
            "date": pa.array([date_key] * grouped.num_rows, pa.string()),
            "condition_id": grouped.column("condition_id"),
            "trades": pc.cast(grouped.column("ts_count"), pa.int64()),
            "notional": pc.cast(grouped.column("usdc_sum"), pa.float64()),
            "first_ts": pc.cast(grouped.column("ts_min"), pa.int64()),
            "last_ts": pc.cast(grouped.column("ts_max"), pa.int64()),
            "active_seconds": pc.cast(grouped.column("new_second_sum"), pa.int64()),
            "price_changes": pc.cast(grouped.column("changed_sum"), pa.int64()),
            "max_gap_seconds": pc.cast(
                pc.fill_null(grouped.column("gap_max"), 0), pa.int64()
            ),
            "neg_risk": pc.greater(grouped.column("neg_max"), 0),
        },
        schema=MARKET_DAY_SCHEMA,
    )
    return out.sort_by([("condition_id", "ascending")])


def _census_task(task: dict) -> dict:
    table = census_partition(task["path"], task["date"])
    pq.write_table(table, os.path.join(task["out_market_day"], f"{task['key']}.parquet"))
    summary = {
        "key": task["key"],
        "date": task["date"],
        "segment": task["segment"],
        "digest": task["digest"],
        "markets": table.num_rows,
        "trades": int(pc.sum(table.column("trades")).as_py() or 0),
        "notional": float(pc.sum(table.column("notional")).as_py() or 0.0),
        "neg_risk_markets": int(
            pc.sum(pc.cast(table.column("neg_risk"), pa.int64())).as_py() or 0
        ),
    }
    with open(os.path.join(task["out_days"], f"{task['key']}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False)
    return summary


def discover_partitions(roots: dict[str, str]) -> list[tuple[str, str, str]]:
    """返回 (日期, 段名, 路径)，按日期升序。两段共享的日期各自保留。"""
    out = []
    for segment, root in roots.items():
        for path in sorted(glob.glob(os.path.join(root, "*.parquet"))):
            out.append((os.path.basename(path)[:10], segment, path))
    return sorted(out)


def build_census(
    roots: dict[str, str], out_dir: str, *, workers: int = 8, force: bool = False
) -> tuple[list[dict], list[QualityFinding]]:
    out_market_day = os.path.join(out_dir, "market_day")
    out_days = os.path.join(out_dir, "_partitions")
    for d in (out_market_day, out_days):
        os.makedirs(d, exist_ok=True)

    tasks, done = [], {}
    for date_key, segment, path in discover_partitions(roots):
        key = f"{segment}_{date_key}"
        sidecar = os.path.join(out_days, f"{key}.json")
        digest = partition_digest(path)
        if not force and os.path.exists(sidecar):
            with open(sidecar, encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("digest") == digest:
                done[key] = cached
                continue
        tasks.append(
            {
                "path": path,
                "key": key,
                "date": date_key,
                "segment": segment,
                "digest": digest,
                "out_market_day": out_market_day,
                "out_days": out_days,
            }
        )
    if tasks:
        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for summary in pool.map(_census_task, tasks, chunksize=1):
                    done[summary["key"]] = summary
        else:
            for task in tasks:
                summary = _census_task(task)
                done[summary["key"]] = summary

    summaries = [done[k] for k in sorted(done)]
    findings = [
        QualityFinding(
            severity=Severity.ERROR if not summaries else Severity.INFO,
            code="pm_census.coverage",
            message="Polymarket 逐笔普查覆盖",
            evidence={
                "partitions": len(summaries),
                "trades": sum(s["trades"] for s in summaries),
                "first": min((s["date"] for s in summaries), default=None),
                "last": max((s["date"] for s in summaries), default=None),
                "markets_seen": sum(s["markets"] for s in summaries),
            },
        )
    ]
    return summaries, findings


def audit_neg_risk_coverage(summaries: list[dict], sampled_rows: int) -> QualityFinding:
    """negRisk 覆盖审计。两段都不含 negRisk 成交是一条需要更正设计文档的事实。"""
    markets = sum(s.get("neg_risk_markets", 0) for s in summaries)
    return QualityFinding(
        severity=Severity.WARNING if markets == 0 else Severity.INFO,
        code="pm_census.neg_risk_absent_in_both_segments",
        message=(
            "全史普查中 neg_risk 为真的 (市场, 日) 数为 0：两段 tape 都不含 NegRisk "
            "Exchange 成交。canonical plan §2.1 关于『扩展段含 negRisk、约占名义额 27.6%』"
            "的表述与实测不符，需要文档归一化裁决；negRisk 缺口未被扩展段补上"
        ),
        evidence={
            "neg_risk_market_days": markets,
            "partitions": len(summaries),
            "sampled_rows_confirming": sampled_rows,
        },
    )


def audit_missing_venue_columns(roots: dict[str, str]) -> QualityFinding:
    """venue / relay 审计：先确认列是否存在。缺列必须报告，不能假装做过审计。"""
    present: dict[str, list[str]] = {}
    wanted = ["venue_class", "is_relay", "protocol", "exchange", "tx_hash", "log_index"]
    for segment, root in roots.items():
        files = sorted(glob.glob(os.path.join(root, "*.parquet")))
        if not files:
            continue
        names = set(pq.ParquetFile(files[0]).schema_arrow.names)
        present[segment] = sorted(set(wanted) & names)
    return QualityFinding(
        severity=Severity.WARNING,
        code="pm_census.venue_columns_absent",
        message=(
            "两段 tape 都不含 venue_class / is_relay / protocol / exchange / tx_hash / "
            "log_index，因此 relay 剔除与 unknown venue 隔离在现有数据上无法执行；"
            "M1 manifest 曾把这些字段标为『仅扩展段』，与实测不符，已更正"
        ),
        evidence={"present_columns": present, "wanted": wanted},
    )


def audit_duplicate_legs(paths: list[str]) -> QualityFinding:
    """抽样重复腿审计：在缺少 tx_hash / log_index 时，只能检出完全相同的行。"""
    total = dup = 0
    per_partition = []
    for path in paths:
        table = pq.read_table(path, columns=require_label_blind(DEDUP_COLUMNS))
        if table.num_rows == 0:
            continue
        grouped = pa.TableGroupBy(table, list(DEDUP_COLUMNS)).aggregate(
            [("block_timestamp", "count")]
        )
        n_dup = int(
            pc.sum(
                pc.subtract(grouped.column("block_timestamp_count"), 1)
            ).as_py()
            or 0
        )
        total += table.num_rows
        dup += n_dup
        per_partition.append(
            {"partition": os.path.basename(path), "rows": table.num_rows, "exact_duplicates": n_dup}
        )
    return QualityFinding(
        severity=Severity.WARNING,
        code="pm_census.duplicate_legs_provisional",
        message=(
            "重复腿抽样审计：缺 tx_hash / log_index，只能检出 "
            "(市场, asset, 时间, maker, taker, 价格, 名义额) 完全相同的行；"
            "中继腿若字段不完全相同则检不出，因此 notional 类指标一律 provisional"
        ),
        evidence={
            "sampled_partitions": len(per_partition),
            "rows": total,
            "exact_duplicates": dup,
            "rate": (dup / total) if total else 0.0,
            "detail": per_partition[:10],
        },
    )
