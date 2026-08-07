"""上下文组装器的合同测试（M4 第三块）。

给 LLM 看什么决定它提什么，所以这一层和评价机一样是研究完整性的一部分。
"""

from __future__ import annotations

import json

import pytest

from arad.harness.context import (
    CONTEXT_VERSION,
    ContextBundle,
    DeclaredBias,
    assemble_proposer_context,
    blinded_history,
    primitive_catalogue,
    record_context,
    render_proposer_prompt,
)
from arad.memory.ledger import EvidenceLedger
from arad.memory.ledger import Role as LedgerRole
from arad.providers.base import ContextLeak, Role

BIASES = [
    DeclaredBias(
        name="菜单后见暴露",
        measurement="2,108 个候选族中 83.7% 只在全史归纳切点才出现",
        consequence="菜单里的机制不是从无偏的宇宙里抽出来的",
    ),
    DeclaredBias(
        name="结果相邻性",
        measurement="晚涌现族在大波动日上的活动份额 27.9%，早涌现族 17.4%，置换 p<0.002",
        consequence="全史归纳在与结果相关的通道上做过选择",
    ),
]


@pytest.fixture
def ledger(tmp_path):
    with EvidenceLedger(str(tmp_path / "l.db")) as led:
        yield led


def build(ledger, **kw):
    base = {
        "ledger": ledger,
        "family": "fam",
        "data_facts": {"sources": ["commodity_bar", "pm_market"], "trading_days": 909},
        "targets": [{"name": "sc_rv_next_session", "rows": 1816}],
        "menu": [{"family_id": "cand:hormuz", "head_tokens": ["hormuz", "strait"]}],
        "menu_biases": BIASES,
        "budget_facts": {"calls_remaining": 5},
        "blockers": ["Polymarket 逐笔 belief 序列未物化"],
    }
    base.update(kw)
    return assemble_proposer_context(**base)


# ---------------------------------------------------------------- 盲化


def test_effect_fields_never_reach_the_proposer_prompt(ledger):
    """账本里有效果字段，但组装出的 prompt 里不能有。"""
    ledger.append("result", {"beta": 0.42, "t_stat": 3.1}, study_id="s1")
    ledger.append(
        "verdict_recorded",
        {"study_id": "s1", "verdict": "null", "next_action": "archive_evidence",
         "rationale": "r"},
        study_id="s1",
    )
    bundle = build(ledger)
    lowered = bundle.prompt.lower()
    for leak in ("beta", "t_stat", "p_value", "sharpe"):
        assert leak not in lowered


def test_assembly_fails_loudly_if_a_leak_slips_in(ledger):
    """组装器自己也可能引入效果字段；渲染后必须再检一次。"""
    with pytest.raises(ContextLeak):
        build(ledger, data_facts={"note": "上一轮 beta 是 0.42"})


def test_history_comes_from_the_blinded_ledger_view(ledger):
    ledger.append("result", {"sharpe": 2.0}, study_id="s1")
    ledger.append(
        "verdict_recorded",
        {"study_id": "s1", "verdict": "underpowered", "next_action": "queue_forward",
         "rationale": "样本不足"},
        study_id="s1",
    )
    history = blinded_history(ledger, "fam")
    assert history["verdict_taxonomy"] == {"underpowered": 1}
    assert "不可见" in history["note"]
    assert json.dumps(history, ensure_ascii=False).count("sharpe") == 0


def test_proposer_sees_verdict_categories_but_not_effects(ledger):
    for i, verdict in enumerate(["null", "blocked", "underpowered"]):
        sid = f"s{i}"
        ledger.append(
            "verdict_recorded",
            {"study_id": sid, "verdict": verdict, "next_action": "archive_evidence",
             "rationale": "r"},
            study_id=sid,
        )
    history = blinded_history(ledger, "fam")
    assert set(history["verdict_taxonomy"]) == {"null", "blocked", "underpowered"}


# ---------------------------------------------------------------- 菜单偏差


def test_declared_biases_must_appear_in_the_prompt(ledger):
    """菜单偏差藏起来就会原样传导成提案偏差且无人知晓。"""
    bundle = build(ledger)
    for bias in BIASES:
        assert bias.name in bundle.prompt
        assert bias.measurement in bundle.prompt
        assert bias.consequence in bundle.prompt


def test_bias_is_quantified_not_hand_waved():
    """偏差必须带实测数字，不能只是"可能有偏"。"""
    for bias in BIASES:
        assert any(ch.isdigit() for ch in bias.measurement), bias.name


def test_bundle_records_its_biases_for_the_ledger(ledger):
    payload = build(ledger).ledger_payload()
    assert len(payload["declared_biases"]) == len(BIASES)
    assert payload["declared_biases"][0]["name"] == "菜单后见暴露"


# ---------------------------------------------------------------- 可回放


def test_the_same_state_yields_the_same_context_id(ledger):
    assert build(ledger).context_id == build(ledger).context_id


def test_changing_the_menu_changes_the_context_id(ledger):
    a = build(ledger)
    b = build(ledger, menu=[{"family_id": "cand:oil", "head_tokens": ["oil"]}])
    assert a.context_id != b.context_id


def test_rendering_is_deterministic(ledger):
    bundle = build(ledger)
    assert render_proposer_prompt(bundle.facts, BIASES) == bundle.prompt


def test_context_is_recorded_as_evidence(ledger):
    bundle = build(ledger)
    record_context(ledger, bundle, "s1")
    events = ledger.read_events(role=LedgerRole.EVALUATOR, study_id="s1")
    recorded = [e for e in events if e["event_type"] == "context_assembled"]
    assert len(recorded) == 1
    payload = recorded[0]["payload"]
    assert payload["context_id"] == bundle.context_id
    assert payload["context_version"] == CONTEXT_VERSION
    assert payload["facts"]["targets"][0]["name"] == "sc_rv_next_session"


# ---------------------------------------------------------------- 原语与合同


def test_primitive_catalogue_is_narrow_and_states_its_rules():
    cat = primitive_catalogue()
    assert cat["step_kinds"] == [
        "difference", "innovation", "ratio", "residualise", "window", "zscore",
    ]
    assert any("offset_seconds 只能非负" in r for r in cat["hard_rules"])
    assert any("UnsupportedMechanism" in r for r in cat["hard_rules"])


def test_prompt_tells_the_model_that_declaring_a_gap_is_valuable(ledger):
    prompt = build(ledger).prompt
    assert "unsupported_mechanism" in prompt
    assert "不是失败" in prompt


def test_prompt_states_what_is_hidden_and_why(ledger):
    """模型应当知道自己被盲化了，以及为什么 —— 否则它会以为信息缺失是疏漏。"""
    prompt = build(ledger).prompt
    assert "看不到" in prompt
    assert "事前假设" in prompt


def test_blockers_and_budget_reach_the_prompt(ledger):
    prompt = build(ledger).prompt
    assert "belief 序列未物化" in prompt
    assert "calls_remaining" in prompt


def test_bundle_is_immutable(ledger):
    import dataclasses

    bundle = build(ledger)
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.prompt = "别的"


def test_context_bundle_requires_a_role():
    with pytest.raises(TypeError):
        ContextBundle(facts={}, prompt="x")  # type: ignore[call-arg]


def test_role_is_the_proposer_role(ledger):
    assert build(ledger).role is Role.PROPOSER


def test_step_schema_matches_the_model_so_a_compliant_model_is_not_rejected():
    """提示词里的字段清单与 Step 的必填集合必须一致。

    这类遗漏已经发生过两次：提示词没写字段名，模型照做却被 extra="forbid" 拒掉。
    把两边钉在一起，第三次就不可能了。
    """
    from arad.features.spec import Step, StepKind
    from arad.harness.context import STEP_SCHEMA

    probe = {
        StepKind.WINDOW: {"source": "commodity_bar", "field": "close", "op": "mean",
                          "window_seconds": 600},
        StepKind.INNOVATION: {"source": "commodity_bar", "field": "close", "op": "mean",
                              "window_seconds": 600, "baseline_seconds": 6000},
        StepKind.RATIO: {"inputs": ["a", "b"]},
        StepKind.DIFFERENCE: {"inputs": ["a", "b"]},
        StepKind.ZSCORE: {"inputs": ["a"], "window_seconds": 36000,
                          "sample_every_seconds": 3600, "min_samples": 5},
        StepKind.RESIDUALISE: {"inputs": ["a"], "controls": ["c"]},
    }
    for kind, fields in probe.items():
        declared = set(STEP_SCHEMA[kind.value]["required"]) - {"name", "kind"}
        assert declared == set(fields), f"{kind.value}: schema 与模型的必填集合不一致"
        # 按 schema 声明的字段构造必须成功：模型照着提示词写就不该被拒
        Step(name="s", kind=kind, **fields)


def test_proposal_output_types_cover_every_field() -> None:
    """顶层字段的类型必须逐个写进契约，不能只写字段名。

    实测：一次真实调用里模型把 `direction` 写成 "positive"，三次尝试全被拒，
    八分钟与三次调用预算白花，而那一次的 feature_spec 完全合法。
    原因是 output_contract 只列了字段名。契约与模型钉在一起，就不会再漏。
    """
    from arad.harness.context import PROPOSAL_OUTPUT_TYPES
    from arad.harness.episode import ProposalOutput

    described = set(PROPOSAL_OUTPUT_TYPES)
    fields = set(ProposalOutput.model_fields) - {"feature_spec", "unsupported_mechanism"}
    assert fields <= described, f"契约漏了字段：{sorted(fields - described)}"
    assert described <= set(ProposalOutput.model_fields), (
        f"契约写了模型没有的字段：{sorted(described - set(ProposalOutput.model_fields))}"
    )
    # direction 的类型必须明确到"整数"，写"方向"是不够的
    assert "整数" in PROPOSAL_OUTPUT_TYPES["direction"]


def test_direction_accepts_closed_word_vocabulary_and_rejects_the_rest() -> None:
    """封闭同义词表可以接受，表外的词必须整条拒掉。

    关键在后半句：`direction` 为 None 时 `to_proposal()` 会写成 0，
    于是一条 falsifiable_condition 写着「为正」的提案会带着「无方向主张」通过，
    预注册就成了空的。宁可整条被拒。
    """
    import pytest
    from pydantic import ValidationError

    from arad.harness.episode import ProposalOutput

    assert ProposalOutput(direction="positive").direction == 1
    assert ProposalOutput(direction="NEGATIVE").direction == -1
    assert ProposalOutput(direction=" short ").direction == -1
    assert ProposalOutput(direction=-1).direction == -1
    for bad in ("上升", "either", "sign", ""):
        with pytest.raises(ValidationError):
            ProposalOutput(direction=bad)
