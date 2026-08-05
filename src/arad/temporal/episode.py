"""Independent Episode、purge/embargo 与样本段污染标签。

Episode 缺省按交易日成组：同一交易日的夜盘与日盘共享同一信息环境，
把它们当两个独立观测会高估样本量。更细的语义去重（同一新闻链、同一事件）
属于 Decision Map #5，不在本票范围内。

样本段按 Merge-Plan-2 §4：真正的前向起点不是写死的日期，而是
`label_start > freeze_at + embargo`；没有 freeze_at 就没有 forward。
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


def classify_segment(
    label_start: datetime,
    label_end: datetime,
    *,
    freeze_at: datetime | None = None,
    embargo: timedelta = timedelta(0),
) -> SampleSegment:
    """按 label 的结束时点归段；结果落在哪一段，样本就属于哪一段。

    只有当协议冻结时点已给出、且 label 窗口整体开始于 freeze_at + embargo 之后，
    才算真正的前向确认样本。
    """
    if freeze_at is not None and label_start > freeze_at + embargo:
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
