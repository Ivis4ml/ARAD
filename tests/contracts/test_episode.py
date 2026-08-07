"""Search Episode 闭环的合同测试（M4 第五块）。

一次 Episode 必须能在无人干预下走完「提案 → 冻结 → 特征 → 评价 → 判决 → 入账」，
且三种非正常产出都降级为证据而不是崩溃。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from arad.evaluation.kernel import EvaluationRequest, EvaluationRow
from arad.features.interpreter import SourceNotImplemented
from arad.harness.context import DeclaredBias, assemble_proposer_context
from arad.harness.episode import ProposalOutput, run_episode, run_round
from arad.memory.ledger import EvidenceLedger
from arad.memory.ledger import Role as LedgerRole
from arad.orchestrator.queue import DurableQueue
from arad.providers.base import EpisodeBudget
from arad.providers.mock import MockProvider

T0 = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
FAMILY = "fam"

BIASES = [DeclaredBias("菜单后见暴露", "83.7% 的族只在全史切点出现", "菜单非无偏")]


def a_proposal_json(**kw) -> str:
    payload = {
        "mechanism": "闭市期间地缘概率创新",
        "source": "polymarket", "target": "sc_rv_next_session",
        "horizon": "next_session", "universe": "sc_dominant", "direction": 1,
        "falsifiable_condition": "无关则证伪", "rationale": "菜单偏差已知，仍值得一试",
        "feature_spec": {
            "feature_id": "f1", "mechanism": "近窗均值",
            "steps": [{"name": "w", "kind": "window", "source": "commodity_bar",
                       "field": "close", "op": "mean", "window_seconds": 600}],
            "output_step": "w", "failure_condition": "窗口内无 bar 时无定义",
            "authored_by": "llm_proposer",
        },
    }
    payload.update(kw)
    return json.dumps(payload, ensure_ascii=False)


GAP_JSON = json.dumps({
    "unsupported_mechanism": {
        "mechanism": "订单簿阶梯",
        "missing_primitive": "order_book_ladder",
        "why_existing_primitives_insufficient": "现有原语只覆盖成交",
    }
}, ensure_ascii=False)


@pytest.fixture
def rig(tmp_path):
    ledger = EvidenceLedger(str(tmp_path / "l.db"))
    queue = DurableQueue(str(tmp_path / "q.db"))
    yield ledger, queue
    ledger.close()
    queue.close()


def assembler(ledger):
    def assemble(task):
        return assemble_proposer_context(
            ledger=ledger, family=FAMILY,
            data_facts={"trading_days": 909}, targets=[{"name": "sc_rv_next_session"}],
            menu=[{"family_id": "cand:hormuz"}], menu_biases=BIASES,
            budget_facts={"calls_remaining": 5}, blockers=[],
        )
    return assemble


def rows_for(n=60):
    rows, labels = [], {}
    for i in range(n):
        decision = T0 + timedelta(hours=6 * i)
        key = f"r{i:03d}"
        rows.append(EvaluationRow(
            row_key=key, episode_id=f"ep{i // 2}", date_cluster=f"d{i // 2}",
            product_cluster="sc", decision_time=decision,
            label_start=decision + timedelta(minutes=1),
            availability_times={"f": decision - timedelta(minutes=5)},
            prediction=float(i % 7), controls={"c": float(i % 3)},
        ))
        labels[key] = float((i * 13) % 11)
    return rows, labels


def evaluator_builder(n=60):
    def build(spec, study_id):
        rows, labels = rows_for(n)
        request = EvaluationRequest(
            study_id=study_id, confirmatory_id="c", family=FAMILY, rows=rows,
            authoritative_keys=[r.row_key for r in rows], cost_model_declared=True,
            placebo_draws=20, min_returns=10, min_clusters=5,
        )
        return request, labels, {"from": "2022-11-01", "to": "2024-12-31"}
    return build


def run_one(rig, script, builder=None, budget=None):
    ledger, queue = rig
    queue.enqueue("t0", "study", {"study_id": "s0"}, now=T0)
    provider = MockProvider(scripts={"proposer": script})
    return run_round(
        queue=queue, ledger=ledger, provider=provider,
        budget=budget or EpisodeBudget(max_calls=10), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=builder or evaluator_builder(),
        now=T0,
    ), provider


# ---------------------------------------------------------------- 闭环


def test_a_full_round_reaches_a_verdict_and_records_everything(rig):
    ledger, _ = rig
    outcome, _ = run_one(rig, [a_proposal_json()])
    assert outcome.outcome == "evaluated"
    # 五个值全部是合法完整产出。null 此前不可达（决定 0005 之前判决只有
    # `BLOCKED if blocked else CANDIDATE` 两条路），这条断言写于那个时期
    assert outcome.verdict in {"candidate", "null", "blocked", "underpowered"}
    kinds = [e["event_type"] for e in ledger.read_events(
        role=LedgerRole.EVALUATOR, study_id="s0")]
    for required in ("context_assembled", "proposal_locked", "hypothesis_locked",
                     "confirmatory_locked", "study_created", "feature_spec_locked",
                     "visible_data_range", "evaluation_result", "verdict_recorded"):
        assert required in kinds, required
    assert ledger.require_intact() > 0


def test_the_round_produces_blinded_feedback(rig):
    outcome, _ = run_one(rig, [a_proposal_json()])
    rendered = outcome.feedback.render()
    for leak in ("beta", "t_stat", "sharpe", "p_value"):
        assert leak not in rendered.lower()


def test_both_denominators_move(rig):
    ledger, _ = rig
    run_one(rig, [a_proposal_json()])
    d = ledger.denominators(FAMILY)
    assert d["proposal_denominator"] == 1
    assert d["statistical_denominator"] == 1  # 读过 outcome 就必须计入


def test_the_context_the_model_saw_is_replayable(rig):
    ledger, _ = rig
    run_one(rig, [a_proposal_json()])
    events = ledger.read_events(role=LedgerRole.EVALUATOR, study_id="s0")
    ctx = next(e for e in events if e["event_type"] == "context_assembled")
    assert ctx["payload"]["context_id"]
    assert ctx["payload"]["declared_biases"][0]["name"] == "菜单后见暴露"


# ---------------------------------------------------------------- 三种降级


def test_bad_json_becomes_evidence_and_the_task_is_requeued(rig):
    ledger, queue = rig
    outcome, _ = run_one(rig, ["不是 JSON"])
    assert outcome.outcome == "parse_failure"
    assert queue.get("t0")["state"] == "ready"      # 任务没丢
    assert queue.get("t0")["last_error"]
    kinds = [e["event_type"] for e in ledger.read_events(role=LedgerRole.EVALUATOR)]
    assert "parse_failure" in kinds


def test_a_declared_primitive_gap_is_a_screened_out_proposal(rig):
    ledger, queue = rig
    outcome, _ = run_one(rig, [GAP_JSON])
    assert outcome.outcome == "primitive_gap"
    d = ledger.denominators(FAMILY)
    assert d["proposal_denominator"] == 1
    assert d["proposals_screened_out"] == 1     # 缺口进分母，标为挡下
    assert queue.get("t0")["state"] == "done"   # 不是失败，任务正常结束
    kinds = [e["event_type"] for e in ledger.read_events(role=LedgerRole.EVALUATOR)]
    assert "primitive_gap_declared" in kinds


def test_an_unimplemented_source_yields_blocked_not_a_crash(rig):
    def build(spec, study_id):
        raise SourceNotImplemented("解释器尚未接入数据源 'pm_market'")

    outcome, _ = run_one(rig, [a_proposal_json()], builder=build)
    assert outcome.outcome == "interpretation_gap"
    assert outcome.verdict == "blocked"


def test_too_few_defined_points_yields_underpowered(rig):
    def build(spec, study_id):
        return None, {}, {"note": "定义点过少"}

    outcome, _ = run_one(rig, [a_proposal_json()], builder=build)
    assert outcome.outcome == "underpowered"
    assert outcome.verdict == "underpowered"


def test_a_proposal_missing_required_fields_is_rejected(rig):
    _, queue = rig
    outcome, _ = run_one(rig, [json.dumps({"mechanism": "只有机制"})])
    assert outcome.outcome == "invalid_proposal"
    assert queue.get("t0")["state"] == "ready"


# ---------------------------------------------------------------- Episode 语义


def test_episode_ends_when_the_budget_runs_out_not_the_service(rig):
    ledger, queue = rig
    for i in range(5):
        queue.enqueue(f"t{i}", "study", {"study_id": f"s{i}"}, now=T0)
    provider = MockProvider(scripts={"proposer": [a_proposal_json()]})
    result = run_episode(
        episode_id="e1", queue=queue, ledger=ledger, provider=provider,
        budget=EpisodeBudget(max_calls=2), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=evaluator_builder(), now=T0,
    )
    assert result.ended_because == "budget_exhausted"
    assert queue.service_state()["state"] == "running"   # 服务没停


def test_episode_ends_cleanly_when_there_is_no_work(rig):
    ledger, queue = rig
    provider = MockProvider(scripts={"proposer": [a_proposal_json()]})
    result = run_episode(
        episode_id="e2", queue=queue, ledger=ledger, provider=provider,
        budget=EpisodeBudget(max_calls=5), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=evaluator_builder(), now=T0,
    )
    assert result.ended_because == "no_runnable_work"
    assert result.rounds == []
    assert queue.service_state()["state"] == "running"


def test_episode_summary_is_recorded(rig):
    ledger, queue = rig
    queue.enqueue("t0", "study", {"study_id": "s0"}, now=T0)
    provider = MockProvider(scripts={"proposer": [a_proposal_json()]})
    run_episode(
        episode_id="e3", queue=queue, ledger=ledger, provider=provider,
        budget=EpisodeBudget(max_calls=5), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=evaluator_builder(), now=T0,
    )
    kinds = [e["event_type"] for e in ledger.read_events(role=LedgerRole.EVALUATOR)]
    assert "episode_started" in kinds and "episode_ended" in kinds


def test_multiple_rounds_run_until_work_is_exhausted(rig):
    ledger, queue = rig
    for i in range(3):
        queue.enqueue(f"t{i}", "study", {"study_id": f"s{i}"}, now=T0)
    provider = MockProvider(scripts={"proposer": [a_proposal_json()]})
    result = run_episode(
        episode_id="e4", queue=queue, ledger=ledger, provider=provider,
        budget=EpisodeBudget(max_calls=20), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=evaluator_builder(), now=T0,
    )
    assert len(result.rounds) == 3
    assert result.ended_because == "no_runnable_work"
    d = ledger.denominators(FAMILY)
    # 内容寻址：同样内容的提案就是同一个提案，分母不因重复提交而膨胀
    assert d["proposal_denominator"] == 1
    # 但每次读 outcome 都必须计入统计分母 —— FWER 关心的是检验次数
    assert d["statistical_denominator"] == 3


def test_distinct_proposals_each_enter_the_proposal_denominator(rig):
    ledger, queue = rig
    horizons = ["next_session", "next_day", "next_week"]
    for i in range(3):
        queue.enqueue(f"t{i}", "study", {"study_id": f"s{i}"}, now=T0)
    provider = MockProvider(
        scripts={"proposer": [a_proposal_json(horizon=h) for h in horizons]}
    )
    run_episode(
        episode_id="e5", queue=queue, ledger=ledger, provider=provider,
        budget=EpisodeBudget(max_calls=20), family=FAMILY, owner="w1",
        assemble=assembler(ledger), build_evaluation=evaluator_builder(), now=T0,
    )
    assert ledger.denominators(FAMILY)["proposal_denominator"] == 3


def test_proposal_output_accepts_either_a_proposal_or_a_gap():
    full = ProposalOutput.model_validate(json.loads(a_proposal_json()))
    assert full.is_gap() is False
    gap = ProposalOutput.model_validate(json.loads(GAP_JSON))
    assert gap.is_gap() is True


def test_a_leaking_context_degrades_to_evidence_instead_of_killing_the_episode(rig):
    """菜单来自数据，token 里出现 alpha/beta/return 是迟早的事。"""
    ledger, queue = rig
    queue.enqueue("t0", "study", {"study_id": "s0"}, now=T0)

    def leaking_assemble(task):
        return assemble_proposer_context(
            ledger=ledger, family=FAMILY, data_facts={},
            targets=[], menu=[{"family_id": "cand:alpha"}], menu_biases=BIASES,
            budget_facts={}, blockers=[],
        )

    result = run_episode(
        episode_id="e-leak", queue=queue, ledger=ledger,
        provider=MockProvider(scripts={"proposer": [a_proposal_json()]}),
        budget=EpisodeBudget(max_calls=5), family=FAMILY, owner="w1",
        assemble=leaking_assemble, build_evaluation=evaluator_builder(), now=T0,
    )
    assert [r.outcome for r in result.rounds] == ["context_blocked"]
    kinds = [e["event_type"] for e in ledger.read_events(
        role=LedgerRole.EVALUATOR, study_id="s0")]
    assert kinds == ["context_blocked"]
    assert queue.service_state()["state"] == "running"
