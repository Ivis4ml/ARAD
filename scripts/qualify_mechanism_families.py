"""机制族的资格筛：**只在 discovery 段上统计**（M17）。

现行的 `qualify_pm_families.py` 对全档案统计。对机制族沿用它会出一个具体的错：
霍尔木兹类族在 discovery 段一个成员都没有，却能靠 2025-26 年的成交额通过资格筛，
于是进了搜索菜单，而模型在 discovery 段引用它时特征处处无定义。
资格筛要回答的是「这个族在**将要被检验的那一段**上有没有信息流」。

阈值沿用 qualify-v1 的四道，只是统计窗口换成 discovery，并输出敏感性曲线：
阈值本身是声明，不是发现，改了就换版本号。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.harness.pm_menu import unresolvedness
from arad.temporal.episode import DISCOVERY_END

MECH_QUALIFICATION_RULE = {
    "version": "qualify-mech-v1",
    "segment": "discovery",
    "min_span_days": 180,
    "min_buckets": 500,
    "min_mean_unresolved": 0.02,
    "min_notional_usdc": 50_000.0,
    "note": (
        "与 qualify-v1 同样的四道阈值，统计窗口限定在 discovery 段。"
        "限定窗口是必要的：族在 2025-26 年的活跃度不能替它在 discovery 段的"
        "可求值性作保。"
    ),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="data/pm_series/mechanism_hourly_discovery.parquet")
    ap.add_argument("--out", default="artifacts/manifests/pm_mechanism_qualification.json")
    ap.add_argument("--prefix", default="mech:")
    args = ap.parse_args()

    table = pq.read_table(args.series)
    rows: dict[str, list] = defaultdict(list)
    for fid, bucket, p, notional in zip(
        table.column("family_id").to_pylist(),
        table.column("bucket_end").to_pylist(),
        table.column("p").to_pylist(),
        table.column("notional").to_pylist(), strict=True,
    ):
        if bucket.date() > DISCOVERY_END:
            continue
        rows[fid].append((bucket, p, notional))

    stats: dict[str, dict] = {}
    for fid, items in rows.items():
        if not fid.startswith(args.prefix):
            continue
        items.sort(key=lambda r: r[0])
        ps = [p for _, p, _ in items if p is not None]
        span = (items[-1][0] - items[0][0]).days if len(items) > 1 else 0
        stats[fid] = {
            "buckets": len(items),
            "span_days": span,
            "from": items[0][0].isoformat(),
            "to": items[-1][0].isoformat(),
            "notional": sum((n or 0.0) for _, _, n in items),
            "mean_unresolved": unresolvedness(ps),
        }

    rule = MECH_QUALIFICATION_RULE
    qualified = sorted(
        fid for fid, s in stats.items()
        if s["span_days"] >= rule["min_span_days"]
        and s["buckets"] >= rule["min_buckets"]
        and s["mean_unresolved"] >= rule["min_mean_unresolved"]
        and s["notional"] >= rule["min_notional_usdc"]
    )

    # 敏感性：每一道阈值单独放松/收紧时，通过的族数怎么变。
    sensitivity = {}
    for key, values in (
        ("min_buckets", [100, 250, 500, 1000, 2000]),
        ("min_span_days", [30, 90, 180, 365]),
        ("min_mean_unresolved", [0.005, 0.01, 0.02, 0.05]),
        ("min_notional_usdc", [1e3, 1e4, 5e4, 2e5]),
    ):
        curve = {}
        for value in values:
            probe = {**rule, key: value}
            curve[str(value)] = sum(
                1 for s in stats.values()
                if s["span_days"] >= probe["min_span_days"]
                and s["buckets"] >= probe["min_buckets"]
                and s["mean_unresolved"] >= probe["min_mean_unresolved"]
                and s["notional"] >= probe["min_notional_usdc"]
            )
        sensitivity[key] = curve

    doc = {
        "rule": rule,
        "built_at": datetime.now(tz=UTC).isoformat(),
        "families": stats,
        "qualified": qualified,
        "threshold_sensitivity": sensitivity,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    Path(args.out).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{'family':26s} {'桶':>7s} {'跨度天':>7s} {'未决性':>7s} {'名义额':>14s}  资格")
    for fid, s in sorted(stats.items()):
        print(f"{fid:26s} {s['buckets']:7d} {s['span_days']:7d} "
              f"{s['mean_unresolved']:7.3f} {s['notional']:14,.0f}  "
              f"{'通过' if fid in qualified else '不通过'}")
    print(f"\n合格 {len(qualified)}/{len(stats)} → {args.out}")


if __name__ == "__main__":
    main()
