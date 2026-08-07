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


# ------------------------------------------------------- 谱系与演化曲线（M9.1）


def a_chain(led: EvidenceLedger, ids: list[str], *, t_stats: list[float]) -> None:
    """一条父子相连的演化链，每一版带一个 t 值。"""
    parent: str | None = None
    for study_id, t in zip(ids, t_stats, strict=True):
        proposal = ProposalSpec(
            mechanism="波动聚集", source="commodity_bar", target="sc_rv_next_session",
            horizon="next_session", universe="sc_dominant", direction=1,
            falsifiable_condition="无关则证伪", proposed_by="llm_proposer",
        )
        hypothesis = HypothesisLock(proposal_id=proposal.content_id, experiment_family=FAMILY)
        confirmatory = ConfirmatoryLock(hypothesis_id=hypothesis.content_id, formula="y ~ x",
                                        preregistered_diagnostics=["placebo"])
        study = StudySpec(study_id=study_id, proposal_id=proposal.content_id,
                          hypothesis_id=hypothesis.content_id,
                          confirmatory_id=confirmatory.content_id,
                          parent_study_id=parent,
                          change_summary="" if parent is None else f"改到 {study_id}")
        led.record_proposal(proposal.content_id, FAMILY)
        led.append("proposal_locked", proposal.payload(), study_id=study_id)
        led.append("hypothesis_locked", hypothesis.payload(), study_id=study_id)
        led.append("confirmatory_locked", confirmatory.payload(), study_id=study_id)
        led.append("study_created", study.payload(), study_id=study_id)
        led.append("visible_data_range", {"segment": "discovery"}, study_id=study_id)
        led.record_outcome_read(f"{study_id}:main", FAMILY, study_id)
        led.append("evaluation_result", {
            "coverage": {"rows_submitted": 900},
            "effects": {"t_stat": t, "slope": 0.03,
                        "ic": {"ic_spearman": t / 40, "kind": "time_series"},
                        "performance": {"sharpe": None,
                                        "sharpe_undefined_reason": "label 不是有符号收益"}},
            "diagnostics": {"placebo": {"placebo_exceed_rate": 0.2}},
            "blocked_reasons": ["未声明成本模型：不得取 candidate"],
            "suggested_verdict": "blocked",
        }, study_id=study_id)
        led.append("verdict_recorded", StudyVerdict(
            study_id=study_id, verdict=Verdict.BLOCKED,
            next_action=NextAction.CREATE_NEW_VERSION, rationale="未声明成本模型",
        ).payload(), study_id=study_id)
        parent = study_id


def test_parent_links_become_one_chain_not_five_isolated_studies(ledger):
    a_chain(ledger, ["s0", "s1", "s2"], t_stats=[3.0, 3.4, 4.6])
    p = project(ledger, family=FAMILY)
    assert len(p.lineage) == 1
    assert p.lineage[0]["study_ids"] == ["s0", "s1", "s2"]


def test_studies_without_parents_stay_separate_chains(ledger):
    """没有父子关系就是没有。把它们按时间连成一条线会让人以为看到了演化。"""
    a_study(ledger, "s0")
    a_study(ledger, "s1", mechanism="另一个机制")
    p = project(ledger, family=FAMILY)
    assert len(p.lineage) == 2
    assert all(len(c["study_ids"]) == 1 for c in p.lineage)


def test_the_curve_carries_the_null_band_and_it_rises_with_the_tests(ledger):
    a_chain(ledger, ["s0", "s1", "s2"], t_stats=[3.0, 3.4, 4.6])
    curve = project(ledger, family=FAMILY).lineage[0]["curves"]["abs_t"]
    assert [round(p["value"], 1) for p in curve] == [3.0, 3.4, 4.6]
    assert [p["running_best"] for p in curve] == [3.0, 3.4, 4.6]
    thresholds = [p["null_threshold"] for p in curve]
    assert thresholds[0] < thresholds[1] < thresholds[2]
    assert [p["tests_so_far"] for p in curve] == [1, 2, 3]


def test_the_curve_reports_ic_and_an_undefined_sharpe_rather_than_a_number(ledger):
    a_chain(ledger, ["s0"], t_stats=[4.0])
    metrics = project(ledger, family=FAMILY).studies[0]["metrics"]
    assert metrics["ic_spearman"] == pytest.approx(0.1)
    assert metrics["sharpe"] is None
    assert "不是有符号收益" in metrics["sharpe_undefined_reason"]


def test_the_react_shell_receives_the_projection(ledger, tmp_path):
    from arad.atlas.app import DATA_ELEMENT_ID, render_app

    a_chain(ledger, ["s0", "s1"], t_stats=[3.0, 4.0])
    paths = render_app(project(ledger, family=FAMILY), tmp_path / "app",
                       freshness=[{"source_id": "commodity_tick", "status": "已扫描"}])
    html = Path(paths["index"]).read_text(encoding="utf-8")
    assert paths["renderer"] == "react"
    assert f'id="{DATA_ELEMENT_ID}"' in html
    assert html.index(DATA_ELEMENT_ID) < html.index("</head>")


def test_injected_data_cannot_close_the_script_tag(ledger, tmp_path):
    """payload 里出现 </script> 会提前结束脚本块，把其余数据当成 HTML 解析。"""
    from arad.atlas.app import render_app

    a_study(ledger, "s0", mechanism="</script><img onerror=alert(1)>")
    paths = render_app(project(ledger, family=FAMILY), tmp_path / "app")
    html = Path(paths["index"]).read_text(encoding="utf-8")
    assert "</script><img" not in html
    assert "\\u003c/script" in html


def test_a_missing_shell_fails_loudly_instead_of_rendering_a_page_without_the_curve(
    ledger, tmp_path
):
    from arad.atlas.app import AppShellMissing, render_app

    a_study(ledger, "s0")
    with pytest.raises(AppShellMissing, match="npm run build"):
        render_app(project(ledger, family=FAMILY), tmp_path / "app",
                   shell_path=tmp_path / "nope.html")


# ------------------------------------------------------- 回放与连续服务（M9.2 / M6）


def test_the_replay_is_the_ledger_in_seq_order(ledger):
    an_episode(ledger)
    a_chain(ledger, ["s0", "s1"], t_stats=[3.0, 4.0])
    beats = project(ledger, family=FAMILY).replay
    assert [b["seq"] for b in beats] == sorted(b["seq"] for b in beats)
    assert len(beats) == ledger.verify_chain()[0]


def test_the_proposal_counter_matches_the_ledger_denominator(ledger):
    """按内容去重，不是数事件次数：参数扫描的多个变体共用一个提案身份。"""
    a_chain(ledger, ["s0", "s1", "s2"], t_stats=[1.0, 2.0, 3.0])
    p = project(ledger, family=FAMILY)
    assert p.replay[-1]["proposals_so_far"] == p.denominators["proposal_denominator"]
    assert p.replay[-1]["tests_so_far"] == p.denominators["statistical_denominator"]


def test_the_point_only_lands_after_the_evaluation_not_at_proposal_time(ledger):
    a_chain(ledger, ["s0"], t_stats=[3.0])
    beats = project(ledger, family=FAMILY).replay
    pending = next(b for b in beats if b["pending_point"])
    landed = next(b for b in beats if b["reveal_point"])
    assert pending["event_type"] == "proposal_locked"
    assert landed["event_type"] == "evaluation_result"
    assert pending["seq"] < landed["seq"]
    # 中间必须隔着「读 outcome」那一拍：带正是在那里抬高
    look = next(b for b in beats if b["event_type"] == "outcome_read")
    assert pending["seq"] < look["seq"] < landed["seq"]


def test_key_moments_point_at_the_beat_where_the_band_overtakes_the_best(ledger):
    """这张图真正的结论不在曲线最高点，而在带追上 running best 的那一拍。"""
    a_chain(ledger, ["s0", "s1", "s2"], t_stats=[0.4, 0.5, 0.45])
    p = project(ledger, family=FAMILY)
    labels = [m["label"] for m in p.key_moments]
    assert "第一次读 outcome" in labels
    assert "零假设带追上 running best" in labels
    overtake = next(m for m in p.key_moments if m["label"].startswith("零假设带"))
    assert p.replay[overtake["beat"]]["event_type"] == "evaluation_result"


def test_a_chain_that_never_falls_behind_has_no_overtake_moment(ledger):
    a_chain(ledger, ["s0", "s1"], t_stats=[9.0, 9.5])
    labels = [m["label"] for m in project(ledger, family=FAMILY).key_moments]
    assert "零假设带追上 running best" not in labels


def test_studies_are_ordered_by_creation_not_lexicographically(ledger):
    """auto-study-10 的字典序在 auto-study-2 之前，而这个页面讲的就是先后。"""
    a_chain(ledger, ["s2", "s10"], t_stats=[1.0, 2.0])
    ids = [s["study_id"] for s in project(ledger, family=FAMILY).studies]
    assert ids == ["s2", "s10"]


def test_service_notes_surface_the_stop_reason(ledger):
    a_chain(ledger, ["s0"], t_stats=[1.0])
    ledger.append("service_stopped", {"stopped_because": "stalled", "rounds": 16})
    ledger.append("human_review_required", {"reason": "问不出新东西"})
    kinds = [n["event_type"] for n in project(ledger, family=FAMILY).service_notes]
    assert kinds == ["service_stopped", "human_review_required"]


def test_the_null_band_accumulates_across_the_family_not_within_a_chain(ledger):
    """分叉时链内自增会把带钉在最低点，读图的人会以为多重检验的负担没涨。"""
    a_chain(ledger, ["a0", "a1"], t_stats=[1.0, 1.1])
    a_chain(ledger, ["b0", "b1"], t_stats=[1.2, 1.3])
    p = project(ledger, family=FAMILY)
    assert len(p.lineage) == 2
    thresholds = [
        pt["null_threshold"] for c in p.lineage for pt in c["curves"]["abs_t"]
    ]
    # 四次检验，四条不同的带高；若按链自增会出现两两重复
    assert len(set(thresholds)) == 4
    assert max(thresholds) == pytest.approx(
        __import__("arad.evaluation.selection", fromlist=["x"]).expected_max_abs_z(4)
    )


def test_the_search_verdict_states_the_comparison_the_app_must_not_compute(ledger):
    a_chain(ledger, ["s0", "s1", "s2"], t_stats=[0.4, 0.5, 0.45])
    ledger.append("service_stopped", {"stopped_because": "stalled"})
    ledger.append("human_review_required", {"reason": "问不出新东西"})
    v = project(ledger, family=FAMILY).search_verdict
    assert v["best_value"] == pytest.approx(0.5)
    assert v["best_study_id"] == "s1"
    assert v["exceeded_band"] is False
    assert v["null_threshold"] > v["best_value"]
    assert v["statistical_denominator"] == 3
    assert v["stopped_because"] == "stalled"
    assert v["human_review_required"] is True
    assert "偏严" in v["caveat"]


def test_a_search_that_cleared_the_band_says_so(ledger):
    a_chain(ledger, ["s0", "s1"], t_stats=[9.0, 9.5])
    v = project(ledger, family=FAMILY).search_verdict
    assert v["exceeded_band"] is True
    assert v["best_value"] == pytest.approx(9.5)


def test_no_verdict_when_nothing_was_ever_evaluated(ledger):
    a_study(ledger, "s0")
    assert project(ledger, family=FAMILY).search_verdict is None


def test_the_verdict_sentence_is_written_by_the_projection_not_the_app(ledger):
    """同一份产物在任何人打开时必须说同一句话，因此判决句不能由前端分支拼。"""
    a_chain(ledger, ["s0"], t_stats=[1.0])
    ledger.append("human_review_required", {"reason": "问不出新东西"})
    v = project(ledger, family=FAMILY).search_verdict
    assert v["headline"] == "这一轮没有留下可用的发现，是否继续搜索已交回人工判断。"


def test_a_run_that_stopped_without_asking_for_review_says_so_more_plainly(ledger):
    a_chain(ledger, ["s0"], t_stats=[1.0])
    v = project(ledger, family=FAMILY).search_verdict
    assert v["headline"] == "这一轮没有留下可用的发现。"
