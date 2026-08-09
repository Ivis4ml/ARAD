"""扫描全量 PM 族小时表，产出资格名单与主题先验标注（M12）。

两个产物：
- artifacts/manifests/pm_family_qualification.json —— 资格筛（纯 PM 侧统计）
- artifacts/manifests/pm_theme_priors.json —— 事前经济映射（读 Alpha-Data
  tier_registry，只读；验证只用外部 ETF 证据，从未接触期货收益）
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pyarrow.compute as pc
import pyarrow.parquet as pq

from arad.harness.pm_menu import QUALIFICATION_RULE, qualify_families

ALL = "data/pm_series/family_hourly_all.parquet"
TIER = ("/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/"
        "data/polymarket/features/tier_registry.parquet")


def main() -> None:
    t = pq.read_table(ALL, columns=["family_id", "bucket_end", "p", "notional"])
    unresolved = pc.multiply(t.column("p"), pc.subtract(1.0, t.column("p")))
    t = t.append_column("unresolved", unresolved)
    g = (t.group_by("family_id")
          .aggregate([("bucket_end", "count"), ("bucket_end", "min"),
                      ("bucket_end", "max"), ("unresolved", "mean"),
                      ("notional", "sum")]))
    stats = {}
    for i in range(g.num_rows):
        fid = g.column("family_id")[i].as_py()
        lo = g.column("bucket_end_min")[i].as_py()
        hi = g.column("bucket_end_max")[i].as_py()
        mu = g.column("unresolved_mean")[i].as_py()
        stats[fid] = {
            "buckets": g.column("bucket_end_count")[i].as_py(),
            "span_days": (hi - lo).days if lo and hi else 0,
            "mean_unresolved": round(mu, 5) if mu is not None else None,
            "notional": round(g.column("notional_sum")[i].as_py() or 0.0, 1),
            "from": lo.isoformat() if lo else "",
        }
    out = qualify_families(stats)
    Path("artifacts/manifests/pm_family_qualification.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"族总数 {len(stats)} · 合格 {len(out['qualified'])} · "
          f"规则 {QUALIFICATION_RULE['version']}")

    # 主题先验：每主题取该主题下最强 tier（只在已建品种上看）与轴语义
    tt = pq.read_table(TIER, columns=["theme", "tier", "theme_axis"])
    agg: dict[tuple, int] = {}
    for i in range(tt.num_rows):
        key = (tt.column("theme")[i].as_py(), tt.column("tier")[i].as_py(),
               tt.column("theme_axis")[i].as_py())
        agg[key] = agg.get(key, 0) + 1
    tier_rows = [(k[0], k[1], k[2], v) for k, v in agg.items()]
    themes: dict[str, dict] = {}
    rank = {"primary": 0, "secondary": 1, "exploratory": 2}
    for theme, tier, axis, pairs in tier_rows:
        cur = themes.get(theme)
        if cur is None or rank.get(tier, 9) < rank.get(cur["tier"], 9):
            themes[theme] = {"tier": tier, "theme_axis": axis, "pairs": pairs}
    digest = hashlib.sha256(Path(TIER).read_bytes()).hexdigest()[:16]
    Path("artifacts/manifests/pm_theme_priors.json").write_text(json.dumps({
        "source": TIER,
        "source_sha256_16": digest,
        "provenance": ("Alpha-Data 扩展轮 P1 事前映射强度表：判定材料先于期货收益，"
                       "验证只用外部 ETF 证据（pre-2026 HAC），从未接触期货收益"),
        "themes": themes,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("主题先验:", {k: v["tier"] for k, v in sorted(themes.items())})


if __name__ == "__main__":
    main()
