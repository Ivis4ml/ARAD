"""as-of join：按 availability_time 重建决策时点的 Point-in-Time View。

两条硬边界：
1. 只返回 `available_time` **严格早于**决策时点的观测。时刻并列按不可用处理，
   歧义一律取保守方向。
2. 列的可用性沿用 M1 的字段合同：banned 列无条件拒绝，provisional 列默认拒绝，
   仅在调用方给出 allow_provisional 与非空 override_reason 时放行（override
   由调用方记入账本）。
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise

import pyarrow as pa

from ..data_catalog.schema import SourceManifest
from .errors import LookaheadError

AVAILABLE_TIME = "available_time"


def _require_aware(ts: datetime, what: str) -> datetime:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError(f"{what} 必须带时区：{ts!r}")
    return ts


@dataclass
class PitSeries:
    """一个按 availability_time 升序排列的只读观测序列。"""

    name: str
    table: pa.Table
    manifest: SourceManifest | None = None
    allow_provisional: set[str] = field(default_factory=set)
    override_reason: str = ""
    _times: list[datetime] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        if AVAILABLE_TIME not in self.table.column_names:
            raise ValueError(f"{self.name} 缺少 {AVAILABLE_TIME} 列，无法作为 PIT 序列")
        dtype = self.table.schema.field(AVAILABLE_TIME).type
        if not pa.types.is_timestamp(dtype) or dtype.tz is None:
            raise ValueError(f"{self.name} 的 {AVAILABLE_TIME} 必须是带时区的时间戳，得到 {dtype}")
        times = self.table.column(AVAILABLE_TIME).to_pylist()
        if any(t is None for t in times):
            raise ValueError(f"{self.name} 的 {AVAILABLE_TIME} 含空值")
        if any(b < a for a, b in pairwise(times)):
            raise ValueError(f"{self.name} 未按 {AVAILABLE_TIME} 升序排列")
        object.__setattr__(self, "_times", times)

    def __len__(self) -> int:
        return self.table.num_rows

    def validate_columns(self, columns: list[str]) -> list[str]:
        if self.manifest is None:
            missing = set(columns) - set(self.table.column_names)
            if missing:
                raise ValueError(f"{self.name} 没有列 {sorted(missing)}")
            return columns
        self.manifest.require_analysis_view(
            columns,
            allow_provisional=self.allow_provisional or None,
            override_reason=self.override_reason,
        )
        return columns

    def index_before(self, decision_time: datetime) -> int | None:
        """最后一条 available_time 严格早于 decision_time 的行号。"""
        _require_aware(decision_time, "decision_time")
        i = bisect_left(self._times, decision_time)
        return i - 1 if i > 0 else None

    def row(self, index: int, columns: list[str]) -> dict:
        out = {AVAILABLE_TIME: self._times[index]}
        for c in columns:
            if c == AVAILABLE_TIME:
                continue
            out[c] = self.table.column(c)[index].as_py()
        return out


def asof_last(series: PitSeries, decision_time: datetime, columns: list[str]) -> dict | None:
    series.validate_columns(columns)
    idx = series.index_before(decision_time)
    if idx is None:
        return None
    row = series.row(idx, columns)
    if row[AVAILABLE_TIME] >= decision_time:  # 防御性复核，正常不会触发
        raise LookaheadError(
            f"{series.name} 的 as-of 结果 {row[AVAILABLE_TIME]} 不早于决策时点 {decision_time}"
        )
    return row


def asof_last_many(
    series: PitSeries, decision_times: list[datetime], columns: list[str]
) -> list[dict | None]:
    series.validate_columns(columns)
    return [asof_last(series, t, columns) for t in decision_times]


def count_before(series: PitSeries, decision_time: datetime) -> int:
    idx = series.index_before(decision_time)
    return 0 if idx is None else idx + 1


def assert_decision_precedes_label(decision_time: datetime, label_start: datetime) -> None:
    _require_aware(decision_time, "decision_time")
    _require_aware(label_start, "label_start")
    if decision_time >= label_start:
        raise LookaheadError(
            f"决策时点 {decision_time} 不早于 label 窗口起点 {label_start}；"
            "任何 feature 都会与标签同时或滞后可用"
        )
