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


# ------------------------------------------- 语义诊断必须回到提案器手里
#
# 原实现用 `if hasattr(provider, "mismatch_codes")` 回传错配码，而该属性只有确定性
# 变异器 `AutoProposer` 有，`ClaudeCliProvider` 没有 —— 诊断对真实模型被静默丢弃。
# 实跑 8 轮里最后三轮连续撞在同一个 `magnitude_vs_signed_label` 上，都被审计拦下
# 且没读 outcome（统计分母因此是 4 而不是 7），正是因为模型无从得知上一轮错在哪。
# M6 票称之为「环真正闭上的地方」，而它只对变异器闭上了。

MAGNITUDE_PROPOSAL = json.dumps({
    "mechanism": "已实现波动的短期创新", "source": "commodity_bar",
    "target": "sc_ret_next_session", "horizon": "next_session",
    "universe": "sc_dominant", "direction": 1,
    "falsifiable_condition": "斜率不显著异于零则证伪",
    "feature_spec": {
        "feature_id": "rv_w", "mechanism": "近窗已实现波动均值",
        "steps": [{"name": "w", "kind": "window", "source": "commodity_bar",
                   "field": "realised_volatility", "op": "mean", "window_seconds": 600}],
        "output_step": "w", "failure_condition": "窗口内无 bar 时无定义",
        "authored_by": "llm_proposer",
    },
}, ensure_ascii=False)


class NoMismatchAttribute:
    """真实 provider 的形状：**没有** `mismatch_codes` 属性。"""

    model_id = "no_attr"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(request_id=request.request_id, role=Role.PROPOSER,
                                raw_text=MAGNITUDE_PROPOSAL, model_id=self.model_id)


def test_semantic_diagnoses_reach_a_provider_without_the_attribute(rig):
    ledger, queue = rig
    seen_tasks: list[dict] = []

    def assemble(task):
        seen_tasks.append(task)
        return assemble_proposer_context(
            ledger=ledger, family=FAMILY, data_facts={},
            targets=[{"name": "sc_ret_next_session"}], menu=[{"family_id": "c"}],
            menu_biases=[DeclaredBias("a", "b", "c")], budget_facts={}, blockers=[],
            learned_mismatches=tuple(task["payload"].get("learned_mismatches") or ()),
        )

    def audit_input(feature, proposal):
        return AuditInput(
            feature=feature, target_record=RETURN_TARGET, proposal_direction=1,
            falsifiable_condition="斜率不显著异于零则证伪",
            wired_sources=frozenset({"commodity_bar"}),
        )

    result = run_service(
        ledger=ledger, queue=queue, provider=NoMismatchAttribute(), family=FAMILY,
        owner="w1", assemble=assemble, build_evaluation=_never_called,
        audit_input=audit_input, seed_task={}, max_rounds=3,
        calls_per_episode=6, stall_rounds=9, now=T0,
    )
    assert result.rounds == 3
    # 第一轮之后，诊断必须出现在后续每一轮的任务载荷里
    assert seen_tasks[0]["payload"]["learned_mismatches"] == []
    for task in seen_tasks[1:]:
        assert task["payload"]["learned_mismatches"] == ["magnitude_vs_signed_label"]


def test_the_diagnosis_is_rendered_into_the_prompt_with_its_explanation(rig):
    """码本身对模型没有意义，必须带上封闭词表里的解释。

    解释文本不含任何数字（有既有测试钉住整张词表），因此它不构成效应通道。
    """
    ledger, _ = rig
    bundle = assemble_proposer_context(
        ledger=ledger, family=FAMILY, data_facts={},
        targets=[{"name": "sc_ret_next_session"}], menu=[{"family_id": "c"}],
        menu_biases=[DeclaredBias("a", "b", "c")], budget_facts={}, blockers=[],
        learned_mismatches=("magnitude_vs_signed_label",),
    )
    assert "magnitude_vs_signed_label" in bundle.prompt
    assert SEMANTIC_MISMATCH_TAXONOMY["magnitude_vs_signed_label"] in bundle.prompt
    assert "不得再犯同样的错配" in bundle.prompt
    # 未登记的码不得被原样渲染出去：自由文本是效应走私的通道
    other = assemble_proposer_context(
        ledger=ledger, family=FAMILY, data_facts={},
        targets=[{"name": "t"}], menu=[{"family_id": "c"}],
        menu_biases=[DeclaredBias("a", "b", "c")], budget_facts={}, blockers=[],
        learned_mismatches=("斜率为负且 t 值 -2.66",),
    )
    assert "2.66" not in other.prompt


def test_two_runs_on_the_same_queue_both_do_work(rig):
    """队列与账本跨运行持久，因此标识必须带上运行 id。

    实测：第二次运行只跑了一轮就以 `no_runnable_work` 停止 —— `auto-task-1`
    在上一次运行里已经是 `done`，入队成了空操作。同一个缺陷更糟的一面是
    `auto-study-N` 也会撞上，两次运行的证据被写进同一个 Study 标识下，
    快照因此混成一份。
    """
    ledger, queue = rig
    ids = []
    for run_id in ("runA", "runB"):
        result = _run(rig, NeverParses(), max_rounds=2, run_id=run_id)
        assert result.stopped_because != "no_runnable_work", run_id
        assert result.rounds == 2, run_id
        ids += [queue.get(f"{run_id}-task-{i}")["task_id"] for i in range(2)]
    assert len(set(ids)) == 4, "四个任务标识必须互不相同"
    studies = {e["study_id"] for e in ledger.read_events(role=LedgerRole.HUMAN)
               if e.get("study_id")}
    assert {"runA-study-0", "runB-study-0"} <= studies


def test_a_repeated_run_id_raises_instead_of_looking_like_clean_completion(rig):
    """标识重复是操作错误，不是「没有可做的工作」。

    `no_runnable_work` 是唯一一个能由缺陷触发、却读起来像干净完成的停止理由：
    入队静默成空操作，服务退出 0，不写 human_review_required。
    实测就是这样丢掉了一次 12 轮的运行 —— 只跑了一轮。
    """
    import pytest as _pytest

    from arad.harness.service import TaskIdentifierCollision

    _run(rig, NeverParses(), max_rounds=1, run_id="same")
    with _pytest.raises(TaskIdentifierCollision, match="same"):
        _run(rig, NeverParses(), max_rounds=1, run_id="same")


def test_the_service_demo_never_passes_a_constant_run_id():
    """时间戳兜底原本写在函数末尾（只为 Atlas 的运行目录命名），
    于是 `--run-id` 缺省时 run_service 拿到的是 None，任务标识变成恒定的
    "None-task-0"，M7.2 要修的冲突原样回来。这条钉住兜底在服务启动**之前**。
    """
    import inspect

    from arad.harness import demo

    src = inspect.getsource(demo.run_service_demo)
    fallback = src.index('run_id = run_id or datetime.now(UTC).strftime')
    call = src.index("result = run_service(")
    assert fallback < call, "运行标识必须在 run_service 之前定下来"


# ------------------------------------------- 幅度判据必须是结构的，不是散文匹配


def _vol_scaled_signed_return() -> FeatureSpec:
    """波动率归一的有符号收益：分子带符号，分母是量级。

    这是真实模型在被告知「幅度对方向」之后连续七轮给出的构造，
    也正是对该诊断的**正确**回应。
    """
    return FeatureSpec(
        feature_id="sc_vol_scaled_session_return", output_step="r",
        mechanism="本 session 的对数收益，按同期已实现波动率归一后取分位排名",
        failure_condition="参考样本不足时无定义", authored_by="t",
        steps=[
            Step(name="ret", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="log_return", op=Op.SUM, window_seconds=86400),
            Step(name="vol", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="realised_volatility", op=Op.MEAN, window_seconds=864000),
            Step(name="scaled", kind=StepKind.RATIO, inputs=["ret", "vol"]),
            Step(name="r", kind=StepKind.RANK_PCT, inputs=["scaled"],
                 window_seconds=86400 * 40, sample_every_seconds=86400, min_samples=10),
        ],
    )


def _dispersion_ratio() -> FeatureSpec:
    """量级 ÷ 量级：仍然没有方向。"""
    return FeatureSpec(
        feature_id="rv_dispersion_ratio", output_step="q",
        mechanism="已实现波动率的离散度相对其自身均值",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[
            Step(name="sd", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="realised_volatility", op=Op.STD, window_seconds=864000),
            Step(name="mu", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="realised_volatility", op=Op.MEAN, window_seconds=864000),
            Step(name="q", kind=StepKind.RATIO, inputs=["sd", "mu"]),
        ],
    )


def test_a_signed_quantity_scaled_by_a_magnitude_is_still_signed():
    """实测事故：审计对 `mechanism` 与 `feature_id` 做子串匹配，
    因此任何用波动率做分母的有符号特征都被判为幅度。

    真实模型连续**七轮**提出 `sum(log_return) / mean(realised_volatility)`，
    七轮全被拦下。它无法逃出这个判定：要表达「按波动率归一」就必须提到波动率。
    判据必须是结构的 —— 一个带方向的输入就足以让输出带方向。
    """
    found = audit(an_input(_vol_scaled_signed_return(), RETURN_TARGET))
    assert [m.code for m in found] == []


def test_a_magnitude_over_a_magnitude_is_still_caught():
    """真阳性必须原样保留，否则这不是修判据，是把闸门拆了。"""
    found = audit(an_input(_dispersion_ratio(), RETURN_TARGET))
    assert [m.code for m in found] == ["magnitude_vs_signed_label"]


def test_prose_alone_no_longer_decides():
    """机制文字提到波动率，而特征取的是对数收益：结构说了算。"""
    spec = FeatureSpec(
        feature_id="plain_momentum", output_step="w",
        mechanism="在高 volatility 环境下，动量的持续性更强",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="log_return", op=Op.SUM, window_seconds=86400)],
    )
    assert audit(an_input(spec, RETURN_TARGET)) == []


def test_the_implemented_kinds_list_matches_the_interpreter():
    """M4.2 新增 rank_pct 时这份清单没同步，而它一声不响 —— 因为全仓没有调用方。

    residualise 是唯一一个语言里可表达、解释器却抛 StepNotImplemented 的类型。
    """
    from arad.features.spec import StepKind as SK
    from arad.harness.audit import IMPLEMENTED_STEP_KINDS

    assert IMPLEMENTED_STEP_KINDS == {k.value for k in SK} - {SK.RESIDUALISE.value}


# ------------------------------------------- universe 解析（M8.4）


def test_a_panel_universe_pools_rows_across_products():
    """面板必须真的汇集多品种，而不是看起来像。

    实测教训：目标名带品种（`sc_ret_next_session`），第一版用 sc 的键去查其余品种的
    标签，把它们全部过滤掉，于是面板与单品种给出**同样的 926 行、同样的 1 个品种簇** ——
    看起来在工作。目标必须按**族名后缀**逐品种解析。
    """
    import os

    import pytest as _pytest

    if not os.path.exists("data/spine/au/target_au_ret_next_session.parquet"):
        _pytest.skip("需要先建多品种 spine")

    from types import SimpleNamespace

    from arad.features.spec import FeatureSpec, Op, Source, Step, StepKind
    from arad.harness.demo import (
        _build_evaluation,
        _load_product,
        _load_sc,
        _product_target_path,
    )

    rows, sc, visible = _load_sc(_product_target_path("sc", "sc_rv_next_session"))
    build = _build_evaluation(sc, rows, visible, loader=_load_product)
    spec = FeatureSpec(
        feature_id="mom", mechanism="上一 session 的对数收益", output_step="w",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="log_return", op=Op.SUM, window_seconds=86400)],
    )

    def run(universe):
        req, _labels, _detail = build(
            spec, "probe", SimpleNamespace(target="sc_ret_next_session", universe=universe)
        )
        return req

    one = run("sc_dominant_t1")
    assert len({r.product_cluster for r in one.rows}) == 1

    two = run("au_dominant_t1")
    assert {r.product_cluster for r in two.rows} == {"au"}
    assert not {r.row_key for r in one.rows} & {r.row_key for r in two.rows}, (
        "跨品种的行键必须互不相交，否则汇集会撞键"
    )


def test_an_unknown_universe_is_refused_not_guessed():
    import pytest as _pytest

    from arad.harness.demo import UnknownUniverse, universe_members

    with _pytest.raises(UnknownUniverse):
        universe_members("随便写的")
