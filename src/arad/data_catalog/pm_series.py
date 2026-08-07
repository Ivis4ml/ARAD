"""Polymarket 候选族的 PIT 序列（M5.2）。

把 8.56 亿笔逐笔成交折成每个候选机制族的时间序列，使 `Source.PM_MARKET` 可求值。
在此之前解释器对它一律抛 `SourceNotImplemented`，因此循环**一个另类因子都产不出**，
搜索空间整个落在量价对照集里。

三条必须做对的事：

1. **概率要归一到同一侧。**每个市场有两侧（outcome_seq 1/2，Yes/No 或 Up/Down），
   `price` 是那一侧代币的价格。直接把两侧混起来平均得到的恒是 0.5 附近的噪声 ——
   整个信号会被这一步毁掉。实测同市场同秒两侧成交的 p1+p2 中位 0.99、80% 落在
   ±0.02 内（缺口是买卖价差），因此按 `p = price if seq == 1 else 1 - price` 归一。
2. **可用时刻取分桶右端。**`block_timestamp` 按 M1 合同已是撮合时刻的保守下界，
   分桶右端比它还要晚一档，因此不可能前视。
3. **族的选择是假设，不是映射表。**本模块只负责把某个族的成交折成序列；
   「哪个族关联哪个品种」由各 Study 在 Hypothesis Lock 里冻结，
   不在这里固化（Decision Map #12 的裁决）。
"""

from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .pm_text_corpus import slug_tokens

PM_SERIES_VERSION = "0.1.0"

#: 序列的字段。窗口/创新/标准化这些步骤直接作用在它们上面。
PM_FIELDS = ("p", "notional", "trades")

SERIES_SCHEMA = pa.schema(
    [
        ("family_id", pa.string()),
        ("bucket_end", pa.timestamp("us", tz="UTC")),
        ("p", pa.float64()),
        ("notional", pa.float64()),
        ("trades", pa.int64()),
        ("conditions", pa.int64()),
    ]
)


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    tokens: frozenset[str]
    markets: int
    trades: int


def load_families(manifest_path: str, *, top: int = 12,
                  include: tuple[str, ...] = ()) -> list[FamilySpec]:
    """从 #12 的产物读候选族。按成交量取前 top 个，外加显式点名的。"""
    doc = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    rows = [f for f in doc["families"] if not f.get("screened_out")]
    rows.sort(key=lambda f: -f.get("trades", 0))
    chosen: dict[str, dict] = {}
    for f in rows[:top]:
        chosen[f["family_id"]] = f
    for f in rows:
        if f["family_id"] in include:
            chosen[f["family_id"]] = f
    return [
        FamilySpec(
            family_id=f["family_id"],
            tokens=frozenset(f["head_tokens"]),
            markets=int(f.get("markets", 0)),
            trades=int(f.get("trades", 0)),
        )
        for f in chosen.values()
    ]


def conditions_by_family(
    market_text_path: str, families: list[FamilySpec]
) -> dict[str, set[str]]:
    """市场 → 族。一个市场可以同时属于多个族，如实记录，不强行归一。"""
    table = pq.read_table(market_text_path, columns=["condition_id", "slug_base"])
    out: dict[str, set[str]] = {f.family_id: set() for f in families}
    for condition_id, slug_base in zip(
        table.column("condition_id").to_pylist(),
        table.column("slug_base").to_pylist(),
        strict=True,
    ):
        tokens = set(slug_tokens(slug_base))
        if not tokens:
            continue
        for family in families:
            if tokens & family.tokens:
                out[family.family_id].add(condition_id)
    return out


def _partition_files(roots: dict[str, str]) -> list[str]:
    files: list[str] = []
    for root in roots.values():
        files.extend(sorted(glob.glob(os.path.join(root, "*.parquet"))))
        files.extend(sorted(glob.glob(os.path.join(root, "*", "*.parquet"))))
    return sorted(set(files))


def build_series(
    roots: dict[str, str],
    membership: dict[str, set[str]],
    *,
    bucket_seconds: int = 3600,
) -> pa.Table:
    """扫一遍 tape，折成 (族, 分桶) 的序列。

    权重用名义额：一笔 1 美元的成交与一笔 10 万美元的成交对"市场信念"的证据强度
    不同，等权平均会让极小额成交主导。
    """
    wanted: set[str] = set()
    for ids in membership.values():
        wanted |= ids
    value_set = pa.array(sorted(wanted), pa.large_string())
    per_family = {
        fid: pa.array(sorted(ids), pa.large_string()) for fid, ids in membership.items()
    }

    # (family, bucket) -> [Σ p·w, Σ w, 笔数, 市场数上界]
    acc: dict[tuple[str, int], list] = {}
    for path in _partition_files(roots):
        table = pq.read_table(
            path,
            columns=["condition_id", "outcome_seq", "price", "usdc_amount",
                     "block_timestamp"],
        )
        if table.num_rows == 0:
            continue
        table = table.filter(pc.is_in(table.column("condition_id"), value_set=value_set))
        if table.num_rows == 0:
            continue
        # 归一到 outcome_seq == 1 一侧：两侧混合后恒在 0.5 附近，信号会被这一步毁掉
        p = pc.if_else(
            pc.equal(table.column("outcome_seq"), 1),
            table.column("price"),
            pc.subtract(1.0, table.column("price")),
        )
        weight = pc.fill_null(table.column("usdc_amount"), 0.0)
        bucket = pc.multiply(
            pc.add(pc.divide(table.column("block_timestamp"), bucket_seconds), 1),
            bucket_seconds,
        )
        table = table.append_column("bucket", bucket)
        table = table.append_column("pw", pc.multiply(p, weight))
        table = table.append_column("w", weight)
        for family_id, ids in per_family.items():
            sub = table.filter(pc.is_in(table.column("condition_id"), value_set=ids))
            if sub.num_rows == 0:
                continue
            grouped = sub.group_by("bucket").aggregate(
                [("pw", "sum"), ("w", "sum"), ("w", "count"),
                 ("condition_id", "count_distinct")],
            )
            for row in grouped.to_pylist():
                key = (family_id, int(row["bucket"]))
                cell = acc.get(key)
                if cell is None:
                    cell = [0.0, 0.0, 0, 0]
                    acc[key] = cell
                cell[0] += row["pw_sum"] or 0.0
                cell[1] += row["w_sum"] or 0.0
                cell[2] += row["w_count"] or 0
                cell[3] = max(cell[3], row["condition_id_count_distinct"] or 0)

    rows = []
    for (family_id, bucket), (num, den, count, conds) in sorted(acc.items()):
        rows.append({
            "family_id": family_id,
            "bucket_end": bucket * 1_000_000,
            "p": (num / den) if den > 0 else None,
            "notional": den,
            "trades": count,
            "conditions": conds,
        })
    table = pa.Table.from_pylist(rows, schema=SERIES_SCHEMA)
    return table.sort_by([("family_id", "ascending"), ("bucket_end", "ascending")])
