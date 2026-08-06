"""Independent Episode、purge/embargo 与样本段污染标签。

Episode 缺省按交易日成组：同一交易日的夜盘与日盘共享同一信息环境，
把它们当两个独立观测会高估样本量。更细的语义去重（同一新闻链、同一事件）
属于 Decision Map #5，不在本票范围内。

样本段按 Merge-Plan-2 §4：真正的前向起点不是写死的日期，而是
`label_start > freeze_at + embargo`；没有 freeze_at 就没有 forward。

**2026-08-05 决定 0004 扩展**：前向门加入 `taxonomy_freeze_at`。分类法若用含裁决
区间的语料归纳，其机制分组被未来塑造过。关键论证是市场宇宙**不是外生文本**：
Polymarket 上创建哪些市场，对真实事件内生，而这些事件恰是推动商品价格的事件
（`hormuz` 从 4 个市场涨到 188 个，正因为发生了同时推动原油波动的地缘事件）。
因此"宇宙后见"与"结果后见"不是两类不相交的污染 —— 在全史宇宙上选机制，
等于在与结果相关的变量上做选择，条件化之后选择偏差就变成估计偏差。
它只在冻结之后到达的前向数据上失效，因为那时裁决数据与选择事件独立。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum

DISCOVERY_END = date(2024, 12, 31)
HISTORICAL_VALIDATION_END = date(2025, 12, 31)

EPISODE_GRAINS = ("trading_day", "session")


class SampleSegment(str, Enum):
    DISCOVERY = "discovery"
    HISTORICAL_VALIDATION = "historical_validation"
    CONTAMINATED_AUDIT = "contaminated_audit"
    FORWARD_CONFIRMATION = "forward_confirmation"


def episode_id(
    product: str, trading_day: date, session_seq: int, *, grain: str = "trading_day"
) -> str:
    if grain not in EPISODE_GRAINS:
        raise ValueError(f"未知的 Episode 粒度 {grain!r}，可选 {EPISODE_GRAINS}")
    if grain == "trading_day":
        return f"{product}:{trading_day.strftime('%Y%m%d')}"
    return f"{product}:{trading_day.strftime('%Y%m%d')}:{session_seq}"


def forward_gate(
    *,
    protocol_freeze_at: datetime | None = None,
    confirmatory_freeze_at: datetime | None = None,
    source_snapshot_at: datetime | None = None,
    taxonomy_freeze_at: datetime | None = None,
    embargo: timedelta = timedelta(0),
) -> datetime | None:
    """§4 的前向门：全部冻结时点取最大，再加 embargo。

    `taxonomy_freeze_at` 由决定 0004 加入：分类法的归纳语料若覆盖裁决区间，
    机制分组就被未来塑造过，该 Study 的前向起点必须推迟到分类法冻结之后。
    任一冻结时点缺失即返回 None —— 没有完整的冻结记录就没有 forward。
    """
    stamps = [
        protocol_freeze_at, confirmatory_freeze_at, source_snapshot_at, taxonomy_freeze_at,
    ]
    present = [t for t in stamps if t is not None]
    if not present:
        return None
    return max(present) + embargo


def classify_segment(
    label_start: datetime,
    label_end: datetime,
    *,
    freeze_at: datetime | None = None,
    taxonomy_freeze_at: datetime | None = None,
    embargo: timedelta = timedelta(0),
) -> SampleSegment:
    """按 label 的结束时点归段；结果落在哪一段，样本就属于哪一段。

    只有当冻结时点已给出、且 label 窗口整体开始于**全部冻结时点的最大值**
    加 embargo 之后，才算真正的前向确认样本（决定 0004：含 taxonomy_freeze_at）。
    """
    gate = forward_gate(
        confirmatory_freeze_at=freeze_at,
        taxonomy_freeze_at=taxonomy_freeze_at,
        embargo=embargo,
    )
    if gate is not None and label_start > gate:
        return SampleSegment.FORWARD_CONFIRMATION
    end_day = label_end.date()
    if end_day <= DISCOVERY_END:
        return SampleSegment.DISCOVERY
    if end_day <= HISTORICAL_VALIDATION_END:
        return SampleSegment.HISTORICAL_VALIDATION
    return SampleSegment.CONTAMINATED_AUDIT


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def purge_embargo_mask(
    candidates: list[dict],
    test_rows: list[dict],
    *,
    embargo: timedelta,
) -> list[bool]:
    """返回与 candidates 等长的保留掩码。

    丢弃三类候选：与任一测试样本同 Episode 的；label 窗口与任一测试样本重叠的；
    决策时点落在测试样本 label 结束后 embargo 区间内的。
    """
    test_episodes = {r["episode_id"] for r in test_rows}
    mask = []
    for row in candidates:
        keep = row["episode_id"] not in test_episodes
        if keep:
            for t in test_rows:
                if _overlaps(
                    row["label_start"], row["label_end"], t["label_start"], t["label_end"]
                ):
                    keep = False
                    break
                if t["label_end"] <= row["decision_time"] < t["label_end"] + embargo:
                    keep = False
                    break
        mask.append(keep)
    return mask
