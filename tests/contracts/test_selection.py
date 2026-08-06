"""选择校正的合同测试（M9.1）。

这一层存在的唯一理由是：一条随迭代上升的曲线，正是选择在纯噪声上必然产出的形状。
因此测试盯的是"零假设带算得对不对"，以及"它是否随看的次数上升"。
"""

from __future__ import annotations

import math

from arad.evaluation.selection import (
    _inv_norm_cdf,
    deflated_sharpe,
    expected_max_abs_z,
    expected_max_sharpe,
    expected_max_z,
    selection_band,
    sharpe_spread,
)


def test_the_inverse_normal_is_accurate_enough_to_use():
    assert _inv_norm_cdf(0.975) == __import__("pytest").approx(1.959964, abs=1e-5)
    assert _inv_norm_cdf(0.5) == __import__("pytest").approx(0.0, abs=1e-9)
    assert _inv_norm_cdf(0.999) == __import__("pytest").approx(3.090232, abs=1e-4)


def test_it_reproduces_the_prior_systems_independently_computed_null():
    """旧系统 hillclimb 记录：81 次试验、试验间 Sharpe 标准差 0.06758419676972037，
    独立算出 sr_null = 0.16595662252137777、年化 2.6344797096947197。

    这是一次跨实现的核对：同一个公式在另一套代码里得到同样的数，
    说明这里的实现不是自说自话。
    """
    value = expected_max_sharpe(81, 0.06758419676972037)
    assert value == __import__("pytest").approx(0.16595662252137777, rel=1e-4)
    assert value * math.sqrt(252) == __import__("pytest").approx(2.6344797096947197, rel=1e-4)


def test_the_one_sided_and_two_sided_bands_are_different_and_used_for_different_things():
    """Sharpe 只朝一个方向挑，|t| 接受任一方向。用错一侧会把零假设抬高约 1.5 倍。"""
    assert expected_max_z(81) < expected_max_abs_z(81)
    assert expected_max_abs_z(81) / expected_max_z(81) == __import__("pytest").approx(
        1.098, abs=0.02
    )


def test_the_band_rises_with_how_many_times_you_looked():
    assert expected_max_abs_z(1) < expected_max_abs_z(10) < expected_max_abs_z(1000)


def test_only_outcome_reads_raise_the_band():
    """被挡下、没读 outcome 的轮次仍留在图上，但不抬高多重检验负担。"""
    points = [
        {"value": 1.0, "counts_toward_denominator": False},
        {"value": 2.0, "counts_toward_denominator": True},
        {"value": 1.5, "counts_toward_denominator": True},
    ]
    band = selection_band(points)
    assert [p["tests_so_far"] for p in band] == [0, 1, 2]
    assert band[0]["null_threshold"] is None
    assert band[1]["null_threshold"] < band[2]["null_threshold"]


def test_running_best_never_goes_down():
    points = [{"value": v, "counts_toward_denominator": True} for v in (1.0, 3.0, 2.0)]
    assert [p["running_best"] for p in selection_band(points)] == [1.0, 3.0, 3.0]


def test_undefined_points_do_not_break_the_running_best():
    points = [{"value": None, "counts_toward_denominator": False},
              {"value": float("nan"), "counts_toward_denominator": False},
              {"value": 2.0, "counts_toward_denominator": True}]
    band = selection_band(points)
    assert band[0]["running_best"] is None
    assert band[2]["running_best"] == 2.0


def test_deflated_sharpe_falls_as_the_selection_benchmark_rises():
    lenient = deflated_sharpe(0.2, benchmark_sharpe=0.05, n_periods=500)
    strict = deflated_sharpe(0.2, benchmark_sharpe=0.19, n_periods=500)
    assert 0.0 <= strict < lenient <= 1.0


def test_a_sharpe_below_the_selection_benchmark_is_more_likely_noise_than_not():
    """旧系统的实测就是这个形状：81 次选出的 2.40 低于零假设的 2.63。"""
    dsr = deflated_sharpe(2.40 / math.sqrt(252),
                          benchmark_sharpe=2.6345 / math.sqrt(252), n_periods=102)
    assert dsr < 0.5


def test_the_band_is_undefined_rather_than_guessed_when_there_is_no_spread():
    assert math.isnan(expected_max_sharpe(1, 0.05))
    assert math.isnan(expected_max_sharpe(50, 0.0))
    assert math.isnan(deflated_sharpe(float("nan"), benchmark_sharpe=0.1, n_periods=100))


def test_the_sharpe_band_needs_the_family_to_have_tried_at_least_twice():
    """尺度取自本链自身的 Sharpe 离散度：一次试验估不出离散度，不能假设一个。"""
    points = [{"value": -0.03, "counts_toward_denominator": True},
              {"value": -0.04, "counts_toward_denominator": True},
              {"value": -0.01, "counts_toward_denominator": True}]
    band = selection_band(points, metric="sharpe", n_periods=800)
    assert band[0]["null_threshold"] is None
    assert band[1]["null_threshold"] is not None
    assert band[1]["null_threshold"] < band[2]["null_threshold"]


def test_the_sharpe_band_uses_the_one_sided_expectation():
    """搜索留下的是 Sharpe 最大的那个，不是 |Sharpe| 最大的那个。"""
    values = [0.10, 0.02, 0.06, 0.04]
    points = [{"value": v, "counts_toward_denominator": True} for v in values]
    band = selection_band(points, metric="sharpe", n_periods=500)
    spread = sharpe_spread(values)
    assert band[-1]["null_threshold"] == __import__("pytest").approx(
        expected_max_sharpe(4, spread)
    )


def test_a_sharpe_under_the_band_gets_a_deflated_probability_below_a_half():
    points = [{"value": v, "counts_toward_denominator": True, "skew": 0.1,
               "excess_kurtosis": 2.0} for v in (-0.035, -0.043, -0.010)]
    band = selection_band(points, metric="sharpe", n_periods=887)
    assert band[-1]["deflated_sharpe"] < 0.5


def test_no_band_and_no_dsr_for_metrics_that_have_no_estimable_null():
    points = [{"value": 0.05, "counts_toward_denominator": True} for _ in range(3)]
    band = selection_band(points, metric="ic_spearman")
    assert all(p["null_threshold"] is None for p in band)
    assert all("deflated_sharpe" not in p for p in band)


def test_the_spread_is_undefined_rather_than_guessed():
    import math as _m

    assert _m.isnan(sharpe_spread([0.1]))
    assert _m.isnan(sharpe_spread([None, float("nan")]))
