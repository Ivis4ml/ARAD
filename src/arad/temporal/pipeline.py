"""SC Temporal Spine 的编排：bar → 主力视图 → 目标 → 控制源 → manifest → 回放清单。"""

from __future__ import annotations

import collections
import json
import os
from datetime import date

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as pads
import pyarrow.parquet as pq
import yaml

from ..data_catalog.schema import QualityFinding, Severity, load_manifest
from .asof import PitSeries, asof_last, count_before
from .build import (
    build_bars,
    day_findings,
    load_daily_panel,
)
from .calendar import TradingCalendar
from .controls import (
    brent_contract,
    cls_contract,
    load_brent_series,
    load_cls_series,
    load_pm_registry_series,
    pm_registry_contract,
)
from .dominant import (
    DominantRule,
    alias_agreement_finding,
    build_dominant_series,
)
from .manifest import (
    SPINE_CODE_VERSION,
    DatasetRef,
    InputRef,
    SpineManifest,
    TargetRecord,
    digest_json,
    fingerprint_table,
    write_spine_manifest,
)
from .replay import build_checklist, render_markdown, stratified_sample
from .sessions import PRODUCTS
from .targets import (
    TARGET_SPECS,
    build_session_bars,
    build_target_table,
    no_trade_counts,
    segment_counts,
)

ASSUMPTIONS = [
    "RV 只取同一连续竞价 segment 内相邻 1 分钟 bar 的对数收益；跨 segment 与跨 session 的价格变化不计入。",
    "集合竞价 bar 单独成 bar 并排除在 RV 收益序列之外；开盘跳空由 diagnostic target 单独度量。",
    "session 开盘价：集合竞价有成交时取竞价成交价，否则取第一根连续竞价 bar 的开盘价。",
    "跳空的前一收盘价必须来自同一合约的上一个 session；换月导致缺前一 session 时记为 no-trade。",
    "execution_lag 取 60 秒，决策时点 = session 开盘前 60 秒；label 窗口自开盘起算。",
    "Episode 缺省按交易日成组（夜盘与日盘同属一个 Episode）。",
    "样本段按 label 结束时点归段；forward 只在给出 freeze_at 与 embargo 时才可能出现，不写死日期。",
    "Brent 采用保守可用规则 D+1 06:00 Asia/Shanghai，字段标为 provisional，消费需受审计 override。",
    "财联社可用时间 = 发布时刻 + 60 秒采集延迟（保守参数，记入 manifest）。",
]

BLOCKERS = [
    (
        "cn_registry_v3.parquet 的市场覆盖仅 2026-01-04 至 2026-07-13，整段落在 contaminated audit "
        "区间；以该登记表为唯一市场来源的 Study（含 M4 tracer bullet 的 Polymarket 腿）只能得到 "
        "contaminated 结论。2022-2025 的市场发现需从 markets_clob.parquet 重建，属 M5 范围。"
    ),
    (
        "Polymarket 逐笔 belief 序列未物化：venue_class 与 is_relay 在 M1 manifest 中为 provisional，"
        "未完成 relay 剔除与 unknown venue 隔离前物化会重复计入名义额。属 M5 范围。"
    ),
    "brent_daily.csv 的来源方与发布时刻未核实，当前用保守规则替代；核实属 acquisition 流程，需人工授权。",
    (
        "Alpha-Data curve_daily.parquet 仅覆盖 2026-01-05 至 2026-07-13，只能作该窗口的独立交叉核对，"
        "无法覆盖 discovery 与 historical validation 段的日频等价性检查。"
    ),
    "郑商所 Turnover 口径与日内倒退的全品种普查仍为 provisional（M1 遗留）；SC 属 INE，本票未触及该问题。",
]


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _minute_bars_for_contract(data_dir: str, contract: str, day_keys: set[str]) -> pa.Table:
    tables = []
    base = os.path.join(data_dir, "bars_1min")
    for day_key in sorted(day_keys):
        path = os.path.join(base, f"{day_key}.parquet")
        if not os.path.exists(path):
            continue
        table = pq.read_table(path)
        if table.num_rows == 0:
            continue
        sub = table.filter(pc.equal(table.column("contract"), contract))
        if sub.num_rows:
            tables.append(sub)
    if not tables:
        return None
    return pa.concat_tables(tables)


def _dominant_view(dominant: pa.Table, calendar: TradingCalendar):
    """主力视图需要的 (合约 → 交易日集合)，额外包含前一交易日以支持同合约跳空。"""
    wanted: dict[str, set[str]] = collections.defaultdict(set)
    owned: set[tuple[int, str]] = set()
    roll_days: set[date] = set()
    for row in dominant.to_pylist():
        contract = row["contract"]
        if not contract or not row["has_data_on_day"]:
            continue
        day_key = str(row["trading_day"])
        wanted[contract].add(day_key)
        owned.add((int(row["trading_day"]), contract))
        day = date(int(day_key[:4]), int(day_key[4:6]), int(day_key[6:]))
        prev = calendar.prev_or_none(day)
        if prev is not None:
            wanted[contract].add(prev.strftime("%Y%m%d"))
        if row["is_roll"]:
            roll_days.add(day)
    return wanted, owned, roll_days


def build_targets(
    data_dir: str,
    dominant: pa.Table,
    calendar: TradingCalendar,
    *,
    product,
    episode_grain: str,
) -> dict[str, pa.Table]:
    wanted, owned, roll_days = _dominant_view(dominant, calendar)
    per_spec: dict[str, list[pa.Table]] = {spec.name: [] for spec in TARGET_SPECS}
    for contract in sorted(wanted):
        bars = _minute_bars_for_contract(data_dir, contract, wanted[contract])
        if bars is None:
            continue
        sessions = build_session_bars(
            bars, product=product, prev_lookup=calendar.prev_or_none
        )
        for spec in TARGET_SPECS:
            table = build_target_table(
                sessions,
                spec,
                product=product,
                episode_grain=episode_grain,
                roll_days=roll_days,
            )
            if table.num_rows == 0:
                continue
            keep = pa.array(
                [
                    (int(r["trading_day"]), r["contract"]) in owned
                    for r in table.select(["trading_day", "contract"]).to_pylist()
                ],
                pa.bool_(),
            )
            table = table.filter(keep)
            if table.num_rows:
                per_spec[spec.name].append(table)
    return {
        name: (
            pa.concat_tables(tables).sort_by(
                [("label_start", "ascending"), ("session_seq", "ascending")]
            )
            if tables
            else None
        )
        for name, tables in per_spec.items()
    }


def spine_build(config_path: str, *, force: bool = False, workers: int | None = None,
                limit_days: int | None = None) -> int:
    cfg = load_config(config_path)
    product = PRODUCTS[cfg["product"]]
    data_dir = cfg["output"]["data_dir"]
    controls_dir = cfg["output"]["controls_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    for d in (data_dir, controls_dir, manifest_dir):
        os.makedirs(d, exist_ok=True)

    commodity = load_manifest(cfg["inputs"]["commodity_manifest"])
    cls_manifest = load_manifest(cfg["inputs"]["cls_manifest"])
    pm_manifest = load_manifest(cfg["inputs"]["polymarket_manifest"])

    print("building trading calendar from archive central directories...", flush=True)
    calendar = TradingCalendar.from_archive(cfg["source"]["root"], cfg["source"]["layouts"])
    findings: list[QualityFinding] = []
    if len(calendar) != commodity.facts.get("trading_days"):
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="calendar.disagrees_with_source_manifest",
                message="交易日历与 M1 商品 manifest 的交易日数不一致",
                evidence={
                    "calendar": len(calendar),
                    "manifest": commodity.facts.get("trading_days"),
                },
            )
        )

    print(f"calendar: {len(calendar)} trading days; building SC bars...", flush=True)
    summaries, session_findings = build_bars(
        product=product.product,
        root=cfg["source"]["root"],
        layouts=cfg["source"]["layouts"],
        out_dir=data_dir,
        calendar=calendar,
        workers=workers or int(cfg["build"]["workers"]),
        force=force,
        limit_days=limit_days,
    )
    findings.extend(session_findings)
    findings.extend(day_findings(summaries))

    built_days = [
        date(int(s["trading_day"][:4]), int(s["trading_day"][4:6]), int(s["trading_day"][6:]))
        for s in summaries
    ]
    nights = {
        d
        for d, s in zip(built_days, summaries)
        if (s.get("envelope") or {}).get("night_open_sod") is not None
    }
    findings.extend(calendar.night_gap_findings(nights))

    print("building t-1 dominant series...", flush=True)
    panel = load_daily_panel(data_dir)
    rule = DominantRule(
        metric=cfg["dominant"]["metric"],
        tie_break=cfg["dominant"]["tie_break"],
        monotone_delivery=bool(cfg["dominant"]["monotone_delivery"]),
    )
    alias = {
        d: s["alias_contract"]
        for d, s in zip(built_days, summaries)
        if s.get("alias_contract")
    }
    dominant, dominant_findings = build_dominant_series(
        panel, built_days, rule=rule, alias=alias
    )
    findings.extend(dominant_findings[:20])
    if len(dominant_findings) > 20:
        findings.append(
            QualityFinding(
                severity=Severity.INFO,
                code="dominant.selected_contract_absent_on_day.summary",
                message="按 t-1 信息选出的主力合约在当日无数据的总次数",
                evidence={"count": len(dominant_findings)},
            )
        )
    findings.append(alias_agreement_finding(dominant))
    pq.write_table(dominant, os.path.join(data_dir, "dominant.parquet"))

    print("materialising targets on the dominant view...", flush=True)
    targets = build_targets(
        data_dir,
        dominant,
        calendar,
        product=product,
        episode_grain=cfg["episode"]["grain"],
    )
    target_records: list[TargetRecord] = []
    for spec in TARGET_SPECS:
        table = targets.get(spec.name)
        record = TargetRecord(**spec.record())
        if table is not None:
            path = os.path.join(data_dir, f"target_{spec.name}.parquet")
            pq.write_table(table, path)
            record.rows = table.num_rows
            record.fingerprint = fingerprint_table(table)
            record.sample_segments = segment_counts(table)
            record.no_trade_reasons = no_trade_counts(table)
        target_records.append(record)

    print("registering control sources...", flush=True)
    first_day, last_day = calendar.days[0], calendar.days[-1]
    poll_delay = int(cfg["controls"]["cls_poll_delay_seconds"])
    cls_series = load_cls_series(
        cfg["controls"]["cls_output_dir"],
        cfg["controls"]["cls_pattern"],
        cls_manifest,
        start=first_day,
        end=last_day,
        poll_delay_seconds=poll_delay,
    )
    pq.write_table(cls_series.table, os.path.join(controls_dir, "cls.parquet"))
    brent_series = load_brent_series(
        cfg["controls"]["brent_csv"], start=first_day, end=last_day
    )
    pq.write_table(brent_series.table, os.path.join(controls_dir, "brent.parquet"))
    pm_series = load_pm_registry_series(
        cfg["controls"]["pm_registry"], product=cfg["controls"]["pm_product"]
    )
    pq.write_table(pm_series.table, os.path.join(controls_dir, "pm_market_slice.parquet"))
    themes = dict(collections.Counter(pm_series.table.column("theme").to_pylist()))
    admit = pm_series.table.column("available_time").to_pylist()
    findings.append(
        QualityFinding(
            severity=Severity.WARNING,
            code="controls.pm_registry_contaminated_window_only",
            message=(
                "Polymarket 市场登记表的 admit_ts 全部落在 contaminated audit 区间；"
                "以该切片为唯一市场来源的 Study 无法得到 discovery 或 historical validation 结论"
            ),
            evidence={
                "markets": pm_series.table.num_rows,
                "themes": themes,
                "first_admit": admit[0].isoformat() if admit else None,
                "last_admit": admit[-1].isoformat() if admit else None,
            },
        )
    )

    control_contracts = [
        cls_contract(cls_manifest, cfg["controls"]["cls_output_dir"], poll_delay),
        brent_contract(cfg["controls"]["brent_csv"]),
        pm_registry_contract(
            cfg["controls"]["pm_registry"],
            product=cfg["controls"]["pm_product"],
            rows=pm_series.table.num_rows,
            themes=themes,
        ),
    ]

    datasets = [
        DatasetRef(
            name="bars_1min",
            path=os.path.join(data_dir, "bars_1min"),
            rows=sum(s["n_bars_1min"] for s in summaries),
            partitions=len(summaries),
            fingerprint=_combine([s["fingerprint_1min"] for s in summaries]),
            note="按交易日分区；指纹为逐日逻辑内容指纹的确定性合并",
        ),
        DatasetRef(
            name="bars_daily",
            path=os.path.join(data_dir, "bars_daily"),
            rows=sum(s["n_bars_daily"] for s in summaries),
            partitions=len(summaries),
            fingerprint=_combine([s["fingerprint_daily"] for s in summaries]),
        ),
        DatasetRef(
            name="dominant",
            path=os.path.join(data_dir, "dominant.parquet"),
            rows=dominant.num_rows,
            fingerprint=fingerprint_table(dominant),
        ),
        DatasetRef(
            name="controls_cls",
            path=os.path.join(controls_dir, "cls.parquet"),
            rows=cls_series.table.num_rows,
            fingerprint=fingerprint_table(cls_series.table.select(["natural_date"])),
            note="指纹只覆盖日期列，正文不进指纹以控制成本",
        ),
        DatasetRef(
            name="controls_brent",
            path=os.path.join(controls_dir, "brent.parquet"),
            rows=brent_series.table.num_rows,
            fingerprint=fingerprint_table(brent_series.table),
        ),
        DatasetRef(
            name="controls_pm_market_slice",
            path=os.path.join(controls_dir, "pm_market_slice.parquet"),
            rows=pm_series.table.num_rows,
            fingerprint=fingerprint_table(pm_series.table),
        ),
    ]

    manifest = SpineManifest(
        spine_id=f"{product.product}-temporal-spine",
        code_version=SPINE_CODE_VERSION,
        config_digest=digest_json(cfg),
        inputs={
            "commodity_tick": InputRef(
                fingerprint=commodity.fingerprint,
                source_snapshot_digest=(
                    commodity.source_snapshot.digest if commodity.source_snapshot else ""
                ),
                scanner_version=commodity.scanner_version,
            ),
            "cls_telegraph": InputRef(
                fingerprint=cls_manifest.fingerprint,
                source_snapshot_digest=(
                    cls_manifest.source_snapshot.digest if cls_manifest.source_snapshot else ""
                ),
                scanner_version=cls_manifest.scanner_version,
            ),
            "polymarket_tape": InputRef(
                fingerprint=pm_manifest.fingerprint,
                source_snapshot_digest=(
                    pm_manifest.source_snapshot.digest if pm_manifest.source_snapshot else ""
                ),
                scanner_version=pm_manifest.scanner_version,
            ),
        },
        calendar=calendar.facts(),
        session_table=product.sessions.describe()
        | {"product_reference": product.reference, "multiplier": product.multiplier,
           "tick_size": product.tick_size, "exchange": product.exchange},
        dominant_rule={
            "version": rule.version,
            "metric": rule.metric,
            "tie_break": rule.tie_break,
            "monotone_delivery": rule.monotone_delivery,
            "information_rule": "只使用严格早于目标交易日的日频面板；喂入当日数据必须报错",
        },
        targets=target_records,
        control_contracts=control_contracts,
        datasets=datasets,
        coverage={
            "trading_days_built": len(summaries),
            "ticks_read": sum(s["n_ticks"] for s in summaries),
            "contracts_seen": len(set(panel.column("contract").to_pylist())),
            "dominant_contracts": len(
                {c for c in dominant.column("contract").to_pylist() if c}
            ),
            "roll_days": int(
                pc.sum(pc.cast(dominant.column("is_roll"), pa.int32())).as_py() or 0
            ),
        },
        findings=findings,
        assumptions=ASSUMPTIONS,
        blockers=BLOCKERS,
    )
    manifest_path = os.path.join(manifest_dir, f"{product.product}_temporal_spine.json")
    write_spine_manifest(manifest, manifest_path)
    print(f"wrote {manifest_path} (fingerprint {manifest.fingerprint[:16]})")

    spine_replay(
        config_path,
        manifest_fingerprint=manifest.fingerprint,
        cls_series=cls_series,
        brent_series=brent_series,
        pm_series=pm_series,
    )

    failed = [f for f in findings if f.severity == Severity.ERROR]
    if failed:
        print(f"QUALITY GATE FAILED: {[f.code for f in failed]}")
        return 2
    return 0


def _combine(digests: list[str]) -> str:
    from .manifest import combine_digests

    return combine_digests(digests)


def spine_replay(
    config_path: str,
    *,
    manifest_fingerprint: str | None = None,
    cls_series: PitSeries | None = None,
    brent_series: PitSeries | None = None,
    pm_series: PitSeries | None = None,
) -> int:
    cfg = load_config(config_path)
    product = PRODUCTS[cfg["product"]]
    data_dir = cfg["output"]["data_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    spec = TARGET_SPECS[0]
    target_path = os.path.join(data_dir, f"target_{spec.name}.parquet")
    rows = pq.read_table(target_path).to_pylist()

    if manifest_fingerprint is None:
        with open(
            os.path.join(manifest_dir, f"{product.product}_temporal_spine.json"), encoding="utf-8"
        ) as f:
            manifest_fingerprint = json.load(f)["fingerprint"]

    if cls_series is None:
        cls_manifest = load_manifest(cfg["inputs"]["cls_manifest"])
        cls_series = PitSeries(
            name="cls_telegraph",
            table=pq.read_table(os.path.join(cfg["output"]["controls_dir"], "cls.parquet")),
            manifest=cls_manifest,
        )
    if brent_series is None:
        brent_series = load_brent_series(
            cfg["controls"]["brent_csv"], start=date(1990, 1, 1), end=date(2100, 1, 1)
        )
    if pm_series is None:
        pm_series = load_pm_registry_series(
            cfg["controls"]["pm_registry"], product=cfg["controls"]["pm_product"]
        )

    daily = pads.dataset(os.path.join(data_dir, "bars_daily"), format="parquet").to_table(
        columns=["contract", "trading_day", "close", "volume", "available_time"]
    )
    daily_by_contract: dict[str, PitSeries] = {}
    bar_calendar = TradingCalendar.from_yyyymmdd(
        sorted({int(d) for d in daily.column("trading_day").to_pylist()}), source="bars_daily"
    )

    def daily_probe(row):
        contract = row["contract"]
        if contract not in daily_by_contract:
            sub = daily.filter(pc.equal(daily.column("contract"), contract)).sort_by(
                [("available_time", "ascending")]
            )
            daily_by_contract[contract] = PitSeries(name="sc_bars_daily", table=sub)
        got = asof_last(daily_by_contract[contract], row["decision_time"], ["trading_day", "close"])
        if got is None:
            return None
        return {
            "availability_time": got["available_time"],
            "trading_day": got["trading_day"],
            "close": got["close"],
        }

    def minute_probe(row):
        day_key = str(row["trading_day"])
        day = date(int(day_key[:4]), int(day_key[4:6]), int(day_key[6:]))
        keys = [day_key]
        prev = bar_calendar.prev_or_none(day)
        if prev:
            keys.insert(0, prev.strftime("%Y%m%d"))
        tables = []
        for k in keys:
            path = os.path.join(data_dir, "bars_1min", f"{k}.parquet")
            if not os.path.exists(path):
                continue
            t = pq.read_table(path)
            sub = t.filter(pc.equal(t.column("contract"), row["contract"]))
            if sub.num_rows:
                tables.append(sub)
        if not tables:
            return None
        table = pa.concat_tables(tables).sort_by([("available_time", "ascending")])
        series = PitSeries(name="sc_bars_1min", table=table)
        got = asof_last(series, row["decision_time"], ["bar_start", "close", "session_name"])
        if got is None:
            return None
        return {
            "availability_time": got["available_time"],
            "bar_start": got["bar_start"].isoformat(),
            "close": got["close"],
            "session_name": got["session_name"],
        }

    def cls_probe(row):
        got = asof_last(cls_series, row["decision_time"], ["Title", "Labels"])
        if got is None:
            return None
        title = (got["Title"] or "")[:40]
        return {
            "availability_time": got["available_time"],
            "title": title,
            "labels": (got["Labels"] or "")[:30],
        }

    def brent_probe(row):
        got = asof_last(brent_series, row["decision_time"], ["timestamp", "value"])
        if got is None:
            return None
        return {
            "availability_time": got["available_time"],
            "quote_date": got["timestamp"],
            "value": got["value"],
        }

    def pm_probe(row):
        got = asof_last(pm_series, row["decision_time"], ["slug", "theme"])
        if got is None:
            return None
        return {
            "availability_time": got["available_time"],
            "admitted_markets": count_before(pm_series, row["decision_time"]),
            "last_slug": got["slug"][:40],
            "theme": got["theme"],
        }

    probes = [
        ("sc_bar_1min_close", "commodity_tick", minute_probe),
        ("sc_bar_daily_close", "commodity_tick", daily_probe),
        ("cls_last_telegraph", "cls_telegraph", cls_probe),
        ("brent_last_close", "intl_brent", brent_probe),
        ("pm_admitted_markets", "pm_cn_registry_v3", pm_probe),
    ]

    seed = int(cfg["replay"]["seed"])
    size = int(cfg["replay"]["sample_size"])
    sampled = stratified_sample(rows, seed=seed, size=size)
    checklist = build_checklist(
        sampled,
        probes,
        seed=seed,
        size=size,
        spine_fingerprint=manifest_fingerprint,
        target_name=spec.name,
        product=product.product,
    )
    json_path = os.path.join(manifest_dir, f"{product.product}_replay_checklist.json")
    md_path = os.path.join(manifest_dir, f"{product.product}_replay_checklist.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(checklist, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(checklist))
    print(f"wrote {json_path} and {md_path}")
    return 0


def spine_verify(config_path: str) -> int:
    """从已物化的 bar 重建目标并与 manifest 中的指纹比对（出口条件 1 的证明）。"""
    cfg = load_config(config_path)
    product = PRODUCTS[cfg["product"]]
    data_dir = cfg["output"]["data_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    with open(
        os.path.join(manifest_dir, f"{product.product}_temporal_spine.json"), encoding="utf-8"
    ) as f:
        manifest = json.load(f)

    ok = True
    dominant = pq.read_table(os.path.join(data_dir, "dominant.parquet"))
    calendar = TradingCalendar.from_yyyymmdd(
        sorted({int(d) for d in dominant.column("trading_day").to_pylist()}), source="dominant"
    )
    rebuilt = build_targets(
        data_dir, dominant, calendar, product=product, episode_grain=cfg["episode"]["grain"]
    )
    for record in manifest["targets"]:
        table = rebuilt.get(record["name"])
        if table is None:
            print(f"MISSING target {record['name']}")
            ok = False
            continue
        got = fingerprint_table(table)
        same = got == record["fingerprint"]
        ok = ok and same
        print(
            f"{record['name']}: rows={table.num_rows} fingerprint={'MATCH' if same else 'MISMATCH'}"
        )
        if not same:
            print(f"  expected {record['fingerprint']}\n  got      {got}")

    for ref in manifest["datasets"]:
        if not ref["path"].endswith(".parquet"):
            continue
        table = pq.read_table(ref["path"])
        if ref["name"] == "controls_cls":
            table = table.select(["natural_date"])
        got = fingerprint_table(table)
        same = got == ref["fingerprint"]
        ok = ok and same
        print(f"{ref['name']}: {'MATCH' if same else 'MISMATCH'}")
    return 0 if ok else 1
