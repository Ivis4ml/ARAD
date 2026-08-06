"""特征解释器与反馈格式化器的合同测试（M4 第四块）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from arad.features.interpreter import (
    BarSeries,
    SourceNotImplemented,
    evaluate_series,
    evaluate_spec,
)
from arad.features.spec import FeatureSpec, Op, Source, Step, StepKind
from arad.harness.feedback import (
    Feedback,
    assert_no_effect_leakage,
    classify,
    format_feedback,
)
from arad.providers.base import ContextLeak

T = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)


def bars(n=120, step=60, start_value=100.0, delta=1.0) -> BarSeries:
    times = [T - timedelta(seconds=step * (n - i)) for i in range(n)]
    values = [start_value + delta * i for i in range(n)]
    return BarSeries(field="close", times=times, values=values)


def series(bs=None):
    return {(Source.COMMODITY_BAR, "close"): bs or bars()}


def spec_of(*steps, output=None) -> FeatureSpec:
    return FeatureSpec(
        feature_id="f", mechanism="m", steps=list(steps),
        output_step=output or steps[-1].name,
        failure_condition="窗口内无 bar 时无定义", authored_by="test",
    )


def window_step(name="w", **kw) -> Step:
    base = {
        "name": name, "kind": StepKind.WINDOW, "source": Source.COMMODITY_BAR,
        "field": "close", "op": Op.MEAN, "window_seconds": 600,
    }
    base.update(kw)
    return Step(**base)


# ---------------------------------------------------------------- PIT 由构造保证


def test_the_window_never_includes_the_decision_time_itself():
    """右端点不含：决策时点那一刻的 bar 不可见。"""
    bs = BarSeries("close", [T - timedelta(seconds=1), T], [1.0, 999.0])
    value = evaluate_spec(spec_of(window_step(op=Op.MAX, window_seconds=600)), T, series(bs))
    assert value == 1.0  # 999.0 落在 T 上，够不到


def test_offset_pushes_the_window_further_into_the_past():
    bs = BarSeries(
        "close",
        [T - timedelta(seconds=s) for s in (900, 300, 60)],
        [1.0, 2.0, 3.0],
    )
    near = evaluate_spec(spec_of(window_step(op=Op.LAST, window_seconds=600)), T, series(bs))
    far = evaluate_spec(
        spec_of(window_step(op=Op.LAST, window_seconds=600, offset_seconds=600)),
        T, series(bs),
    )
    assert near == 3.0
    assert far == 1.0  # 偏移后只看得到更早的那根


def test_future_bars_are_unreachable_no_matter_the_parameters():
    """把未来 bar 放进序列，任何合法参数组合都取不到它。"""
    bs = BarSeries(
        "close",
        [T - timedelta(seconds=60), T + timedelta(seconds=60)],
        [1.0, 10_000.0],
    )
    for window in (60, 600, 86400):
        for offset in (0, 60, 3600):
            value = evaluate_spec(
                spec_of(window_step(op=Op.MAX, window_seconds=window, offset_seconds=offset)),
                T, series(bs),
            )
            assert value is None or value == 1.0


# ---------------------------------------------------------------- 求值


def test_undefined_returns_none_not_zero():
    """窗口内无数据时无定义。返回 0 会被下游当成"没有信号"，那是伪造。"""
    empty = BarSeries("close", [], [])
    assert evaluate_spec(spec_of(window_step()), T, series(empty)) is None


@pytest.mark.parametrize(
    ("op", "expect"), [(Op.LAST, 3.0), (Op.MEAN, 2.0), (Op.SUM, 6.0),
                       (Op.COUNT, 3.0), (Op.MIN, 1.0), (Op.MAX, 3.0)]
)
def test_aggregations(op, expect):
    bs = BarSeries(
        "close", [T - timedelta(seconds=s) for s in (300, 200, 100)], [1.0, 2.0, 3.0]
    )
    assert evaluate_spec(spec_of(window_step(op=op)), T, series(bs)) == expect


def test_std_needs_at_least_two_points():
    bs = BarSeries("close", [T - timedelta(seconds=100)], [1.0])
    assert evaluate_spec(spec_of(window_step(op=Op.STD)), T, series(bs)) is None


def test_innovation_is_the_near_window_minus_the_baseline():
    value = evaluate_spec(
        spec_of(window_step(kind=StepKind.INNOVATION, window_seconds=600,
                            baseline_seconds=3600)),
        T, series(),
    )
    assert value is not None and value > 0  # 序列上升，近窗均值高于长基线


def test_ratio_and_difference_chain():
    steps = [
        window_step("a", op=Op.MAX),
        window_step("b", op=Op.MIN),
        Step(name="d", kind=StepKind.DIFFERENCE, inputs=["a", "b"]),
    ]
    assert evaluate_spec(spec_of(*steps), T, series()) > 0


def test_ratio_by_zero_is_undefined():
    bs = BarSeries("close", [T - timedelta(seconds=100)], [0.0])
    steps = [
        window_step("a", op=Op.LAST), window_step("b", op=Op.LAST),
        Step(name="r", kind=StepKind.RATIO, inputs=["a", "b"]),
    ]
    assert evaluate_spec(spec_of(*steps), T, series(bs)) is None


def test_unimplemented_source_is_a_recorded_gap_not_a_crash():
    with pytest.raises(SourceNotImplemented, match="原语缺口"):
        evaluate_spec(
            spec_of(window_step(source=Source.PM_MARKET, field="price")), T, series()
        )


def test_series_evaluation_reports_coverage_and_degeneracy():
    times = [T - timedelta(hours=i) for i in range(5)]
    values, stats = evaluate_series(spec_of(window_step()), times, series())
    assert stats["decision_points"] == 5
    assert stats["defined"] + stats["undefined"] == 5
    assert "constant" in stats
    assert len(values) == 5


def test_constant_feature_is_flagged():
    """恒定特征是单位错误的信号；解释器先报出来，评价机再拒绝。"""
    flat = BarSeries("close", [T - timedelta(seconds=s) for s in (300, 200, 100)],
                     [7.0, 7.0, 7.0])
    _, stats = evaluate_series(spec_of(window_step(op=Op.MEAN)), [T], series(flat))
    assert stats["constant"] is True


# ---------------------------------------------------------------- 反馈盲化


def result_with(reasons, coverage=None):
    return {
        "study_id": "s1",
        "blocked_reasons": reasons,
        "coverage": coverage or {"rows_submitted": 976, "episodes": 499,
                                 "product_clusters": 1, "slope_hint": 0.85},
    }


def test_numeric_block_reasons_are_categorised_not_passed_through():
    """原样回传"置换斜率 1.000"就是让提案器看见结果。"""
    fb = format_feedback(
        result_with(["置换检验未通过：1.000 的置换斜率不小于实际值"]), "blocked"
    )
    assert fb.failure_categories == ["placebo_failed"]
    assert "1.000" not in fb.render()
    assert "斜率" not in fb.render()


def test_unknown_reasons_are_dropped_not_passed_along_just_in_case():
    fb = format_feedback(result_with(["某个新出现的、含 0.42 的原因"]), "blocked")
    assert fb.failure_categories == []
    assert fb.unclassified_count == 1
    assert "0.42" not in fb.render()


def test_coverage_is_whitelisted():
    """覆盖字段是白名单：结果里混进来的 slope_hint 不会被带出去。"""
    fb = format_feedback(result_with([]), "candidate")
    assert "slope_hint" not in fb.coverage
    assert fb.coverage["episodes"] == 499


@pytest.mark.parametrize(
    ("reason", "category"),
    [
        ("观测数 12 低于预注册下限 100", "insufficient_sample"),
        ("未声明成本模型：不得取 candidate", "cost_model_missing"),
        ("单点影响过大：最大 DFBETA 占斜率 0.62", "single_point_influence"),
        ("cluster_b 维只有一组，双向 cluster 退化", "cluster_structure_insufficient"),
        ("回归不可识别：回归元没有变异", "not_identified"),
    ],
)
def test_taxonomy_covers_the_evaluator_block_reasons(reason, category):
    assert classify(reason) == category


def test_guidance_never_contains_numbers():
    for reasons in ([], ["观测数 12 低于预注册下限 100"],
                    ["置换检验未通过：1.0"], ["单点影响过大：0.6"]):
        assert_no_effect_leakage(format_feedback(result_with(reasons), "blocked"))


def test_feedback_render_passes_the_blinding_guard():
    fb = format_feedback(result_with(["置换检验未通过：1.0"]), "blocked")
    assert isinstance(fb, Feedback)
    from arad.providers.base import Role, assert_blinded

    assert_blinded(fb.render(), Role.PROPOSER)


def test_a_leaking_guidance_would_be_caught():
    with pytest.raises(ValueError, match="含数字"):
        assert_no_effect_leakage(
            Feedback(study_id="s", verdict="blocked", guidance="beta 约为 0.8")
        )


def test_format_feedback_refuses_to_emit_effect_words():
    with pytest.raises(ContextLeak):
        format_feedback({"study_id": "sharpe 很高", "blocked_reasons": []}, "blocked")


def test_zscore_refuses_to_pretend_it_standardised_anything():
    """原样返回输入会让评价机为一个并非规格声明的数出具结果。宁可判 blocked。"""
    from arad.features.interpreter import StepNotImplemented

    spec = FeatureSpec(
        feature_id="f", mechanism="m", output_step="z",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[
            Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.MEAN, window_seconds=600),
            Step(name="z", kind=StepKind.ZSCORE, inputs=["w"], window_seconds=86400),
        ],
    )
    series = {(Source.COMMODITY_BAR, "close"): BarSeries(
        field="close",
        times=[datetime(2026, 1, 1, 9, 0, tzinfo=UTC)],
        values=[1.0],
    )}
    with pytest.raises(StepNotImplemented, match="zscore"):
        evaluate_spec(spec, datetime(2026, 1, 1, 10, 0, tzinfo=UTC), series)


def test_describe_is_lossless_so_the_spec_can_be_rebuilt_from_the_ledger():
    """账本里存的是 describe()。规格若不能从证据里重建，快照就不自包含。"""
    spec = FeatureSpec(
        feature_id="f", mechanism="m", output_step="r",
        failure_condition="分母退化", authored_by="t",
        steps=[
            Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="realised_volatility", op=Op.STD, window_seconds=432000),
            Step(name="b", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="realised_volatility", op=Op.MEAN, window_seconds=432000),
            Step(name="r", kind=StepKind.RATIO, inputs=["a", "b"]),
        ],
    )
    described = spec.describe()
    rebuilt = FeatureSpec(
        feature_id=described["feature_id"], mechanism=described["mechanism"],
        steps=[Step(**s) for s in described["steps"]],
        output_step=described["output_step"],
        failure_condition=described["failure_condition"], authored_by="t",
    )
    assert rebuilt.content_id == spec.content_id
