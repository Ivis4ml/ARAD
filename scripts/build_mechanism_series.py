"""把机制族成员折成小时序列，并同时折出各自的词汇前身作为对照（M16）。

两条序列用**同一份代码、同一套聚合口径**产出，唯一的差别是成员资格与极性。
这是「机制族与词汇族到底有多不同」这个问题能被回答的前提。

产物：data/pm_series/mechanism_hourly.parquet（family_id 形如 mech:ISR_IRAN 与 cand:iran）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pyarrow.parquet as pq
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.data_catalog.pm_series import build_mechanism_series
from arad.data_catalog.pm_text_corpus import slug_tokens


def lexical_membership(market_text_path: str, families_manifest: str,
                       wanted: set[str]) -> dict[str, dict[str, int]]:
    """对照族的成员，判据与 conditions_by_family 逐字相同，极性一律 +1。"""
    doc = json.loads(Path(families_manifest).read_text(encoding="utf-8"))
    tokens = {f["family_id"]: set(f["head_tokens"])
              for f in doc["families"] if f["family_id"] in wanted}
    out: dict[str, dict[str, int]] = {fid: {} for fid in tokens}
    text = pq.read_table(market_text_path, columns=["condition_id", "slug_base"])
    for cid, slug_base in zip(text.column("condition_id").to_pylist(),
                              text.column("slug_base").to_pylist(), strict=True):
        toks = set(slug_tokens(slug_base))
        if not toks:
            continue
        for fid, fam_tokens in tokens.items():
            if toks & fam_tokens:
                out[fid][cid] = 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/pm_index.yaml")
    ap.add_argument("--membership", default="data/pm_index/mechanism_membership.parquet")
    ap.add_argument("--mech-manifest",
                    default="artifacts/manifests/pm_mechanism_families.json")
    ap.add_argument("--market-text", default="data/pm_index/market_text.parquet")
    ap.add_argument("--families-manifest",
                    default="artifacts/manifests/pm_candidate_families.json")
    ap.add_argument("--out", default="data/pm_series/mechanism_hourly.parquet")
    ap.add_argument("--date-max", default=None,
                    help="只读该日期之前的分区（形如 2024-12-31），纯读取优化")
    ap.add_argument("--bucket-seconds", type=int, default=3600)
    ap.add_argument("--max-stale-seconds", type=int, default=86_400)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    roots = cfg["source"]["roots"]

    table = pq.read_table(args.membership)
    membership: dict[str, dict[str, int]] = {}
    for fid, cid, pol in zip(table.column("family_id").to_pylist(),
                             table.column("condition_id").to_pylist(),
                             table.column("polarity").to_pylist(), strict=True):
        membership.setdefault(f"mech:{fid}", {})[cid] = int(pol)

    mech_manifest = json.loads(Path(args.mech_manifest).read_text(encoding="utf-8"))
    predecessors = {
        info["lexical_predecessor"]
        for info in mech_manifest["families"].values()
        if info.get("lexical_predecessor")
    }
    membership.update(
        lexical_membership(args.market_text, args.families_manifest, predecessors))

    print(f"折 {len(membership)} 条序列（机制族 + 词汇前身）")
    for fid, members in sorted(membership.items()):
        print(f"  {fid:24s} {len(members)} 个成员市场")

    series = build_mechanism_series(
        roots, membership,
        bucket_seconds=args.bucket_seconds,
        max_stale_seconds=args.max_stale_seconds,
        date_max=args.date_max,
    )
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    pq.write_table(series, args.out)
    print(f"\n{series.num_rows} 行 → {args.out}")


if __name__ == "__main__":
    main()
