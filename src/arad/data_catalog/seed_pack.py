"""外部种子包的分道接入（M21 / 决定 0013 §四）。

Rev-PLM 的种子包里有两份清单，它们的性质完全不同，因此走两条通道：

一、`driver_gaps_do_not_propose`：某个价格形成驱动在预测市场上**没有可结算工具**。
   这是一条关于**宇宙存在性**的事实，不含任何检验结果，因此可以进提案器上下文 ——
   它省下的是「提了一条根本没有数据的机制」所浪费的整轮预算。
   但只有其中**时间不变**的那一半可以直接用：理由写「从未存在」或
   「连续量／微观结构变量，无法表述为可结算事件」的 29 条，在任何窗口都成立；
   写「当前无活跃市场」「检索词未命中」的另外 30 条是 2026-08 的快照性质，
   实测已找到反例（禽流感、H5N1、港口罢工在 discovery 段各有可结算市场），
   未经逐条重核不得使用。

二、`negative_evidence`：外部程序在**重叠数据**上跑出的检验统计量（p 值、方向、
   跨年份稳定性）。它是结果，绝不进提案器 —— 其检验窗口 2023-10 至 2026-07 同时
   覆盖本项目的 discovery 段与封存段，进提案器即是绕道的数据窥探。
   它只进评价机一侧的封禁表：同型提案在读取 outcome **之前**被判 blocked，
   理由如实记入账本。

两条通道的共同纪律：进提案器的那一份必须过 `assert_blinded`（种子包里
`matched_products[].symbol` 的 `IC` 与 `driver_id` 的 `se_asia_resource_policy`
都会命中效果字段词表，因此只能做白名单投影，不能整体传入）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SEED_PACK_VERSION = "seed-pack/v1"

#: 时间不变的缺口理由：这些在任何评价窗口上都成立。
_TIME_INVARIANT_MARKERS = ("从未", "无法表述", "连续量", "微观结构")


class SeedPackError(RuntimeError):
    """种子包不合法或路径不存在。宁可不接，也不接一份来路不明的清单。"""


@dataclass(frozen=True)
class SeedPack:
    pack_id: str
    checked_at: str
    absent_drivers: tuple[dict[str, str], ...]
    external_refutations: tuple[dict[str, Any], ...]

    def proposer_view(self) -> dict:
        """进提案器的那一份：只有存在性事实，没有任何检验结果。"""
        return {
            "version": SEED_PACK_VERSION,
            "pack_id": self.pack_id,
            "checked_at": self.checked_at,
            "absent_drivers": [dict(d) for d in self.absent_drivers],
            "note": (
                "这些价格形成驱动在预测市场上没有可结算工具，"
                "以它们为机制的提案无法用本数据源检验。清单只含**存在性**，"
                "不含任何检验结果；只收录在任何窗口都成立的条目"
                "（写「当前无活跃市场」的快照性条目未收录，因为实测有反例）"
            ),
        }

    def auditor_view(self) -> dict:
        """只给非盲化角色：外部否证记录，用于在读取结果之前拦下同型提案。"""
        return {
            "version": SEED_PACK_VERSION,
            "pack_id": self.pack_id,
            "external_refutations": [dict(r) for r in self.external_refutations],
            "note": (
                "外部程序在与本项目 discovery 段与封存段重叠的窗口上跑出的检验结果。"
                "**绝不进提案器上下文**：那是绕道的数据窥探。"
            ),
        }


def load_seed_pack(path: str | Path) -> SeedPack:
    source = Path(path)
    if not source.exists():
        raise SeedPackError(f"找不到种子包 {source}")
    doc = json.loads(source.read_text(encoding="utf-8"))
    meta = doc.get("meta") or {}
    gaps = doc.get("driver_gaps_do_not_propose") or []
    absent = tuple(
        {"driver": g.get("name_cn", ""), "channel": g.get("channel", ""),
         "reason": g.get("gap_reason", "")}
        for g in gaps
        if any(marker in (g.get("gap_reason") or "") for marker in _TIME_INVARIANT_MARKERS)
    )
    negative = doc.get("negative_evidence") or {}
    refutations = tuple(
        {"pair": row.get("pair"), "direction": row.get("direction"),
         "note": "外部 FDR 通过项；同型提案须声明新增控制或分层"}
        for row in (negative.get("fdr_passes_period_specific") or [])
    )
    return SeedPack(
        pack_id=str(meta.get("month") or source.stem),
        checked_at=str(meta.get("snapshot_checked_at") or ""),
        absent_drivers=absent,
        external_refutations=refutations,
    )
