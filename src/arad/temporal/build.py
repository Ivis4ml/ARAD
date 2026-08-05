"""SC 窄切片 Temporal Spine 的构建流水线。

单遍读取 SC 的逐合约 tick（只解压 SC 条目），逐 (合约, 交易日) 归一化后同时产出
1 分钟与日频 bar；随后用**只含 t-1 信息**的日频面板构造主力视图，再在主力视图上
物化两个目标。

幂等与恢复：每个交易日写一份 sidecar，键为该日 SC 条目 (名字, CRC, 大小) 的聚合
摘要。重跑时摘要一致则跳过，来源变化则该日重建。
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor
from datetime import date

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.dataset as pads
import pyarrow.parquet as pq

from ..data_catalog.schema import QualityFinding, Severity
from .bars import BARS_1MIN_SCHEMA, BARS_DAILY_SCHEMA, bars_1min, bars_daily
from .calendar import TradingCalendar
from .manifest import fingerprint_table
from .sessions import PRODUCTS, Placement, ProductReference
from .ticks import enrich

_CONTRACT_RE = re.compile(r"^([a-z]{1,2})(\d{3,4})_(20\d{6})\.csv$")
_ALIAS_RE = re.compile(r"^([a-z]{1,2})主力连续_(20\d{6})\.csv$")

TICK_CONVERT = pacsv.ConvertOptions(
    column_types={
        "TradingDay": pa.int32(),
        "InstrumentID": pa.string(),
        "UpdateTime": pa.string(),
        "UpdateMillisec": pa.int16(),
        "LastPrice": pa.float64(),
        "Volume": pa.int64(),
        "BidPrice1": pa.float64(),
        "BidVolume1": pa.int32(),
        "AskPrice1": pa.float64(),
        "AskVolume1": pa.int32(),
        "AveragePrice": pa.float64(),
        "Turnover": pa.float64(),
        "OpenInterest": pa.float64(),
        "UpperLimitPrice": pa.float64(),
        "LowerLimitPrice": pa.float64(),
    }
)


def _decode(info: zipfile.ZipInfo) -> str:
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


def scan_product_entries(root: str, layouts: list[str], product: str) -> dict[str, dict]:
    """只读 zip 中央目录，按交易日汇总某个品种的逐合约条目与主力连续别名条目。"""
    zip_paths: list[str] = []
    for pat in layouts:
        zip_paths.extend(glob.glob(os.path.join(root, pat)))
    days: dict[str, dict] = {}
    for zp in sorted(set(zip_paths)):
        try:
            with zipfile.ZipFile(zp) as zf:
                infos = zf.infolist()
        except zipfile.BadZipFile:
            continue
        for info in infos:
            if info.is_dir():
                continue
            name = _decode(info)
            base = os.path.basename(name)
            m = _CONTRACT_RE.match(base)
            if m and m.group(1) == product:
                day = days.setdefault(m.group(3), {"entries": [], "alias": None})
                day["entries"].append(
                    {
                        "zip": zp,
                        "entry": info.filename,
                        "contract": f"{m.group(1)}{m.group(2)}",
                        "crc": info.CRC,
                        "size": info.file_size,
                    }
                )
                continue
            a = _ALIAS_RE.match(base)
            if a and a.group(1) == product:
                day = days.setdefault(a.group(2), {"entries": [], "alias": None})
                day["alias"] = {"zip": zp, "entry": info.filename}
    for day in days.values():
        day["entries"].sort(key=lambda e: e["contract"])
        day["digest"] = hashlib.sha256(
            "".join(f"{e['contract']}|{e['crc']}|{e['size']};" for e in day["entries"]).encode()
        ).hexdigest()
    return days


def _read_alias_contract(zp: str, entry: str) -> str | None:
    with zipfile.ZipFile(zp) as zf, zf.open(entry) as fh:
        fh.readline()
        line = fh.readline().decode("utf-8", "replace")
    parts = line.split(",")
    return parts[1] if len(parts) > 1 else None


def _observed_envelope(ticks: pa.Table) -> dict:
    """记录该合约当日各 session 实测的首末秒，用于与声明时段表比对。"""
    out: dict[str, int | None] = {}
    in_session = ticks.filter(
        pc.is_in(
            ticks.column("placement"),
            value_set=pa.array([Placement.SEGMENT.value, Placement.AUCTION.value]),
        )
    )
    night = in_session.filter(pc.equal(in_session.column("session_seq"), 0))
    day = in_session.filter(pc.equal(in_session.column("session_seq"), 1))
    if night.num_rows:
        sods = night.column("sod")
        evening = pc.filter(sods, pc.greater_equal(sods, 43200))
        morning = pc.filter(sods, pc.less(sods, 43200))
        out["night_open_sod"] = pc.min(evening).as_py() if len(evening) else None
        out["night_close_sod"] = pc.max(morning).as_py() if len(morning) else None
    if day.num_rows:
        out["day_open_sod"] = pc.min(day.column("sod")).as_py()
        out["day_close_sod"] = pc.max(day.column("sod")).as_py()
    outside = ticks.filter(pc.equal(ticks.column("placement"), Placement.OUTSIDE.value))
    out["outside_minutes"] = sorted(
        {int(s) // 60 for s in outside.column("sod").to_pylist()}
    )[:10]
    return out


def build_day(task: dict) -> dict:
    """构建单个交易日的 SC bar。返回摘要，parquet 直接写盘。"""
    product: ProductReference = PRODUCTS[task["product"]]
    trading_day = date.fromisoformat(task["trading_day"])
    prev = date.fromisoformat(task["prev_trading_day"]) if task["prev_trading_day"] else None
    minute_tables, daily_tables = [], []
    findings: list[dict] = []
    envelope: dict = {}
    n_ticks = 0

    for e in task["entries"]:
        with zipfile.ZipFile(e["zip"]) as zf:
            blob = zf.read(e["entry"])
        if not blob:
            continue
        raw = pacsv.read_csv(pa.BufferReader(blob), convert_options=TICK_CONVERT)
        if raw.num_rows == 0:
            continue
        ticks, day_findings = enrich(
            raw, product=product, trading_day=trading_day, prev_trading_day=prev
        )
        n_ticks += ticks.num_rows
        findings.extend(f.model_dump(mode="json") for f in day_findings)
        minute_tables.append(bars_1min(ticks, product=product))
        daily_tables.append(bars_daily(ticks, product=product))
        env = _observed_envelope(ticks)
        for k, v in env.items():
            if k == "outside_minutes":
                envelope.setdefault(k, [])
                envelope[k] = sorted(set(envelope[k]) | set(v))[:10]
            elif v is not None:
                cur = envelope.get(k)
                if k.endswith("open_sod"):
                    envelope[k] = v if cur is None else min(cur, v)
                else:
                    envelope[k] = v if cur is None else max(cur, v)
        del ticks, raw

    minutes = (
        pa.concat_tables(minute_tables) if minute_tables else BARS_1MIN_SCHEMA.empty_table()
    )
    daily = pa.concat_tables(daily_tables) if daily_tables else BARS_DAILY_SCHEMA.empty_table()

    day_key = task["trading_day"]
    pq.write_table(minutes, os.path.join(task["out_1min"], f"{day_key}.parquet"))
    pq.write_table(daily, os.path.join(task["out_daily"], f"{day_key}.parquet"))

    alias = None
    if task.get("alias"):
        alias = _read_alias_contract(task["alias"]["zip"], task["alias"]["entry"])

    summary = {
        "trading_day": day_key,
        "prev_trading_day": task["prev_trading_day"],
        "digest": task["digest"],
        "contracts": len(task["entries"]),
        "n_ticks": n_ticks,
        "n_bars_1min": minutes.num_rows,
        "n_bars_daily": daily.num_rows,
        "alias_contract": alias,
        "envelope": envelope,
        "findings": findings,
        "fingerprint_1min": fingerprint_table(minutes),
        "fingerprint_daily": fingerprint_table(daily),
    }
    with open(os.path.join(task["out_days"], f"{day_key}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False)
    return summary


def build_bars(
    *,
    product: str,
    root: str,
    layouts: list[str],
    out_dir: str,
    calendar: TradingCalendar,
    workers: int,
    force: bool = False,
    limit_days: int | None = None,
) -> tuple[list[dict], list[QualityFinding]]:
    """扫描、构建（可恢复）并返回每日摘要。"""
    days = scan_product_entries(root, layouts, product)
    out_1min = os.path.join(out_dir, "bars_1min")
    out_daily = os.path.join(out_dir, "bars_daily")
    out_days = os.path.join(out_dir, "_days")
    for d in (out_1min, out_daily, out_days):
        os.makedirs(d, exist_ok=True)

    findings: list[QualityFinding] = []
    ordered = sorted(days)
    if limit_days:
        ordered = ordered[-limit_days:]

    tasks, done = [], {}
    for day_key in ordered:
        info = days[day_key]
        trading_day = date(int(day_key[:4]), int(day_key[4:6]), int(day_key[6:]))
        sidecar = os.path.join(out_days, f"{day_key}.json")
        if not force and os.path.exists(sidecar):
            with open(sidecar, encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("digest") == info["digest"]:
                done[day_key] = cached
                continue
        prev = calendar.prev_or_none(trading_day)
        tasks.append(
            {
                "product": product,
                "trading_day": day_key,
                "prev_trading_day": prev.isoformat() if prev else None,
                "entries": info["entries"],
                "alias": info["alias"],
                "digest": info["digest"],
                "out_1min": out_1min,
                "out_daily": out_daily,
                "out_days": out_days,
            }
        )

    if tasks:
        if workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                for summary in pool.map(build_day, tasks, chunksize=1):
                    done[summary["trading_day"]] = summary
        else:
            for task in tasks:
                summary = build_day(task)
                done[summary["trading_day"]] = summary

    summaries = [done[k] for k in ordered if k in done]
    findings.extend(_session_verification_findings(summaries, product))
    return summaries, findings


def _session_verification_findings(
    summaries: list[dict], product: str
) -> list[QualityFinding]:
    """把全部交易日的实测 session 包络与声明时段表比对（单遍扫描的附带产物）。"""
    table = PRODUCTS[product].sessions
    findings: list[QualityFinding] = []
    extremes: dict[str, list[int]] = {}
    outside_minutes: dict[int, int] = {}
    for s in summaries:
        env = s.get("envelope") or {}
        for k in ("night_open_sod", "night_close_sod", "day_open_sod", "day_close_sod"):
            if env.get(k) is not None:
                extremes.setdefault(k, []).append(int(env[k]))
        for minute in env.get("outside_minutes", []):
            outside_minutes[minute] = outside_minutes.get(minute, 0) + 1

    declared = {
        "night_open_sod": (table.session("night").auction_start, table.session("night").open),
        "night_close_sod": (None, table.session("night").close),
        "day_open_sod": (table.session("day").auction_start, table.session("day").open),
        "day_close_sod": (None, table.session("day").close),
    }
    observed_summary = {}
    for key, values in sorted(extremes.items()):
        lo, hi = min(values), max(values)
        observed_summary[key] = {"min": lo, "max": hi, "days": len(values)}
        for sod in (lo, hi):
            got = table.classify(sod)
            if got.placement is Placement.OUTSIDE:
                findings.append(
                    QualityFinding(
                        severity=Severity.WARNING,
                        code="sessions.observed_outside_declared",
                        message="实测 session 包络落在声明时段表之外，需人工裁决",
                        evidence={"product": product, "which": key, "seconds_of_day": sod},
                    )
                )
    findings.append(
        QualityFinding(
            severity=Severity.INFO,
            code="sessions.observed_envelope",
            message="全史实测 session 首末秒包络与声明时段表的比对结果",
            evidence={
                "observed": observed_summary,
                "declared": {
                    k: [str(v[0]) if v[0] else None, str(v[1])] for k, v in declared.items()
                },
            },
        )
    )
    if outside_minutes:
        top = sorted(outside_minutes.items(), key=lambda kv: -kv[1])[:8]
        findings.append(
            QualityFinding(
                severity=Severity.INFO,
                code="ticks.out_of_session_minutes",
                message="时段表之外 tick 的分钟分布（按出现的交易日数排序）",
                evidence={
                    "top_minutes": [
                        {"time": f"{m // 60:02d}:{m % 60:02d}", "days": n} for m, n in top
                    ]
                },
            )
        )
    return findings


def load_daily_panel(out_dir: str) -> pa.Table:
    dataset = pads.dataset(os.path.join(out_dir, "bars_daily"), format="parquet")
    table = dataset.to_table(columns=["trading_day", "contract", "volume", "open_interest_close"])
    return table.rename_columns(
        ["trading_day", "contract", "volume", "open_interest"]
    ).sort_by([("trading_day", "ascending"), ("contract", "ascending")])


def day_findings(summaries: list[dict]) -> list[QualityFinding]:
    """把逐日 finding 汇总为按 code 计数的少数几条，避免 manifest 被逐日噪声淹没。"""
    buckets: dict[str, dict] = {}
    for s in summaries:
        for f in s.get("findings", []):
            b = buckets.setdefault(
                f["code"], {"severity": f["severity"], "message": f["message"], "days": set(), "rows": 0}
            )
            b["days"].add(s["trading_day"])
            b["rows"] += int(f.get("evidence", {}).get("rows", 0) or 0)
    out = []
    for code, b in sorted(buckets.items()):
        out.append(
            QualityFinding(
                severity=Severity(b["severity"]),
                code=code,
                message=b["message"],
                evidence={
                    "trading_days": len(b["days"]),
                    "rows": b["rows"],
                    "first_days": sorted(b["days"])[:5],
                },
            )
        )
    return out
