"""Research Atlas 的合同测试（M9）。

Atlas 的价值只有在两件事同时成立时才存在：它讲得清楚一次 Episode，
且它讲的每一句都能追回账本。因此这里的测试盯的是**映射的边界**，不是外观：
没有 Study 归属的事件不能消失、没有 study_created 的轮次不能被当成账本缺口、
真实的账本缺口必须刺眼、渲染不得写入账本、forward 不得可见。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from arad.atlas.project import project
from arad.atlas.render import render_html, render_site
from arad.atlas.sources import data_freshness
from arad.memory.ledger import EvidenceLedger, Role
from arad.memory.snapshot import SnapshotIncomplete
from arad.registry.specs import (
    ConfirmatoryLock,
    HypothesisLock,
    NextAction,
    ProposalSpec,
    StudySpec,
    StudyVerdict,
    Verdict,
)

T0 = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
FAMILY = "fam"


@pytest.fixture
def ledger(tmp_path):
    with EvidenceLedger(str(tmp_path / "l.db")) as led:
        yield led


def a_study(
    led: EvidenceLedger,
    study_id: str,
    *,
    verdict: Verdict = Verdict.BLOCKED,
    next_action: NextAction = NextAction.ARCHIVE_EVIDENCE,
    with_evaluation: bool = False,
    omit_visible_range: bool = False,
    mechanism: str = "闭市期间地缘概率创新",
) -> None:
    proposal = ProposalSpec(
        mechanism=mechanism, source="polymarket", target="sc_rv_next_session",
        horizon="next_session", universe="sc_dominant", direction=1,
        falsifiable_condition="无关则证伪", proposed_by="llm_proposer",
    )
    hypothesis = HypothesisLock(proposal_id=proposal.content_id, experiment_family=FAMILY)
    confirmatory = ConfirmatoryLock(
        hypothesis_id=hypothesis.content_id, formula="y ~ x",
        preregistered_diagnostics=["leakage", "placebo"],
    )
    study = StudySpec(study_id=study_id, proposal_id=proposal.content_id,
                      hypothesis_id=hypothesis.content_id,
                      confirmatory_id=confirmatory.content_id)
    led.record_proposal(proposal.content_id, FAMILY)
    led.append("proposal_locked", proposal.payload(), study_id=study_id)
    led.append("hypothesis_locked", hypothesis.payload(), study_id=study_id)
    led.append("confirmatory_locked", confirmatory.payload(), study_id=study_id)
    led.append("study_created", study.payload(), study_id=study_id)
    if not omit_visible_range:
        led.append("visible_data_range", {"segment": "discovery", "rows": 1027},
                   study_id=study_id)
    if with_evaluation:
        led.record_outcome_read(f"{study_id}:main", FAMILY, study_id)
        led.append("evaluation_result", {
            "evaluator_version": "0.1.0",
            "coverage": {"rows_submitted": 1027},
            "effects": {"slope": 0.411649, "t_stat": 5.642207},
            "diagnostics": {"placebo": {"placebo_exceed_rate": 0.0}},
            "blocked_reasons": ["未声明成本模型：不得取 candidate"],
            "suggested_verdict": "blocked",
            "request_digest": "a" * 64, "result_digest": "b" * 64,
        }, study_id=study_id)
    led.append("verdict_recorded", StudyVerdict(
        study_id=study_id, verdict=verdict, next_action=next_action,
        rationale="演示",
    ).payload(), study_id=study_id)


def an_episode(led: EvidenceLedger, *, with_gap: bool = True) -> None:
    led.append("episode_started", {"episode_id": "e1", "family": FAMILY,
                                   "budget": {"max_calls": 12}})
    if with_gap:
        led.append("primitive_gap_declared", {
            "mechanism": "闭市期间地缘政治概率的跳变强度",
            "missing_primitive": "event_count_since_last_session_close",
            "why_existing_primitives_insufficient": "现有 window 算子只能按固定秒数回看",
        })
    led.append("episode_ended", {"episode_id": "e1", "rounds": 2,
                                 "ended_because": "no_runnable_work",
                                 "outcomes": {"evaluated": 1, "primitive_gap": 1}})


# ------------------------------------------------------- 没有 Study 归属的事件


def test_events_without_a_study_survive_into_the_episode_layer(ledger):
    an_episode(ledger)
    a_study(ledger, "s0")
    p = project(ledger, family=FAMILY)
    kinds = [e["event_type"] for ep in p.episodes for e in ep["events"]]
    assert "primitive_gap_declared" in kinds
    assert p.totals["primitive_gaps"] == 1


def test_the_declared_gap_is_actually_rendered(ledger):
    an_episode(ledger)
    html = render_html(project(ledger, family=FAMILY))
    assert "event_count_since_last_session_close" in html
    assert "声明原语缺口" in html


def test_an_orphan_gap_outside_any_episode_is_not_dropped(ledger):
    ledger.append("primitive_gap_declared", {"mechanism": "m", "missing_primitive": "p",
                                             "why_existing_primitives_insufficient": "q"})
    p = project(ledger, family=FAMILY)
    assert p.totals["primitive_gaps"] == 1
    assert "无 Episode 归属" in p.episodes[-1]["episode_id"]


# ------------------------------------------------------- 有 study_id 不等于有 Study


def test_a_round_without_study_created_is_an_aborted_round_not_a_ledger_gap(ledger):
    ledger.append("context_assembled", {"context_id": "c"}, study_id="s9")
    ledger.append("parse_failure", {"attempts": 3, "last_error": "not json"},
                  study_id="s9")
    p = project(ledger, family=FAMILY)
    assert p.studies == []
    assert [a["study_id"] for a in p.aborted_rounds] == ["s9"]
    assert "无法解析" in p.aborted_rounds[0]["reason"]


def test_a_real_ledger_gap_is_loud(ledger):
    a_study(ledger, "s0", omit_visible_range=True)
    with pytest.raises(SnapshotIncomplete):
        project(ledger, family=FAMILY)


def test_the_loud_failure_can_be_inspected_without_strict_mode(ledger):
    """诊断时可以关掉严格模式，但那不是默认，也不写进渲染路径。"""
    a_study(ledger, "s0", omit_visible_range=True)
    p = project(ledger, family=FAMILY, strict=False)
    assert p.studies[0]["snapshot"]["visible_data_range"] is None


# ------------------------------------------------------- 能力边界


def test_atlas_reads_as_human_so_the_snapshot_layer_is_not_empty(ledger):
    a_study(ledger, "s0", with_evaluation=True)
    p = project(ledger, family=FAMILY)
    effects = p.studies[0]["snapshot"]["evaluation"]["effects"]
    assert effects["slope"] == pytest.approx(0.411649)
    assert "5.64221" in render_html(p)


def test_forward_is_shown_as_reserved_never_as_data(ledger):
    a_study(ledger, "s0", verdict=Verdict.UNDERPOWERED,
            next_action=NextAction.QUEUE_FORWARD)
    p = project(ledger, family=FAMILY)
    assert p.studies[0]["forward_reserved"] is True
    html = render_html(p)
    assert "预约待裁决" in html
    assert "forward 区间的数据与标签在 Atlas 中不可见" in html


def test_rendering_never_writes_to_the_ledger(ledger, tmp_path):
    a_study(ledger, "s0", with_evaluation=True)
    an_episode(ledger)
    before = ledger.require_intact()
    render_site(project(ledger, family=FAMILY), tmp_path / "site")
    after, broken = ledger.verify_chain()
    assert (after, broken) == (before, [])


# ------------------------------------------------------- 完整性与产物


def test_a_tampered_ledger_is_reported_not_hidden(ledger, tmp_path):
    """触发器挡住进程内的改写，哈希链挡住绕过触发器的改写。两道都要有。"""
    a_study(ledger, "s0")
    ledger.close()
    import sqlite3

    attacker = sqlite3.connect(str(tmp_path / "l.db"))
    attacker.execute("DROP TRIGGER events_no_update")   # 拥有文件即可绕过触发器
    attacker.execute("UPDATE events SET payload='{}' WHERE seq=2")
    attacker.commit()
    attacker.close()
    with EvidenceLedger(str(tmp_path / "l.db")) as reopened:
        p = project(reopened, family=FAMILY, strict=False)
        assert p.chain["intact"] is False
        assert "哈希链断裂" in render_html(p)


def test_the_site_writes_both_a_page_and_a_machine_readable_copy(ledger, tmp_path):
    a_study(ledger, "s0", with_evaluation=True)
    an_episode(ledger)
    paths = render_site(project(ledger, family=FAMILY), tmp_path / "site",
                        freshness=[{"source_id": "commodity_tick", "status": "已扫描"}])
    doc = json.loads(Path(paths["data"]).read_text(encoding="utf-8"))
    assert doc["denominators"]["statistical_denominator"] == 1
    assert doc["data_freshness"][0]["source_id"] == "commodity_tick"
    assert "<!doctype html>" in Path(paths["index"]).read_text(encoding="utf-8")


def test_payload_text_cannot_inject_markup(ledger):
    a_study(ledger, "s0", mechanism="<script>alert(1)</script>")
    html = render_html(project(ledger, family=FAMILY))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_coverage_counts_studies_by_family_source_and_horizon(ledger):
    a_study(ledger, "s0")
    a_study(ledger, "s1", mechanism="另一个机制")
    cells = project(ledger, family=FAMILY).coverage
    assert len(cells) == 1
    assert cells[0]["studies"] == 2
    assert cells[0]["verdicts"] == {"blocked": 2}


def test_missing_source_manifests_are_reported_not_guessed(tmp_path):
    rows = data_freshness(tmp_path)
    assert [r["status"] for r in rows] == ["manifest 未生成"] * 3


def test_a_full_projection_survives_a_ledger_with_only_an_episode(ledger):
    """第一版可能一个 Study 都没有，只有缺口声明。Atlas 仍必须渲染得出来。"""
    an_episode(ledger)
    html = render_html(project(ledger, family=FAMILY))
    assert "尚无 Study" in html
    assert "event_count_since_last_session_close" in html


def test_events_are_read_with_the_human_role(ledger):
    """proposer 视图会遮蔽效果字段；Atlas 若用它，快照层就空了。"""
    a_study(ledger, "s0", with_evaluation=True)
    blinded = ledger.read_events(role=Role.PROPOSER, study_id="s0")
    payloads = [e["payload"] for e in blinded if e["event_type"] == "evaluation_result"]
    assert payloads and "slope" not in json.dumps(payloads[0])
    assert "slope" in json.dumps(project(ledger, family=FAMILY).to_dict(), default=str)
