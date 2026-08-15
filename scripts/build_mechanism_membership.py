"""编译机制族成员表（M16）。

产物：
  data/pm_index/mechanism_membership.parquet   成员（含极性、首笔成交、归段）
  data/pm_index/mechanism_excluded.parquet     被排除者（含理由，规则的盲区在此可核）
  artifacts/manifests/pm_mechanism_families.json  规则集内容指纹与逐族统计

同时给出每个机制族的**词汇前身**：在 discovery 段包含其成员最多的那个 `cand:` 族。
前身不是人挑的，是按成员重合算出来的；它是后续序列重合度测量的对照方。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.data_catalog.pm_mechanism_families import (
    MECHANISM_RULE_VERSION,
    compile_membership,
    load_rules,
    rules_content_id,
)
from arad.data_catalog.pm_text_corpus import slug_tokens
from arad.temporal.episode import DISCOVERY_END, HISTORICAL_VALIDATION_END


def lexical_predecessors(
    market_text_path: str, families_manifest: str, membership,
) -> dict[str, dict]:
    """每个机制族在 discovery 段的成员，最多落在哪个词汇族里。"""
    doc = json.loads(Path(families_manifest).read_text(encoding="utf-8"))
    # 词表倒排：1,998 个族逐个与 120 万个市场求交集是 24 亿次集合运算，
    # 按 token 建倒排后只需扫一遍市场。判据与 conditions_by_family 逐字相同。
    token_owners: dict[str, list[str]] = {}
    family_totals: Counter = Counter()
    for f in doc["families"]:
        if f.get("screened_out"):
            continue
        for tok in f["head_tokens"]:
            token_owners.setdefault(tok, []).append(f["family_id"])

    text = pq.read_table(market_text_path, columns=["condition_id", "slug_base"])
    owner: dict[str, list[str]] = {}
    for cid, slug_base in zip(text.column("condition_id").to_pylist(),
                              text.column("slug_base").to_pylist(), strict=True):
        hits: set[str] = set()
        for tok in slug_tokens(slug_base):
            hits.update(token_owners.get(tok, ()))
        if hits:
            owner[cid] = sorted(hits)
            for fid in hits:
                family_totals[fid] += 1

    out: dict[str, dict] = {}
    rows = membership.to_pylist()
    for fam in sorted({r["family_id"] for r in rows}):
        disc = [r["condition_id"] for r in rows
                if r["family_id"] == fam and r["first_trade_segment"] == "discovery"]
        counts: Counter = Counter()
        for cid in disc:
            for lex in owner.get(cid, []):
                counts[lex] += 1
        best, hit = (counts.most_common(1)[0] if counts else (None, 0))
        out[fam] = {
            "lexical_predecessor": best,
            "shared_discovery_markets": hit,
            "mechanism_discovery_markets": len(disc),
            "share_of_mechanism_in_predecessor": (hit / len(disc)) if disc else None,
            "predecessor_total_markets": (family_totals.get(best, 0) if best else 0),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-dir", default="configs/pm_mechanism_families")
    ap.add_argument("--market-text", default="data/pm_index/market_text.parquet")
    ap.add_argument("--market-presence", default="data/pm_index/market_presence.parquet")
    ap.add_argument("--families-manifest",
                    default="artifacts/manifests/pm_candidate_families.json")
    ap.add_argument("--out-dir", default="data/pm_index")
    ap.add_argument("--manifest",
                    default="artifacts/manifests/pm_mechanism_families.json")
    args = ap.parse_args()

    rules = load_rules(args.rules_dir)
    result = compile_membership(
        args.market_text, args.market_presence, rules,
        discovery_end=DISCOVERY_END, validation_end=HISTORICAL_VALIDATION_END,
        strict_unmatched_segment="discovery",
    )
    membership_path = os.path.join(args.out_dir, "mechanism_membership.parquet")
    excluded_path = os.path.join(args.out_dir, "mechanism_excluded.parquet")
    pq.write_table(result.membership, membership_path)
    pq.write_table(result.excluded, excluded_path)

    predecessors = lexical_predecessors(
        args.market_text, args.families_manifest, result.membership)

    excluded_rows = result.excluded.to_pylist()
    blind = Counter(
        r["family_id"] for r in excluded_rows
        if r["reason"] == "no_stage_matched" and r["first_trade_segment"] == "discovery")

    manifest = {
        "version": MECHANISM_RULE_VERSION,
        "content_id": rules_content_id(rules),
        "built_at": datetime.now(tz=UTC).isoformat(),
        "seed_pack": sorted({r.seed_pack for r in rules.values() if r.seed_pack}),
        "segments": {
            "discovery_end": DISCOVERY_END.isoformat(),
            "historical_validation_end": HISTORICAL_VALIDATION_END.isoformat(),
        },
        "membership_rows": result.membership.num_rows,
        "excluded_rows": result.excluded.num_rows,
        "discovery_blind_spots": dict(blind),
        "families": {
            fid: {
                **stats,
                "name_cn": rules[fid].name_cn,
                "mechanism_cn": rules[fid].mechanism_cn,
                "themes": list(rules[fid].themes),
                "expected_discovery_markets": rules[fid].expected_discovery_markets,
                "notes": rules[fid].notes,
                **predecessors.get(fid, {}),
            }
            for fid, stats in result.stats.items()
        },
        "rules": {fid: rules[fid].describe() for fid in sorted(rules)},
        "note": (
            "成员资格只由 slug 谓词与首笔公开成交定义，不引用任何期货结果，"
            "也不枚举 token 清单。规则在 discovery 段的提问语法上标定，"
            "该段盲区为零；2025-26 年语法分化，其他段的盲区如实计入 excluded。"
        ),
    }
    os.makedirs(os.path.dirname(args.manifest), exist_ok=True)
    with open(args.manifest, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"成员 {result.membership.num_rows} 行 → {membership_path}")
    print(f"排除 {result.excluded.num_rows} 行 → {excluded_path}")
    print(f"规则集指纹 {manifest['content_id'][:16]} → {args.manifest}")
    for fid, info in predecessors.items():
        print(f"  {fid:22s} 词汇前身 {info['lexical_predecessor']!s:18s} "
              f"覆盖 {info['shared_discovery_markets']}/{info['mechanism_discovery_markets']}")


if __name__ == "__main__":
    main()
