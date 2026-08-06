"""Polymarket 市场文本元数据的 PIT 可证性审计（Decision Map #12 的取证阶段）。

语义映射必须建在"历史时点确实可见"的文本上。本模块不做任何语义分类，只回答
两个前置问题：

1. 每个文本字段在两段 tape 里的填充率；
2. 同一市场在两次抓取之间，文本字段是否发生过变化。

跨段比对是决定性证据：同一 `condition_id` 在 HF 段与扩展段被分别抓取过，
两次取值不同即证明该字段可变、历史时点不可见，不能直接作为语义映射的输入。
"""

from __future__ import annotations

import collections
import glob
import os
import re

import pyarrow as pa
import pyarrow.parquet as pq

from .schema import QualityFinding, Severity

METADATA_AUDIT_VERSION = "0.1.0"

#: 市场级文本字段：唯一键是 condition_id。
MARKET_FIELDS = ("market_slug", "category", "category_refined")

#: 资产级文本字段：唯一键是 asset_id。一个市场天然有多个 outcome token，
#: 按市场级审计它会把 YES/NO 两个标签当成"同一实体的两个取值"，造出假漂移。
ASSET_FIELDS = ("outcome_label",)

TEXT_FIELDS = MARKET_FIELDS + ASSET_FIELDS

#: Polymarket 会在 slug 末尾追加消歧数字段（可能多次追加）。
_SLUG_SUFFIX = re.compile(r"(?:-\d+)+$")


def normalize_slug(slug: str | None) -> str | None:
    """去掉 slug 末尾的消歧数字段，得到跨抓取稳定的基名。

    实测：同一市场在两次抓取之间 slug 会增长（`...-by-end-of-june` →
    `...-by-end-of-june-796-981-212`）。以完整 slug 为键的映射会在市场改名后
    静默失配，因此语义映射必须以 `condition_id` 为键、以基名为文本特征。
    """
    if slug is None:
        return None
    return _SLUG_SUFFIX.sub("", slug) or slug


def _sample(files: list[str], n: int) -> list[str]:
    if not files or n <= 0:
        return []
    step = max(1, len(files) // n)
    return files[::step][:n]


def _collect(table: pa.Table, key: str, fields, store: dict[str, dict]) -> None:
    grouped = pa.TableGroupBy(table, [key, *fields]).aggregate([(key, "count")])
    columns = {c: grouped.column(c).to_pylist() for c in [key, *fields]}
    for i, entity in enumerate(columns[key]):
        bucket = store.setdefault(entity, {f: set() for f in fields})
        for field in fields:
            bucket[field].add(columns[field][i])


def _segment_metadata(root: str, n: int) -> tuple[dict[str, dict], dict[str, dict], dict, int]:
    """抽样读取一段的文本元数据。

    市场级字段按 condition_id 归并，资产级字段按 asset_id 归并：用错键会把
    同一市场的多个 outcome token 当成同一实体的多个取值，产生假漂移。
    """
    per_market: dict[str, dict] = {}
    per_asset: dict[str, dict] = {}
    non_null = dict.fromkeys(TEXT_FIELDS, 0)
    rows = 0
    columns = ["condition_id", "asset_id", *TEXT_FIELDS]
    for path in _sample(sorted(glob.glob(os.path.join(root, "*.parquet"))), n):
        table = pq.read_table(path, columns=columns)
        rows += table.num_rows
        for field in TEXT_FIELDS:
            non_null[field] += table.num_rows - table.column(field).null_count
        _collect(table, "condition_id", MARKET_FIELDS, per_market)
        _collect(table, "asset_id", ASSET_FIELDS, per_asset)
    return per_market, per_asset, non_null, rows


def census_segment_markets(census_dir: str) -> dict[str, set[str]]:
    """从 M2.5 普查产物读取每段出现过的市场集合。"""
    out: dict[str, set[str]] = {}
    for path in sorted(glob.glob(os.path.join(census_dir, "market_day", "*.parquet"))):
        segment = os.path.basename(path).split("_", 1)[0]
        ids = pq.read_table(path, columns=["condition_id"]).column("condition_id").to_pylist()
        out.setdefault(segment, set()).update(ids)
    return out


def audit_metadata_provenance(
    roots: dict[str, str], census_dir: str, *, sample_partitions: int = 40
) -> tuple[list[QualityFinding], dict]:
    """审计文本元数据的填充率与跨段可变性。不做任何语义判断。"""
    findings: list[QualityFinding] = []
    coverage: dict[str, dict] = {}
    per_segment: dict[str, dict[str, dict]] = {}

    per_segment_assets: dict[str, dict[str, dict]] = {}
    for segment, root in roots.items():
        per_market, per_asset, non_null, rows = _segment_metadata(root, sample_partitions)
        per_segment[segment] = per_market
        per_segment_assets[segment] = per_asset
        coverage[segment] = {
            "sampled_rows": rows,
            "fill_rate": {f: (non_null[f] / rows if rows else 0.0) for f in TEXT_FIELDS},
            "markets_sampled": len(per_market),
            "assets_sampled": len(per_asset),
        }
        empty = sorted(f for f in TEXT_FIELDS if rows and non_null[f] == 0)
        if empty:
            findings.append(
                QualityFinding(
                    severity=Severity.ERROR,
                    code="pm_metadata.field_absent_in_segment",
                    message=(
                        f"段 {segment} 的文本字段 {empty} 全为空；依赖这些字段的语义映射"
                        "在该段无法执行"
                    ),
                    evidence={"segment": segment, "fields": empty, "sampled_rows": rows},
                )
            )
        drift = {f: sum(1 for b in per_market.values() if len(b[f]) > 1) for f in MARKET_FIELDS}
        drift.update(
            {f: sum(1 for b in per_asset.values() if len(b[f]) > 1) for f in ASSET_FIELDS}
        )
        if any(drift.values()):
            findings.append(
                QualityFinding(
                    severity=Severity.WARNING,
                    code="pm_metadata.intra_segment_drift",
                    message=f"段 {segment} 内同一实体的文本字段出现多个取值",
                    evidence={
                        "segment": segment,
                        "entities_with_multiple_values": drift,
                        "keys": {"market_fields": "condition_id", "asset_fields": "asset_id"},
                    },
                )
            )

    segments = sorted(per_segment)
    cross: dict = {"comparable_markets": 0, "differs": {}, "differs_after_normalisation": {}}
    if len(segments) == 2:
        a, b = segments
        census = census_segment_markets(census_dir) if os.path.isdir(census_dir) else {}
        both = census.get(a, set()) & census.get(b, set())
        common = [c for c in set(per_segment[a]) & set(per_segment[b]) if not both or c in both]
        cross["comparable_markets"] = len(common)
        raw = collections.Counter()
        normalised = collections.Counter()
        examples: list[dict] = []
        for key, fields, store in (
            ("condition_id", MARKET_FIELDS, per_segment),
            ("asset_id", ASSET_FIELDS, per_segment_assets),
        ):
            entities = (
                common
                if key == "condition_id"
                else sorted(set(store[a]) & set(store[b]))
            )
            if key == "asset_id":
                cross["comparable_assets"] = len(entities)
            for entity in entities:
                for field in fields:
                    va = next(iter(store[a][entity][field]))
                    vb = next(iter(store[b][entity][field]))
                    if va == vb:
                        continue
                    raw[field] += 1
                    if field == "market_slug" and normalize_slug(va) == normalize_slug(vb):
                        continue
                    normalised[field] += 1
                    if len(examples) < 5:
                        examples.append({"field": field, key: entity[:16], a: va, b: vb})
        cross["differs"] = dict(raw)
        cross["differs_after_normalisation"] = dict(normalised)
        cross["examples"] = examples
        if raw:
            findings.append(
                QualityFinding(
                    severity=Severity.ERROR,
                    code="pm_metadata.mutable_across_scrapes",
                    message=(
                        "同一市场的文本元数据在两次抓取之间发生变化，"
                        "证明这些字段历史时点不可见；语义映射必须以 condition_id 为键，"
                        "以跨抓取稳定的基名为文本特征，并对每个版本留快照"
                    ),
                    evidence={
                        "segments": segments,
                        "comparable_markets": len(common),
                        "differs": dict(raw),
                        "differs_after_slug_normalisation": dict(normalised),
                        "examples": examples,
                    },
                )
            )
    facts = {
        "version": METADATA_AUDIT_VERSION,
        "coverage": coverage,
        "cross_segment": cross,
        "normalisation_rule": (
            "market_slug 去掉末尾的 (-<数字>)+ 消歧段后作为基名；"
            "基名是跨抓取稳定的文本特征，完整 slug 保留为观测值"
        ),
    }
    return findings, facts
