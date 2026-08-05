"""商品期货 tick 归档的只读扫描器。

只读 zip 中央目录，不解压任何数据。处理三种归档形态与两种文件名编码：
- 形态 A：2022/2023/2024 年目录下的 YYYYMM.zip，内部 YYYYMM/YYYYMMDD/*.csv，
  文件名为 CP437 存储的 GBK；
- 形态 B：根目录 YYYYMM.zip（2025 至 2026-06），同 A；
- 形态 C：202607/YYYYMMDD.zip，扁平布局，UTF-8 文件名（zip flag bit 0x800）。
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import zipfile
from collections import defaultdict

from .schema import (
    CoveragePartition,
    FieldAvailability,
    QualityFinding,
    Severity,
    SourceManifest,
    SourceSnapshot,
    TimeSemantics,
)

CD_GUARANTEE = (
    "对每个 zip 条目的 (解码文件名, CRC32, 原始大小) 按序聚合 sha256。"
    "可检测：任何改变条目 CRC 的内容修改（含等长替换）、条目增删与改名。"
    "不可检测：CRC32 碰撞级别的构造性篡改。"
)

_DAY_RE = re.compile(r"(20\d{6})")
_CONTRACT_RE = re.compile(r"([A-Za-z]{1,2})\d{3,4}_20\d{6}\.csv$")

TICK_COLUMNS: list[FieldAvailability] = [
    FieldAvailability(name="TradingDay", dtype="int64", semantic="交易日（夜盘归属次日）", unit="YYYYMMDD"),
    FieldAvailability(name="InstrumentID", dtype="str", semantic="合约代码（郑商所三位年码需补世纪位）"),
    FieldAvailability(name="UpdateTime", dtype="str", semantic="快照时刻，仅时分秒，无日期", unit="HH:MM:SS"),
    FieldAvailability(name="UpdateMillisec", dtype="int64", semantic="快照毫秒", unit="ms"),
    FieldAvailability(name="LastPrice", dtype="float64", semantic="最新价", unit="价格"),
    FieldAvailability(name="Volume", dtype="int64", semantic="日内累计成交量（需差分）", unit="手"),
    FieldAvailability(name="BidPrice1", dtype="float64", semantic="买一价（仅一档）", unit="价格"),
    FieldAvailability(name="BidVolume1", dtype="int64", semantic="买一量", unit="手"),
    FieldAvailability(name="AskPrice1", dtype="float64", semantic="卖一价（仅一档）", unit="价格"),
    FieldAvailability(name="AskVolume1", dtype="int64", semantic="卖一量", unit="手"),
    FieldAvailability(
        name="AveragePrice", dtype="float64",
        semantic="日内均价 Turnover/Volume，除郑商所外含合约乘数", unit="混合口径",
        provisional=True,
    ),
    FieldAvailability(
        name="Turnover", dtype="float64",
        semantic="日内累计成交额；郑商所不含合约乘数且存在日内倒退", unit="元（口径分交易所）",
        provisional=True,
    ),
    FieldAvailability(name="OpenInterest", dtype="float64", semantic="持仓量（瞬时水平值）", unit="手"),
    FieldAvailability(name="UpperLimitPrice", dtype="float64", semantic="当日涨停价", unit="价格"),
    FieldAvailability(name="LowerLimitPrice", dtype="float64", semantic="当日跌停价", unit="价格"),
]


def _decode_name(info: zipfile.ZipInfo) -> str:
    """zip 条目名解码：flag 0x800 为 UTF-8，否则为 CP437 存储的 GBK。"""
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


def scan(root: str, layouts: list[str]) -> SourceManifest:
    zip_paths: list[str] = []
    for pat in layouts:
        zip_paths.extend(sorted(glob.glob(os.path.join(root, pat))))
    zip_paths = sorted(set(zip_paths))

    partitions: list[CoveragePartition] = []
    findings: list[QualityFinding] = []
    day_files: dict[str, int] = defaultdict(int)
    products: set[str] = set()
    encodings: dict[str, int] = defaultdict(int)
    bad_zips: list[str] = []
    total_files = 0
    total_uncompressed = 0
    h = hashlib.sha256()

    for zp in zip_paths:
        try:
            with zipfile.ZipFile(zp) as zf:
                infos = zf.infolist()
        except zipfile.BadZipFile:
            bad_zips.append(zp)
            continue
        days_in_zip: set[str] = set()
        n_csv = 0
        z_bytes = 0
        for info in infos:
            if info.is_dir():
                continue
            name = _decode_name(info)
            h.update(f"{name}|{info.CRC}|{info.file_size}".encode())
            if not name.lower().endswith(".csv"):
                continue
            n_csv += 1
            z_bytes += info.file_size
            encodings["utf8" if info.flag_bits & 0x800 else "cp437/gbk"] += 1
            m = _DAY_RE.search(os.path.basename(zp)) or _DAY_RE.search(name)
            # 日期优先从条目路径提取（形态 A/B 内部有 YYYYMMDD 目录）
            md = _DAY_RE.findall(name)
            day = None
            for cand in md:
                if len(cand) == 8:
                    day = cand
                    break
            if day is None and m:
                day = m.group(1) if len(m.group(1)) == 8 else None
            if day:
                days_in_zip.add(day)
                day_files[day] += 1
            cm = _CONTRACT_RE.search(name)
            if cm:
                products.add(cm.group(1))
        total_files += n_csv
        total_uncompressed += z_bytes
        partitions.append(
            CoveragePartition(
                key=os.path.relpath(zp, root),
                path=zp,
                files=n_csv,
                bytes=z_bytes,
                start=min(days_in_zip) if days_in_zip else None,
                end=max(days_in_zip) if days_in_zip else None,
            )
        )

    trading_days = sorted(day_files)
    if not zip_paths:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="commodity.no_archives",
                message="未发现任何 zip 归档（路径或 layouts 配置错误）",
                evidence={"root": root, "layouts": layouts},
            )
        )
    elif total_files == 0 or not trading_days:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="commodity.empty_source",
                message="归档中没有任何 CSV 条目或无法识别任何交易日",
                evidence={"zip_count": len(zip_paths), "csv_files": total_files},
            )
        )
    if bad_zips:
        findings.append(
            QualityFinding(
                severity=Severity.ERROR,
                code="commodity.bad_zip",
                message=f"{len(bad_zips)} zip archives unreadable",
                evidence={"paths": bad_zips},
            )
        )
    findings.append(
        QualityFinding(
            severity=Severity.INFO,
            code="commodity.filename_encoding",
            message="zip 条目文件名编码分布（cp437/gbk 需转码）",
            evidence=dict(encodings),
        )
    )
    findings.append(
        QualityFinding(
            severity=Severity.WARNING,
            code="commodity.provisional_facts",
            message=(
                "以下事实为 provisional，待内容级审计确认：郑商所 Turnover 口径与倒退频率、"
                "空壳文件比例、各品种可用区间、主力连续文件与逐合约文件的全史对应关系"
            ),
        )
    )

    ts = TimeSemantics(
        event_time="TradingDay + UpdateTime + UpdateMillisec（夜盘归属次一交易日，自然日需经交易日历还原）",
        publication_time="等同 event_time（交易所实时行情广播）",
        availability_time="实时约等于 event_time；本数据集为事后归档快照，研究回放取 event_time",
        availability_rule="feature availability_time = tick event_time（还原自然日后）；归档滞后约 1 天仅影响增量更新",
        timezone="Asia/Shanghai（UpdateTime 无日期无时区，必须结合 TradingDay 与品种时段表还原）",
        unit_notes="Volume/Turnover 为日内累计量；Turnover 单位分交易所（郑商所不含乘数）",
    )

    return SourceManifest(
        source_id="commodity_tick",
        root_uri=root,
        time_semantics=ts,
        fields=TICK_COLUMNS,
        partitions=partitions,
        findings=findings,
        facts={
            "zip_count": len(zip_paths),
            "csv_files": total_files,
            "uncompressed_bytes": total_uncompressed,
            "trading_days": len(trading_days),
            "first_day": trading_days[0] if trading_days else None,
            "last_day": trading_days[-1] if trading_days else None,
            "products_nominal": sorted(products),
            "product_count_nominal": len(products),
        },
        source_snapshot=SourceSnapshot(
            method="zip_central_directory_sha256", digest=h.hexdigest(), guarantee=CD_GUARANTEE
        ),
    )
