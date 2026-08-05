"""SourceManifest 合同测试：禁用字段、未知字段、指纹确定性。"""

import pytest

from arad.data_catalog.schema import (
    BannedFieldAccess,
    CoveragePartition,
    FieldAvailability,
    SourceManifest,
    TimeSemantics,
    UnknownFieldAccess,
)


def _manifest() -> SourceManifest:
    return SourceManifest(
        source_id="cls_telegraph",
        root_uri="/tmp/x",
        time_semantics=TimeSemantics(
            event_time="e", publication_time="p", availability_time="a",
            availability_rule="r", timezone="Asia/Shanghai",
        ),
        fields=[
            FieldAvailability(name="Content", dtype="str", semantic="正文"),
            FieldAvailability(name="Labels", dtype="str", semantic="标签"),
            FieldAvailability(
                name="Reads", dtype="int64", semantic="阅读数快照",
                banned=True, banned_reason="抓取时刻累计值，前视",
            ),
        ],
        partitions=[CoveragePartition(key="2024", path="/tmp/x", files=1)],
    )


def test_banned_field_access_is_hard_error():
    m = _manifest()
    with pytest.raises(BannedFieldAccess):
        m.require_analysis_view(["Content", "Reads"])


def test_unknown_field_has_no_contract():
    m = _manifest()
    with pytest.raises(UnknownFieldAccess):
        m.require_analysis_view(["Content", "Sentiment"])


def test_allowed_view_passes():
    m = _manifest()
    assert m.require_analysis_view(["Content", "Labels"]) == ["Content", "Labels"]


def test_banned_field_requires_reason():
    with pytest.raises(ValueError):
        FieldAvailability(name="Reads", dtype="int64", semantic="x", banned=True)


def test_fingerprint_is_deterministic_and_ignores_generated_at():
    a, b = _manifest(), _manifest()
    a.finalize()
    b.finalize()
    assert a.fingerprint == b.fingerprint
    assert a.generated_at != "" and b.generated_at != ""


def test_fingerprint_changes_with_content():
    a, b = _manifest(), _manifest()
    b.partitions[0] = CoveragePartition(key="2024", path="/tmp/x", files=2)
    assert a.compute_fingerprint() != b.compute_fingerprint()
