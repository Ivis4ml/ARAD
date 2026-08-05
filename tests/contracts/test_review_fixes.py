"""M1 交叉审查修复的回归测试。

对应 Codex 审查的两个 P0 与三个 P1：
- P0 空数据源必须阻断质量闸门；
- P0 指纹必须能检测等长内容变化；
- P1 全分区 schema 漂移审计；
- P1 provisional 字段默认禁止消费；
- 最小 seam row-key 采样。
"""

import zipfile

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from arad.data_catalog import cls as cls_scanner
from arad.data_catalog import commodity as commodity_scanner
from arad.data_catalog import polymarket as pm_scanner
from arad.data_catalog.schema import ProvisionalFieldAccess

# ---------- P0: 空数据源阻断 ----------

def test_empty_commodity_source_blocks_gate(tmp_path):
    m = commodity_scanner.scan(str(tmp_path), ["*.zip"])
    assert not m.gate_passed()
    assert any(f.code == "commodity.no_archives" for f in m.findings)


def test_empty_polymarket_source_blocks_gate(tmp_path):
    m = pm_scanner.scan(str(tmp_path / "hf"), str(tmp_path / "ext"), "2026-04-28")
    assert not m.gate_passed()
    codes = {f.code for f in m.gate_errors()}
    assert "polymarket.hf.empty" in codes
    assert "polymarket.ext.empty" in codes
    assert "polymarket.seam_stats_missing" in codes


def test_empty_cls_source_blocks_gate(tmp_path):
    m = cls_scanner.scan(str(tmp_path), "财联社电报*.csv", content_sample_files=1)
    assert not m.gate_passed()
    assert any(f.code == "cls.empty_source" for f in m.findings)


def test_cli_returns_nonzero_on_gate_failure(tmp_path):
    import yaml

    from arad.cli import data_audit

    cfg = {
        "commodity_tick": {"root": str(tmp_path / "c"), "layouts": ["*.zip"]},
        "polymarket": {
            "hf_daily_aligned": str(tmp_path / "hf"),
            "extension_tape": str(tmp_path / "ext"),
            "seam_date": "2026-04-28",
        },
        "cls": {"output_dir": str(tmp_path / "n"), "filename_pattern": "*.csv"},
    }
    cfg_path = tmp_path / "sources.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert data_audit(str(cfg_path), str(tmp_path / "out")) == 2


# ---------- P0: 指纹检测等长内容变化 ----------

def _commodity_zip(root, payload: bytes):
    (root / "2023").mkdir(exist_ok=True)
    with zipfile.ZipFile(root / "2023" / "202301.zip", "w") as zf:
        zf.writestr("202301/20230103/rb2305_20230103.csv", payload)


def test_fingerprint_detects_equal_length_zip_content_change(tmp_path):
    _commodity_zip(tmp_path, b"TradingDay\n2023010A\n")
    m1 = commodity_scanner.scan(str(tmp_path), ["2023/*.zip"])
    _commodity_zip(tmp_path, b"TradingDay\n2023010B\n")
    m2 = commodity_scanner.scan(str(tmp_path), ["2023/*.zip"])
    assert m1.source_snapshot.digest != m2.source_snapshot.digest
    assert m1.compute_fingerprint() != m2.compute_fingerprint()


def test_fingerprint_detects_equal_length_cls_content_change(tmp_path):
    p = tmp_path / "财联社电报2024-01-01.csv"
    header = "Index,Time,Title,Content,Labels,Reads,Comments,Shares\n"
    p.write_text(header + "1,08:00:00,t,内容A,标,1,2,3\n", encoding="utf-8")
    m1 = cls_scanner.scan(str(tmp_path), "财联社电报*.csv", content_sample_files=1)
    p.write_text(header + "1,08:00:00,t,内容B,标,1,2,3\n", encoding="utf-8")
    m2 = cls_scanner.scan(str(tmp_path), "财联社电报*.csv", content_sample_files=1)
    assert m1.source_snapshot.digest != m2.source_snapshot.digest
    assert m1.compute_fingerprint() != m2.compute_fingerprint()


def test_polymarket_snapshot_declares_guarantee(tmp_path):
    hf, ext = tmp_path / "hf", tmp_path / "ext"
    _write_pm(str(hf / "date=2026-04-28" / "a.parquet"), [1_745_800_000])
    _write_pm(str(ext / "2026-04-28.parquet"), [1_745_820_000])
    m = pm_scanner.scan(str(hf), str(ext), "2026-04-28")
    assert m.source_snapshot is not None
    assert "不可检测" in m.source_snapshot.guarantee


# ---------- P1: 全分区 schema 漂移 ----------

def _write_pm(path, ts_values, extra_col=False, asset="a1"):
    import os

    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "block_timestamp": pa.array(ts_values, type=pa.int64()),
        "asset_id": pa.array([asset] * len(ts_values), type=pa.string()),
        "price": pa.array([0.5] * len(ts_values), type=pa.float64()),
        "usdc_amount": pa.array([100.0] * len(ts_values), type=pa.float64()),
    }
    if extra_col:
        data["drifted"] = pa.array([1] * len(ts_values), type=pa.int32())
    pq.write_table(pa.table(data), path)


def test_schema_drift_across_partitions_is_reported(tmp_path):
    hf, ext = tmp_path / "hf", tmp_path / "ext"
    _write_pm(str(hf / "date=2026-04-27" / "a.parquet"), [1_745_700_000])
    _write_pm(str(hf / "date=2026-04-28" / "b.parquet"), [1_745_800_000], extra_col=True)
    _write_pm(str(ext / "2026-04-28.parquet"), [1_745_820_000])
    m = pm_scanner.scan(str(hf), str(ext), "2026-04-28")
    drift = [f for f in m.findings if f.code == "polymarket.hf.schema_drift"]
    assert len(drift) == 1
    assert m.facts["hf"]["schema_signatures"] == 2


# ---------- seam row-key 采样 ----------

def test_seam_rowkey_duplicate_is_error(tmp_path):
    hf, ext = tmp_path / "hf", tmp_path / "ext"
    # 同一复合键 (ts, asset, price, usdc) 出现在两段 → 必须 error
    _write_pm(str(hf / "date=2026-04-28" / "a.parquet"), [1_745_800_000, 1_745_810_000])
    _write_pm(str(ext / "2026-04-28.parquet"), [1_745_810_000, 1_745_830_000])
    m = pm_scanner.scan(str(hf), str(ext), "2026-04-28")
    seam = next(f for f in m.findings if f.code == "polymarket.seam")
    assert seam.severity.value == "error"
    assert seam.evidence["rowkey_overlap"] == 1


def test_seam_clean_when_keys_disjoint(tmp_path):
    hf, ext = tmp_path / "hf", tmp_path / "ext"
    _write_pm(str(hf / "date=2026-04-28" / "a.parquet"), [1_745_800_000])
    _write_pm(str(ext / "2026-04-28.parquet"), [1_745_820_000])
    m = pm_scanner.scan(str(hf), str(ext), "2026-04-28")
    seam = next(f for f in m.findings if f.code == "polymarket.seam")
    assert seam.severity.value == "info"
    assert seam.evidence["rowkey_overlap"] == 0
    assert m.gate_passed()


# ---------- P1: provisional 字段默认禁止 ----------

def test_provisional_field_blocked_by_default(tmp_path):
    m = pm_scanner.scan(str(tmp_path / "hf"), str(tmp_path / "ext"), "2026-04-28")
    with pytest.raises(ProvisionalFieldAccess):
        m.require_analysis_view(["price", "neg_risk"])


def test_provisional_field_needs_reasoned_override(tmp_path):
    m = pm_scanner.scan(str(tmp_path / "hf"), str(tmp_path / "ext"), "2026-04-28")
    with pytest.raises(ProvisionalFieldAccess):
        m.require_analysis_view(["neg_risk"], allow_provisional={"neg_risk"})
    ok = m.require_analysis_view(
        ["neg_risk"],
        allow_provisional={"neg_risk"},
        override_reason="仅用于 negRisk 覆盖率审计，不入特征",
    )
    assert ok == ["neg_risk"]


def test_analysis_fields_excludes_provisional(tmp_path):
    m = pm_scanner.scan(str(tmp_path / "hf"), str(tmp_path / "ext"), "2026-04-28")
    fields = set(m.analysis_fields())
    assert "neg_risk" not in fields
    assert "price" in fields
