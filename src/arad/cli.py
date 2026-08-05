"""ARAD 命令行入口。

M1: `python -m arad.cli data-audit [--config configs/data_sources.yaml] [--out artifacts/manifests]`
只读扫描三个数据源，生成机器 manifest 与人类审计报告。不解压、不物化、不回测。
"""

from __future__ import annotations

import argparse
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
    args = parser.parse_args(argv)
    if args.cmd == "data-audit":
        return data_audit(args.config, args.out)
    return 1


if __name__ == "__main__":
    sys.exit(main())
