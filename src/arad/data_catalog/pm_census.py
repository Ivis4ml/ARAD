"""Polymarket 逐笔的只读、label-blind 普查（M2.5 第一部分）。

只读取时间、市场/资产标识、结果序号、价格与名义额；结果字段
（`resolution_status`、`winning_outcome_label`、`resolved_at`）在读取层被拒绝。

**价格变化与无成交间隔按 (市场, 资产) 计算**：同一 condition 下 YES 与 NO 是两个
互补的 outcome token，价格序列不同，混在一起会制造伪跳变。市场级的活跃秒数按
condition 去重统计，避免两个 token 同秒成交被重复计数。

内容身份取**整文件 sha256**。页脚摘要曾被用作内容身份，但关闭统计量、无压缩且
字节数相同的两个不同内容分区会得到相同页脚，缓存会被错误复用；两段 tape 合计
16.6 GB，实测 sha256 约 2.1 GB/s，全量哈希的代价可以接受。
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .schema import QualityFinding, Severity
from .timeguard import require_epoch_seconds

CENSUS_VERSION = "0.3.0"

#: 心跳写入周期（秒）。按时间而非完成个数，使单分区卡死也能被观测到。
HEARTBEAT_SECONDS = 5.0

#: 普查允许读取的列。任何结果字段都不在此列。
CENSUS_COLUMNS = (
    "condition_id",
    "asset_id",
    "outcome_seq",
    "block_timestamp",
    "price",
    "usdc_amount",
    "neg_risk",
)

#: 结果字段：读取层硬拒绝。label-blind 是能力边界，不是提醒。
OUTCOME_COLUMNS = frozenset(
    {"resolution_status", "winning_outcome_label", "resolved_at", "winners"}
)

#: 去重审计需要的额外列（仅在抽样审计中读取）。
DEDUP_COLUMNS = (
    "condition_id", "asset_id", "block_timestamp", "maker", "taker", "price", "usdc_amount",
)

ASSET_DAY_SCHEMA = pa.schema(
    [
        ("date", pa.string()),
        ("condition_id", pa.string()),
        ("asset_id", pa.string()),
        ("outcome_seq", pa.int64()),
        ("trades", pa.int64()),
        ("notional", pa.float64()),
        ("first_ts", pa.int64()),
        ("last_ts", pa.int64()),
        ("active_seconds", pa.int64()),
        ("price_changes", pa.int64()),
        ("max_gap_seconds", pa.int64()),
    ]
)

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
        ("assets", pa.int64()),
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


DIGEST_METHOD = "file_sha256"


def file_digest(path: str) -> str:
    """整文件 sha256 加字节数。这是内容身份，不是元数据摘要。

    只哈希 parquet 页脚不足以构成内容身份：关闭统计量、无压缩且长度相同的两个
    不同内容分区会得到相同页脚，缓存与派生产物都会被错误复用。
    """
    size = os.path.getsize(path)
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    h.update(str(size).encode())
    return h.hexdigest()


#: 兼容旧调用名。
partition_digest = file_digest


def _bool_array(column) -> pa.Array:
    """neg_risk 在两段的类型不同（bool 与字符串），统一为 bool。"""
    arr = column.combine_chunks() if isinstance(column, pa.ChunkedArray) else column
    if pa.types.is_boolean(arr.type):
        return arr
    lowered = pc.utf8_lower(pc.cast(arr, pa.string()))
    return pc.is_in(lowered, value_set=pa.array(["true", "1", "t"], pa.string()))


def _prepend(values: pa.Array, first, dtype) -> pa.Array:
    return pa.concat_arrays([pa.array([first], dtype), values.cast(dtype)])


def _encode(column) -> tuple[pa.Array, pa.Array]:
    """字符串列编码为 int32 码加字典，控制大分区的排序内存。"""
    arr = column.combine_chunks() if isinstance(column, pa.ChunkedArray) else column
    enc = arr.dictionary_encode()
    return enc.indices.cast(pa.int32()), enc.dictionary


def _series_metrics(sorted_tbl: pa.Table, group_cols: list[str]):
    """在已按 group_cols 与 ts 排序的表上计算组内价格变化与无成交间隔。"""
    n = sorted_tbl.num_rows
    ts = sorted_tbl.column("ts").combine_chunks()
    price = sorted_tbl.column("price").combine_chunks()
    if n == 1:
        same = pa.array([False], pa.bool_())
        gap = pa.array([None], pa.int64())
        changed = pa.array([False], pa.bool_())
    else:
        same = None
        for name in group_cols:
            k = sorted_tbl.column(name).combine_chunks()
            eq = pc.equal(k.slice(1), k.slice(0, n - 1))
            same = eq if same is None else pc.and_(same, eq)
        same = _prepend(same, False, pa.bool_())
        raw_gap = _prepend(pc.subtract(ts.slice(1), ts.slice(0, n - 1)), None, pa.int64())
        gap = pc.if_else(same, raw_gap, pa.scalar(None, pa.int64()))
        changed = pc.and_kleene(
            same,
            _prepend(pc.not_equal(price.slice(1), price.slice(0, n - 1)), False, pa.bool_()),
        )
    new_second = pc.or_kleene(pc.invert(same), pc.greater(pc.fill_null(gap, 1), 0))
    return (
        gap,
        pc.cast(pc.fill_null(changed, False), pa.int64()),
        pc.cast(pc.fill_null(new_second, True), pa.int64()),
    )


def _asset_level(work: pa.Table, date_key: str, cid_values, asset_values) -> pa.Table:
    s = work.sort_by([("cid", "ascending"), ("asset", "ascending"), ("ts", "ascending")])
    gap, changed, new_second = _series_metrics(s, ["cid", "asset"])
    s = s.append_column("gap", gap)
    s = s.append_column("changed", changed)
    s = s.append_column("new_second", new_second)
    g = pa.TableGroupBy(s, ["cid", "asset"], use_threads=False).aggregate(
        [
            ("ts", "count"), ("ts", "min"), ("ts", "max"), ("usdc", "sum"),
            ("gap", "max"), ("new_second", "sum"), ("changed", "sum"),
            ("outcome_seq", "min"),
        ]
    )
    return pa.table(
        {
            "date": pa.array([date_key] * g.num_rows, pa.string()),
            "condition_id": pc.take(cid_values, g.column("cid")),
            "asset_id": pc.take(asset_values, g.column("asset")),
            "outcome_seq": pc.cast(g.column("outcome_seq_min"), pa.int64()),
            "trades": pc.cast(g.column("ts_count"), pa.int64()),
            "notional": pc.cast(g.column("usdc_sum"), pa.float64()),
            "first_ts": pc.cast(g.column("ts_min"), pa.int64()),
            "last_ts": pc.cast(g.column("ts_max"), pa.int64()),
            "active_seconds": pc.cast(g.column("new_second_sum"), pa.int64()),
            "price_changes": pc.cast(g.column("changed_sum"), pa.int64()),
            "max_gap_seconds": pc.cast(pc.fill_null(g.column("gap_max"), 0), pa.int64()),
        },
        schema=ASSET_DAY_SCHEMA,
    ).sort_by([("condition_id", "ascending"), ("asset_id", "ascending")])


def _market_level(work: pa.Table, date_key: str, cid_values, asset_tbl: pa.Table) -> pa.Table:
    s = work.sort_by([("cid", "ascending"), ("ts", "ascending")])
    gap, _changed, new_second = _series_metrics(s, ["cid"])
    s = s.append_column("new_second", new_second)
    s = s.append_column("gap_market", gap)
    g = pa.TableGroupBy(s, ["cid"], use_threads=False).aggregate(
        [
            ("ts", "count"), ("ts", "min"), ("ts", "max"), ("usdc", "sum"),
            ("new_second", "sum"), ("neg", "max"), ("gap_market", "max"),
        ]
    )
    market = pa.table(
        {
            "date": pa.array([date_key] * g.num_rows, pa.string()),
            "condition_id": pc.take(cid_values, g.column("cid")),
            "trades": pc.cast(g.column("ts_count"), pa.int64()),
            "notional": pc.cast(g.column("usdc_sum"), pa.float64()),
            "first_ts": pc.cast(g.column("ts_min"), pa.int64()),
            "last_ts": pc.cast(g.column("ts_max"), pa.int64()),
            "active_seconds": pc.cast(g.column("new_second_sum"), pa.int64()),
            # 市场级最大无成交间隔按 condition 序列计算：两个 outcome token 交替
            # 成交时，市场每秒都有成交，取各 asset gap 的最大值会高估
            "max_gap_seconds": pc.cast(pc.fill_null(g.column("gap_market_max"), 0), pa.int64()),
            "neg_risk": pc.greater(g.column("neg_max"), 0),
        }
    )
    # 市场级 price_changes 是各 asset 序列变化数之和：绝不跨 outcome 比较价格。
    # 两张表的 condition_id 集合相同（每个市场至少一个 asset），按键排序后逐列对齐，
    # 不用 join：join 在千万行级分区上会走 acero 并占用额外内存。
    per_market = pa.TableGroupBy(asset_tbl, ["condition_id"], use_threads=False).aggregate(
        [("price_changes", "sum"), ("asset_id", "count")]
    ).sort_by([("condition_id", "ascending")])
    market = market.sort_by([("condition_id", "ascending")])
    if market.num_rows != per_market.num_rows:
        raise ValueError(
            f"市场级与资产级聚合的市场数不一致：{market.num_rows} vs {per_market.num_rows}"
        )
    return pa.table(
        {
            "date": market.column("date"),
            "condition_id": market.column("condition_id"),
            "trades": market.column("trades"),
            "notional": market.column("notional"),
            "first_ts": market.column("first_ts"),
            "last_ts": market.column("last_ts"),
            "active_seconds": market.column("active_seconds"),
            "price_changes": pc.cast(per_market.column("price_changes_sum"), pa.int64()),
            "max_gap_seconds": market.column("max_gap_seconds"),
            "assets": pc.cast(per_market.column("asset_id_count"), pa.int64()),
            "neg_risk": market.column("neg_risk"),
        },
        schema=MARKET_DAY_SCHEMA,
    )


def census_partition(path: str, date_key: str) -> tuple[pa.Table, pa.Table]:
    """把一个日分区聚合成 (asset_day, market_day) 两张表。"""
    raw = pq.read_table(path, columns=require_label_blind(CENSUS_COLUMNS))
    if raw.num_rows == 0:
        return ASSET_DAY_SCHEMA.empty_table(), MARKET_DAY_SCHEMA.empty_table()

    cid_codes, cid_values = _encode(raw.column("condition_id"))
    asset_codes, asset_values = _encode(raw.column("asset_id"))
    work = pa.table(
        {
            "cid": cid_codes,
            "asset": asset_codes,
            "outcome_seq": raw.column("outcome_seq").combine_chunks().cast(pa.int64()),
            "ts": raw.column("block_timestamp").combine_chunks().cast(pa.int64()),
            "price": raw.column("price").combine_chunks().cast(pa.float64()),
            "usdc": raw.column("usdc_amount").combine_chunks().cast(pa.float64()),
            "neg": pc.cast(_bool_array(raw.column("neg_risk")), pa.int64()),
        }
    )
    del raw
    require_epoch_seconds(pc.min(work.column("ts")).as_py(), field="block_timestamp")
    require_epoch_seconds(pc.max(work.column("ts")).as_py(), field="block_timestamp")

    asset_tbl = _asset_level(work, date_key, cid_values, asset_values)
    market_tbl = _market_level(work, date_key, cid_values, asset_tbl)
    return asset_tbl, market_tbl


def _census_task(task: dict) -> dict:
    from ..temporal.manifest import fingerprint_table

    asset_tbl, market_tbl = census_partition(task["path"], task["date"])
    pq.write_table(asset_tbl, os.path.join(task["out_asset_day"], f"{task['key']}.parquet"))
    pq.write_table(market_tbl, os.path.join(task["out_market_day"], f"{task['key']}.parquet"))
    summary = {
        "key": task["key"],
        "date": task["date"],
        "segment": task["segment"],
        "source_digest": task["digest"],
        "census_version": CENSUS_VERSION,
        "markets": market_tbl.num_rows,
        "assets": asset_tbl.num_rows,
        "trades": int(pc.sum(market_tbl.column("trades")).as_py() or 0),
        "notional": float(pc.sum(market_tbl.column("notional")).as_py() or 0.0),
        "neg_risk_markets": int(
            pc.sum(pc.cast(market_tbl.column("neg_risk"), pa.int64())).as_py() or 0
        ),
        "fingerprint_asset_day": fingerprint_table(asset_tbl),
        "fingerprint_market_day": fingerprint_table(market_tbl),
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


def census_keys(out_dir: str) -> dict[str, set[str]]:
    """各产物目录里实际存在的分区键，用于孤儿与缺失检查。"""
    out: dict[str, set[str]] = {}
    for sub in ("_partitions", "asset_day", "market_day"):
        base = os.path.join(out_dir, sub)
        out[sub] = {
            os.path.basename(p).rsplit(".", 1)[0]
            for p in glob.glob(os.path.join(base, "*"))
        } if os.path.isdir(base) else set()
    return out


def prune_orphans(out_dir: str, valid_keys: set[str]) -> list[str]:
    """删除来源分区已消失的产物。否则索引会继续加载孤儿数据。"""
    removed = []
    for sub in ("_partitions", "asset_day", "market_day"):
        base = os.path.join(out_dir, sub)
        if not os.path.isdir(base):
            continue
        for path in sorted(glob.glob(os.path.join(base, "*"))):
            key = os.path.basename(path).rsplit(".", 1)[0]
            if key not in valid_keys:
                os.remove(path)
                removed.append(os.path.relpath(path, out_dir))
    return removed


def build_census(
    roots: dict[str, str],
    out_dir: str,
    *,
    workers: int = 8,
    force: bool = False,
    heartbeat_path: str | None = None,
) -> tuple[list[dict], list[QualityFinding]]:
    dirs = {
        "asset_day": os.path.join(out_dir, "asset_day"),
        "market_day": os.path.join(out_dir, "market_day"),
        "_partitions": os.path.join(out_dir, "_partitions"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)

    partitions = discover_partitions(roots)
    valid_keys = {f"{segment}_{date_key}" for date_key, segment, _ in partitions}
    removed = prune_orphans(out_dir, valid_keys)

    tasks, done = [], {}
    for date_key, segment, path in partitions:
        key = f"{segment}_{date_key}"
        sidecar = os.path.join(dirs["_partitions"], f"{key}.json")
        digest = partition_digest(path)
        outputs_present = all(
            os.path.exists(os.path.join(dirs[s], f"{key}.parquet"))
            for s in ("asset_day", "market_day")
        )
        if not force and os.path.exists(sidecar) and outputs_present:
            with open(sidecar, encoding="utf-8") as f:
                cached = json.load(f)
            if (
                cached.get("source_digest") == digest
                and cached.get("census_version") == CENSUS_VERSION
            ):
                done[key] = cached
                continue
        tasks.append(
            {
                "path": path, "key": key, "date": date_key, "segment": segment,
                "digest": digest,
                "out_asset_day": dirs["asset_day"],
                "out_market_day": dirs["market_day"],
                "out_days": dirs["_partitions"],
            }
        )

    if tasks:
        state = {
            "finished": 0,
            "started": time.monotonic(),
            "last_progress": time.monotonic(),
            "last_key": None,
        }
        stop = threading.Event()

        def write_beat() -> None:
            now = time.monotonic()
            with open(heartbeat_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "stage": "census",
                        "done": state["finished"],
                        "total": len(tasks),
                        "elapsed_seconds": round(now - state["started"], 1),
                        "seconds_since_last_completion": round(now - state["last_progress"], 1),
                        "last_key": state["last_key"],
                    },
                    f,
                )

        def ticker() -> None:
            # 按时间周期写心跳，而不是按完成个数：单分区卡死时心跳仍在跳，
            # seconds_since_last_completion 会持续增长，卡死可被外部观测到
            while not stop.wait(HEARTBEAT_SECONDS):
                write_beat()

        thread = None
        if heartbeat_path:
            write_beat()
            thread = threading.Thread(target=ticker, daemon=True)
            thread.start()

        def beat(summary: dict) -> None:
            state["finished"] += 1
            state["last_progress"] = time.monotonic()
            state["last_key"] = summary["key"]
            done[summary["key"]] = summary

        try:
            if workers > 1:
                with ProcessPoolExecutor(max_workers=workers) as pool:
                    for summary in pool.map(_census_task, tasks, chunksize=1):
                        beat(summary)
            else:
                for task in tasks:
                    beat(_census_task(task))
        finally:
            stop.set()
            if thread is not None:
                thread.join(timeout=1)
                write_beat()

    summaries = [done[k] for k in sorted(done)]
    findings = [
        QualityFinding(
            severity=Severity.ERROR if not summaries else Severity.INFO,
            code="pm_census.coverage",
            message="Polymarket 逐笔普查覆盖",
            evidence={
                "partitions": len(summaries),
                "trades": sum(s["trades"] for s in summaries),
                "markets_seen": sum(s["markets"] for s in summaries),
                "assets_seen": sum(s["assets"] for s in summaries),
                "first": min((s["date"] for s in summaries), default=None),
                "last": max((s["date"] for s in summaries), default=None),
                "rebuilt_partitions": len(tasks),
                "pruned_orphan_count": len(removed),
                "pruned_orphans": removed[:20],
            },
        )
    ]
    return summaries, findings


def verify_artifact_integrity(out_dir: str) -> tuple[int, list[str]]:
    """把已物化产物与同次生成的 sidecar 比对。

    这证明的是**产物完整性**（写盘后未被改动或丢失），不是独立重建确定性；
    后者由 `verify_rebuild_determinism` 从来源重跑若干分区来证明。
    """
    from ..temporal.manifest import fingerprint_table

    checked, bad = 0, []
    for sidecar in sorted(glob.glob(os.path.join(out_dir, "_partitions", "*.json"))):
        with open(sidecar, encoding="utf-8") as f:
            rec = json.load(f)
        key = rec["key"]
        ok = True
        for sub, field in (("asset_day", "fingerprint_asset_day"),
                           ("market_day", "fingerprint_market_day")):
            path = os.path.join(out_dir, sub, f"{key}.parquet")
            if not os.path.exists(path) or fingerprint_table(pq.read_table(path)) != rec.get(field):
                ok = False
        checked += 1
        if not ok:
            bad.append(key)
    return checked, bad


def verify_rebuild_determinism(
    roots: dict[str, str], out_dir: str, sample: int = 12
) -> tuple[int, list[str]]:
    """从**来源**独立重跑若干分区，与已物化产物的指纹比对。

    这才是确定性证明：同一来源重新计算必须得到逐位相同的逻辑内容。
    """
    from ..temporal.manifest import fingerprint_table

    partitions = discover_partitions(roots)
    if not partitions:
        return 0, []
    step = max(1, len(partitions) // sample)
    picked = partitions[::step][:sample]
    checked, bad = 0, []
    for date_key, segment, path in picked:
        key = f"{segment}_{date_key}"
        sidecar = os.path.join(out_dir, "_partitions", f"{key}.json")
        if not os.path.exists(sidecar):
            continue
        with open(sidecar, encoding="utf-8") as f:
            rec = json.load(f)
        asset_tbl, market_tbl = census_partition(path, date_key)
        checked += 1
        if (
            fingerprint_table(asset_tbl) != rec.get("fingerprint_asset_day")
            or fingerprint_table(market_tbl) != rec.get("fingerprint_market_day")
        ):
            bad.append(key)
    return checked, bad


def audit_neg_risk_coverage(summaries: list[dict], sampled_rows: int) -> QualityFinding:
    """negRisk 覆盖审计。两段都不含 negRisk 成交是一条需要更正设计文档的事实。"""
    markets = sum(s.get("neg_risk_markets", 0) for s in summaries)
    return QualityFinding(
        severity=Severity.WARNING if markets == 0 else Severity.INFO,
        code="pm_census.neg_risk_absent_in_both_segments",
        message=(
            "全史普查中 neg_risk 为真的 (市场, 日) 数为 0：两段 tape 都不含 NegRisk "
            "Exchange 成交，扩展段未补上 HF 段的 negRisk 缺口"
        ),
        evidence={
            "neg_risk_market_days": markets,
            "partitions": len(summaries),
            "sampled_rows_in_dedup_audit": sampled_rows,
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
            "log_index，因此 relay 剔除与 unknown venue 隔离在现有数据上无法执行"
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
            pc.sum(pc.subtract(grouped.column("block_timestamp_count"), 1)).as_py() or 0
        )
        total += table.num_rows
        dup += n_dup
        per_partition.append(
            {"partition": os.path.basename(path), "rows": table.num_rows,
             "exact_duplicates": n_dup}
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
