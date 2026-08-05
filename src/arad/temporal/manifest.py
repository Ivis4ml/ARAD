"""Spine manifest 与逻辑内容指纹。

指纹只对**逻辑内容**取哈希（列名排序、行规范化为 JSON），不对 parquet 字节取哈希：
parquet footer 含写入器元数据，逐次运行可能不同，用字节哈希会把可重现的产物
误判为已变化。spine 指纹同时折入来源 manifest 指纹、来源内容身份、配置摘要与
代码版本，因此来源数据一变，产物指纹必然失效。
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import pyarrow as pa
from pydantic import BaseModel, Field

from ..data_catalog.schema import QualityFinding

SPINE_CODE_VERSION = "0.1.0"


def _json_default(value: Any) -> str:
    return str(value)


def canonical_rows(table: pa.Table) -> list[str]:
    columns = sorted(table.column_names)
    rows = table.select(columns).to_pylist()
    return [
        json.dumps(row, sort_keys=True, ensure_ascii=False, default=_json_default) for row in rows
    ]


def fingerprint_table(table: pa.Table, *, sort_rows: bool = True) -> str:
    """一张表的逻辑内容指纹。sort_rows 使指纹不依赖行顺序。"""
    rows = canonical_rows(table)
    if sort_rows:
        rows.sort()
    h = hashlib.sha256()
    h.update(f"columns:{','.join(sorted(table.column_names))}\n".encode())
    for row in rows:
        h.update(row.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def combine_digests(digests: list[str]) -> str:
    h = hashlib.sha256()
    for d in sorted(digests):
        h.update(d.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def digest_json(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=_json_default)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class InputRef(BaseModel):
    """所依赖的来源 manifest。指纹与内容身份都记录，任一变化都使 spine 失效。"""

    fingerprint: str
    source_snapshot_digest: str = ""
    scanner_version: str = ""


class DatasetRef(BaseModel):
    name: str
    path: str
    rows: int
    fingerprint: str
    partitions: int = 0
    note: str = ""


class ControlContract(BaseModel):
    """控制数据源的可用时间合同（声明式，不是扫描出来的）。"""

    source_id: str
    root_uri: str
    availability_rule: str
    timezone: str
    banned_fields: list[str] = Field(default_factory=list)
    provisional_fields: list[str] = Field(default_factory=list)
    audited_override_reason: str = ""
    notes: str = ""


class TargetRecord(BaseModel):
    name: str
    kind: str
    description: str
    execution_lag_seconds: int
    tradable_claim: bool
    params: dict[str, Any] = Field(default_factory=dict)
    label_rule: str = "full_session"
    rows: int = 0
    fingerprint: str = ""
    sample_segments: dict[str, int] = Field(default_factory=dict)
    sample_segments_valued: dict[str, int] = Field(default_factory=dict)
    no_trade_reasons: dict[str, int] = Field(default_factory=dict)


class SpineManifest(BaseModel):
    spine_id: str
    code_version: str = SPINE_CODE_VERSION
    generated_at: str = ""
    config_digest: str
    inputs: dict[str, InputRef] = Field(default_factory=dict)
    calendar: dict[str, Any] = Field(default_factory=dict)
    session_table: dict[str, Any] = Field(default_factory=dict)
    dominant_rule: dict[str, Any] = Field(default_factory=dict)
    targets: list[TargetRecord] = Field(default_factory=list)
    control_contracts: list[ControlContract] = Field(default_factory=list)
    datasets: list[DatasetRef] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)
    findings: list[QualityFinding] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    fingerprint: str = ""

    def compute_fingerprint(self) -> str:
        payload = self.model_dump(exclude={"generated_at", "fingerprint"})
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=_json_default)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def finalize(self) -> SpineManifest:
        self.fingerprint = self.compute_fingerprint()
        self.generated_at = datetime.now(UTC).isoformat()
        return self

    def gate_errors(self) -> list[QualityFinding]:
        return [f for f in self.findings if f.severity.value == "error"]

    def gate_passed(self) -> bool:
        return not self.gate_errors()


def write_spine_manifest(manifest: SpineManifest, path: str) -> None:
    manifest.finalize()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, ensure_ascii=False, indent=2, default=_json_default)
        f.write("\n")


def load_spine_manifest(path: str) -> SpineManifest:
    with open(path, encoding="utf-8") as f:
        return SpineManifest.model_validate(json.load(f))
