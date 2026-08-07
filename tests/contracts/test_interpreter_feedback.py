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


#: 覆盖准入要求回看窗口整段落在序列覆盖范围内。测试序列刻意只放几个点，
#: 因此必须显式声明覆盖起点 —— 这正是 coverage_start 存在的理由：
#: "这段时间源是有覆盖的，只是恰好没有 bar" 与 "这段时间根本没有数据" 是两回事。
COVERS_FROM = T - timedelta(days=30)


def bars(n=120, step=60, start_value=100.0, delta=1.0) -> BarSeries:
    times = [T - timedelta(seconds=step * (n - i)) for i in range(n)]
    values = [start_value + delta * i for i in range(n)]
    return BarSeries(field="close", times=times, values=values,
                     coverage_start=COVERS_FROM)


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
    bs = BarSeries("close", [T - timedelta(seconds=1), T], [1.0, 999.0],
                      coverage_start=COVERS_FROM)
    value = evaluate_spec(spec_of(window_step(op=Op.MAX, window_seconds=600)), T, series(bs))
    assert value == 1.0  # 999.0 落在 T 上，够不到


def test_offset_pushes_the_window_further_into_the_past():
    bs = BarSeries(
        "close",
        [T - timedelta(seconds=s) for s in (900, 300, 60)],
        [1.0, 2.0, 3.0],
        coverage_start=COVERS_FROM,
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
        coverage_start=COVERS_FROM,
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
    empty = BarSeries("close", [], [], coverage_start=COVERS_FROM)
    assert evaluate_spec(spec_of(window_step()), T, series(empty)) is None


@pytest.mark.parametrize(
    ("op", "expect"), [(Op.LAST, 3.0), (Op.MEAN, 2.0), (Op.SUM, 6.0),
                       (Op.COUNT, 3.0), (Op.MIN, 1.0), (Op.MAX, 3.0)]
)
def test_aggregations(op, expect):
    bs = BarSeries(
        "close", [T - timedelta(seconds=s) for s in (300, 200, 100)], [1.0, 2.0, 3.0],
        coverage_start=COVERS_FROM,
    )
    assert evaluate_spec(spec_of(window_step(op=op)), T, series(bs)) == expect


def test_std_needs_at_least_two_points():
    bs = BarSeries("close", [T - timedelta(seconds=100)], [1.0],
                   coverage_start=COVERS_FROM)
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
    bs = BarSeries("close", [T - timedelta(seconds=100)], [0.0],
                   coverage_start=COVERS_FROM)
    steps = [
        window_step("a", op=Op.LAST), window_step("b", op=Op.LAST),
        Step(name="r", kind=StepKind.RATIO, inputs=["a", "b"]),
    ]
    assert evaluate_spec(spec_of(*steps), T, series(bs)) is None


def test_unimplemented_source_is_a_recorded_gap_not_a_crash():
    """pm_market 已接入（M5.2），未接入的仍必须是被记录的缺口而不是崩溃。"""
    with pytest.raises(SourceNotImplemented, match="原语缺口"):
        evaluate_spec(
            spec_of(window_step(source=Source.CLS, field="headline_count")), T, series()
        )


def test_a_wired_source_without_a_series_is_still_a_gap():
    """接入不等于任何字段都有序列：族没物化就该如实报缺口。"""
    with pytest.raises(SourceNotImplemented, match="没有为"):
        evaluate_spec(
            spec_of(window_step(source=Source.PM_MARKET, field="cand:nope:p")),
            T, series(),
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
                     [7.0, 7.0, 7.0], coverage_start=COVERS_FROM)
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


def test_residualise_refuses_to_pretend_it_residualised_anything():
    """原样返回输入会让评价机为一个并非规格声明的数出具结果。宁可判 blocked。"""
    from arad.features.interpreter import StepNotImplemented

    spec = FeatureSpec(
        feature_id="f", mechanism="m", output_step="r",
        failure_condition="控制序列缺失", authored_by="t",
        steps=[
            window_step("w"),
            Step(name="r", kind=StepKind.RESIDUALISE, inputs=["w"],
                 controls=["sc_own_information"]),
        ],
    )
    with pytest.raises(StepNotImplemented, match="residualise"):
        evaluate_spec(spec, T, series())


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
    # 结构性断言：模型的每个字段都必须出现在摘要里。写死字段名的重建是循环论证 ——
    # 上一版就因为重建时手填 authored_by="t"，而摘要里根本没有这个字段，
    # 测试对遗漏完全无感。
    assert set(FeatureSpec.model_fields) <= set(described)
    usable = {k: v for k, v in described.items() if k in FeatureSpec.model_fields}
    usable["steps"] = [Step(**step) for step in described["steps"]]
    rebuilt = FeatureSpec(**usable)
    assert rebuilt.content_id == spec.content_id
    assert rebuilt.model_dump() == spec.model_dump()


# ---------------------------------------------------------------- zscore（M4.1）


def zscore_spec(**kw) -> FeatureSpec:
    step = {"name": "z", "kind": StepKind.ZSCORE, "inputs": ["w"],
            "window_seconds": 36000, "sample_every_seconds": 3600, "min_samples": 5}
    step.update(kw)
    return spec_of(window_step("w", op=Op.LAST, window_seconds=3600), Step(**step))


def test_zscore_standardises_against_its_own_past_and_nothing_else():
    """参考分布来自输入步骤在 t - k*sample_every 上的取值，与调用方请求了什么无关。"""
    bs = bars(n=600, step=60, start_value=100.0, delta=1.0)
    value = evaluate_spec(zscore_spec(), T, series(bs))
    # 手算：输入步骤在 t 与 t-3600k 上的取值，样本严格取自过去
    from arad.features.interpreter import EvalContext, _sample_std

    ctx = EvalContext(series=series(bs))
    spec = zscore_spec()
    current = evaluate_spec(spec_of(window_step("w", op=Op.LAST, window_seconds=3600)),
                            T, series(bs))
    samples = [
        evaluate_spec(spec_of(window_step("w", op=Op.LAST, window_seconds=3600)),
                      T - timedelta(seconds=3600 * k), series(bs))
        for k in range(1, 11)
    ]
    samples = [v for v in samples if v is not None]
    expected = (current - sum(samples) / len(samples)) / _sample_std(samples)
    assert value == pytest.approx(expected)
    assert spec.steps[1].kind is StepKind.ZSCORE and ctx.memo == {}


def test_the_reference_grid_comes_from_the_spec_not_from_the_caller():
    """同一份规格在不同的决策点请求下，同一时刻必须得到同一个数。"""
    bs = bars(n=600, step=60)
    dense = [T - timedelta(seconds=600 * i) for i in range(8)]
    sparse = [T]
    a, _ = evaluate_series(zscore_spec(), dense, series(bs))
    b, _ = evaluate_series(zscore_spec(), sparse, series(bs))
    assert a[0] == b[0]


def test_zscore_is_undefined_when_the_reference_is_truncated():
    """假日截断参考分布时判无定义，绝不用剩下几个样本硬出一个数。"""
    short = BarSeries("close", [T - timedelta(seconds=60 * i) for i in range(1, 40)],
                      [float(i) for i in range(1, 40)],
                      coverage_start=T - timedelta(days=30))
    assert evaluate_spec(zscore_spec(min_samples=9), T, series(short)) is None


def test_repeated_readings_do_not_count_as_information():
    """采样步长小于数据节奏时会反复读到同一批数据；门槛计互异取值而非样本个数。"""
    sparse = BarSeries("close", [T - timedelta(hours=9), T - timedelta(minutes=30)],
                       [5.0, 6.0], coverage_start=T - timedelta(days=30))
    spec = spec_of(
        window_step("w", op=Op.LAST, window_seconds=86400),
        Step(name="z", kind=StepKind.ZSCORE, inputs=["w"], window_seconds=36000,
             sample_every_seconds=3600, min_samples=5),
    )
    values, stats = evaluate_series(spec, [T], series(sparse))
    reported = stats["reference_samples"]["z"]
    # 样本个数够，互异取值只有一个：每小时采样反复读到同一根 bar
    assert reported["defined_min"] >= 5
    assert reported["distinct_min"] == 1
    assert values == [None]


def test_a_flat_reference_distribution_is_undefined_not_infinite():
    flat = BarSeries("close", [T - timedelta(seconds=60 * i) for i in range(1, 700)],
                     [7.0] * 699, coverage_start=T - timedelta(days=30))
    assert evaluate_spec(zscore_spec(), T, series(flat)) is None


def test_reference_samples_are_reported_in_coverage():
    """参考分布被截断多少必须进证据：现有 coverage 与影响点闸门都看不见它。"""
    bs = bars(n=600, step=60)
    _, stats = evaluate_series(zscore_spec(), [T, T - timedelta(hours=1)], series(bs))
    reported = stats["reference_samples"]["z"]
    assert reported["expected_per_point"] == 10
    assert reported["points"] == 2
    assert reported["defined_min"] <= 10
    assert "distinct_median" in reported


def test_the_lookback_admission_makes_evaluability_imply_a_unique_value():
    """完整序列与其后缀，在双方都准入的点上必须逐位相同。"""
    full = bars(n=2000, step=60)
    tail = BarSeries("close", full.times[300:], full.values[300:],
                     coverage_start=full.times[300])
    times = [T - timedelta(seconds=60 * i) for i in range(0, 200, 20)]
    a, _ = evaluate_series(zscore_spec(), times, series(full))
    b, _ = evaluate_series(zscore_spec(), times, series(tail))
    both = [(x, y) for x, y in zip(a, b, strict=True) if y is not None]
    assert both, "后缀序列上应当仍有准入的决策点"
    assert all(x == y for x, y in both)


def test_a_window_reaching_before_coverage_is_undefined():
    """声明为 20 日均值的东西不能在序列开头变成"能取到多少算多少"。"""
    bs = BarSeries("close", [T - timedelta(seconds=100)], [1.0],
                   coverage_start=T - timedelta(seconds=200))
    assert evaluate_spec(spec_of(window_step(window_seconds=600)), T, series(bs)) is None
    assert evaluate_spec(spec_of(window_step(window_seconds=150)), T, series(bs)) == 1.0


# ---------------------------------------------------------------- rank_pct


def _sampled_step(kind: StepKind, name: str) -> Step:
    return Step(name=name, kind=kind, inputs=["w"], window_seconds=86400 * 40,
                sample_every_seconds=86400, min_samples=10)


def _spec_with(kind: StepKind, name: str) -> FeatureSpec:
    return FeatureSpec(
        feature_id=f"f_{name}", mechanism="重尾量的归一", output_step=name,
        failure_condition="参考样本不足时无定义", authored_by="t",
        steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="close", op=Op.LAST, window_seconds=3600),
               _sampled_step(kind, name)],
    )


#: bar 放在采样点**前一分钟**：窗口右端点是开区间（PIT 纪律），
#: 正好落在采样时刻的 bar 会被排除，整条特征就全程无定义。
_BAR_LEAD = timedelta(minutes=1)


def _daily_series(values: list[float]) -> BarSeries:
    """每天一根 bar，第 i 根对应 T - (n-1-i) 天。"""
    n = len(values)
    times = [T - timedelta(days=n - 1 - i) - _BAR_LEAD for i in range(n)]
    return BarSeries(field="close", times=times, values=values,
                     coverage_start=T - timedelta(days=400))


def _with_outlier_at(position: int) -> BarSeries:
    """一条重尾序列：绝大多数是小值，一天是其余全部的数百倍。

    互异取值要够多：门槛计**互异**样本数，只有 7 个不同的小值时整条特征无定义，
    而那是采样门槛在起作用，不是这些测试要验的东西。
    """
    values = [1.0 + (i % 37) * 0.01 for i in range(120)]
    values[position] = 500.0
    return _daily_series(values)


def _max_leverage(xs: list[float]) -> float:
    mean = sum(xs) / len(xs)
    sxx = sum((x - mean) ** 2 for x in xs)
    return max((x - mean) ** 2 / sxx for x in xs) if sxx > 0 else 1.0


def _both(position: int):
    data = {(Source.COMMODITY_BAR, "close"): _with_outlier_at(position)}
    times = [T - timedelta(days=d) for d in range(35, 0, -1)]
    z, _ = evaluate_series(_spec_with(StepKind.ZSCORE, "z"), times, data)
    r, _ = evaluate_series(_spec_with(StepKind.RANK_PCT, "r"), times, data)
    zs = [v for v in z if v is not None]
    rs = [v for v in r if v is not None]
    assert len(zs) == len(rs) > 30, "两者必须在同样的点上有定义，否则比的不是一回事"
    return zs, rs


def test_rank_pct_stops_one_point_from_owning_the_regressor():
    """离群日落在**被评估的点**里：zscore 的取值本身重尾，单点占掉回归元几乎全部变异。

    实测：zscore 的最大杠杆 0.97，即一个观测决定了斜率；rank_pct 是 0.11。
    这正是本原语存在的理由 —— 一条真实特征的最大杠杆是 0.607，
    而当时的语言里没有任何稳健变换可用。
    """
    zs, rs = _both(100)
    assert all(0.0 <= v <= 1.0 for v in rs), "分位排名必须落在 [0,1]"
    assert _max_leverage(zs) > 0.9
    assert _max_leverage(rs) < 0.2


def test_rank_pct_survives_an_outlier_in_its_own_reference_window():
    """离群日落在**参考窗口**里：zscore 的失效方式反过来 —— 不是杠杆过大，是信号被压平。

    离群值撑爆参考分布的标准差，于是其余全部取值被压到几乎相同，
    评价机会正确地报「回归元没有变异」，那一轮白花。
    实测 zscore 的极差 0.005，rank_pct 的极差 0.95。
    """
    zs, rs = _both(80)
    assert max(zs) - min(zs) < 0.01, "zscore 在这里被压平了"
    assert max(rs) - min(rs) > 0.5, "分位排名保住了区分度"


def test_rank_pct_ties_each_count_a_half():
    """平局各算一半，取值因此可精确算出，不靠近似。

    构造：参考样本恰好是 1..40（40 个互异取值），当前值为 5。
    严格小于的有 4 个，相等的有 1 个，于是分位排名 = (4 + 0.5) / 40 = 0.1125。
    平局若整个算「小于」会得到 0.125，若整个不算会得到 0.100，三者可区分。
    """
    values = [float(41 - k) for k in range(1, 41)] + [5.0]
    data = {(Source.COMMODITY_BAR, "close"): _daily_series(values)}
    value = evaluate_spec(_spec_with(StepKind.RANK_PCT, "r"), T, data)
    assert value == pytest.approx(0.1125)


def test_rank_pct_and_zscore_cannot_be_nested_in_each_other():
    """交叉嵌套与同类嵌套一样被拒：对已归一的量再归一没有确定含义。"""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="输入链上还有采样类步骤"):
        FeatureSpec(
            feature_id="f", mechanism="m", output_step="z",
            failure_condition="c", authored_by="t",
            steps=[Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                        field="close", op=Op.LAST, window_seconds=3600),
                   _sampled_step(StepKind.RANK_PCT, "r"),
                   Step(name="z", kind=StepKind.ZSCORE, inputs=["r"],
                        window_seconds=86400 * 40, sample_every_seconds=86400,
                        min_samples=10)],
        )
