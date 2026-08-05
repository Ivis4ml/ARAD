"""SourceManifest 与 Availability Contract 的机器可读 schema。

M1 的核心合同：每个数据源必须声明 event/publication/availability 三种时间的语义、
单位与时区、禁用字段和不确定性，任何字段没有可用时间合同则 Study 无法消费它。
provisional（歧义未解决）字段默认禁止消费，除非调用方使用带理由的受审计 override。
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

SCANNER_VERSION = "0.2.0"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class TimeSemantics(BaseModel):
    """一个数据源的时间合同。availability_rule 描述研究时点可用性判定。"""

    event_time: str
    publication_time: str
    availability_time: str
    availability_rule: str
    timezone: str
    unit_notes: str = ""


class FieldAvailability(BaseModel):
    """单个字段的可用性合同。

    banned 字段禁止进入任何历史分析视图；provisional 字段（口径或语义歧义未解决）
    默认同样不可消费，仅可经 require_analysis_view 的受审计 override 使用。
    """

    name: str
    dtype: str
    semantic: str
    unit: str = ""
    banned: bool = False
    banned_reason: str = ""
    provisional: bool = False

    @model_validator(mode="after")
    def _banned_needs_reason(self) -> FieldAvailability:
        if self.banned and not self.banned_reason:
            raise ValueError(f"banned field {self.name!r} requires banned_reason")
        return self


class CoveragePartition(BaseModel):
    """一个覆盖分区（月包、日分区或文件组）的元数据。行数缺省表示未物化统计。"""

    key: str
    path: str
    files: int
    rows: int | None = None
    bytes: int | None = None
    start: str | None = None
    end: str | None = None
    notes: str = ""


class QualityFinding(BaseModel):
    severity: Severity
    code: str
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class SourceSnapshot(BaseModel):
    """来源内容身份：使指纹能够检测内容变化，而不只是元数据变化。

    guarantee 必须写明该身份的检测保证等级（哪些篡改可检测、哪些不可）。
    """

    method: str
    digest: str
    guarantee: str


class SourceManifest(BaseModel):
    source_id: str
    root_uri: str
    scanner_version: str = SCANNER_VERSION
    generated_at: str = ""
    time_semantics: TimeSemantics
    fields: list[FieldAvailability]
    partitions: list[CoveragePartition]
    findings: list[QualityFinding] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)
    source_snapshot: SourceSnapshot | None = None
    fingerprint: str = ""

    def banned_fields(self) -> set[str]:
        return {f.name for f in self.fields if f.banned}

    def provisional_fields(self) -> set[str]:
        return {f.name for f in self.fields if f.provisional and not f.banned}

    def analysis_fields(self) -> list[str]:
        """历史分析视图默认允许的字段：排除 banned 与 provisional。"""
        return [f.name for f in self.fields if not f.banned and not f.provisional]

    def gate_errors(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity == Severity.ERROR]

    def gate_passed(self) -> bool:
        return not self.gate_errors()

    def compute_fingerprint(self) -> str:
        """确定性指纹：覆盖 manifest 全部内容（含 source_snapshot 的内容身份、
        scanner 版本、字段合同、分区与事实），排除 generated_at 与 fingerprint 自身。

        内容变化的检测能力由 source_snapshot.guarantee 声明，指纹本身不做额外承诺。
        """
        payload = self.model_dump(exclude={"generated_at", "fingerprint"})
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def finalize(self) -> SourceManifest:
        self.fingerprint = self.compute_fingerprint()
        self.generated_at = datetime.now(UTC).isoformat()
        return self

    def require_analysis_view(
        self,
        columns: list[str],
        *,
        allow_provisional: set[str] | None = None,
        override_reason: str = "",
    ) -> list[str]:
        """校验一组列可用于历史分析。这是硬边界而非提醒。

        - banned 列：无条件拒绝；
        - provisional 列：默认拒绝；仅当列名出现在 allow_provisional 且提供了
          非空 override_reason 时放行（override 应被调用方记入账本）；
        - 无合同列：拒绝。
        """
        banned = set(columns) & self.banned_fields()
        if banned:
            raise BannedFieldAccess(
                f"columns {sorted(banned)} are banned for historical analysis "
                f"in source {self.source_id!r}"
            )
        provisional = set(columns) & self.provisional_fields()
        allowed = allow_provisional or set()
        blocked = provisional - allowed
        if blocked:
            raise ProvisionalFieldAccess(
                f"columns {sorted(blocked)} are provisional (unresolved semantics) "
                f"in source {self.source_id!r}; blocked by default"
            )
        if provisional and not override_reason:
            raise ProvisionalFieldAccess(
                f"provisional columns {sorted(provisional)} require a non-empty "
                "override_reason for audited access"
            )
        known = {f.name for f in self.fields}
        unknown = set(columns) - known
        if unknown:
            raise UnknownFieldAccess(
                f"columns {sorted(unknown)} have no availability contract "
                f"in source {self.source_id!r}"
            )
        return columns


class BannedFieldAccess(RuntimeError):
    """访问了被禁用的历史字段（例如财联社热度快照）。"""


class ProvisionalFieldAccess(RuntimeError):
    """访问了口径歧义未解决的字段。歧义必须 blocked，除非受审计 override。"""


class UnknownFieldAccess(RuntimeError):
    """访问了没有可用时间合同的字段。M1 合同：没有合同则不可消费。"""


def write_manifest(manifest: SourceManifest, path: str) -> None:
    manifest.finalize()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")


def load_manifest(path: str) -> SourceManifest:
    with open(path, encoding="utf-8") as f:
        return SourceManifest.model_validate(json.load(f))
