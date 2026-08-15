"""规格→代码生成的合同测试（M8）。

M4 的裁决是「规格与代码不一致按缺陷处理」。**因此代码由规格确定性生成，不由模型写** ——
生成式在构造上就不可能不一致，而人写或模型写的只能靠事后比对。这里的核心测试就是
那条硬判据：生成代码在同一批序列上的取值必须与解释器**逐位相同**。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from arad.features.codegen import to_formula, to_python
from arad.features.interpreter import BarSeries, evaluate_spec
from arad.features.spec import FeatureSpec, Op, Source, Step, StepKind

T0 = datetime(2026, 1, 1, tzinfo=UTC)
COVERS = T0 - timedelta(days=400)


# 造数必须有曲率：线性序列上「短窗均值 − 长窗均值」是常数，互异取值只有一个，
# zscore 会全程无定义 —— 那是正确行为，但测试就什么也没验到
def _wave(i: int) -> float:
    return 100.0 + i * 0.37 + 8.0 * math.sin(i / 13.0) + 3.0 * math.cos(i / 5.0)


def bars(field: str, n: int = 900, step: int = 3600, f=_wave):
    times = [T0 - timedelta(seconds=step * (n - i)) for i in range(n)]
    return BarSeries(field=field, times=times, values=[f(i) for i in range(n)],
                     coverage_start=COVERS)


def series_for(*fields: str) -> dict:
    return {(Source.COMMODITY_BAR, f): bars(f) for f in fields}


def as_plain(series: dict) -> dict:
    return {f"{src.value}.{field}": (s.times, s.values) for (src, field), s in series.items()}


def run_generated(spec: FeatureSpec, at: datetime, series: dict):
    namespace: dict = {}
    exec(compile(to_python(spec), f"<{spec.feature_id}>", "exec"), namespace)  # noqa: S102
    return namespace["compute"](at, as_plain(series), coverage_start=COVERS)


SPECS = {
    "window": FeatureSpec(
        feature_id="w", mechanism="窗口均值", output_step="a",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="close", op=Op.MEAN, window_seconds=86400)],
    ),
    "offset": FeatureSpec(
        feature_id="o", mechanism="带滞后的最后值", output_step="a",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                    field="close", op=Op.LAST, window_seconds=7200,
                    offset_seconds=86400)],
    ),
    "difference": FeatureSpec(
        feature_id="d", mechanism="两窗之差", output_step="c",
        failure_condition="任一窗无数据", authored_by="t",
        steps=[
            Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.SUM, window_seconds=86400),
            Step(name="b", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.SUM, window_seconds=604800),
            Step(name="c", kind=StepKind.DIFFERENCE, inputs=["a", "b"]),
        ],
    ),
    "ratio": FeatureSpec(
        feature_id="r", mechanism="两窗之比", output_step="c",
        failure_condition="分母为零", authored_by="t",
        steps=[
            Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.SUM, window_seconds=21600),
            Step(name="b", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.SUM, window_seconds=172800),
            Step(name="c", kind=StepKind.RATIO, inputs=["a", "b"]),
        ],
    ),
    "innovation": FeatureSpec(
        feature_id="i", mechanism="创新量", output_step="a",
        failure_condition="窗口内无数据", authored_by="t",
        steps=[Step(name="a", kind=StepKind.INNOVATION, source=Source.COMMODITY_BAR,
                    field="close", op=Op.MEAN, window_seconds=86400,
                    baseline_seconds=604800)],
    ),
    "zscore": FeatureSpec(
        feature_id="z", mechanism="标准化的创新量", output_step="z",
        failure_condition="参考分布被截断", authored_by="t",
        steps=[
            Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.MEAN, window_seconds=86400),
            Step(name="b", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.MEAN, window_seconds=604800),
            Step(name="d", kind=StepKind.DIFFERENCE, inputs=["a", "b"]),
            Step(name="z", kind=StepKind.ZSCORE, inputs=["d"], window_seconds=1728000,
                 sample_every_seconds=86400, min_samples=8),
        ],
    ),
    "rank_pct": FeatureSpec(
        feature_id="r", mechanism="创新量在自身过去分布中的分位排名", output_step="r",
        failure_condition="参考分布被截断",
        authored_by="t",
        steps=[
            Step(name="a", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.MEAN, window_seconds=86400),
            Step(name="b", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.MEAN, window_seconds=604800),
            Step(name="d", kind=StepKind.DIFFERENCE, inputs=["a", "b"]),
            Step(name="r", kind=StepKind.RANK_PCT, inputs=["d"], window_seconds=1728000,
                 sample_every_seconds=86400, min_samples=8),
        ],
    ),
}


@pytest.mark.parametrize("name", sorted(SPECS))
def test_generated_code_reproduces_the_interpreter_bit_for_bit(name):
    """这是本模块存在的全部理由：生成的代码不是「另一份实现」，是同一份语义。"""
    spec = SPECS[name]
    series = series_for("close")
    checked = 0
    for hours in range(0, 240, 11):
        at = T0 - timedelta(hours=hours)
        a = evaluate_spec(spec, at, series)
        b = run_generated(spec, at, series)
        if a is None and b is None:
            continue
        checked += 1
        assert a is not None and b is not None, (name, at, a, b)
        assert abs(a - b) < 1e-12, (name, at, a, b)
    assert checked > 0, f"{name} 全程无定义，这条测试没有验到任何东西"


def test_the_generated_file_says_it_must_not_be_hand_edited():
    code = to_python(SPECS["zscore"])
    assert "请勿手改" in code
    assert SPECS["zscore"].content_id in code       # 改规格才能改代码
    assert "REQUIRED_LOOKBACK_SECONDS" in code


def test_the_generated_code_returns_none_never_zero_when_undefined():
    spec = SPECS["window"]
    empty = {(Source.COMMODITY_BAR, "close"): BarSeries("close", [], [],
                                                        coverage_start=COVERS)}
    assert run_generated(spec, T0, empty) is None


def test_residualise_is_generated_and_matches_the_interpreter():
    """`residualise` 由「未实现」变为可求值（M9.5），生成代码与解释器仍须逐位一致。

    存在的理由是实测的：真实模型在面板上给出 |t| = 9.3 的特征，分母是
    `mean(realised_volatility)` 而目标就是已实现波动 —— 它重新发现了波动率聚集，
    是教科书级的 Baseline Control。没有这一步，任何与波动相关的目标都会被它淹没。
    """
    from datetime import timedelta as _td

    spec = FeatureSpec(
        feature_id="res", mechanism="对 Brent 残差化", output_step="r",
        failure_condition="控制取值不变时不可识别", authored_by="t",
        steps=[
            Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="close", op=Op.LAST, window_seconds=86400 * 2),
            Step(name="r", kind=StepKind.RESIDUALISE, inputs=["w"], controls=["brent"],
                 window_seconds=86400 * 40, sample_every_seconds=86400, min_samples=10),
        ],
    )
    n = 200
    times = [T0 - _td(days=n - i) - _td(minutes=1) for i in range(n)]
    control = [1.0 + 0.01 * i for i in range(n)]
    close = [2 * v + ((-1) ** i) * 0.05 for i, v in enumerate(control)]
    series = {
        (Source.COMMODITY_BAR, "close"): BarSeries(
            field="close", times=times, values=close,
            coverage_start=T0 - _td(days=400)),
        (Source.INTL, "brent"): BarSeries(
            field="brent", times=times, values=control,
            coverage_start=T0 - _td(days=400)),
    }
    checked = 0
    for days in range(0, 60, 7):
        at = T0 - _td(days=days)
        a = evaluate_spec(spec, at, series)
        b = run_generated(spec, at, series)
        if a is None and b is None:
            continue
        checked += 1
        assert a is not None and b is not None, (at, a, b)
        assert abs(a - b) < 1e-12, (at, a, b)
        # x = 2c ± 0.05：残差化之后只剩噪声那一层
        assert abs(a) < 0.2, (at, a)
    assert checked > 0

def test_the_formula_names_every_step_and_ends_at_the_output():
    lines = to_formula(SPECS["zscore"])
    assert len(lines) == len(SPECS["zscore"].steps) + 1
    assert lines[-1].endswith("z")
    assert "μ" in "".join(lines) and "互异取值不足" in "".join(lines)


# ---------------------------------------------------------------- 因子卡


def a_card(discovery_t, sealed_t, sealed_rows=400, clean=True):
    from arad.registry.alpha_card import AlphaCard

    return AlphaCard(
        spec=SPECS["window"], mechanism="窗口均值", family="fam",
        discovery={"t_stat": discovery_t, "ic_spearman": 0.05, "rows": 900},
        sealed=(None if sealed_t is None
                else {"t_stat": sealed_t, "ic_spearman": 0.01, "rows": sealed_rows,
                      "segment": "historical_validation"}),
        taxonomy_clean=clean,
    )


def test_a_sign_flip_in_the_sealed_segment_is_a_failure_not_a_pass():
    """看 |t| 会把符号翻转读成「保住了」—— 本次会话的人就这样读错过一次。"""
    assert a_card(-1.762, +1.400).status == "sealed_failed"
    assert a_card(+1.762, +1.400).status == "sealed_survived"


def test_a_collapsed_magnitude_is_a_failure_even_with_the_same_sign():
    assert a_card(+3.0, +0.2).status == "sealed_failed"


def test_too_few_sealed_rows_is_undecidable_not_a_pass():
    card = a_card(+3.0, +2.9, sealed_rows=40)
    assert card.status == "sealed_underpowered"
    assert "判不了" in card.meaning()


def test_a_card_without_a_sealed_result_never_claims_out_of_sample_evidence():
    card = a_card(+3.0, None)
    assert card.status == "discovery_only"
    assert "没有任何样本外证据" in card.meaning()


def test_a_dirty_taxonomy_is_stated_even_when_the_sealed_segment_held():
    card = a_card(+3.0, +2.5, clean=False)
    assert card.status == "sealed_survived"
    assert "分类法不干净" in card.meaning()
    assert "样本外也救不了" in card.meaning()


def test_every_card_says_it_may_not_be_a_candidate_without_a_cost_model():
    assert "不得取 candidate" in a_card(+1.0, +1.0).meaning()


def test_the_card_carries_the_generated_code_and_the_formula():
    payload = a_card(+1.0, +1.0).payload()
    assert payload["code"].startswith('"""')
    assert payload["formula"][-1].startswith("输出 =")
    assert payload["content_id"] == SPECS["window"].content_id


def test_the_meaning_text_carries_no_markdown_markers():
    """这段话同时进 .md 与 app 的纯文本段落，后者会把 `**` 原样显示。已犯过四次。"""
    for d_t, s_t, clean in ((-1.7, 1.4, True), (3.0, 2.5, False), (1.0, None, True)):
        text = a_card(d_t, s_t, clean=clean).meaning()
        assert "**" not in text, text
        assert "`" not in text


def test_multi_control_residualise_codegen_matches_interpreter():
    """决定 0009 方向：双控制残差化的生成码与解释器逐位一致。"""

    t0 = datetime(2024, 1, 1, tzinfo=UTC)
    day = 86400
    n = 60
    times = [t0 + timedelta(days=i) for i in range(n)]
    c1 = [math.sin(i / 5.0) for i in range(n)]
    c2 = [((i * 7) % 11) / 11.0 for i in range(n)]
    x = [2 + 1.5 * a - 0.7 * b + ((i * 13) % 17 - 8) / 100.0
         for i, (a, b) in enumerate(zip(c1, c2))]
    series = {
        (Source.COMMODITY_BAR, "sig"): BarSeries(
            field="sig", times=times, values=x, coverage_start=times[0]),
        (Source.INTL, "brent"): BarSeries(
            field="brent", times=times, values=c1, coverage_start=times[0]),
        (Source.COMMODITY_BAR, "realised_volatility"): BarSeries(
            field="realised_volatility", times=times, values=c2,
            coverage_start=times[0]),
    }
    spec = FeatureSpec(
        feature_id="f2c", mechanism="m", output_step="r",
        failure_condition="奇异", authored_by="t",
        steps=[
            Step(name="w", kind=StepKind.WINDOW, source=Source.COMMODITY_BAR,
                 field="sig", op=Op.LAST, window_seconds=2 * day),
            Step(name="r", kind=StepKind.RESIDUALISE, inputs=["w"],
                 controls=["brent", "own_realised_volatility"],
                 window_seconds=40 * day, sample_every_seconds=day,
                 min_samples=10),
        ],
    )
    at = times[-1] + timedelta(hours=1)
    want = evaluate_spec(spec, at, series)
    namespace: dict = {}
    exec(compile(to_python(spec), "<f2c>", "exec"), namespace)  # noqa: S102
    got = namespace["compute"](at, as_plain(series))
    assert want is not None and got == want
