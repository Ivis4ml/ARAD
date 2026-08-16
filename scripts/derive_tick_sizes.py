"""从 spine 分钟 bar 实测归纳各品种的最小价格增量（tick size）。

品种注册表只有 SC 带权威 tick_size（人工录入的合约规格），其余刻意为 None：
「在那之前不编造数字」。成本模型需要全品种的 tick size，因此按 M8.4 的路数
从数据归纳：取每品种最近若干天的分钟 close，收集相邻非零价差的绝对值，
取其最小值在多数天上的众数。归纳值与 SC 权威值的一致性作为方法的自检。

输出 configs/tick_sizes_derived.json（数据事实，带方法与样本量标注）。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from itertools import pairwise
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pyarrow.parquet as pq

SPINE = Path("data/spine")
DAYS = 20            # 每品种取最近 20 个交易日足够：一天内价差样本上千
EPS = 1e-9


def derive(product: str) -> dict | None:
    bars_dir = SPINE / product / "bars_1min"
    if not bars_dir.is_dir():
        return None
    days = sorted(bars_dir.glob("*.parquet"))[-DAYS:]
    if not days:
        return None
    per_day_min: list[float] = []
    for day in days:
        closes = pq.read_table(day, columns=["close"]).column("close").to_pylist()
        diffs = sorted({round(abs(a - b), 6)
                        for a, b in pairwise(closes)
                        if a is not None and b is not None and abs(a - b) > EPS})
        if diffs:
            per_day_min.append(diffs[0])
    if not per_day_min:
        return None
    tick, votes = Counter(per_day_min).most_common(1)[0]
    return {"tick_size": tick, "days_sampled": len(per_day_min),
            "days_agreeing": votes}


def main() -> None:
    out: dict[str, dict] = {}
    for pdir in sorted(SPINE.iterdir()):
        if not (pdir / "bars_1min").is_dir():
            continue
        row = derive(pdir.name)
        if row:
            out[pdir.name] = row
    # 自检：sc 的归纳值必须与权威值一致，否则方法本身不可信
    sc = out.get("sc", {}).get("tick_size")
    assert sc == 0.1, f"sc 归纳值 {sc} 与权威值 0.1 不符，方法不可信"
    payload = {
        "method": ("每品种最近 20 个交易日分钟 close 的相邻非零价差绝对值，"
                   "取每日最小值的众数。自检：sc 归纳值与权威合约规格一致"),
        "products": out,
    }
    Path("configs/tick_sizes_derived.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} 个品种 · sc 自检通过（0.1）")
    fails = {k: v for k, v in out.items() if v["days_agreeing"] < v["days_sampled"] * 0.6}
    if fails:
        print("低一致性品种（多数日不一致，用时注意）:", sorted(fails))


if __name__ == "__main__":
    main()
