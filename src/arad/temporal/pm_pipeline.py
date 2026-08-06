"""M2.5 编排：只读普查 → PIT Market Index → 审计与 manifest。

不生成 PM tick × SC tick 的逐秒对齐表。本流水线只回答"在每个 SC 决策 cutoff 上，
按点时化规则有多少市场可用、能形成多少 PM 观测、成交集中度诊断如何"，
特征本身留待 Study 在其冻结的 cutoff 上按需生成。
"""

from __future__ import annotations

import collections
import glob
import json
import os
from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from ..data_catalog.pm_census import (
    CENSUS_VERSION,
    DIGEST_METHOD,
    Heartbeat,
    audit_duplicate_legs,
    audit_missing_venue_columns,
    audit_neg_risk_coverage,
    build_census,
    discover_partitions,
    file_digest,
    verify_artifact_integrity,
    verify_rebuild_determinism,
)
from ..data_catalog.pm_metadata_audit import (
    METADATA_AUDIT_VERSION,
    audit_metadata_provenance,
)
from ..data_catalog.pm_text_corpus import (
    CORPUS_VERSION,
    build_market_text,
    corpus_findings,
    coverage_curve,
)
from ..data_catalog.schema import QualityFinding, Severity, load_manifest
from .episode import SampleSegment, classify_segment
from .manifest import (
    DatasetRef,
    InputRef,
    SpineManifest,
    combine_digests,
    digest_json,
    fingerprint_table,
    write_spine_manifest,
)
from .pm_market_index import (
    PitMarketIndex,
    PitMarketIndexConfig,
    complete_days_before,
    kish_n_eff,
)

ASSUMPTIONS = [
    "市场存在性只由首笔公开成交决定；eligible_from = block_timestamp + 冻结的可得性延迟。",
    "流动性资格只由决策时点之前**已完整结束**的分区日计算，不参与成员资格判定。",
    "滚动名义额一律 provisional：两段 tape 都没有 venue/relay 列，中继腿无法剔除。",
    "不建立全局优质市场表；门槛由每个 Study 自行冻结后传入。",
    "接缝日（2026-04-28）在两段各有一个分区，同一 (日, 市场) 合并为一行后再计活跃天数。",
    "普查是 label-blind 的：resolution / winner / resolved_at 在读取层被拒绝。",
]

BLOCKERS = [
    (
        "两段 tape 都不含 venue_class / is_relay / protocol / exchange / tx_hash / log_index，"
        "relay 剔除与 unknown venue 隔离在现有数据上无法执行。M1 manifest 曾把这 7 个字段"
        "标为『仅扩展段』，与实测不符（两段**列名集合相同、均为 24 列**，但类型存在 "
        "15 处冲突），已作为 M1 缺陷记录。"
        "在补齐链上字段之前，一切名义额类指标只能作 provisional。"
    ),
    (
        "语义映射（地缘 / 能源 / 商品关联）不在本票范围：必须从原始市场标题、描述与"
        "创建时间构造版本化映射，另立票。在此之前 PM 侧没有可用的机制分组。"
    ),
    (
        "negRisk 成交在两段 tape 中都不存在（见 finding "
        "pm_census.neg_risk_absent_in_both_segments 的结构化证据）。按裁决 negRisk 回补"
        "与 2026-07-14 之后续爬不作为前置条件；只有普查证明缺口会阻断目标机制时，"
        "才单独申请 acquisition 授权。"
    ),
    (
        "抽样重复腿检出率见 finding pm_census.duplicate_legs_provisional 的结构化证据。"
        "缺 tx_hash / log_index，无法区分中继腿与真实重复成交，因此名义额类指标"
        "一律 provisional，且成员资格不得由名义额单独决定。"
    ),
]


_CODE_DIGEST_NOTE = "整包代码内容哈希：src/arad/**/*.py 加 pyproject.toml、uv.lock"


def _code_digest() -> str:
    """整个包的代码内容哈希加依赖锁，取代手写版本号与手列文件清单。

    手列依赖必然遗漏（manifest.py、timeguard.py、episode.py 都被本流水线间接依赖），
    因此直接哈希 `src/arad/**/*.py` 与 pyproject.toml、uv.lock。
    """
    import hashlib

    pkg = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo = os.path.dirname(os.path.dirname(pkg))
    paths = sorted(glob.glob(os.path.join(pkg, "**", "*.py"), recursive=True))
    for extra in ("pyproject.toml", "uv.lock"):
        candidate = os.path.join(repo, extra)
        if os.path.exists(candidate):
            paths.append(candidate)
    h = hashlib.sha256()
    for path in paths:
        h.update(os.path.relpath(path, repo).encode())
        with open(path, "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


def _input_refs(cfg: dict, pm_manifest, summaries: list[dict]) -> dict[str, InputRef]:
    """登记全部参与产物生成的输入，包括参照表与 SC 目标表。"""
    refs = {
        "polymarket_tape": InputRef(
            fingerprint=pm_manifest.fingerprint,
            source_snapshot_digest=(
                pm_manifest.source_snapshot.digest if pm_manifest.source_snapshot else ""
            ),
            scanner_version=pm_manifest.scanner_version,
        ),
        "polymarket_tape_partitions": InputRef(
            fingerprint=combine_digests([s["source_digest"] for s in summaries]),
            source_snapshot_digest=f"{DIGEST_METHOD}_per_partition",
            scanner_version=CENSUS_VERSION,
        ),
    }
    # 只登记**实际被消费**的输入。markets_clob 当前未被消费，登记它会造成
    # 虚假的依赖关系；它以 deferred_sources 形式记录，留给 Decision Map #12。
    for name, path in (
        ("asset_map", cfg["audit"]["asset_map"]),
        ("sc_target", cfg["sc"]["target_parquet"]),
    ):
        if path and os.path.exists(path):
            refs[name] = InputRef(
                fingerprint=file_digest(path), source_snapshot_digest=DIGEST_METHOD
            )
    return refs


def pm_metadata_audit(config_path: str) -> int:
    """#12 的取证阶段：只审计文本元数据的填充率与跨抓取可变性，不做语义判断。"""
    cfg = load_config(config_path)
    roots = dict(cfg["source"]["roots"])
    out_dir = cfg["output"]["data_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    pm_manifest = load_manifest(cfg["inputs"]["polymarket_manifest"])

    print("auditing market metadata provenance...", flush=True)
    findings, facts = audit_metadata_provenance(
        roots, out_dir, sample_partitions=int(cfg["audit"]["metadata_sample_partitions"])
    )
    manifest = SpineManifest(
        spine_id="pm-metadata-audit",
        code_version=f"metadata-audit-{METADATA_AUDIT_VERSION}/src-{_code_digest()}",
        config_digest=digest_json(cfg),
        inputs={
            "polymarket_tape": InputRef(
                fingerprint=pm_manifest.fingerprint,
                source_snapshot_digest=(
                    pm_manifest.source_snapshot.digest if pm_manifest.source_snapshot else ""
                ),
                scanner_version=pm_manifest.scanner_version,
            )
        },
        coverage=facts,
        findings=findings,
        assumptions=[
            (
                "本审计只看文本字段是否存在与是否变化，不做任何语义分类；"
                "分类法、金标样本与跨模型一致性审计属 Decision Map #12 的后续阶段。"
            ),
            (
                "市场级字段按 condition_id 归并，资产级字段按 asset_id 归并："
                "用错键会把同一市场的多个 outcome token 当成同一实体的多个取值。"
            ),
        ],
        blockers=[
            (
                "语义映射的可用文本受限于上述填充率与可变性结论；"
                "任何以完整 slug 为键的映射都会在市场改名后静默失配。"
            ),
        ],
    )
    path = os.path.join(manifest_dir, "pm_metadata_audit.json")
    write_spine_manifest(manifest, path)
    print(f"wrote {path} (fingerprint {manifest.fingerprint[:16]})")
    return 0 if manifest.gate_passed() else 2


def pm_text_corpus(config_path: str) -> int:
    """#12 自下而上第一层：确定性的文本语料与模板归纳，不使用任何模型。"""
    cfg = load_config(config_path)
    roots = dict(cfg["source"]["roots"])
    out_dir = cfg["output"]["data_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    pm_manifest = load_manifest(cfg["inputs"]["polymarket_manifest"])
    presence_path = os.path.join(out_dir, "market_presence.parquet")
    if not os.path.exists(presence_path):
        raise FileNotFoundError("缺少 market_presence.parquet；请先运行 pm-index build")

    hb = Heartbeat(os.path.join(out_dir, "_heartbeat.json")).start()
    market_text = build_market_text(roots, heartbeat=hb)
    text_path = os.path.join(out_dir, "market_text.parquet")
    pq.write_table(market_text, text_path)

    hb.stage("template_induction")
    presence = pq.read_table(presence_path, columns=["condition_id", "first_trade_ts"])
    curve = coverage_curve(
        market_text,
        presence,
        list(cfg["text"]["induction_cutoffs"]),
        int(cfg["text"]["min_markets_per_template"]),
    )
    findings = corpus_findings(market_text, curve)
    hb.stop()

    manifest = SpineManifest(
        spine_id="pm-text-corpus",
        code_version=f"text-corpus-{CORPUS_VERSION}/src-{_code_digest()}",
        config_digest=digest_json(cfg),
        inputs={
            "polymarket_tape": InputRef(
                fingerprint=pm_manifest.fingerprint,
                source_snapshot_digest=(
                    pm_manifest.source_snapshot.digest if pm_manifest.source_snapshot else ""
                ),
                scanner_version=pm_manifest.scanner_version,
            ),
            "market_presence": InputRef(
                fingerprint=file_digest(presence_path), source_snapshot_digest=DIGEST_METHOD
            ),
        },
        coverage={"coverage_curve": curve, "markets": market_text.num_rows},
        datasets=[
            DatasetRef(
                name="market_text",
                path=text_path,
                rows=market_text.num_rows,
                fingerprint=fingerprint_table(market_text),
            )
        ],
        findings=findings,
        assumptions=[
            (
                "机制族自下而上归纳（2026-08-05 人类裁决），不沿用旧系统的 8 个主题："
                "那 8 个主题是看过结果后写成的规则表，继承它等于继承选择偏差。"
            ),
            (
                "本层完全确定性、不使用任何模型。模板是语法层的候选分组，不是机制族；"
                "语义命名、跨模型一致性审计与金标裁决属后续阶段。"
            ),
            (
                "归纳期切点是冻结参数：用全史文本归纳分类法等于用后见的市场宇宙定义分组，"
                "因此每个版本记录 induction_cutoff 并实测期外覆盖率。"
            ),
        ],
        blockers=[
            (
                "机制族尚未命名：模板只是语法分组，市场→机制族与机制族→商品品种"
                "都还未定，PM 侧仍无可用的机制分族。"
            ),
        ],
    )
    path = os.path.join(manifest_dir, "pm_text_corpus.json")
    write_spine_manifest(manifest, path)
    print(f"wrote {path} (fingerprint {manifest.fingerprint[:16]})")
    return 0 if manifest.gate_passed() else 2


def pm_families(config_path: str, ledger_path: str, out_path: str) -> int:
    """#12 第二层：候选机制族归纳并登记为提案。命名与金标属后续阶段。"""
    from ..data_catalog.pm_entity_clusters import ClusterSpec
    from ..data_catalog.pm_family_proposals import register_families
    from ..data_catalog.pm_text_corpus import InductionSpec
    from ..memory.ledger import EvidenceLedger

    cfg = load_config(config_path)
    out_dir = cfg["output"]["data_dir"]
    text = pq.read_table(os.path.join(out_dir, "market_text.parquet"))
    presence = pq.read_table(
        os.path.join(out_dir, "market_presence.parquet"),
        columns=["condition_id", "first_trade_ts"],
    )
    totals = pq.read_table(os.path.join(out_dir, "market_totals.parquet"))
    families_cfg = cfg["families"]
    spec = ClusterSpec(
        induction=InductionSpec(
            families_cfg["induction_cutoff"],
            min_markets_per_template=int(cfg["text"]["min_markets_per_template"]),
        ),
        max_tokens=int(families_cfg["max_tokens"]),
        min_cooccurrence=int(families_cfg["min_cooccurrence"]),
        min_pmi=float(families_cfg["min_pmi"]),
        mutual_knn=int(families_cfg["mutual_knn"]),
        clustering=families_cfg["clustering"],
        resolution=float(families_cfg["resolution"]),
    )
    from ..data_catalog.pm_pipeline_variants import register_variants

    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with EvidenceLedger(ledger_path) as ledger:
        # 先记管线变体：被弃变体与最终族属于同一批探索，必须一起进分母
        report_variants = register_variants(ledger)
        report = register_families(
            ledger, text, presence, totals, spec,
            min_markets=int(families_cfg["min_markets"]),
        )
        report["pipeline_variants"] = report_variants
        report["ledger_events"] = ledger.require_intact()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")
    print(json.dumps(
        {"families_registered": report["families_registered"],
         "families_screened_out": report["families_screened_out"],
         "family_denominators": report["denominators"],
         "variants_recorded": report_variants["variants_recorded"],
         "variants_abandoned": report_variants["variants_abandoned"],
         "variant_denominators": report_variants["denominators"],
         "ledger_events": report["ledger_events"]},
        ensure_ascii=False, indent=2))
    return 0


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _segment_of(date_str: str) -> str:
    day = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
    return classify_segment(day, day + timedelta(days=1)).value


def segment_profile(summaries: list[dict]) -> dict:
    """按 ARAD 样本段汇总普查结果。段划分沿用 canonical plan，本票不改。"""
    agg: dict[str, dict] = {}
    for s in summaries:
        seg = _segment_of(s["date"])
        b = agg.setdefault(
            seg, {"partitions": 0, "trades": 0, "notional": 0.0, "neg_risk_markets": 0}
        )
        b["partitions"] += 1
        b["trades"] += s["trades"]
        b["notional"] += s["notional"]
        b["neg_risk_markets"] += s.get("neg_risk_markets", 0)
    total = sum(b["trades"] for b in agg.values()) or 1
    for b in agg.values():
        b["trade_share"] = b["trades"] / total
    return {s.value: agg.get(s.value) for s in SampleSegment if s.value in agg}


def _daily_market_sets(market_day: pa.Table) -> tuple[dict[str, set[int]], dict[str, int]]:
    """把逐 (日, 市场) 表压成 日 → 市场整数码集合，便于窗口并集计数。"""
    codes: dict[str, int] = {}
    by_day: dict[str, set[int]] = collections.defaultdict(set)
    dates = market_day.column("date").to_pylist()
    cids = market_day.column("condition_id").to_pylist()
    for d, c in zip(dates, cids):
        code = codes.get(c)
        if code is None:
            code = len(codes)
            codes[c] = code
        by_day[d].add(code)
    return by_day, codes


def observations_at_cutoffs(
    index: PitMarketIndex,
    cutoffs: list[datetime],
    *,
    lookback_days: int,
) -> tuple[pa.Table, dict]:
    """在每个 SC 决策 cutoff 上统计点时化可用市场数与近期有成交的市场数。"""
    by_day, _ = _daily_market_sets(index.market_day)
    presence = index.presence
    eligible_us = [int(t.timestamp() * 1_000_000) for t in presence.column("eligible_from").to_pylist()]

    rows = []
    for cutoff in cutoffs:
        cut = cutoff.astimezone(UTC)
        cut_us = int(cut.timestamp() * 1_000_000)
        # presence 已按 eligible_from 升序：二分即得存在市场数
        lo, hi = 0, len(eligible_us)
        while lo < hi:
            mid = (lo + hi) // 2
            if eligible_us[mid] < cut_us:
                lo = mid + 1
            else:
                hi = mid
        present = lo
        active: set[int] = set()
        for day in complete_days_before(cut, lookback_days):
            active |= by_day.get(day, set())
        rows.append(
            {
                "cutoff": cut,
                "markets_present": present,
                "markets_active_in_window": len(active),
            }
        )
    table = pa.table(
        {
            "cutoff": pa.array([r["cutoff"] for r in rows], pa.timestamp("us", tz="UTC")),
            "markets_present": pa.array([r["markets_present"] for r in rows], pa.int64()),
            "markets_active_in_window": pa.array(
                [r["markets_active_in_window"] for r in rows], pa.int64()
            ),
        }
    )
    active_counts = [r["markets_active_in_window"] for r in rows]
    summary = {
        "cutoffs": len(rows),
        "lookback_days": lookback_days,
        "cutoffs_with_zero_active_markets": sum(1 for n in active_counts if n == 0),
        "median_active_markets": sorted(active_counts)[len(active_counts) // 2]
        if active_counts
        else 0,
        "max_active_markets": max(active_counts) if active_counts else 0,
    }
    return table, summary


def trade_concentration(index: PitMarketIndex, cutoff_table: pa.Table) -> dict:
    """成交集中度，**不是**统计有效样本量。

    这里的 Kish 等价数只按成交笔数加权衡量集中度，没有考虑序列相关、Episode 或
    市场簇。真正的 n_eff 需要双向 cluster、HAC 与 block bootstrap，属评价机
    （Merge-Plan-2 §5.4，M3）范围。本字段只用于说明"逐笔行数远不是独立样本量"，
    不得直接用作任何功效计算的分母。
    """
    md = index.market_day
    per_market = collections.Counter()
    per_day = collections.Counter()
    for cid, day, trades in zip(
        md.column("condition_id").to_pylist(),
        md.column("date").to_pylist(),
        md.column("trades").to_pylist(),
    ):
        per_market[cid] += trades
        per_day[day] += trades
    nominal = sum(per_market.values())
    active = [
        n for n in cutoff_table.column("markets_active_in_window").to_pylist() if n > 0
    ]
    return {
        "nominal_trades": nominal,
        "distinct_markets": len(per_market),
        "distinct_utc_days": len(per_day),
        "kish_concentration_equivalent_over_markets": round(
            kish_n_eff(list(per_market.values())), 1
        ),
        "kish_concentration_equivalent_over_days": round(kish_n_eff(list(per_day.values())), 1),
        "sc_cutoffs_with_any_active_market": len(active),
        "is_effective_sample_size": False,
        "note": (
            "以上是按成交笔数加权的 Kish 集中度等价数，**不是**统计有效样本量："
            "未考虑序列相关、Episode 与市场簇。真正的 n_eff 需要双向 cluster、HAC 与 "
            "block bootstrap，属评价机（M3）范围。此处只说明逐笔行数远不是独立样本量。"
        ),
    }


def audit_asset_outcome_mapping(paths: list[str], asset_map_path: str) -> QualityFinding:
    """抽样核对 tape 的 (asset_id → condition_id, outcome_seq) 与 asset_map 是否一致。"""
    ref = pq.read_table(asset_map_path, columns=["asset_id", "condition_id", "outcome_seq"])
    ref_map = {
        a: (c, o)
        for a, c, o in zip(
            ref.column("asset_id").to_pylist(),
            ref.column("condition_id").to_pylist(),
            ref.column("outcome_seq").to_pylist(),
        )
    }
    checked = mismatched = unknown = 0
    for path in paths:
        t = pq.read_table(path, columns=["asset_id", "condition_id", "outcome_seq"])
        seen = set(
            zip(
                t.column("asset_id").to_pylist(),
                t.column("condition_id").to_pylist(),
                t.column("outcome_seq").to_pylist(),
            )
        )
        for asset, cond, seq in seen:
            checked += 1
            got = ref_map.get(asset)
            if got is None:
                unknown += 1
            elif got != (cond, seq):
                mismatched += 1
    return QualityFinding(
        severity=Severity.WARNING if (mismatched or unknown) else Severity.INFO,
        code="pm_census.asset_outcome_mapping",
        message="抽样核对 tape 的 asset→(市场, 结果序号) 映射与 asset_map.parquet",
        evidence={
            "sampled_partitions": len(paths),
            "distinct_triples_checked": checked,
            "mismatched": mismatched,
            "not_in_asset_map": unknown,
        },
    )


def pm_index_build(
    config_path: str, *, force: bool = False, workers: int | None = None
) -> int:
    cfg = load_config(config_path)
    roots = dict(cfg["source"]["roots"])
    out_dir = cfg["output"]["data_dir"]
    manifest_dir = cfg["output"]["manifest_dir"]
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(manifest_dir, exist_ok=True)

    hb = Heartbeat(os.path.join(out_dir, "_heartbeat.json")).start()
    print("census: streaming per-partition aggregation (label-blind)...", flush=True)
    summaries, findings = build_census(
        roots,
        out_dir,
        workers=workers or int(cfg["build"]["workers"]),
        force=force,
        heartbeat=hb,
    )

    hb.stage("indexing")
    print("building PIT market index...", flush=True)
    config = PitMarketIndexConfig(
        availability_delay_seconds=int(cfg["index"]["availability_delay_seconds"])
    )
    index = PitMarketIndex.from_census_dir(
        out_dir, config=config, expected_keys={s["key"] for s in summaries}
    )
    pq.write_table(index.presence, os.path.join(out_dir, "market_presence.parquet"))
    pq.write_table(index.asset_presence, os.path.join(out_dir, "asset_presence.parquet"))

    checked, bad = verify_artifact_integrity(out_dir, heartbeat=hb)
    findings.append(
        QualityFinding(
            severity=Severity.ERROR if bad else Severity.INFO,
            code="pm_census.artifact_integrity_verified",
            message=(
                "已物化产物与同次生成的 sidecar 指纹一致（产物完整性，"
                "不构成独立重建确定性证明）"
            ),
            evidence={"partitions_checked": checked, "mismatched": bad[:10],
                      "mismatched_count": len(bad)},
        )
    )
    r_checked, r_bad = verify_rebuild_determinism(
        roots, out_dir, sample=int(cfg["audit"]["determinism_sample"]), heartbeat=hb
    )
    findings.append(
        QualityFinding(
            severity=Severity.ERROR if r_bad else Severity.INFO,
            code="pm_census.rebuild_determinism_sampled",
            message="从来源独立重跑抽样分区，与已物化产物的逻辑指纹逐位比对",
            evidence={"partitions_rebuilt": r_checked, "mismatched": r_bad[:10],
                      "mismatched_count": len(r_bad)},
        )
    )

    hb.stage("auditing")
    print("auditing venue columns, duplicate legs and asset mapping...", flush=True)
    partitions = discover_partitions(roots)
    step = max(1, len(partitions) // int(cfg["audit"]["sample_partitions"]))
    sample_paths = [p for _, _, p in partitions[::step]][: int(cfg["audit"]["sample_partitions"])]
    findings.append(audit_missing_venue_columns(roots))
    dup = audit_duplicate_legs(sample_paths)
    findings.append(dup)
    findings.append(audit_neg_risk_coverage(summaries, int(dup.evidence.get("rows", 0))))
    findings.append(audit_asset_outcome_mapping(sample_paths, cfg["audit"]["asset_map"]))

    hb.stage("sc_cutoff_observations")
    print("counting observations at SC decision cutoffs...", flush=True)
    target_path = cfg["sc"]["target_parquet"]
    cutoff_table = None
    obs_summary: dict = {}
    n_eff: dict = {}
    if os.path.exists(target_path):
        targets = pq.read_table(target_path, columns=["decision_time"])
        cutoffs = targets.column("decision_time").to_pylist()
        cutoff_table, obs_summary = observations_at_cutoffs(
            index, cutoffs, lookback_days=int(cfg["index"]["lookback_days"])
        )
        pq.write_table(cutoff_table, os.path.join(out_dir, "sc_cutoff_observations.parquet"))
        n_eff = trade_concentration(index, cutoff_table)
    else:
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="pm_index.sc_targets_missing",
                message="未找到 SC 目标表，跳过按决策 cutoff 的观测数统计",
                evidence={"path": target_path},
            )
        )

    profile = segment_profile(summaries)
    findings.append(
        QualityFinding(
            severity=Severity.WARNING,
            code="pm_census.segment_concentration",
            message=(
                "Polymarket 逐笔在 ARAD 样本段之间极度不均衡；样本段划分按裁决不在本票修改，"
                "普查结果供后续按 Study Family 决定各机制的段划分"
            ),
            evidence={
                s: {"trades": v["trades"], "share": round(v["trade_share"], 5)}
                for s, v in profile.items()
            },
        )
    )

    pm_manifest = load_manifest(cfg["inputs"]["polymarket_manifest"])
    datasets = [
        {
            "name": "asset_presence",
            "path": os.path.join(out_dir, "asset_presence.parquet"),
            "rows": index.asset_presence.num_rows,
            "fingerprint": fingerprint_table(index.asset_presence),
        },
        {
            "name": "asset_day",
            "path": os.path.join(out_dir, "asset_day"),
            "rows": sum(s["assets"] for s in summaries),
            "partitions": len(summaries),
            "fingerprint": combine_digests(
                [s["fingerprint_asset_day"] for s in summaries]
            ),
            "note": "逐分区产物逻辑指纹的确定性合并（不是来源摘要）",
        },
        {
            "name": "market_day",
            "path": os.path.join(out_dir, "market_day"),
            "rows": sum(s["markets"] for s in summaries),
            "partitions": len(summaries),
            "fingerprint": combine_digests(
                [s["fingerprint_market_day"] for s in summaries]
            ),
            "note": "逐分区产物逻辑指纹的确定性合并（不是来源摘要）",
        },
        {
            "name": "market_presence",
            "path": os.path.join(out_dir, "market_presence.parquet"),
            "rows": index.presence.num_rows,
            "fingerprint": fingerprint_table(index.presence),
        },
    ]
    if cutoff_table is not None:
        datasets.append(
            {
                "name": "sc_cutoff_observations",
                "path": os.path.join(out_dir, "sc_cutoff_observations.parquet"),
                "rows": cutoff_table.num_rows,
                "fingerprint": fingerprint_table(cutoff_table),
            }
        )

    manifest = SpineManifest(
        spine_id="pm-market-index",
        code_version=f"census-{CENSUS_VERSION}/index-{config.version}/src-{_code_digest()}",
        config_digest=digest_json(cfg),
        inputs=_input_refs(cfg, pm_manifest, summaries),
        calendar={"utc_partitions": len(summaries)},
        session_table={"note": "PM 无交易时段概念；对齐由 SC 决策 cutoff 驱动"},
        dominant_rule=config.describe(),
        coverage={
            "index": index.facts(),
            "segments": profile,
            "sc_cutoff_observations": obs_summary,
            "trade_concentration": n_eff,
        },
        datasets=[DatasetRef(**d) for d in datasets],
        deprecated_sources=[
            {
                "source_id": "markets_clob",
                "root_uri": cfg["audit"].get("markets_clob", ""),
                "status": "deferred_not_consumed",
                "reason": (
                    "markets_clob 的 end_date_iso / game_start_time / tags 等字段没有"
                    "可证明的历史时点可见性，未经 PIT 审计；M2.5 的市场与资产身份完全"
                    "来自 tape 的首笔公开成交，不消费本表"
                ),
                "deferred_to": "Decision Map #12（Polymarket 市场语义映射）",
            }
        ],
        findings=findings,
        assumptions=ASSUMPTIONS,
        blockers=BLOCKERS,
    )
    path = os.path.join(manifest_dir, "pm_market_index.json")
    write_spine_manifest(manifest, path)
    hb.stop()
    print(f"wrote {path} (fingerprint {manifest.fingerprint[:16]})")
    return 0 if manifest.gate_passed() else 2
