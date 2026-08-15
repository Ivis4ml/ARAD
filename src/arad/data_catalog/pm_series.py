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


#: 机制族序列的字段。比词汇族多两个：
#: `dp` 是构成受控的分桶变化（只由同时出现在相邻两桶的成员的重定价构成），
#: `conditions` 是当桶活跃成员数。实测词汇族日度 Δp 方差的九成来自构成移动
#: （当日哪些市场在成交），只看 p 电平的构造测的多半是构成而不是信念。
MECH_FIELDS = ("p", "notional", "trades", "conditions", "dp")

MECH_SERIES_SCHEMA = pa.schema(
    [
        ("family_id", pa.string()),
        ("bucket_end", pa.timestamp("us", tz="UTC")),
        ("p", pa.float64()),
        ("notional", pa.float64()),
        ("trades", pa.int64()),
        ("conditions", pa.int64()),
        ("dp", pa.float64()),
    ]
)


def build_mechanism_series(
    roots: dict[str, str],
    membership: dict[str, dict[str, int]],
    *,
    bucket_seconds: int = 3600,
    max_stale_seconds: int = 86_400,
    date_max: str | None = None,
) -> pa.Table:
    """按机制成员与极性折出族序列，并给出构成受控的变化量。

    与 `build_series` 的差别只有两处，其余口径逐字相同（成交额加权、按
    `outcome_seq == 1` 归一、分桶取右端），以便「成员资格」成为唯一变化的变量：

    1. **极性同号化**：`q = p` 或 `q = 1 − p`，由成员的 polarity 决定。
       同一机制的否定式提问（「封锁被解除」之于「封锁发生」）不折就会在族内相互抵消。
    2. **dp**：相邻两个有成交的分桶之间，只对**同时出现在两桶**的成员求加权重定价，
       权重取前一桶的成交额。新入族或退出的成员不贡献电平跳变。两桶间隔超过
       `max_stale_seconds` 时 dp 无定义（写 null，不写 0：写 0 等于声称没有移动）。

    `date_max` 只用于按分区文件名裁掉不需要的日期（分区名形如 2024-12-31.parquet），
    是纯粹的读取优化，不改变任何一个分桶的取值。
    """
    wanted: set[str] = set()
    for members in membership.values():
        wanted |= set(members)
    value_set = pa.array(sorted(wanted), pa.large_string())

    # family -> (bucket, condition) -> [Σ q·w, Σ w, 笔数]
    acc: dict[str, dict[tuple[int, str], list]] = {fid: {} for fid in membership}
    for path in _partition_files(roots):
        if date_max is not None and os.path.basename(path)[:10] > date_max:
            continue
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
        table = table.append_column("q_raw", p)
        table = table.append_column("w", weight)
        table = table.append_column("bucket", bucket)
        for family_id, members in membership.items():
            ids = pa.array(sorted(members), pa.large_string())
            sub = table.filter(pc.is_in(table.column("condition_id"), value_set=ids))
            if sub.num_rows == 0:
                continue
            cells = acc[family_id]
            for cid, pv, wv, bv in zip(sub.column("condition_id").to_pylist(),
                                       sub.column("q_raw").to_pylist(),
                                       sub.column("w").to_pylist(),
                                       sub.column("bucket").to_pylist(), strict=True):
                polarity = members.get(cid)
                if polarity is None or pv is None:
                    continue
                q = pv if polarity == 1 else 1.0 - pv
                key = (int(bv), cid)
                cell = cells.get(key)
                if cell is None:
                    cell = [0.0, 0.0, 0]
                    cells[key] = cell
                cell[0] += q * wv
                cell[1] += wv
                cell[2] += 1

    rows: list[dict] = []
    for family_id in sorted(acc):
        per_bucket: dict[int, dict[str, tuple[float, float, int]]] = {}
        for (bucket, cid), (qw, w, n) in acc[family_id].items():
            per_bucket.setdefault(bucket, {})[cid] = (qw, w, n)
        prev_bucket: int | None = None
        prev_members: dict[str, tuple[float, float, int]] = {}
        for bucket in sorted(per_bucket):
            members_here = per_bucket[bucket]
            num = sum(v[0] for v in members_here.values())
            den = sum(v[1] for v in members_here.values())
            trades = sum(v[2] for v in members_here.values())
            dp = None
            if prev_bucket is not None and bucket - prev_bucket <= max_stale_seconds:
                shared = [cid for cid in members_here if cid in prev_members]
                weight_sum = sum(prev_members[cid][1] for cid in shared)
                if weight_sum > 0:
                    moved = 0.0
                    for cid in shared:
                        prev_qw, prev_w, _ = prev_members[cid]
                        cur_qw, cur_w, _ = members_here[cid]
                        if prev_w <= 0 or cur_w <= 0:
                            continue
                        moved += prev_w * ((cur_qw / cur_w) - (prev_qw / prev_w))
                    dp = moved / weight_sum
            rows.append({
                "family_id": family_id,
                "bucket_end": bucket * 1_000_000,
                "p": (num / den) if den > 0 else None,
                "notional": den,
                "trades": trades,
                "conditions": len(members_here),
                "dp": dp,
            })
            prev_bucket, prev_members = bucket, members_here
    table = pa.Table.from_pylist(rows, schema=MECH_SERIES_SCHEMA)
    return table.sort_by([("family_id", "ascending"), ("bucket_end", "ascending")])


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
