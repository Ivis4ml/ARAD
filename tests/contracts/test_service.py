"""连续研究服务与语义审计的合同测试（M6）。

这一层的存在理由是「循环不能停在一张写死的变体表上」。因此测试盯的是：
诊断是盲化的、错配的一版不消耗多重检验预算、诊断会被记住而不是来回震荡、
停滞由与结果无关的判据触发，且停下来时是**请求人工复核**而不是自行判定没戏。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from arad.features.spec import FeatureSpec, Op, Source, Step, StepKind
from arad.harness.audit import (
    SEMANTIC_MISMATCH_TAXONOMY,
    AuditInput,
    audit,
    render_for_proposer,
)
from arad.harness.context import DeclaredBias, assemble_proposer_context
from arad.harness.mutate import next_proposal
from arad.harness.service import INFRASTRUCTURE_OUTCOMES, run_service
from arad.memory.ledger import EvidenceLedger
from arad.memory.ledger import Role as LedgerRole
from arad.orchestrator.queue import DurableQueue
from arad.providers.base import ProviderRequest, ProviderResponse, Role
from arad.registry.specs import EFFECT_FIELDS

RETURN_TARGET = {
    "name": "sc_ret_next_session", "label_rule": "entry_to_close",
    "label_is_return": True, "tradable_claim": True,
}
RV_TARGET = {
    "name": "sc_rv_next_session", "label_rule": "full_session",
    "label_is_return": False, "tradable_claim": False,
}


def magnitude_feature() -> FeatureSpec:
    return FeatureSpec(
        feature_id="rv_z", mechanism="已实现波动的短期创新", output_step="w",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="realised_volatility", op=Op.MEAN, window_seconds=600)],
    )


def signed_feature() -> FeatureSpec:
    return FeatureSpec(
        feature_id="mom", mechanism="价格动量", output_step="w",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="log_return", op=Op.SUM, window_seconds=600)],
    )


def an_input(feature, target, **kw) -> AuditInput:
    base = {
        "feature": feature, "target_record": target, "proposal_direction": 1,
        "falsifiable_condition": "斜率不显著异于零则证伪",
        "wired_sources": frozenset({"commodity_bar"}),
    }
    base.update(kw)
    return AuditInput(**base)


def test_a_magnitude_feature_against_a_signed_label_is_caught_without_any_effect():
    """这个诊断本会话由人做出，全程没有用到任何效应量。"""
    found = audit(an_input(magnitude_feature(), RETURN_TARGET))
    assert [m.code for m in found] == ["magnitude_vs_signed_label"]


def test_the_same_feature_is_fine_against_a_magnitude_label():
    assert audit(an_input(magnitude_feature(), RV_TARGET)) == []


def test_a_signed_feature_against_a_signed_label_passes():
    assert audit(an_input(signed_feature(), RETURN_TARGET)) == []


def test_an_undeclared_direction_cannot_be_falsified_on_a_signed_label():
    found = audit(an_input(signed_feature(), RETURN_TARGET, proposal_direction=0))
    assert [m.code for m in found] == ["direction_undeclared"]


def test_an_unwired_source_is_caught_before_any_data_is_touched():
    feature = FeatureSpec(
        feature_id="pm", mechanism="概率创新", output_step="w",
        failure_condition="无数据", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.PM_MARKET,
                    field="mid_price", op=Op.LAST, window_seconds=600)],
    )
    found = audit(an_input(feature, RETURN_TARGET))
    assert "source_not_wired" in [m.code for m in found]


def test_what_reaches_the_proposer_is_a_closed_vocabulary_with_no_numbers():
    """自由文本会成为把效应走私给下一版的通道，因此词表必须封闭。"""
    rendered = render_for_proposer(audit(an_input(magnitude_feature(), RETURN_TARGET)))
    dumped = json.dumps(rendered, ensure_ascii=False)
    assert all(m["code"] in SEMANTIC_MISMATCH_TAXONOMY for m in rendered)
    for leak in EFFECT_FIELDS:
        assert leak not in dumped.lower()
    assert not any(ch.isdigit() for ch in "".join(m["explanation"] for m in rendered))


def test_the_mutator_switches_mechanism_when_told_the_label_is_signed():
    magnitude, _ = next_proposal(step_index=0, mismatch_codes=(),
                                 target_name="sc_ret_next_session")
    fixed, plan = next_proposal(step_index=1,
                                mismatch_codes=("magnitude_vs_signed_label",),
                                target_name="sc_ret_next_session", parent=1)
    fields = {s["field"] for s in json.loads(magnitude)["feature_spec"]["steps"] if s.get("field")}
    fixed_fields = {s["field"] for s in json.loads(fixed)["feature_spec"]["steps"] if s.get("field")}
    assert fields == {"realised_volatility"}
    assert fixed_fields == {"log_return"}
    assert plan.reason_code == "magnitude_vs_signed_label"


def test_paired_window_features_never_use_two_equal_windows():
    """两窗相等时 difference/ratio 恒为零或一，评价机会正确地报「回归元没有变异」，
    但那一轮白花。动量、关注度两类都是成对窗口，都要守这一条。"""
    for step in range(18):
        spec = json.loads(next_proposal(
            step_index=step, mismatch_codes=("magnitude_vs_signed_label",),
            target_name="sc_ret_next_session", parent=1,
        )[0])["feature_spec"]
        paired = [s for s in spec["steps"] if s.get("window_seconds")]
        if len(paired) != 2 or {s["field"] for s in paired} != {paired[0]["field"]}:
            continue
        # 同字段的两个窗口：要么窗长不同，要么用 offset 取的是不同时段
        a, b = paired
        assert (a["window_seconds"] != b["window_seconds"]
                or a.get("offset_seconds", 0) != b.get("offset_seconds", 0)), (step, spec)


def test_the_loop_can_now_express_polymarket_features():
    """接入 pm_market 之前循环一个另类因子都产不出，搜索空间整个落在量价对照集里。"""
    sources = set()
    for step in range(12):
        spec = json.loads(next_proposal(
            step_index=step, mismatch_codes=("magnitude_vs_signed_label",),
            target_name="sc_ret_next_session", parent=1,
        )[0])
        sources.add(spec["source"])
    assert "polymarket" in sources
    assert "commodity_bar" in sources


def test_the_mutator_is_deterministic():
    a = next_proposal(step_index=3, mismatch_codes=(), target_name="t")[0]
    b = next_proposal(step_index=3, mismatch_codes=(), target_name="t")[0]
    assert a == b


def test_every_mutation_is_a_valid_spec():
    for step in range(16):
        for codes in ((), ("magnitude_vs_signed_label",)):
            payload = json.loads(next_proposal(
                step_index=step, mismatch_codes=codes, target_name="t", parent=1)[0])
            FeatureSpec(**payload["feature_spec"])


@pytest.mark.parametrize("code", sorted(SEMANTIC_MISMATCH_TAXONOMY))
def test_every_taxonomy_entry_explains_itself_without_numbers(code):
    text = SEMANTIC_MISMATCH_TAXONOMY[code]
    assert text.strip()
    assert not any(ch.isdigit() for ch in text)


# ------------------------------------------- 停止语义：故障不是「问不出新东西」
#
# 这一节钉的是一次真实事故：`--provider claude` 的第一轮里，模型三次都把
# `direction` 写成 `"positive"`，三次尝试全被拒，八分钟与三次调用预算白花。
# 服务当时把「这一轮没走到提案」按停滞计数，于是一个 schema 缺陷会被写成
# 「模型问不出新东西」请人来看。两种停法要人做的判断不是一回事，必须分开。

T0 = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)
FAMILY = "fam"
UNPARSEABLE = "我认为应当研究地缘风险与原油的关系。"


class NeverParses:
    """执行通道彻底不可用：每次都返回读不出 JSON 的输出。"""

    model_id = "never_parses"

    def __init__(self, raw: str = UNPARSEABLE) -> None:
        self.raw = raw
        self.calls = 0

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(
            request_id=request.request_id, role=Role.PROPOSER,
            raw_text=self.raw, model_id=self.model_id,
        )


@pytest.fixture
def rig(tmp_path):
    ledger = EvidenceLedger(str(tmp_path / "l.db"))
    queue = DurableQueue(str(tmp_path / "q.db"))
    yield ledger, queue
    ledger.close()
    queue.close()


def _assembler(ledger):
    def assemble(task):
        return assemble_proposer_context(
            ledger=ledger, family=FAMILY,
            data_facts={"trading_days": 909}, targets=[{"name": "sc_rv_next_session"}],
            menu=[{"family_id": "cand:hormuz"}],
            menu_biases=[DeclaredBias("菜单后见暴露", "只在全史切点出现", "菜单非无偏")],
            budget_facts={"calls_remaining": 5}, blockers=[],
        )
    return assemble


def _never_called(*a, **kw):  # pragma: no cover - 没形成提案时不该走到评价
    raise AssertionError("没有形成提案的一轮不该进入评价")


def _run(rig, provider, **kw):
    ledger, queue = rig
    return run_service(
        ledger=ledger, queue=queue, provider=provider, family=FAMILY, owner="w1",
        assemble=_assembler(ledger), build_evaluation=_never_called,
        audit_input=_never_called, seed_task={}, calls_per_episode=6,
        stall_rounds=3, now=T0, **kw,
    )


def test_repeated_parse_failure_is_not_reported_as_stalled(rig):
    ledger, _ = rig
    result = _run(rig, NeverParses(), max_rounds=8)
    assert result.stopped_because == "provider_unusable", (
        "连续解析失败是执行通道故障，不是「问不出新东西」"
    )
    assert result.infrastructure_failures == 3
    assert result.distinct_features == 0
    # 请人来看的理由必须说清这不是研究结论
    reviews = [e["payload"] for e in ledger.read_events(role=LedgerRole.HUMAN)
               if e["event_type"] == "human_review_required"]
    assert len(reviews) == 1
    assert "不构成关于该机制族的任何研究结论" in reviews[0]["reason"]
    assert "新的提案内容" not in reviews[0]["reason"]


def test_infrastructure_outcomes_are_exactly_the_pre_proposal_failures():
    """名单必须与 episode 里那几个"还没形成提案"的结局一致。

    漏一个，该结局就会重新被算进停滞；多一个，真正的停滞就永远判不出来。
    判据可验证：这些结局都在 `record_proposal` 之前返回，因此既没有 proposal_id
    也没有 feature_id，对"还有没有新问题可问"不构成任何证据。
    """
    assert INFRASTRUCTURE_OUTCOMES == {
        "parse_failure", "provider_error", "context_blocked", "invalid_proposal",
    }


def test_parse_failure_records_every_attempt_not_just_the_last(rig):
    """三次尝试各错在哪都要留下，否则下一次多分钟的失败同样无从查起。"""
    ledger, _ = rig
    _run(rig, NeverParses(), max_rounds=1)
    failures = [e["payload"] for e in ledger.read_events(role=LedgerRole.HUMAN)
                if e["event_type"] == "parse_failure"]
    assert failures, "解析失败必须进账本"
    payload = failures[0]
    assert len(payload["attempt_errors"]) == payload["attempts"] == 3
    # 摘录截在 500 字，靠长度才能把截断与格式错误分开
    assert payload["raw_length"] == len(UNPARSEABLE)


def test_a_word_direction_no_longer_burns_the_round(rig):
    """真实事故的回归：`"positive"` 曾让三次尝试全废。

    现在它规范化为 1，一次调用即通过解析。这里只验"不再重试到死"；
    提案缺其余必填字段仍会被判 invalid_proposal，那是另一回事。
    """
    ledger, _ = rig
    provider = NeverParses(raw='{"direction": "positive"}')
    result = _run(rig, provider, max_rounds=1)
    assert provider.calls == 1, "解析通过就不该有修复重试"
    events = [e["event_type"] for e in ledger.read_events(role=LedgerRole.HUMAN)]
    assert "parse_failure" not in events
    assert result.infrastructure_failures == 1
