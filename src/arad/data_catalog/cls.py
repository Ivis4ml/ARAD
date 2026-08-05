"""财联社电报历史数据的只读扫描器。

逐文件行数与表头一致性、逐日覆盖与缺口、内容抽样（Time 格式、Content 非空）。
互动量字段（Reads/Comments/Shares）为抓取时刻快照，历史分析中永久禁用。
"""

from __future__ import annotations

import csv
import glob
import hashlib
import os
import random
import re
from collections import defaultdict
from datetime import date, timedelta

from .schema import (
    CoveragePartition,
    FieldAvailability,
    QualityFinding,
    Severity,
    SourceManifest,
    SourceSnapshot,
    TimeSemantics,
)

CONTENT_GUARANTEE = (
    "对全部 CSV 文件的原始字节按文件名序聚合 sha256（全文哈希）。"
    "可检测：任何内容修改（含等长替换）、文件增删。无已知盲区。"
)

_FNAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\.csv$")
_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")

EXPECTED_HEADER = ["Index", "Time", "Title", "Content", "Labels", "Reads", "Comments", "Shares"]


def _count_rows(path: str) -> tuple[int, list[str]]:
    """返回 (数据行数, 表头)。逐块计数，避免整文件载入。"""
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        n = sum(1 for _ in reader)
    return n, header


def scan(output_dir: str, filename_pattern: str, content_sample_files: int = 12) -> SourceManifest:
    files = sorted(glob.glob(os.path.join(output_dir, filename_pattern)))
    findings: list[QualityFinding] = []
    per_year_rows: dict[str, int] = defaultdict(int)
    per_year_files: dict[str, int] = defaultdict(int)
    dates: list[date] = []
    bad_headers: list[str] = []
    total_rows = 0

    partitions: list[CoveragePartition] = []
    year_first_last: dict[str, list[str]] = {}
    h = hashlib.sha256()

    for fp in files:
        m = _FNAME_RE.search(os.path.basename(fp))
        if not m:
            continue
        d = date.fromisoformat(m.group(1))
        dates.append(d)
        h.update(os.path.basename(fp).encode())
        with open(fp, "rb") as raw:
            while chunk := raw.read(1 << 20):
                h.update(chunk)
        n, header = _count_rows(fp)
        total_rows += n
        y = str(d.year)
        per_year_rows[y] += n
        per_year_files[y] += 1
        yr = year_first_last.setdefault(y, [m.group(1), m.group(1)])
        yr[0], yr[1] = min(yr[0], m.group(1)), max(yr[1], m.group(1))
        if header != EXPECTED_HEADER:
            bad_headers.append(fp)

    for y in sorted(per_year_rows):
        partitions.append(
            CoveragePartition(
                key=y,
                path=output_dir,
                files=per_year_files[y],
                rows=per_year_rows[y],
                start=year_first_last[y][0],
                end=year_first_last[y][1],
            )
        )

    if not files or total_rows == 0:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="cls.empty_source",
                message="未发现任何数据文件或数据行（路径或文件名模式错误）",
                evidence={"output_dir": output_dir, "files": len(files), "rows": total_rows},
            )
        )

    # 日历缺口（自然日口径；本源为全年每日发布）
    gaps: list[str] = []
    if dates:
        dset = set(dates)
        cur, end = min(dates), max(dates)
        while cur <= end:
            if cur not in dset:
                gaps.append(cur.isoformat())
            cur += timedelta(days=1)
    if gaps:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="cls.calendar_gap",
                message=f"{len(gaps)} 个自然日缺失",
                evidence={"days": gaps[:50]},
            )
        )
    if bad_headers:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="cls.header_mismatch",
                message=f"{len(bad_headers)} 个文件表头与预期不符",
                evidence={"paths": bad_headers[:10]},
            )
        )

    # 内容抽样
    rng = random.Random(20260805)
    sample = rng.sample(files, min(content_sample_files, len(files)))
    bad_time = 0
    empty_content = 0
    sampled_rows = 0
    for fp in sample:
        with open(fp, newline="", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                sampled_rows += 1
                if not _TIME_RE.match((row.get("Time") or "").strip()):
                    bad_time += 1
                if not (row.get("Content") or "").strip():
                    empty_content += 1
    findings.append(
        QualityFinding(
            severity=Severity.INFO if bad_time == 0 and empty_content == 0 else Severity.WARNING,
            code="cls.content_sample",
            message="内容抽样：Time 格式与 Content 非空检查",
            evidence={
                "sampled_files": len(sample),
                "sampled_rows": sampled_rows,
                "bad_time_format": bad_time,
                "empty_content": empty_content,
            },
        )
    )
    findings.append(
        QualityFinding(
            severity=Severity.INFO,
            code="cls.in_roll_universe",
            message=(
                "覆盖率限定：历史回填只见 in_roll=1 的可见母体；相对实时快照并集的内容"
                "覆盖率经归日比对为 99% 至 100%（scripts/verify_cls_coverage.py），"
                "未进入滚动列表的条目两个来源都不可见"
            ),
        )
    )
    findings.append(
        QualityFinding(
            severity=Severity.INFO,
            code="cls.coverage_end",
            message="数据止于最后覆盖日；此后缺口的回爬属于 acquisition 流程，需人类授权",
            evidence={"last_day": max(dates).isoformat() if dates else None},
        )
    )

    fields = [
        FieldAvailability(name="Index", dtype="int64", semantic="源内序号"),
        FieldAvailability(name="Time", dtype="str", semantic="发布时刻（北京时间，日期在文件名）", unit="HH:MM:SS"),
        FieldAvailability(name="Title", dtype="str", semantic="正文【】前缀的提取（约 21% 为空，非缺失）"),
        FieldAvailability(name="Content", dtype="str", semantic="电报正文（中位约 155 字）"),
        FieldAvailability(name="Labels", dtype="str", semantic="主题/板块标签（约 82.6% 覆盖）"),
        FieldAvailability(
            name="Reads", dtype="int64", semantic="阅读数（抓取时刻快照）",
            banned=True, banned_reason="抓取时刻累计值，含事后信息（前视）；历史部分已饱和无截面信息",
        ),
        FieldAvailability(
            name="Comments", dtype="int64", semantic="评论数（抓取时刻快照）",
            banned=True, banned_reason="抓取时刻累计值，含事后信息（前视）",
        ),
        FieldAvailability(
            name="Shares", dtype="int64", semantic="分享数（抓取时刻快照）",
            banned=True, banned_reason="抓取时刻累计值，含事后信息（前视）",
        ),
    ]

    ts = TimeSemantics(
        event_time="电报发布时刻（文件名日期 + Time）",
        publication_time="等同 event_time（财联社滚动列表实时发布）",
        availability_time="publication_time 加轮询延迟；历史回放取 publication_time 并加保守延迟参数",
        availability_rule="feature availability_time = 文件名日期 + Time（Asia/Shanghai）+ 声明的采集延迟",
        timezone="Asia/Shanghai",
        unit_notes="Time 无日期成分，跨零点电报归属由文件名日期决定",
    )

    return SourceManifest(
        source_id="cls_telegraph",
        root_uri=output_dir,
        time_semantics=ts,
        fields=fields,
        partitions=partitions,
        findings=findings,
        facts={
            "files": len(files),
            "rows": total_rows,
            "first_day": min(dates).isoformat() if dates else None,
            "last_day": max(dates).isoformat() if dates else None,
            "calendar_gaps": len(gaps),
        },
        source_snapshot=SourceSnapshot(
            method="content_sha256", digest=h.hexdigest(), guarantee=CONTENT_GUARANTEE
        ),
    )
