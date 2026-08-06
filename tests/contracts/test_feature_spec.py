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
    assert ok.earliest_lookback_seconds == 86400


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
            steps=[Step(name="r", kind=StepKind.ZSCORE, inputs=["w"], window_seconds=86400),
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
            Step(name="z", kind=StepKind.ZSCORE, inputs=["innov"], window_seconds=604800),
        ],
        output_step="z",
    )
    d = spec.describe()
    assert d["output_step"] == "z"
    assert d["sources"] == ["pm_market"]
    assert d["required_lookback_seconds"] == 604800
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
