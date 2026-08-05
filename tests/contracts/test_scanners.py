"""scanner 合同测试：用合成 fixture 验证三个扫描器的关键行为。

不触碰真实 221 GB 数据；真实数据的审计由 `arad data-audit` 产出并另行核对。
"""

import csv
import os
import zipfile

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from arad.data_catalog import cls as cls_scanner
from arad.data_catalog import commodity as commodity_scanner
from arad.data_catalog import polymarket as pm_scanner
from arad.data_catalog.schema import BannedFieldAccess

# ---------- commodity ----------

def _make_zip(path, entries, utf8=False):
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in entries:
            if not utf8:
                # 模拟 CP437 存储的 GBK 文件名
                name = name.encode("gbk").decode("cp437")
            zf.writestr(name, content)


def test_commodity_scanner_decodes_gbk_and_counts_days(tmp_path):
    root = tmp_path
    (root / "2023").mkdir()
    _make_zip(
        root / "2023" / "202301.zip",
        [
            ("202301/20230103/rb2305_20230103.csv", "TradingDay\n20230103\n"),
            ("202301/20230103/rb主力连续_20230103.csv", "TradingDay\n20230103\n"),
            ("202301/20230104/cu2302_20230104.csv", "TradingDay\n20230104\n"),
        ],
    )
    (root / "202607").mkdir()
    _make_zip(
        root / "202607" / "20260701.zip",
        [("AP610_20260701.csv", "TradingDay\n20260701\n")],
        utf8=True,
    )
    m = commodity_scanner.scan(str(root), ["2023/*.zip", "202607/*.zip"])
    assert m.facts["trading_days"] == 3
    assert m.facts["first_day"] == "20230103"
    assert m.facts["last_day"] == "20260701"
    assert "rb" in m.facts["products_nominal"]
    assert "AP" in m.facts["products_nominal"]
    enc = next(f for f in m.findings if f.code == "commodity.filename_encoding")
    assert enc.evidence.get("cp437/gbk", 0) == 3
    assert enc.evidence.get("utf8", 0) == 1


def test_commodity_scanner_reports_bad_zip(tmp_path):
    bad = tmp_path / "202502.zip"
    bad.write_bytes(b"not a zip")
    m = commodity_scanner.scan(str(tmp_path), ["*.zip"])
    assert any(f.code == "commodity.bad_zip" for f in m.findings)


# ---------- polymarket ----------

def _write_parquet(path, ts_values, neg_risk_type="string"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if neg_risk_type == "string":
        neg = pa.array(["f"] * len(ts_values), type=pa.string())
    else:
        neg = pa.array([False] * len(ts_values), type=pa.bool_())
    t = pa.table(
        {
            "block_timestamp": pa.array(ts_values, type=pa.int64()),
            "asset_id": pa.array(["a1"] * len(ts_values), type=pa.string()),
            "price": pa.array([0.5] * len(ts_values), type=pa.float64()),
            "usdc_amount": pa.array([100.0] * len(ts_values), type=pa.float64()),
            "neg_risk": neg,
        }
    )
    pq.write_table(t, path)


def test_polymarket_scanner_detects_type_conflict_and_clean_seam(tmp_path):
    hf = tmp_path / "hf"
    ext = tmp_path / "ext"
    seam = "2026-04-28"
    _write_parquet(str(hf / f"date={seam}" / "part.parquet"), [1_745_800_000, 1_745_820_000])
    _write_parquet(
        str(ext / f"{seam}.parquet"), [1_745_820_240, 1_745_830_000], neg_risk_type="bool"
    )
    m = pm_scanner.scan(str(hf), str(ext), seam)
    conflicts = m.facts["schema_conflicts"]
    assert "neg_risk" in conflicts
    seam_finding = next(f for f in m.findings if f.code == "polymarket.seam")
    assert seam_finding.evidence["range_overlap"] is False
    assert seam_finding.evidence["gap_seconds"] == 240


def test_polymarket_scanner_flags_seam_overlap_as_error(tmp_path):
    hf = tmp_path / "hf"
    ext = tmp_path / "ext"
    seam = "2026-04-28"
    _write_parquet(str(hf / f"date={seam}" / "part.parquet"), [1_745_800_000, 1_745_830_000])
    _write_parquet(str(ext / f"{seam}.parquet"), [1_745_820_000, 1_745_840_000])
    m = pm_scanner.scan(str(hf), str(ext), seam)
    seam_finding = next(f for f in m.findings if f.code == "polymarket.seam")
    assert seam_finding.severity.value == "error"
    assert seam_finding.evidence["range_overlap"] is True


def test_polymarket_resolved_at_is_banned():
    """字段合同来自实测 schema，因此用真实 manifest 断言禁用集合。"""
    from arad.data_catalog.schema import load_manifest

    m = load_manifest("artifacts/manifests/polymarket_tape.json")
    assert {"resolved_at", "winning_outcome_label", "resolution_status"} <= m.banned_fields()


def test_polymarket_contract_only_declares_columns_that_exist():
    """M1 第三轮修复：合同曾声明 7 个数据里没有的链上列，导致下游以为 relay 可审计。"""
    from arad.data_catalog.schema import load_manifest

    m = load_manifest("artifacts/manifests/polymarket_tape.json")
    names = {f.name for f in m.fields}
    assert names & {"tx_hash", "log_index", "venue_class", "is_relay", "protocol", "exchange"} == set()
    finding = next(f for f in m.findings if f.code == "polymarket.chain_columns_absent")
    assert set(finding.evidence["missing"]) >= {"is_relay", "venue_class", "tx_hash"}


# ---------- cls ----------

def _write_cls_csv(path, rows, header=None):
    header = header or cls_scanner.EXPECTED_HEADER
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def test_cls_scanner_counts_and_flags_gap_and_bans_engagement(tmp_path):
    _write_cls_csv(
        tmp_path / "财联社电报2024-01-01.csv",
        [[1, "08:00:00", "t", "内容A", "标签", 1, 2, 3]],
    )
    # 2024-01-02 缺失
    _write_cls_csv(
        tmp_path / "财联社电报2024-01-03.csv",
        [[1, "09:00:00", "t", "内容B", "标签", 1, 2, 3],
         [2, "10:00:00", "t", "内容C", "标签", 1, 2, 3]],
    )
    m = cls_scanner.scan(str(tmp_path), "财联社电报*.csv", content_sample_files=2)
    assert m.facts["rows"] == 3
    assert m.facts["calendar_gaps"] == 1
    gap = next(f for f in m.findings if f.code == "cls.calendar_gap")
    assert gap.evidence["days"] == ["2024-01-02"]
    assert m.banned_fields() == {"Reads", "Comments", "Shares"}
    with pytest.raises(BannedFieldAccess):
        m.require_analysis_view(["Content", "Reads"])


def test_cls_scanner_flags_header_mismatch(tmp_path):
    _write_cls_csv(
        tmp_path / "财联社电报2024-01-01.csv",
        [[1, "08:00:00", "x"]],
        header=["Index", "Time", "Body"],
    )
    m = cls_scanner.scan(str(tmp_path), "财联社电报*.csv", content_sample_files=1)
    assert any(f.code == "cls.header_mismatch" for f in m.findings)
