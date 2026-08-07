"""连续研究服务与语义审计的合同测试（M6）。

这一层的存在理由是「循环不能停在一张写死的变体表上」。因此测试盯的是：
诊断是盲化的、错配的一版不消耗多重检验预算、诊断会被记住而不是来回震荡、
停滞由与结果无关的判据触发，且停下来时是**请求人工复核**而不是自行判定没戏。
"""

from __future__ import annotations

import json

import pytest

from arad.features.spec import FeatureSpec, Op, Source, Step, StepKind
from arad.harness.audit import (
    SEMANTIC_MISMATCH_TAXONOMY,
    AuditInput,
    audit,
    render_for_proposer,
)
from arad.harness.mutate import next_proposal
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
