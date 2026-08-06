"""特征规格语言的合同测试（M4 第一块）。

最重要的性质：**前视在这门语言里无法表达**，而不是写出来之后被拦下。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from arad.features.spec import (
    FeatureSpec,
    Op,
    Source,
    Step,
    StepKind,
    UnsupportedMechanism,
)


def window(name="w", **kw) -> Step:
    base = {
        "name": name, "kind": StepKind.WINDOW, "source": Source.PM_MARKET,
        "field": "price", "op": Op.MEAN, "window_seconds": 3600,
    }
    base.update(kw)
    return Step(**base)


def a_spec(**kw) -> FeatureSpec:
    base = {
        "feature_id": "f1",
        "mechanism": "闭市期间地缘概率创新",
        "steps": [window()],
        "output_step": "w",
        "failure_condition": "窗口内无成交时该特征无意义",
        "authored_by": "test",
    }
    base.update(kw)
    return FeatureSpec(**base)


# ---------------------------------------------------------------- 前视不可表达


def test_negative_offset_is_rejected_by_the_language():
    """负偏移意味着引用决策时点之后的数据；语言层直接拒绝。"""
    with pytest.raises(ValidationError, match="不能为负"):
        window(offset_seconds=-1)


def test_zero_offset_is_allowed_because_windows_end_before_the_decision():
    assert window(offset_seconds=0).offset_seconds == 0


def test_window_length_must_be_positive():
    with pytest.raises(ValidationError, match="必须为正"):
        window(window_seconds=0)
    with pytest.raises(ValidationError, match="必须为正"):
        window(window_seconds=-3600)


def test_there_is_no_primitive_that_can_reference_the_future():
    """穷举 StepKind：没有任何一种能表达"决策时点之后"。"""
    for kind in StepKind:
        fields = set(Step.model_fields)
        assert "lead_seconds" not in fields
        assert "future_window" not in fields
        assert kind.value in {k.value for k in StepKind}
    # offset 是唯一的时间平移，且被约束为非负
    assert Step.model_fields["offset_seconds"].default == 0


# ---------------------------------------------------------------- 步骤合法性


@pytest.mark.parametrize("missing", ["source", "field", "op"])
def test_window_step_must_declare_its_data(missing):
    with pytest.raises(ValidationError, match="必须声明"):
        window(**{missing: None})


def test_innovation_baseline_must_be_longer_than_the_observation_window():
    with pytest.raises(ValidationError, match="必须长于"):
        Step(
            name="i", kind=StepKind.INNOVATION, source=Source.PM_MARKET, field="price",
            op=Op.MEAN, window_seconds=3600, baseline_seconds=3600,
        )
    ok = Step(
        name="i", kind=StepKind.INNOVATION, source=Source.PM_MARKET, field="price",
        op=Op.MEAN, window_seconds=3600, baseline_seconds=86400,
    )
    assert ok.own_lookback_seconds == 86400


@pytest.mark.parametrize("kind", [StepKind.RATIO, StepKind.DIFFERENCE])
def test_binary_steps_need_exactly_two_inputs(kind):
    with pytest.raises(ValidationError, match="恰好两个"):
        Step(name="r", kind=kind, inputs=["a"])


def test_residualise_needs_controls():
    with pytest.raises(ValidationError, match="至少一个控制项"):
        Step(name="r", kind=StepKind.RESIDUALISE, inputs=["a"], controls=[])


def test_window_steps_do_not_reference_other_steps():
    with pytest.raises(ValidationError, match="不引用其他步骤"):
        window(inputs=["other"])


# ---------------------------------------------------------------- 规格合法性


def test_steps_must_be_in_dependency_order_and_acyclic():
    with pytest.raises(ValidationError, match="尚未定义"):
        a_spec(
            steps=[Step(name="r", kind=StepKind.ZSCORE, inputs=["w"],
                        window_seconds=86400, sample_every_seconds=3600,
                        min_samples=6),
                   window()],
            output_step="r",
        )


def test_duplicate_step_names_are_rejected():
    with pytest.raises(ValidationError, match="重复"):
        a_spec(steps=[window(), window()], output_step="w")


def test_output_step_must_exist():
    with pytest.raises(ValidationError, match="output_step"):
        a_spec(output_step="nope")


def test_mechanism_and_failure_condition_are_mandatory():
    """没有经济含义与失败条件的特征不是 Feature，只是一个变换。"""
    with pytest.raises(ValidationError, match="必须声明"):
        a_spec(mechanism="  ")
    with pytest.raises(ValidationError, match="必须声明"):
        a_spec(failure_condition="")


def test_spec_is_frozen_and_content_addressed():
    a, b = a_spec(), a_spec()
    assert a.content_id == b.content_id
    assert a_spec(mechanism="别的机制").content_id != a.content_id
    with pytest.raises(ValidationError):
        a.feature_id = "f2"


def test_unknown_field_is_rejected():
    """extra=forbid：LLM 编造字段会立即失败，而不是被静默忽略。"""
    with pytest.raises(ValidationError):
        a_spec(lookahead_hint="please cheat")


# ---------------------------------------------------------------- 代码是可选的


def test_code_is_optional_but_the_spec_never_is():
    plain = a_spec()
    assert plain.declares_code() is False
    with_code = a_spec(code_artifact_id="sha256:abc")
    assert with_code.declares_code() is True
    # 代码改变了，规格身份也随之改变：两者绑定，不能各走各的
    assert with_code.content_id != plain.content_id


def test_describe_is_machine_readable_for_the_ledger_and_atlas():
    spec = a_spec(
        steps=[
            window("innov", kind=StepKind.INNOVATION, baseline_seconds=86400),
            Step(name="z", kind=StepKind.ZSCORE, inputs=["innov"],
                 window_seconds=604800, sample_every_seconds=86400, min_samples=5),
        ],
        output_step="z",
    )
    d = spec.describe()
    assert d["output_step"] == "z"
    assert d["sources"] == ["pm_market"]
    # 回看深度沿 DAG 累加：zscore 的参考样本本身取到 t-604800，每个样本又要把
    # innovation 的 86400 基线再往前推一次。逐步取 max 会把这个数写小。
    assert d["required_lookback_seconds"] == 604800 + 86400
    assert [s["kind"] for s in d["steps"]] == ["innovation", "zscore"]
    assert d["content_id"] == spec.content_id


# ---------------------------------------------------------------- 原语缺口是证据


def test_unsupported_mechanism_is_a_recordable_artifact():
    """原语不够用时，LLM 应当声明缺口，而不是绕过语言。"""
    gap = UnsupportedMechanism(
        mechanism="订单簿阶梯的隐含分布变化",
        missing_primitive="order_book_ladder",
        why_existing_primitives_insufficient="现有原语只覆盖成交，不覆盖挂单阶梯",
    )
    assert gap.missing_primitive
    with pytest.raises(ValidationError):
        gap.mechanism = "别的"


# ---------------------------------------------------------------- zscore 的规格约束


def a_zscore(**kw) -> Step:
    base = {"name": "z", "kind": StepKind.ZSCORE, "inputs": ["w"],
            "window_seconds": 36000, "sample_every_seconds": 3600, "min_samples": 5}
    base.update(kw)
    return Step(**base)


def test_zscore_must_declare_its_own_sampling_grid():
    """采样网格是规格的一部分。让实现替它决定，同一 content id 会得到不同的数。"""
    with pytest.raises(ValidationError, match="sample_every_seconds"):
        Step(name="z", kind=StepKind.ZSCORE, inputs=["w"], window_seconds=36000)


def test_a_zscore_that_can_never_be_defined_is_rejected_at_the_language_layer():
    with pytest.raises(ValidationError, match="不可能有定义"):
        a_zscore(window_seconds=7200, sample_every_seconds=3600, min_samples=5)


def test_the_reference_sample_count_is_bounded():
    with pytest.raises(ValidationError, match="超过上限"):
        a_zscore(window_seconds=3600 * 600, sample_every_seconds=3600, min_samples=5)


def test_sampling_fields_belong_to_zscore_only():
    with pytest.raises(ValidationError, match="只属于 zscore"):
        window(sample_every_seconds=3600)


def test_derived_steps_reject_offset_because_it_was_silently_ignored():
    """让它生效会使同一个 content id 算出另一个数；拒绝不改变任何现存规格的值。"""
    with pytest.raises(ValidationError, match="不接受 offset_seconds"):
        Step(name="r", kind=StepKind.RATIO, inputs=["a", "b"], offset_seconds=60)


def test_unreachable_steps_are_rejected():
    """求值够不到它，而 describe() 仍会声称本特征用了它的数据源。"""
    with pytest.raises(ValidationError, match="不可达"):
        a_spec(
            steps=[window("live"),
                   window("dead", source=Source.PM_MARKET, field="price")],
            output_step="live",
        )


def test_nested_zscore_is_rejected():
    with pytest.raises(ValidationError, match="输入链上还有 zscore"):
        a_spec(
            steps=[window("w"), a_zscore(name="z1"),
                   a_zscore(name="z2", inputs=["z1"])],
            output_step="z2",
        )


def test_the_content_id_of_a_pinned_spec_does_not_drift_silently():
    """金标：新增字段或改默认值都会改变全部 content id，这里让它可见而不是无声发生。"""
    spec = FeatureSpec(
        feature_id="pinned", mechanism="金标规格", output_step="w",
        failure_condition="窗口内无数据", authored_by="test",
        spec_version="0.2.0",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="realised_volatility", op=Op.MEAN, window_seconds=86400)],
    )
    assert spec.content_id == (
        "89500f5803d6e55cd572697625ed8999e9368597064e1daa7f1a44c38778f4ac"
    )
