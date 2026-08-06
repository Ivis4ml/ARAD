"""Evidence Ledger 与冻结规格的合同测试（M3 第一块）。

四条边界必须由代码或数据库强制，不由约定：只能追加、哈希链可检篡改、
统计分母只增不减、proposer 读不到效果字段。
"""

from __future__ import annotations

import sqlite3

import pytest
from pydantic import ValidationError

from arad.memory.ledger import (
    CapabilityDenied,
    EvidenceLedger,
    LedgerIntegrityError,
    Role,
)
from arad.memory.snapshot import (
    SnapshotIncomplete,
    collect_snapshot,
    render_markdown,
    require_complete,
)
from arad.registry.specs import (
    ConfirmatoryLock,
    HypothesisLock,
    NextAction,
    ProposalSpec,
    StudyVerdict,
    Verdict,
)


@pytest.fixture
def ledger(tmp_path):
    with EvidenceLedger(str(tmp_path / "ledger.db")) as led:
        yield led


def a_proposal(**kw) -> ProposalSpec:
    base = {
        "mechanism": "闭市期间地缘概率创新",
        "source": "polymarket",
        "target": "sc_rv_next_session",
        "horizon": "next_session",
        "universe": "sc_dominant",
        "direction": 1,
        "falsifiable_condition": "概率创新与下一 session 已实现波动无关则证伪",
        "proposed_by": "test",
    }
    base.update(kw)
    return ProposalSpec(**base)


# ---------------------------------------------------------------- 冻结规格


def test_content_id_is_stable_and_content_sensitive():
    a, b = a_proposal(), a_proposal()
    assert a.content_id == b.content_id
    assert a_proposal(direction=-1).content_id != a.content_id


def test_specs_are_frozen():
    spec = a_proposal()
    with pytest.raises(ValidationError):
        spec.mechanism = "别的机制"


@pytest.mark.parametrize("field", ["mechanism", "target", "falsifiable_condition", "proposed_by"])
def test_proposal_requires_its_core_fields(field):
    with pytest.raises(ValueError):
        a_proposal(**{field: "  "})


def test_direction_must_be_a_sign():
    with pytest.raises(ValueError):
        a_proposal(direction=2)


def test_confirmatory_lock_requires_preregistered_diagnostics():
    """事后补三个检验再继续叫 confirmatory 是不允许的。"""
    with pytest.raises(ValueError):
        ConfirmatoryLock(hypothesis_id="h", formula="f", preregistered_diagnostics=[])
    ok = ConfirmatoryLock(
        hypothesis_id="h", formula="f", preregistered_diagnostics=["placebo", "leakage"]
    )
    assert ok.content_id


def test_verdict_vocabulary_is_exactly_five_values():
    assert {v.value for v in Verdict} == {
        "candidate", "null", "underpowered", "blocked", "error"
    }
    assert "ship" not in {v.value for v in Verdict}
    assert "kill" not in {v.value for v in Verdict}


def test_scheduling_actions_are_separate_from_verdicts():
    values = {a.value for a in NextAction}
    assert "queue_forward" in values and "archive_evidence" in values
    assert values & {v.value for v in Verdict} == set()


def test_verdict_requires_a_rationale():
    with pytest.raises(ValueError):
        StudyVerdict(
            study_id="s", verdict=Verdict.NULL, next_action=NextAction.ARCHIVE_EVIDENCE,
            rationale="",
        )


# ---------------------------------------------------------------- 追加式


def test_events_cannot_be_updated(ledger):
    ledger.append("proposal_locked", {"a": 1})
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        ledger._conn.execute("UPDATE events SET payload = '{}' WHERE seq = 1")


def test_events_cannot_be_deleted(ledger):
    """禁止 KILL 删除证据：删除在数据库层失败，不靠提示词。"""
    ledger.append("proposal_locked", {"a": 1})
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        ledger._conn.execute("DELETE FROM events WHERE seq = 1")
    assert ledger.require_intact() == 1


def test_hash_chain_links_every_event(ledger):
    first = ledger.append("a", {"x": 1})
    second = ledger.append("b", {"x": 2})
    events = ledger.read_events(role=Role.EVALUATOR)
    assert events[0]["event_hash"] == first
    assert events[1]["prev_hash"] == first
    assert events[1]["event_hash"] == second
    assert ledger.require_intact() == 2


def test_tampering_breaks_the_chain(tmp_path):
    path = str(tmp_path / "l.db")
    led = EvidenceLedger(path)
    led.append("a", {"x": 1})
    led.append("b", {"x": 2})
    led.close()
    # 绕过触发器直接改写（模拟外部篡改）
    raw = sqlite3.connect(path)
    raw.executescript("DROP TRIGGER events_no_update; UPDATE events SET payload='{\"x\":99}'"
                      " WHERE seq=1;")
    raw.commit()
    raw.close()
    led = EvidenceLedger(path)
    count, broken = led.verify_chain()
    # 定位到被改动的那一条：重算哈希与存储哈希不符
    assert count == 2 and broken == [1]
    with pytest.raises(LedgerIntegrityError):
        led.require_intact()
    led.close()


# ---------------------------------------------------------------- 两本分母


def test_screened_out_proposals_still_count_in_the_proposal_denominator(ledger):
    ledger.record_proposal("p1", "fam", screened_out=False)
    ledger.record_proposal("p2", "fam", screened_out=True, reason="功效预检不足")
    d = ledger.denominators("fam")
    assert d["proposal_denominator"] == 2
    assert d["proposals_screened_out"] == 1


def test_screened_out_proposal_needs_a_reason(ledger):
    with pytest.raises(ValueError):
        ledger.record_proposal("p3", "fam", screened_out=True)


def test_statistical_denominator_counts_every_outcome_read(ledger):
    ledger.record_outcome_read("t1", "fam", "s1")
    ledger.record_outcome_read("t2", "fam", "s1")
    assert ledger.denominators("fam")["statistical_denominator"] == 2


def test_statistical_denominator_cannot_shrink(ledger):
    """看过 outcome 就必须计入；筛掉或没报告也不能回缩。"""
    ledger.record_outcome_read("t1", "fam", "s1")
    with pytest.raises(sqlite3.IntegrityError, match="cannot shrink"):
        ledger._conn.execute("DELETE FROM statistical_denominator WHERE test_id='t1'")
    with pytest.raises(sqlite3.IntegrityError, match="cannot shrink"):
        ledger._conn.execute("UPDATE statistical_denominator SET family='other'")


def test_proposal_denominator_cannot_shrink(ledger):
    ledger.record_proposal("p1", "fam")
    with pytest.raises(sqlite3.IntegrityError, match="cannot shrink"):
        ledger._conn.execute("DELETE FROM proposal_denominator WHERE proposal_id='p1'")


# ---------------------------------------------------------------- 能力边界


def test_proposer_cannot_read_effect_fields(ledger):
    ledger.append("result", {"beta": 0.42, "t_stat": 3.1, "coverage": 0.9}, study_id="s1")
    evaluator = ledger.read_events(role=Role.EVALUATOR, study_id="s1")[0]["payload"]
    assert evaluator["beta"] == 0.42
    proposer = ledger.read_events(role=Role.PROPOSER, study_id="s1")[0]["payload"]
    assert proposer["beta"] == "<redacted:effect-field>"
    assert proposer["t_stat"] == "<redacted:effect-field>"
    assert proposer["coverage"] == 0.9  # 功效与覆盖信息允许可见


def test_effect_fields_cannot_hide_in_nested_structures(ledger):
    ledger.append(
        "result",
        {"diagnostics": {"placebo": {"p_value": 0.01}}, "legs": [{"sharpe": 1.2}]},
        study_id="s1",
    )
    payload = ledger.read_events(role=Role.PROPOSER, study_id="s1")[0]["payload"]
    assert payload["diagnostics"]["placebo"]["p_value"] == "<redacted:effect-field>"
    assert payload["legs"][0]["sharpe"] == "<redacted:effect-field>"


def test_proposer_cannot_dump_the_whole_ledger(ledger):
    ledger.append("result", {"beta": 1.0}, study_id="s1")
    with pytest.raises(CapabilityDenied):
        ledger.read_events(role=Role.PROPOSER)


# ---------------------------------------------------------------- 快照渲染


def _full_study(ledger) -> str:
    proposal = a_proposal()
    hyp = HypothesisLock(proposal_id=proposal.content_id, experiment_family="fam")
    conf = ConfirmatoryLock(
        hypothesis_id=hyp.content_id, formula="rv ~ innovation + controls",
        preregistered_diagnostics=["placebo", "leakage", "influence"],
    )
    sid = "study-1"
    ledger.record_proposal(proposal.content_id, "fam")
    ledger.append("proposal_locked", proposal.payload(), study_id=sid)
    ledger.append("hypothesis_locked", hyp.payload(), study_id=sid)
    ledger.append("confirmatory_locked", conf.payload(), study_id=sid)
    ledger.append(
        "visible_data_range",
        {"from": "2022-11-01", "to": "2024-12-31", "segment": "discovery"},
        study_id=sid,
    )
    ledger.record_outcome_read("t1", "fam", sid)
    verdict = StudyVerdict(
        study_id=sid, verdict=Verdict.NULL, next_action=NextAction.ARCHIVE_EVIDENCE,
        rationale="效应方向与预注册不符且不显著",
    )
    ledger.append("verdict_recorded", verdict.payload(), study_id=sid)
    return sid


def test_a_synthetic_study_replays_into_a_self_contained_snapshot(ledger):
    sid = _full_study(ledger)
    events = ledger.read_events(role=Role.EVALUATOR, study_id=sid)
    snap = require_complete(collect_snapshot(events, ledger.denominators("fam")))
    assert snap["verdict"]["verdict"] == "null"
    assert snap["proposal"]["mechanism"]
    assert snap["confirmatory_lock"]["preregistered_diagnostics"]
    text = render_markdown(snap)
    assert "判决快照" in text and "statistical denominator" in text
    assert "forward 数据与标签不可见" in text


def test_a_missing_lock_is_reported_as_a_ledger_gap(ledger):
    """拼不出完整快照即账本缺口，必须报错而不是渲染出残缺快照。"""
    ledger.append("proposal_locked", {"mechanism": "m"}, study_id="s2")
    ledger.append(
        "verdict_recorded",
        {"study_id": "s2", "verdict": "null", "next_action": "archive_evidence",
         "rationale": "r"},
        study_id="s2",
    )
    events = ledger.read_events(role=Role.EVALUATOR, study_id="s2")
    with pytest.raises(SnapshotIncomplete, match="hypothesis_lock"):
        require_complete(collect_snapshot(events, ledger.denominators()))


def test_blocked_study_needs_no_outcome_reads(ledger):
    """blocked 与 underpowered 可能一次 outcome 都没读，仍必须能渲染快照。"""
    sid = "s3"
    for kind, payload in (
        ("proposal_locked", {"mechanism": "m"}),
        ("hypothesis_locked", {"experiment_family": "fam"}),
        ("confirmatory_locked", {"formula": "f"}),
        ("visible_data_range", {"from": "2022-11-01", "to": "2024-12-31"}),
        ("verdict_recorded", {"study_id": sid, "verdict": "blocked",
                              "next_action": "wait_for_data", "rationale": "数据缺口"}),
    ):
        ledger.append(kind, payload, study_id=sid)
    events = ledger.read_events(role=Role.EVALUATOR, study_id=sid)
    snap = require_complete(collect_snapshot(events, ledger.denominators()))
    assert snap["outcome_reads"] == []
