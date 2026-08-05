"""Polymarket 两段 tape 的只读扫描器。

核验内容：
- 分区覆盖与行数（HF daily_aligned 与自爬 extension_tape）；
- **全部分区**的 schema 签名与段内漂移（不以单一文件代表整段）；
- 两段间的列类型冲突；
- 接缝日（seam_date）时间范围加最小 row-key 采样（复合键交集必须为空）；
- 来源内容身份：全部 parquet footer 字节的聚合哈希（保证等级见 guarantee 声明）。

零分区、接缝统计缺失、row-key 重叠均为 error 级发现，阻断质量闸门。
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import struct

import pyarrow.parquet as pq

from .schema import (
    CoveragePartition,
    FieldAvailability,
    QualityFinding,
    Severity,
    SourceManifest,
    SourceSnapshot,
    TimeSemantics,
)

_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

_SEAM_KEY_COLUMNS = ["block_timestamp", "asset_id", "price", "usdc_amount"]

FOOTER_GUARANTEE = (
    "parquet footer 字节聚合哈希（含全部行组的列统计、偏移与布局）加文件大小。"
    "可检测：schema 变化、行组增删、任何改变列统计或布局的内容修改。"
    "不可检测：等长且不改变任何列 min/max 统计与页偏移的数据页篡改。"
)


def _partition_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(root, "**", "*.parquet"), recursive=True))


def _date_of(path: str) -> str | None:
    m = _DATE_RE.search(os.path.basename(path)) or _DATE_RE.search(os.path.dirname(path))
    return m.group(1) if m else None


def _footer_digest(fp: str, h: hashlib._hashlib.HASH) -> None:
    """读取 parquet footer 原始字节并入哈希：末尾 8 字节为 footer 长度 + 'PAR1'。"""
    size = os.path.getsize(fp)
    with open(fp, "rb") as f:
        f.seek(size - 8)
        tail = f.read(8)
        (footer_len,) = struct.unpack("<I", tail[:4])
        f.seek(size - 8 - footer_len)
        h.update(f.read(footer_len))
    h.update(str(size).encode())


def _scan_segment(
    root: str, key_prefix: str, h: hashlib._hashlib.HASH
) -> tuple[list[CoveragePartition], dict, dict[str, str], list[QualityFinding]]:
    parts: list[CoveragePartition] = []
    findings: list[QualityFinding] = []
    total_rows = 0
    dates: list[str] = []
    schema_signatures: dict[str, list[str]] = {}
    files = _partition_files(root)
    for fp in files:
        md = pq.read_metadata(fp)
        total_rows += md.num_rows
        d = _date_of(fp)
        if d:
            dates.append(d)
        schema = md.schema.to_arrow_schema()
        sig = ";".join(f"{n}:{schema.field(n).type}" for n in sorted(schema.names))
        schema_signatures.setdefault(sig, []).append(fp)
        _footer_digest(fp, h)
        parts.append(
            CoveragePartition(
                key=f"{key_prefix}:{d or os.path.basename(fp)}",
                path=fp,
                files=1,
                rows=md.num_rows,
                bytes=os.path.getsize(fp),
                start=d,
                end=d,
            )
        )
    if not files:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code=f"polymarket.{key_prefix}.empty",
                message=f"段 {key_prefix} 未发现任何 parquet 分区（路径错误或数据缺失）",
                evidence={"root": root},
            )
        )
    if len(schema_signatures) > 1:
        by_count = sorted(schema_signatures.items(), key=lambda kv: -len(kv[1]))
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code=f"polymarket.{key_prefix}.schema_drift",
                message=(
                    f"段 {key_prefix} 内存在 {len(schema_signatures)} 种 schema 签名，"
                    "历史分区 schema 不一致"
                ),
                evidence={
                    "signature_counts": {sig[:120]: len(fps) for sig, fps in by_count},
                    "first_minority_file": by_count[1][1][0],
                },
            )
        )
    schema_types: dict[str, str] = {}
    if files:
        # 段类型以多数签名为准（漂移已另行报告）
        majority_sig = max(schema_signatures.items(), key=lambda kv: len(kv[1]))[1][0]
        schema = pq.read_schema(majority_sig)
        schema_types = {name: str(schema.field(name).type) for name in schema.names}
    facts = {
        "partitions": len(files),
        "rows": total_rows,
        "first_date": min(dates) if dates else None,
        "last_date": max(dates) if dates else None,
        "schema_signatures": len(schema_signatures) if files else 0,
    }
    return parts, facts, schema_types, findings


def _timestamp_range_on(files: list[str], column: str = "block_timestamp") -> tuple[int, int] | None:
    lo, hi = None, None
    for fp in files:
        md = pq.read_metadata(fp)
        try:
            idx = md.schema.to_arrow_schema().names.index(column)
        except ValueError:
            return None
        for rg in range(md.num_row_groups):
            st = md.row_group(rg).column(idx).statistics
            if st is None or not st.has_min_max:
                return None
            lo = st.min if lo is None else min(lo, st.min)
            hi = st.max if hi is None else max(hi, st.max)
    if lo is None:
        return None
    return int(lo), int(hi)


def _seam_rowkeys(files: list[str]) -> set[tuple] | None:
    """读取接缝日分区的复合键（最小 row-key 采样）。缺列则返回 None。"""
    keys: set[tuple] = set()
    for fp in files:
        schema = pq.read_schema(fp)
        if not set(_SEAM_KEY_COLUMNS) <= set(schema.names):
            return None
        table = pq.read_table(fp, columns=_SEAM_KEY_COLUMNS)
        cols = [table.column(c).to_pylist() for c in _SEAM_KEY_COLUMNS]
        keys.update(zip(*cols, strict=True))
    return keys


#: 字段合同的注解覆盖层。语义、禁用与 provisional 标记按列名给出；
#: 字段清单本身**由实测 schema 决定**，不在此硬编码。M1 首版曾把文档叙述里的
#: 链上列（tx_hash / venue_class / is_relay 等）直接写进合同，实测两段都没有这些列，
#: 造成下游以为 relay 审计可执行。现在缺列会产生 error 级 finding 并阻断质量闸门。
FIELD_ANNOTATIONS: dict[str, dict] = {
    "asset_id": {"semantic": "结果代币标识"},
    "block_timestamp": {"semantic": "链上出块时间（保守可用时间）", "unit": "epoch 秒 UTC"},
    "price": {"semantic": "成交概率价", "unit": "[0,1]"},
    "maker": {"semantic": "maker 钱包地址"},
    "taker": {"semantic": "taker 钱包地址"},
    "taker_direction": {"semantic": "taker 方向 BUY/SELL"},
    "usdc_amount": {"semantic": "名义金额", "unit": "USDC"},
    "fee_usdc": {"semantic": "手续费", "unit": "USDC"},
    "condition_id": {"semantic": "市场键"},
    "outcome_seq": {"semantic": "结果序号"},
    "neg_risk": {
        "semantic": "negRisk 市场标记（两段类型冲突，口径未统一；全史实测未见为真的成交）",
        "provisional": True,
    },
    "category": {"semantic": "市场类别（元数据回填）"},
    "category_refined": {"semantic": "细化类别（元数据回填）"},
    "outcome_label": {"semantic": "本代币对应结果标签"},
    "winning_outcome_label": {
        "semantic": "最终获胜结果标签",
        "banned": True,
        "banned_reason": "结算结果，历史分析中为未来信息",
    },
    "resolution_status": {
        "semantic": "结算状态",
        "banned": True,
        "banned_reason": "结算生命周期信息，历史分析中为未来信息",
    },
    "taker_base_fee": {"semantic": "taker 基础费率"},
    "maker_base_fee": {"semantic": "maker 基础费率"},
    "opens_at": {"semantic": "市场开放时间（元数据，可能回填修订）", "provisional": True},
    "close_at": {"semantic": "市场关闭时间（元数据，可能回填修订）", "provisional": True},
    "resolved_at": {
        "semantic": "市场结算时间",
        "banned": True,
        "banned_reason": "结算时间不得替代历史可用时间；仅可用于事后生命周期分析",
    },
    "market_slug": {"semantic": "市场 slug"},
    "p_event": {"semantic": "归一事件概率"},
    "D": {"semantic": "归一方向 ±1"},
}

#: 设计文档曾声称存在、但必须由实测确认的链上列。缺失即报告，不再写进合同。
EXPECTED_CHAIN_COLUMNS = (
    "block_number", "log_index", "tx_hash", "exchange", "venue_class", "protocol", "is_relay",
)


def _build_field_contract(
    hf_schema: dict[str, str], ext_schema: dict[str, str]
) -> tuple[list[FieldAvailability], list[QualityFinding]]:
    """字段合同由**实测列**生成，注解只作覆盖层。

    - 实测有列但无注解：仍进合同，标 provisional（语义未声明即不可消费）；
    - 注解有名但实测无列：不进合同，产生 error 级 finding；
    - 设计文档声称存在的链上列缺失：单独产生 error 级 finding。
    """
    findings: list[QualityFinding] = []
    observed = dict(hf_schema)
    for name, dtype in ext_schema.items():
        if name in observed and observed[name] != dtype:
            observed[name] = f"hf:{observed[name]} / ext:{dtype}"
        else:
            observed.setdefault(name, dtype)

    fields: list[FieldAvailability] = []
    for name in sorted(observed):
        anno = dict(FIELD_ANNOTATIONS.get(name, {}))
        if not anno:
            anno = {
                "semantic": "实测存在但未声明语义；没有合同即不可消费",
                "provisional": True,
            }
        fields.append(FieldAvailability(name=name, dtype=observed[name], **anno))

    declared_only = sorted(set(FIELD_ANNOTATIONS) - set(observed))
    if declared_only:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="polymarket.annotated_field_absent",
                message="字段注解引用了实测不存在的列；合同不得声明数据里没有的字段",
                evidence={"names": declared_only},
            )
        )
    missing_chain = sorted(set(EXPECTED_CHAIN_COLUMNS) - set(observed))
    if missing_chain:
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="polymarket.chain_columns_absent",
                message=(
                    "设计文档声称存在的链上列在两段实测中都不存在；"
                    "relay 剔除、unknown venue 隔离与逐笔主键去重在现有数据上无法执行"
                ),
                evidence={"missing": missing_chain, "observed_columns": len(observed)},
            )
        )
    return fields, findings


def scan(hf_root: str, ext_root: str, seam_date: str) -> SourceManifest:
    findings: list[QualityFinding] = []
    h = hashlib.sha256()

    hf_parts, hf_facts, hf_types, f1 = _scan_segment(hf_root, "hf", h)
    ext_parts, ext_facts, ext_types, f2 = _scan_segment(ext_root, "ext", h)
    findings.extend(f1)
    findings.extend(f2)

    conflicts = {
        name: {"hf": hf_types[name], "ext": ext_types[name]}
        for name in sorted(set(hf_types) & set(ext_types))
        if hf_types[name] != ext_types[name]
    }
    if conflicts:
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="polymarket.schema_conflict",
                message=f"两段 tape 存在 {len(conflicts)} 处列类型冲突，UNION 前必须统一",
                evidence=conflicts,
            )
        )

    # 接缝检查：时间范围 + 最小 row-key 采样
    hf_seam = [p.path for p in hf_parts if p.start == seam_date]
    ext_seam = [p.path for p in ext_parts if p.start == seam_date]
    seam_evidence: dict = {"seam_date": seam_date}
    hf_range = _timestamp_range_on(hf_seam) if hf_seam else None
    ext_range = _timestamp_range_on(ext_seam) if ext_seam else None
    if hf_range and ext_range:
        overlap = not (hf_range[1] < ext_range[0] or ext_range[1] < hf_range[0])
        gap_s = ext_range[0] - hf_range[1]
        seam_evidence.update(
            {"hf_range": hf_range, "ext_range": ext_range, "range_overlap": overlap,
             "gap_seconds": gap_s}
        )
        hf_keys = _seam_rowkeys(hf_seam)
        ext_keys = _seam_rowkeys(ext_seam)
        if hf_keys is None or ext_keys is None:
            findings.append(
                QualityFinding(
                    severity=Severity.ERROR,
                    code="polymarket.seam_rowkey_unavailable",
                    message="接缝日 row-key 采样列缺失，无法完成行级接缝核验",
                    evidence=seam_evidence,
                )
            )
        else:
            dup = len(hf_keys & ext_keys)
            seam_evidence.update(
                {"hf_seam_rows": len(hf_keys), "ext_seam_rows": len(ext_keys),
                 "rowkey_overlap": dup}
            )
            findings.append(
                QualityFinding(
                    severity=Severity.ERROR if (overlap or dup) else Severity.INFO,
                    code="polymarket.seam",
                    message=(
                        "接缝日存在范围重叠或复合键重复，拼接必须先去重"
                        if (overlap or dup)
                        else f"接缝无重叠：范围间隔 {gap_s} 秒，复合键交集为 0"
                    ),
                    evidence=seam_evidence,
                )
            )
    else:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="polymarket.seam_stats_missing",
                message="接缝日统计不可得（缺分区或缺列统计），接缝核验未完成",
                evidence=seam_evidence,
            )
        )

    findings.append(
        QualityFinding(
            severity=Severity.WARNING,
            code="polymarket.provisional_facts",
            message=(
                "以下事实为 provisional：relay legs 清理完备性与 unknown venue 分布"
                "（两段都缺 venue/relay 列，现有数据上不可审计）。"
                "negRisk：两段实测均未见 neg_risk 为真的成交（见 M2.5 全史普查），"
                "扩展段并未补上 HF 段的 negRisk 缺口"
            ),
        )
    )

    fields, field_findings = _build_field_contract(hf_types, ext_types)
    findings.extend(field_findings)

    ts = TimeSemantics(
        event_time="CLOB 撮合时间（不可观测）",
        publication_time="block_timestamp（链上出块，实测平均滞后撮合约 2 秒，逐笔滞后未知）",
        availability_time="block_timestamp（保守下界）",
        availability_rule="feature availability_time = block_timestamp；禁止用 resolved_at 或市场元数据的回填时间",
        timezone="UTC（epoch 秒）",
        unit_notes="block_timestamp 为 epoch 秒；毫秒/微秒量级数值应触发单位断言失败",
    )

    return SourceManifest(
        source_id="polymarket_tape",
        root_uri=f"{hf_root} + {ext_root}",
        time_semantics=ts,
        fields=fields,
        partitions=hf_parts + ext_parts,
        findings=findings,
        facts={
            "hf": hf_facts,
            "extension": ext_facts,
            "schema_conflicts": conflicts,
        },
        source_snapshot=SourceSnapshot(
            method="parquet_footer_sha256", digest=h.hexdigest(), guarantee=FOOTER_GUARANTEE
        ),
    )
