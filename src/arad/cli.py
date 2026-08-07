"""ARAD 命令行入口。

M1: `python -m arad.cli data-audit [--config configs/data_sources.yaml] [--out artifacts/manifests]`
只读扫描三个数据源，生成机器 manifest 与人类审计报告。不解压、不物化、不回测。

M2: `python -m arad.cli spine build|replay|verify [--config configs/spine_sc.yaml]`
构建 SC 窄切片 Temporal Spine。bar 与控制视图写入 gitignored 的 `data/`，
manifest 与人工回放清单写入 `artifacts/manifests/`。

M2.5: `python -m arad.cli pm-index build [--config configs/pm_index.yaml]`
Polymarket 只读、label-blind 普查与 PIT Market Index。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import yaml

from .data_catalog import cls as cls_scanner
from .data_catalog import commodity as commodity_scanner
from .data_catalog import polymarket as pm_scanner
from .data_catalog.report import render
from .data_catalog.schema import write_manifest


def data_audit(config_path: str, out_dir: str) -> int:
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    os.makedirs(out_dir, exist_ok=True)

    manifests = []

    c = cfg["commodity_tick"]
    print("scanning commodity tick archives (central directories only)...", flush=True)
    m1 = commodity_scanner.scan(c["root"], c["layouts"])
    write_manifest(m1, os.path.join(out_dir, "commodity_tick.json"))
    manifests.append(m1)

    p = cfg["polymarket"]
    print("scanning polymarket parquet metadata...", flush=True)
    m2 = pm_scanner.scan(p["hf_daily_aligned"], p["extension_tape"], p["seam_date"])
    write_manifest(m2, os.path.join(out_dir, "polymarket_tape.json"))
    manifests.append(m2)

    n = cfg["cls"]
    print("scanning cls telegraph csv coverage...", flush=True)
    m3 = cls_scanner.scan(n["output_dir"], n["filename_pattern"], n.get("content_sample_files", 12))
    write_manifest(m3, os.path.join(out_dir, "cls_telegraph.json"))
    manifests.append(m3)

    report = render(manifests)
    report_path = os.path.join(out_dir, "audit_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"wrote {len(manifests)} manifests and {report_path}")

    failed = [m.source_id for m in manifests if not m.gate_passed()]
    if failed:
        print(f"QUALITY GATE FAILED for: {', '.join(failed)} (Study 只能 blocked)")
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="arad")
    sub = parser.add_subparsers(dest="cmd", required=True)
    audit = sub.add_parser("data-audit", help="只读扫描三源并生成 manifest 与审计报告")
    audit.add_argument("--config", default="configs/data_sources.yaml")
    audit.add_argument("--out", default="artifacts/manifests")

    spine = sub.add_parser("spine", help="SC 窄切片 Temporal Spine（M2）")
    spine_sub = spine.add_subparsers(dest="spine_cmd", required=True)
    for name, helptext in (
        ("build", "构建 bar、主力视图、目标与控制视图"),
        ("replay", "只重新生成人工回放清单"),
        ("verify", "从已物化 bar 重建目标并比对指纹"),
    ):
        p = spine_sub.add_parser(name, help=helptext)
        p.add_argument("--config", default="configs/spine_sc.yaml")
        if name == "build":
            p.add_argument("--force", action="store_true", help="忽略 sidecar 强制重建每一天")
            p.add_argument("--workers", type=int, default=None)
            p.add_argument("--limit-days", type=int, default=None, help="只构建最近 N 个交易日（冒烟用）")

    pmi = sub.add_parser("pm-index", help="Polymarket 只读普查与 PIT Market Index（M2.5）")
    pmi_sub = pmi.add_subparsers(dest="pm_cmd", required=True)
    pmb = pmi_sub.add_parser("build", help="普查、建索引、审计并生成 manifest")
    pmb.add_argument("--config", default="configs/pm_index.yaml")
    pmb.add_argument("--force", action="store_true")
    pmb.add_argument("--workers", type=int, default=None)
    pma = pmi_sub.add_parser("metadata-audit", help="文本元数据的 PIT 可证性审计（#12 取证）")
    pma.add_argument("--config", default="configs/pm_index.yaml")
    pmt = pmi_sub.add_parser("text-corpus", help="确定性文本语料与模板归纳（#12 第一层）")
    pmt.add_argument("--config", default="configs/pm_index.yaml")
    pms = pmi_sub.add_parser("series", help="候选族的 PIT 序列，使 pm_market 可求值（M5.2）")
    pms.add_argument("--config", default="configs/pm_index.yaml")
    pms.add_argument("--families-manifest",
                     default="artifacts/manifests/pm_candidate_families.json")
    pms.add_argument("--top", type=int, default=0, help="按成交量取前 N 个族")
    pms.add_argument("--include", default="cand:iran,cand:russia,cand:israel",
                     help="额外点名的族，逗号分隔")
    pms.add_argument("--bucket-seconds", type=int, default=3600)
    pms.add_argument("--out", default="data/pm_series/family_hourly.parquet")

    pmf = pmi_sub.add_parser("families", help="候选机制族归纳并登记为提案（#12 第二层）")
    pmf.add_argument("--config", default="configs/pm_index.yaml")
    pmf.add_argument("--ledger", default="data/ledger/arad.db")
    pmf.add_argument("--out", default="artifacts/manifests/pm_candidate_families.json")

    study = sub.add_parser("study", help="Study 账本与快照（M3）")
    study_sub = study.add_subparsers(dest="study_cmd", required=True)
    sd = study_sub.add_parser("demo", help="用真实 spine 数据走完一次判决并渲染快照")
    sd.add_argument("--ledger", default="data/ledger/arad.db")
    sd.add_argument("--target", default="data/spine/sc/target_sc_rv_next_session.parquet")
    sd.add_argument("--out", default="artifacts/manifests/study_snapshot_demo.md")
    sb = study_sub.add_parser("baseline", help="最小 Baseline Control：SC 自身波动持续性")
    sb.add_argument("--target", default="data/spine/sc/target_sc_rv_next_session.parquet")
    sb.add_argument("--segment", default="discovery")
    sb.add_argument("--out", default="artifacts/manifests/baseline_sc_rv_persistence.json")

    episode = sub.add_parser("episode", help="Search Episode 闭环（M4）")
    ep_sub = episode.add_subparsers(dest="episode_cmd", required=True)
    ed = ep_sub.add_parser("demo", help="在真实 SC 数据上跑一次 Episode 并渲染 Atlas")
    ed.add_argument("--ledger", default="data/ledger/episode_demo.db")
    ed.add_argument("--queue", default="data/ledger/episode_demo_queue.db")
    ed.add_argument("--target", default="data/spine/sc/target_sc_rv_next_session.parquet")
    ed.add_argument("--atlas", default="artifacts/atlas")
    ed.add_argument("--manifests", default="artifacts/manifests")
    ed.add_argument("--provider", default="mock", choices=("mock", "lineage", "claude"),
                    help="mock 走四种结局脚本；lineage 走一条五版演化链；"
                         "claude 真实调用 `claude -p`（花钱）")
    ed.add_argument("--model", default="claude-opus-5")

    svc = ep_sub.add_parser("service", help="连续研究：一轮接一轮直到边界或停滞（M6）")
    svc.add_argument("--ledger", default="data/ledger/service.db")
    svc.add_argument("--queue", default="data/ledger/service_queue.db")
    svc.add_argument("--target", default="data/spine/sc/target_sc_rv_next_session.parquet")
    svc.add_argument("--atlas", default="artifacts/atlas_service")
    svc.add_argument("--manifests", default="artifacts/manifests")
    svc.add_argument("--max-rounds", type=int, default=24)
    svc.add_argument("--runs", default="runs")
    svc.add_argument("--run-id", default=None)
    svc.add_argument("--provider", default="mutator", choices=("mutator", "claude"),
                     help="mutator 走确定性变异器；claude 让真实模型自主提案（花钱）")
    svc.add_argument("--model", default="claude-opus-5")

    atlas = sub.add_parser("atlas", help="Research Atlas 只读投影（M9）")
    atlas_sub = atlas.add_subparsers(dest="atlas_cmd", required=True)
    asv = atlas_sub.add_parser("serve", help="只读 API + 独立 app（只绑本机）")
    asv.add_argument("--runs", default="runs")
    asv.add_argument("--host", default="127.0.0.1")
    asv.add_argument("--port", type=int, default=8770)
    ar = atlas_sub.add_parser("render", help="从账本渲染静态站点")
    ar.add_argument("--ledger", default="data/ledger/arad.db")
    ar.add_argument("--queue", default=None, help="可选：读取 Research Service 状态")
    ar.add_argument("--family", default=None, help="只统计某个 experiment family 的分母")
    ar.add_argument("--out", default="artifacts/atlas")
    ar.add_argument("--manifests", default="artifacts/manifests")
    ar.add_argument("--runs", default=None,
                    help="同时把这次投影落成 runs/<id>/ 供独立 app 读取")
    ar.add_argument("--run-id", default=None)
    ar.add_argument("--renderer", default="react", choices=("react", "static"),
                    help="react：单页应用（含演化曲线）；static：服务端渲染的静态页")

    args = parser.parse_args(argv)
    if args.cmd == "data-audit":
        return data_audit(args.config, args.out)
    if args.cmd == "spine":
        from .temporal.pipeline import spine_build, spine_replay, spine_verify

        if args.spine_cmd == "build":
            return spine_build(
                args.config,
                force=args.force,
                workers=args.workers,
                limit_days=args.limit_days,
            )
        if args.spine_cmd == "replay":
            return spine_replay(args.config)
        return spine_verify(args.config)
    if args.cmd == "pm-index":
        from .temporal.pm_pipeline import (
            pm_index_build,
            pm_metadata_audit,
            pm_text_corpus,
        )

        if args.pm_cmd == "metadata-audit":
            return pm_metadata_audit(args.config)
        if args.pm_cmd == "text-corpus":
            return pm_text_corpus(args.config)
        if args.pm_cmd == "series":
            from .data_catalog.pm_series import (
                build_series,
                conditions_by_family,
                load_families,
            )

            with open(args.config, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            fams = load_families(
                args.families_manifest, top=args.top,
                include=tuple(x for x in args.include.split(",") if x),
            )
            memb = conditions_by_family(
                os.path.join(cfg["output"]["data_dir"], "market_text.parquet"), fams
            )
            table = build_series(cfg["source"]["roots"], memb,
                                 bucket_seconds=args.bucket_seconds)
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            import pyarrow.parquet as _pq

            _pq.write_table(table, args.out)
            print(json.dumps({
                "families": {f.family_id: len(memb[f.family_id]) for f in fams},
                "rows": table.num_rows,
                "bucket_seconds": args.bucket_seconds,
                "out": args.out,
            }, ensure_ascii=False, indent=2))
            return 0
        if args.pm_cmd == "families":
            from .temporal.pm_pipeline import pm_families

            return pm_families(args.config, args.ledger, args.out)
        return pm_index_build(args.config, force=args.force, workers=args.workers)
    if args.cmd == "study":
        if args.study_cmd == "baseline":
            from .evaluation.baseline import run_baseline

            result = run_baseline(args.target, segment=args.segment)
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                f.write("\n")
            print(json.dumps(
                {k: result[k] for k in
                 ("study_id", "inventory", "sample_segment", "coverage",
                  "effects", "blocked_reasons", "suggested_verdict")},
                ensure_ascii=False, indent=2, default=str))
            return 0
        from .memory.demo import run_demo

        result = run_demo(args.ledger, args.target, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "episode":
        if args.episode_cmd == "service":
            from .harness.demo import run_service_demo

            result = run_service_demo(
                ledger_path=args.ledger, queue_path=args.queue, target_path=args.target,
                atlas_dir=args.atlas, manifest_dir=args.manifests,
                max_rounds=args.max_rounds, runs_root=args.runs, run_id=args.run_id,
                provider_kind=args.provider, model=args.model,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            return 0
        from .harness.demo import run_episode_demo

        result = run_episode_demo(
            ledger_path=args.ledger, queue_path=args.queue, target_path=args.target,
            atlas_dir=args.atlas, manifest_dir=args.manifests,
            provider_kind=args.provider, model=args.model,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.cmd == "atlas":
        if args.atlas_cmd == "serve":
            from .atlas.server import serve

            serve(args.runs, host=args.host, port=args.port)
            return 0
        from .atlas.app import render_app
        from .atlas.project import project
        from .atlas.render import render_site
        from .atlas.sources import data_freshness
        from .memory.ledger import EvidenceLedger

        service = None
        if args.queue:
            from .orchestrator.queue import DurableQueue

            with DurableQueue(args.queue) as q:
                service = {**q.service_state(), "tasks": q.stats()}
        with EvidenceLedger(args.ledger) as ledger:
            projection = project(ledger, family=args.family, service=service)
            fresh = data_freshness(args.manifests)
            paths = (
                render_app(projection, args.out, freshness=fresh)
                if args.renderer == "react"
                else {**render_site(projection, args.out, freshness=fresh),
                      "renderer": "static"}
            )
        if args.runs:
            from datetime import UTC, datetime

            from .atlas.runs import write_run
            from .memory.ledger import Role as _Role

            run_id = args.run_id or datetime.now(UTC).strftime("run_%Y%m%d_%H%M%S")
            with EvidenceLedger(args.ledger) as led:
                events = led.read_events(role=_Role.HUMAN)
            paths["run"] = write_run(projection, args.runs, run_id,
                                     events=events, freshness=fresh)["run_id"]
        print(json.dumps({**paths, **projection.totals, "chain": projection.chain},
                         ensure_ascii=False, indent=2, default=str))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
