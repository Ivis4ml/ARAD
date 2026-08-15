"""序列重合度：机制族与它的词汇前身到底有多不同（M16）。

这个测量决定两件事，因此必须先于它们做：

1. 机制族的检验能不能算作新问题（若与前身高度重合，那是同一次检验的重放，
   既不该另开分母，也不该重测 run26 已经读过的目标）；
2. 重合度低到什么程度才算「不是改名」。

判据全部取自 Polymarket 一侧，与期货结果无关，因此**不占检验分母**，
与资格筛（QUALIFICATION_RULE）是同一条声明。

统计量刻意不用线性相关：这里要回答的是「两条序列是不是同一个东西」，
序数一致比例与符号一致比例对量纲与异常值都不敏感，且不使用任何效应字段名。
在 `dp`（构成受控的重定价分量）与 `p`（电平）上各算一遍：实测词汇族日度 Δp 方差的
九成来自构成移动，只在 p 上算重合度会把构成噪声当成机制差异，使门恒开。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

OVERLAP_RULE = {
    "version": "series-overlap-v1",
    "pair_samples": 200_000,
    "seed": 0,
    "min_common_buckets": 100,
    "quantile_bins": 10,
    "note": (
        "序数一致比例 = 随机抽取的两个时点上，两条序列给出同向排序的比例，"
        "0.5 为无关联、1.0 为完全同序。符号一致比例只在两条序列同时非零处计。"
        "全部判据只用 Polymarket 侧序列，不占检验分母。"
    ),
}


def _rank_agreement(a: list[float], b: list[float], *, samples: int, seed: int) -> float:
    rng = random.Random(seed)
    n = len(a)
    if n < 2:
        return float("nan")
    agree = total = 0
    for _ in range(samples):
        i = rng.randrange(n)
        j = rng.randrange(n)
        if i == j:
            continue
        da, db = a[i] - a[j], b[i] - b[j]
        if da == 0 or db == 0:
            continue
        total += 1
        if (da > 0) == (db > 0):
            agree += 1
    return agree / total if total else float("nan")


def _sign_agreement(a: list[float], b: list[float]) -> float:
    pairs = [(x, y) for x, y in zip(a, b, strict=True) if x != 0 and y != 0]
    if not pairs:
        return float("nan")
    return sum(1 for x, y in pairs if (x > 0) == (y > 0)) / len(pairs)


def _quantile_overlap(a: list[float], b: list[float], bins: int) -> float:
    def bucketise(xs: list[float]) -> list[int]:
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        out = [0] * len(xs)
        for rank, idx in enumerate(order):
            out[idx] = min(bins - 1, rank * bins // len(xs))
        return out
    if len(a) < bins:
        return float("nan")
    qa, qb = bucketise(a), bucketise(b)
    return sum(1 for x, y in zip(qa, qb, strict=True) if x == y) / len(a)


def _load(series_path: str, *, date_max: str | None) -> dict[str, dict[int, dict]]:
    table = pq.read_table(series_path)
    out: dict[str, dict[int, dict]] = defaultdict(dict)
    for fid, bucket, p, dp, notional in zip(
        table.column("family_id").to_pylist(),
        table.column("bucket_end").to_pylist(),
        table.column("p").to_pylist(),
        table.column("dp").to_pylist(),
        table.column("notional").to_pylist(), strict=True,
    ):
        day = bucket.date().isoformat()
        if date_max is not None and day > date_max:
            continue
        out[fid][int(bucket.timestamp())] = {"p": p, "dp": dp, "notional": notional}
    return out


def compare(left: dict[int, dict], right: dict[int, dict], field: str) -> dict:
    common = sorted(set(left) & set(right))
    a = [left[t][field] for t in common]
    b = [right[t][field] for t in common]
    keep = [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]
    if len(keep) < OVERLAP_RULE["min_common_buckets"]:
        return {"common_buckets": len(keep), "insufficient": True}
    xs = [x for x, _ in keep]
    ys = [y for _, y in keep]
    return {
        "common_buckets": len(keep),
        "rank_agreement_share": round(_rank_agreement(
            xs, ys, samples=OVERLAP_RULE["pair_samples"], seed=OVERLAP_RULE["seed"]), 4),
        "sign_agreement_share": round(_sign_agreement(xs, ys), 4),
        "quantile_overlap_share": round(_quantile_overlap(
            xs, ys, OVERLAP_RULE["quantile_bins"]), 4),
    }


def decision_grid(target_path: str, *, date_max: str) -> list[int]:
    """SC 在 discovery 段的决策时点（epoch 秒）。

    决策时点是**开盘前 60 秒**（日盘 08:59、夜盘 20:59），15:00 与 02:30 是 label_end。
    因此窗口长 21600 秒、offset 取 0 时，窗口整体落在停市区间；加 offset 反而推进交易时段。
    """
    table = pq.read_table(target_path, columns=["decision_time", "sample_segment"])
    out = []
    for ts, seg in zip(table.column("decision_time").to_pylist(),
                       table.column("sample_segment").to_pylist(), strict=True):
        if seg != "discovery":
            continue
        if ts.date().isoformat() > date_max:
            continue
        out.append(int(ts.timestamp()))
    return sorted(out)


def window_values(series: dict[int, dict], grid: list[int], *,
                  window_seconds: int, field: str) -> list[float | None]:
    """每个决策时点上，窗口内该字段的成交额加权均值（严格早于决策时点）。"""
    buckets = sorted(series)
    out: list[float | None] = []
    for t in grid:
        lo = t - window_seconds
        num = den = 0.0
        for b in buckets:
            if b <= lo:
                continue
            if b >= t:
                break
            value = series[b][field]
            weight = series[b]["notional"] or 0.0
            if value is None or weight <= 0:
                continue
            num += value * weight
            den += weight
        out.append(num / den if den > 0 else None)
    return out


def compare_on_grid(left: dict[int, dict], right: dict[int, dict], grid: list[int], *,
                    window_seconds: int, field: str) -> dict:
    a = window_values(left, grid, window_seconds=window_seconds, field=field)
    b = window_values(right, grid, window_seconds=window_seconds, field=field)
    keep = [(x, y) for x, y in zip(a, b, strict=True) if x is not None and y is not None]
    if len(keep) < 30:
        return {"both_defined_points": len(keep), "insufficient": True}
    xs = [x for x, _ in keep]
    ys = [y for _, y in keep]
    return {
        "grid_points": len(grid),
        "left_defined_points": sum(1 for x in a if x is not None),
        "right_defined_points": sum(1 for x in b if x is not None),
        "both_defined_points": len(keep),
        "rank_agreement_share": round(_rank_agreement(
            xs, ys, samples=OVERLAP_RULE["pair_samples"], seed=OVERLAP_RULE["seed"]), 4),
        "quantile_overlap_share": round(_quantile_overlap(
            xs, ys, OVERLAP_RULE["quantile_bins"]), 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", default="data/pm_series/mechanism_hourly_discovery.parquet")
    ap.add_argument("--mech-manifest",
                    default="artifacts/manifests/pm_mechanism_families.json")
    ap.add_argument("--out", default="artifacts/manifests/pm_family_series_overlap.json")
    ap.add_argument("--date-max", default="2024-12-31")
    ap.add_argument("--target", default="data/spine/sc/target_sc_rv_next_session.parquet")
    ap.add_argument("--window-seconds", type=int, default=21_600)
    args = ap.parse_args()

    series = _load(args.series, date_max=args.date_max)
    grid = decision_grid(args.target, date_max=args.date_max)
    manifest = json.loads(Path(args.mech_manifest).read_text(encoding="utf-8"))

    pairs: dict[str, dict] = {}
    for fam, info in manifest["families"].items():
        pred = info.get("lexical_predecessor")
        left, right = f"mech:{fam}", pred
        if pred is None or left not in series or right not in series:
            pairs[fam] = {"skipped": "序列缺失", "lexical_predecessor": pred}
            continue
        pairs[fam] = {
            "lexical_predecessor": pred,
            "shared_discovery_markets": info.get("shared_discovery_markets"),
            "mechanism_discovery_markets": info.get("mechanism_discovery_markets"),
            "predecessor_total_markets": info.get("predecessor_total_markets"),
            "on_repricing": compare(series[left], series[right], "dp"),
            "on_level": compare(series[left], series[right], "p"),
            "on_decision_grid": compare_on_grid(
                series[left], series[right], grid,
                window_seconds=args.window_seconds, field="p"),
        }

    # 参照系：机制族之间两两比较，给出「本来就不同的两条序列」长什么样。
    mech_ids = sorted(k for k in series if k.startswith("mech:"))
    reference: list[dict] = []
    for i, a in enumerate(mech_ids):
        for b in mech_ids[i + 1:]:
            got = compare(series[a], series[b], "dp")
            if not got.get("insufficient"):
                reference.append({"left": a, "right": b, "on_repricing": got})

    # 判据的阈值不是手挑的，取自参照分布本身：无关机制族两两的序数一致比例上界
    # 就是「两条序列本来就不同」能达到的最高值，与地板 E_2(n) 取自极大值分布是同一个道理。
    ref_values = [r["on_repricing"]["rank_agreement_share"] for r in reference]
    distinct_upper = round(max(ref_values), 3) if ref_values else None
    replay_lower = round((distinct_upper + 1.0) / 2, 3) if distinct_upper else None
    for fam, row in pairs.items():
        gd = row.get("on_decision_grid") if not row.get("skipped") else None
        if not gd or gd.get("insufficient") or distinct_upper is None:
            row["verdict"] = "undetermined"
            continue
        got = gd["rank_agreement_share"]
        row["verdict"] = (
            "distinct_object" if got <= distinct_upper
            else "replay_of_predecessor" if got > replay_lower
            else "partially_overlapping")

    doc = {
        "rule": OVERLAP_RULE,
        "thresholds": {
            "distinct_upper": distinct_upper,
            "replay_lower": replay_lower,
            "derivation": (
                "distinct_upper 取参照分布（无关机制族两两）的序数一致比例上界；"
                "replay_lower 取 distinct_upper 与 1.0 的中点。两者都由数据的参照分布"
                "决定，不由本次结果决定。判据作用在决策网格上的窗口取值，"
                "因为那才是特征真正看到的量。"
            ),
            "consequence": (
                "distinct_object：与前身在决策网格上不可区分于无关序列，"
                "可作为新问题对待；partially_overlapping：并入既有族分母，不另起地板；"
                "replay_of_predecessor：同一次检验的重放，既不另开分母也不重测已读过的目标。"
            ),
        },
        "built_at": datetime.now(tz=UTC).isoformat(),
        "series": os.path.basename(args.series),
        "segment": f"discovery (≤{args.date_max})",
        "decision_grid": {
            "points": len(grid),
            "window_seconds": args.window_seconds,
            "offset_seconds": 0,
            "note": ("决策时点为开盘前 60 秒（日盘 08:59、夜盘 20:59）；"
                     "offset 取 0 时该窗口整体落在停市区间。"),
        },
        "mechanism_vs_lexical_predecessor": pairs,
        "reference_unrelated_mechanism_pairs": reference,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    print(f"{'family':22s} {'前身':16s} {'重定价桶':>8s} {'序数一致':>8s} "
          f"{'符号一致':>8s} | {'电平序数':>8s}")
    for fam, row in pairs.items():
        if row.get("skipped"):
            print(f"{fam:22s} {row.get('lexical_predecessor')} 跳过：{row['skipped']}")
            continue
        rp, lv = row["on_repricing"], row["on_level"]
        if rp.get("insufficient"):
            print(f"{fam:22s} {row['lexical_predecessor']:16s} "
                  f"共同桶仅 {rp['common_buckets']}，样本不足")
            continue
        gd = row["on_decision_grid"]
        gd_txt = ("样本不足" if gd.get("insufficient")
                  else f"{gd['rank_agreement_share']:.3f}（{gd['both_defined_points']} 点）")
        print(f"{fam:22s} {row['lexical_predecessor']:16s} {rp['common_buckets']:8d} "
              f"{rp['rank_agreement_share']:8.3f} {rp['sign_agreement_share']:8.3f} | "
              f"{lv.get('rank_agreement_share', float('nan')):8.3f} | 决策网格 {gd_txt} "
              f"| {row['verdict']}")
    if reference:
        vals = [r["on_repricing"]["rank_agreement_share"] for r in reference]
        print(f"\n参照（无关机制族两两，共 {len(reference)} 对）序数一致比例："
              f"中位 {sorted(vals)[len(vals)//2]:.3f}，"
              f"区间 [{min(vals):.3f}, {max(vals):.3f}]")
    print(f"\n→ {args.out}")


if __name__ == "__main__":
    main()
