"""最小评价机的合同测试（M3 第二块）。

M3 出口条件要求"故意泄漏、单位错误、结果依赖过滤和记录删除全部失败"。
前三条在这里，第四条在 test_ledger.py。
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import pytest

from arad.evaluation import stats
from arad.evaluation.kernel import (
    DegenerateControl,
    EvaluationRequest,
    EvaluationRow,
    LabelAccessDenied,
    LeakageDetected,
    OutcomeDependentFiltering,
    evaluate,
)

BASE = datetime(2024, 1, 1, tzinfo=UTC)


def make_rows(n=60, *, leak=False, constant_control=False, seed=7):
    import random

    rng = random.Random(seed)
    rows, labels = [], {}
    for i in range(n):
        decision = BASE + timedelta(hours=6 * i)
        label_start = decision + timedelta(minutes=1)
        available = decision + timedelta(minutes=5) if leak else decision - timedelta(minutes=5)
        pred = rng.gauss(0, 1)
        rows.append(
            EvaluationRow(
                row_key=f"r{i:03d}",
                episode_id=f"ep{i // 2:03d}",
                date_cluster=f"d{i // 2:03d}",
                product_cluster="sc",
                decision_time=decision,
                label_start=label_start,
                availability_times={"pm_innovation": available},
                prediction=pred,
                controls={"news": 0.0 if constant_control else rng.gauss(0, 1)},
            )
        )
        labels[f"r{i:03d}"] = rng.gauss(0, 1)
    return rows, labels


def a_request(rows, **kw):
    base = {
        "study_id": "s1",
        "confirmatory_id": "c1",
        "family": "fam",
        "rows": rows,
        "authoritative_keys": [r.row_key for r in rows],
        "cost_model_declared": True,
        "placebo_draws": 40,
        "min_clusters": 5,
    }
    base.update(kw)
    return EvaluationRequest(**base)


# ---------------------------------------------------------------- 三条必须失败


def test_deliberate_leakage_fails(): 
    """feature 在决策时点之后才可用 —— 评价机必须拒绝出具结果。"""
    rows, labels = make_rows(leak=True)
    with pytest.raises(LeakageDetected, match="availability_time"):
        evaluate(a_request(rows), labels, role="evaluator")


def test_decision_at_or_after_label_start_fails():
    rows, labels = make_rows()
    bad = rows[0]
    rows[0] = EvaluationRow(
        **{**bad.__dict__, "label_start": bad.decision_time}
    )
    with pytest.raises(LeakageDetected, match="不早于 label 起点"):
        evaluate(a_request(rows), labels, role="evaluator")


def test_constant_control_fails_as_a_unit_error():
    """旧系统真实故障：微秒时间戳按纳秒解析，新闻控制恒为零仍给出显著结果。"""
    rows, labels = make_rows(constant_control=True)
    with pytest.raises(DegenerateControl, match="恒为"):
        evaluate(a_request(rows), labels, role="evaluator")


def test_missing_control_value_fails():
    rows, labels = make_rows()
    bad = rows[0]
    rows[0] = EvaluationRow(**{**bad.__dict__, "controls": {}})
    with pytest.raises(DegenerateControl, match="缺失"):
        evaluate(a_request(rows), labels, role="evaluator")


def test_outcome_dependent_filtering_fails():
    """看过结果之后再删行：没有预注册排除规则就必须失败。"""
    rows, labels = make_rows()
    kept = rows[:50]
    request = a_request(kept, authoritative_keys=[r.row_key for r in rows])
    with pytest.raises(OutcomeDependentFiltering, match="没有预注册的排除规则"):
        evaluate(request, labels, role="evaluator")


def test_preregistered_exclusions_are_accepted():
    rows, labels = make_rows()
    kept = rows[:50]
    dropped = {r.row_key: "预注册：交易所数据错误" for r in rows[50:]}
    request = a_request(
        kept, authoritative_keys=[r.row_key for r in rows], preregistered_exclusions=dropped
    )
    result = evaluate(request, labels, role="evaluator")
    assert result["coverage"]["rows_excluded_preregistered"] == 10


def test_rows_outside_the_authoritative_set_fail():
    rows, labels = make_rows()
    request = a_request(rows, authoritative_keys=[r.row_key for r in rows[:30]])
    with pytest.raises(OutcomeDependentFiltering, match="权威行集合之外"):
        evaluate(request, labels, role="evaluator")


# ---------------------------------------------------------------- 能力边界


@pytest.mark.parametrize("role", ["proposer", "orchestrator", "research_worker", "human"])
def test_only_the_evaluator_may_read_labels(role):
    rows, labels = make_rows()
    with pytest.raises(LabelAccessDenied):
        evaluate(a_request(rows), labels, role=role)


# ---------------------------------------------------------------- 结构化输出


def test_result_reports_all_independence_dimensions():
    """Merge-Plan-2 §5.4：nominal n、双向 cluster、HAC、Episode、序列相关必须同时出现。"""
    rows, labels = make_rows()
    result = evaluate(a_request(rows), labels, role="evaluator")
    d = result["diagnostics"]
    assert d["nominal_n"] == 60
    assert d["episode"]["clusters"] == 30
    assert d["date_cluster"]["clusters"] == 30
    assert d["product_cluster"]["clusters"] == 1
    assert "kish_n_eff" in d["episode"]
    assert d["two_way_cluster"]["clusters_a"] == 30
    assert d["two_way_cluster"]["degenerate_dimension"] == "cluster_b"  # 单品种
    assert d["hac"]["lag"] == 5
    assert "suggested_block_length" in d
    assert "不替代" in d["note"]


def test_kish_is_reported_alongside_cluster_and_hac_not_instead_of_them():
    rows, labels = make_rows()
    d = evaluate(a_request(rows), labels, role="evaluator")["diagnostics"]
    assert d["episode"]["kish_n_eff"] > 0
    assert not math.isnan(d["two_way_cluster"]["se"])
    assert "se" in d["hac"]


def test_result_is_deterministic_and_content_addressed():
    rows, labels = make_rows()
    a = evaluate(a_request(rows), labels, role="evaluator")
    b = evaluate(a_request(rows), labels, role="evaluator")
    assert a["request_digest"] == b["request_digest"]
    assert a["result_digest"] == b["result_digest"]


def test_changing_one_prediction_changes_both_digests():
    rows, labels = make_rows()
    a = evaluate(a_request(rows), labels, role="evaluator")
    bad = rows[0]
    rows[0] = EvaluationRow(**{**bad.__dict__, "prediction": bad.prediction + 1.0})
    b = evaluate(a_request(rows), labels, role="evaluator")
    assert a["request_digest"] != b["request_digest"]
    assert a["result_digest"] != b["result_digest"]


# ---------------------------------------------------------------- 准入


def test_random_predictions_do_not_become_a_candidate():
    """预测与标签独立时，置换检验应当挡住它。"""
    rows, labels = make_rows(n=80, seed=11)
    result = evaluate(a_request(rows), labels, role="evaluator")
    assert result["suggested_verdict"] != "candidate"
    assert result["blocked_reasons"]


def test_missing_cost_model_blocks_candidate():
    rows, labels = make_rows()
    result = evaluate(a_request(rows, cost_model_declared=False), labels, role="evaluator")
    assert any("成本模型" in r for r in result["blocked_reasons"])


def test_too_few_episodes_yields_underpowered_not_null():
    rows, labels = make_rows(n=40)
    result = evaluate(a_request(rows, min_clusters=100), labels, role="evaluator")
    assert result["suggested_verdict"] == "underpowered"


def test_single_influential_point_blocks_candidate():
    rows, labels = make_rows(n=60, seed=3)
    # 造一个极端点：预测与标签同时被推得很远
    bad = rows[0]
    rows[0] = EvaluationRow(**{**bad.__dict__, "prediction": 50.0})
    labels[bad.row_key] = 50.0
    result = evaluate(a_request(rows), labels, role="evaluator")
    assert any("单点影响过大" in r for r in result["blocked_reasons"])


# ---------------------------------------------------------------- 统计原语


def test_ols_recovers_a_known_slope():
    x = [float(i) for i in range(20)]
    y = [3.0 + 2.0 * xi for xi in x]
    intercept, slope, resid = stats.ols(y, x)
    assert slope == pytest.approx(2.0)
    assert intercept == pytest.approx(3.0)
    assert max(abs(r) for r in resid) < 1e-9


def test_ols_refuses_a_constant_regressor():
    with pytest.raises(ValueError, match="没有变异"):
        stats.ols([1.0, 2.0, 3.0], [5.0, 5.0, 5.0])


def test_two_way_cluster_se_exceeds_naive_when_clusters_are_coarse():
    """粗 cluster 会放大方差；只报单向或不报 cluster 会低估不确定性。"""
    x = [float(i % 7) - 3 for i in range(70)]
    resid = [1.0 if i % 7 < 4 else -1.0 for i in range(70)]
    products = [f"p{i % 5}" for i in range(70)]
    fine = stats.two_way_cluster_se(x, resid, [f"d{i}" for i in range(70)], products)
    coarse = stats.two_way_cluster_se(x, resid, [f"d{i // 10}" for i in range(70)], products)
    assert coarse["variance"] > fine["variance"]
    assert fine["degenerate_dimension"] is None


def test_single_cluster_dimension_degrades_to_one_way_and_says_so():
    """单品种样本：双向 cluster 恒为零，必须降级并声明，而不是吐 NaN。"""
    x = [float(i % 7) - 3 for i in range(70)]
    resid = [1.0 if i % 7 < 4 else -1.0 for i in range(70)]
    got = stats.two_way_cluster_se(x, resid, [f"d{i // 10}" for i in range(70)], ["sc"] * 70)
    assert got["degenerate_dimension"] == "cluster_b"
    assert got["fell_back_to"] == "cluster_a"
    assert got["variance"] > 0 and not math.isnan(got["se"])
    assert "显式声明" in got["note"]


def test_block_length_grows_with_serial_dependence():
    import random as _random

    rng = _random.Random(5)
    independent = [rng.gauss(0, 1) for _ in range(200)]
    persistent = [float(i % 50) for i in range(200)]
    assert stats.suggested_block_length(persistent) > stats.suggested_block_length(independent)


def test_block_length_reacts_to_strong_negative_autocorrelation_too():
    """块自助关心的是序列相关的强度，正负都算。"""
    alternating = [(-1.0) ** i for i in range(200)]
    assert stats.suggested_block_length(alternating) > 1


def test_kish_n_eff_penalises_concentration():
    assert stats.kish_n_eff([1.0] * 10) == pytest.approx(10.0)
    assert stats.kish_n_eff([100.0, 1.0, 1.0]) < 2.0


def test_placebo_is_seeded_and_reproducible():
    x = [float(i) for i in range(40)]
    y = [float((i * 7) % 11) for i in range(40)]
    groups = [f"g{i // 2}" for i in range(40)]
    a = stats.placebo_slope_distribution(y, x, groups, draws=30, seed=1)
    b = stats.placebo_slope_distribution(y, x, groups, draws=30, seed=1)
    assert a == b
    c = stats.placebo_slope_distribution(y, x, groups, draws=30, seed=2)
    assert c["seed"] == 2


# ---------------------------------------------------------------- Baseline Control

import os

BASELINE_TARGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "spine", "sc", "target_sc_rv_next_session.parquet",
)


@pytest.mark.skipif(not os.path.exists(BASELINE_TARGET), reason="需要先运行 spine build")
def test_baseline_pairs_only_the_same_session_type():
    """夜盘与日盘的波动水平系统性不同；相邻 session 配对会造出假的负持续性。"""
    from arad.evaluation.baseline import build_rows

    rows, labels = build_rows(BASELINE_TARGET, "discovery")
    assert len(rows) > 500
    for r in rows:
        session = r.row_key.rsplit(":", 1)[1]
        assert session in ("night", "day")
    assert set(labels) == {r.row_key for r in rows}


@pytest.mark.skipif(not os.path.exists(BASELINE_TARGET), reason="需要先运行 spine build")
def test_baseline_rows_are_pit_clean_by_construction():
    from arad.evaluation.baseline import build_rows

    rows, _ = build_rows(BASELINE_TARGET, "discovery")
    for r in rows:
        assert r.decision_time < r.label_start
        for available in r.availability_times.values():
            assert available < r.decision_time


@pytest.mark.skipif(not os.path.exists(BASELINE_TARGET), reason="需要先运行 spine build")
def test_baseline_volatility_persistence_has_the_expected_sign():
    """对数已实现波动的一阶持续性应为正。负号说明配对构造有误。"""
    from arad.evaluation.baseline import run_baseline

    result = run_baseline(BASELINE_TARGET)
    assert result["effects"]["slope"] > 0.5
    assert result["diagnostics"]["placebo"]["placebo_exceed_rate"] < 0.05
    assert result["coverage"]["min_lead_seconds"] > 0


@pytest.mark.skipif(not os.path.exists(BASELINE_TARGET), reason="需要先运行 spine build")
def test_baseline_is_not_counted_as_an_alternative_factor():
    """纯量价因子不能被统计为另类因子（Merge-Plan-2 §3.1）。"""
    from arad.evaluation.baseline import run_baseline

    result = run_baseline(BASELINE_TARGET)
    assert result["inventory"] == "baseline_control"
    assert "不计入 Alternative Factor Inventory" in result["inventory_note"]


@pytest.mark.skipif(not os.path.exists(BASELINE_TARGET), reason="需要先运行 spine build")
def test_single_product_sample_cannot_reach_candidate():
    """单品种样本识别不出横截面相关结构，评价机必须拒绝给 candidate。"""
    from arad.evaluation.baseline import run_baseline

    result = run_baseline(BASELINE_TARGET)
    assert result["suggested_verdict"] != "candidate"
    assert any("只有一组" in r for r in result["blocked_reasons"])


def test_controls_are_declared_as_integrity_checked_only():
    """一元回归里 controls 不进回归；产物必须显式声明，避免下游误以为已控制。"""
    rows, labels = make_rows()
    d = evaluate(a_request(rows), labels, role="evaluator")["diagnostics"]
    assert d["controls_are_integrity_checked_only"] is True
    assert "不进入回归" in d["controls_note"]


# ---------------------------------------------------------------- IC 与 Sharpe


def test_ic_is_reported_and_labelled_as_time_series():
    """截面 IC 需要同一时点多个标的；本样本没有那个维度，叫它 IC 而不注明是误导。"""
    rows, labels = make_rows()
    result = evaluate(a_request(rows), labels, role="evaluator")
    ic = result["effects"]["ic"]
    assert ic["kind"] == "time_series"
    assert -1.0 <= ic["ic_spearman"] <= 1.0
    assert "截面 IC" in ic["note"]


def test_sharpe_is_undefined_when_the_label_is_not_a_return():
    """已实现波动不是收益。给一个能被误读的数字，不如给一个明确的未定义与理由。"""
    rows, labels = make_rows()
    result = evaluate(a_request(rows), labels, role="evaluator")
    perf = result["effects"]["performance"]
    assert perf["sharpe"] is None
    assert "不是有符号收益" in perf["sharpe_undefined_reason"]


def test_sharpe_is_computed_once_the_caller_declares_a_return_label():
    rows, labels = make_rows()
    request = a_request(rows, label_is_return=True, periods_per_year=485.3,
                        target_name="sc_ret_next_session", label_rule="entry_to_close")
    perf = evaluate(request, labels, role="evaluator")["effects"]["performance"]
    assert perf["sharpe"] is not None
    assert perf["position_rule"] == "sign_unit"
    assert "pre-cost" in perf["note"]
    assert math.isfinite(perf["skew"])
    assert perf["periods_per_year_derived"] is not None


def test_declaring_a_return_label_changes_the_request_identity():
    """同一批预测、两种 label 语义，不能共用一个 request 摘要。"""
    rows, _ = make_rows()
    a = a_request(rows)
    b = a_request(rows, label_is_return=True, label_rule="entry_to_close")
    assert a.digest() != b.digest()


def test_a_return_claim_on_a_non_return_label_rule_is_refused():
    """没有这道检查，tradable_claim 就只是装饰：一张已实现波动的表照样能出年化 Sharpe。"""
    from arad.evaluation.kernel import LabelIsNotAReturn

    rows, labels = make_rows()
    request = a_request(rows, label_is_return=True,
                        target_name="sc_rv_next_session", label_rule="full_session")
    with pytest.raises(LabelIsNotAReturn, match="不产出有符号收益"):
        evaluate(request, labels, role="evaluator")


def test_the_kernel_and_the_spine_agree_on_which_rules_produce_returns():
    """两处各存一份常量，必须钉在一起，否则加了新规则只改一边就会静默放行。"""
    from arad.evaluation.kernel import RETURN_LABEL_RULES as kernel_rules
    from arad.temporal.targets import RETURN_LABEL_RULES as spine_rules

    assert kernel_rules == spine_rules


def test_the_annualisation_factor_is_derived_from_the_actual_decision_times():
    """SC 一天两个 session，沿用 252 会把年化 Sharpe 低估约三成。"""
    rows, labels = make_rows(n=120)
    request = a_request(rows, label_is_return=True, periods_per_year=252.0,
                        target_name="sc_ret_next_session", label_rule="entry_to_close")
    perf = evaluate(request, labels, role="evaluator")["effects"]["performance"]
    # 造数每 6 小时一个决策点 -> 每年约 1461 个
    assert perf["periods_per_year_derived"] > 1000
    assert perf["periods_per_year_declared"] == 252.0


# ---------------------------------------------------------------- 分位组合与相关矩阵


def test_the_quantile_portfolio_bets_only_on_the_two_extremes():
    """与 sign_unit 度量的不是同一件事：它问「最极端的两端是否真的不同」。"""
    pred = [float(i) for i in range(200)]
    label = [0.01 if i >= 190 else (-0.01 if i < 10 else 0.0) for i in range(200)]
    q = stats.quantile_portfolio(pred, label, top=0.05, bottom=0.05)
    assert q["defined"] is True
    assert q["n_long"] == 10 and q["n_short"] == 10
    assert q["long_mean"] == pytest.approx(0.01)
    assert q["short_mean"] == pytest.approx(-0.01)
    assert q["long_short_spread"] == pytest.approx(0.02)


def test_excess_is_measured_against_the_sample_mean_not_against_zero():
    """本仓库没有资金成本模型，把参照当零会高估超额。"""
    pred = list(range(100))
    label = [0.05] * 100          # 全样本收益恒定，任何分位都不该有超额
    q = stats.quantile_portfolio([float(p) for p in pred], label)
    assert q["benchmark_mean"] == pytest.approx(0.05)
    assert q["long_excess"] == pytest.approx(0.0)
    assert q["short_excess"] == pytest.approx(0.0)


def test_a_quantile_portfolio_is_undefined_rather_than_guessed_on_thin_samples():
    assert stats.quantile_portfolio([1.0, 2.0], [0.1, 0.2])["defined"] is False


def test_the_evaluation_records_both_position_rules_never_one_of_them():
    """两者是同一次 outcome 读取的两种汇总；事后挑好看的那个才是选择偏差。"""
    rows, labels = make_rows()
    request = a_request(rows, label_is_return=True, target_name="sc_ret_next_session",
                        label_rule="entry_to_close")
    perf = evaluate(request, labels, role="evaluator")["effects"]["performance"]
    assert perf["position_rule"] == "sign_unit"
    assert "quantile_portfolio" in perf
    assert perf["quantile_portfolio"]["defined"] is True


def test_effective_signals_counts_independent_ideas_not_variants():
    """自检必须包含边界：这三个案例分别抓出过两个真实缺陷。"""
    ident = [[1.0 if i == j else 0.0 for j in range(5)] for i in range(5)]
    collinear = [[1.0] * 5 for _ in range(5)]
    near = [[1.0, 0.99], [0.99, 1.0]]
    assert stats.effective_independent_signals(ident)[
        "effective_independent_signals"] == pytest.approx(5.0, abs=1e-6)
    # 整数特征值处的浮点噪声曾让这一项算出 2.0
    assert stats.effective_independent_signals(collinear)[
        "effective_independent_signals"] == pytest.approx(1.0, abs=1e-6)
    # Li & Ji 的估计量在这里给出 2.00，即把高度相关的两个信号当成两次独立检验
    assert stats.effective_independent_signals(near)[
        "effective_independent_signals"] < 1.1


def test_the_correlation_matrix_is_symmetric_with_a_unit_diagonal():
    m = stats.correlation_matrix({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "b": [2.0, 4.0, 6.0, 8.0, 10.0],
        "c": [5.0, 1.0, 4.0, 2.0, 3.0],
    })
    n = len(m["names"])
    for i in range(n):
        assert m["matrix"][i][i] == pytest.approx(1.0)
        for j in range(n):
            assert m["matrix"][i][j] == pytest.approx(m["matrix"][j][i])
    # a 与 b 是同一个想法的两种写法
    ia, ib = m["names"].index("a"), m["names"].index("b")
    assert m["matrix"][ia][ib] == pytest.approx(1.0)


def test_a_clean_null_is_not_accused_of_single_point_influence():
    """真实事故的回归：一条 t = -0.03 的干净零结果被报成「最大 DFBETA 占斜率 9.72」。

    `|DFBETA| / |β̂|` 在 β̂ → 0 时发散，因此这道闸门在**根本没有效应**时最响，
    而那时并不存在任何被单点主导的结论 —— 那条真实特征的最大杠杆只有 0.022。
    这里用纯噪声复现同一形态：t = -0.059，旧口径 11.86，而最大杠杆是正常的。
    """
    rows, labels = make_rows(n=60, seed=7)
    result = evaluate(a_request(rows), labels, role="evaluator")
    infl = result["diagnostics"]["influence"]
    assert abs(result["effects"]["t_stat"]) < 0.5, "这一条必须是零结果，否则测的不是同一件事"
    assert infl["dfbeta_over_slope"] > 10, "旧口径确实会在这里触发"
    assert infl["max_abs_dfbetas"] < 1.0
    assert infl["max_leverage"] < 0.2, "没有任何单点主导：杠杆是正常的"
    assert not any("单点影响过大" in r for r in result["blocked_reasons"])


def test_max_leverage_does_not_depend_on_the_labels():
    """最大杠杆是 DFBETA 里不含残差的那一半，因此读标签之前就可算。

    这一条是「只用 X 的诊断通道」是否可能存在的前提：它对提案器不构成效应泄漏。
    """
    x = [0.0, 1.0, 2.0, 3.0, 40.0]
    a = stats.influence_on_slope(x, [0.1, -0.2, 0.3, -0.1, 0.05])
    b = stats.influence_on_slope(x, [-9.0, 4.0, 0.0, 7.0, -3.0])
    assert a["max_leverage"] == b["max_leverage"]
    assert a["max_leverage"] > 0.9, "一个点远离其余全部时，它几乎独占回归元的变异"


def test_the_influence_gate_is_scaled_by_the_standard_error_not_the_estimate():
    """闸门读的必须是 DFBETAS。把两个口径同时报出来，是为了让口径变更可回放。"""
    rows, labels = make_rows(n=60, seed=3)
    bad = rows[0]
    rows[0] = EvaluationRow(**{**bad.__dict__, "prediction": 50.0})
    labels[bad.row_key] = 50.0
    result = evaluate(a_request(rows), labels, role="evaluator")
    infl = result["diagnostics"]["influence"]
    assert {"max_abs_dfbetas", "dfbeta_over_slope", "max_leverage"} <= set(infl)
    reason = next(r for r in result["blocked_reasons"] if "单点影响过大" in r)
    assert "标准误" in reason and "占斜率" not in reason


def test_an_unusable_standard_error_does_not_become_an_influence_finding(monkeypatch):
    """标准误量不出来时，单点影响是**无定义**，不是"超限"。

    分母取 inf 会让账本写下「斜率移动 inf 个标准误」，紧挨着另一条说 cluster 方差
    不可用的理由 —— 把度量失败报成关于特征的实质发现，与本票要修的是同一类错误。
    """
    real = stats.two_way_cluster_se

    def broken(*a, **kw):
        return {**real(*a, **kw), "se": float("nan"), "variance_negative": True}

    monkeypatch.setattr(stats, "two_way_cluster_se", broken)
    rows, labels = make_rows(n=60, seed=3)
    result = evaluate(a_request(rows), labels, role="evaluator")
    assert not any("单点影响过大" in r for r in result["blocked_reasons"])
    assert any("cluster 方差非正" in r for r in result["blocked_reasons"])
    infl = result["diagnostics"]["influence"]
    assert infl["gate_evaluable"] is False
    assert math.isnan(infl["max_abs_dfbetas"])


# ---------------------------------------------------------------- 判决语义（决定 0005）


def test_a_clean_negative_result_is_recorded_as_null_not_blocked():
    """否定结论必须能被记成 null。

    此前 `Verdict.NULL` 从未被任何代码路径产出：判决是
    `BLOCKED if blocked else CANDIDATE`，而 `cost_model_declared=False` 对每一条
    Study 都成立，于是一个干净的否定与一个真正判不出来的 Study 无从区分。
    整套系统存在的理由正是让否定结论可信。
    """
    rows, labels = make_rows(n=60, seed=7)
    result = evaluate(a_request(rows, cost_model_declared=False), labels, role="evaluator")
    assert "placebo_failed" in result["blocked_reason_kinds"]
    assert result["suggested_verdict"] == "null"
    # null 必须带着它的排除界，否则它只是「没找到」而不是「排除了什么」
    bound = result["null_exclusion_bound"]
    assert bound["mde_at_2p8_se"] > 0
    assert "M5" in bound["note"]


def test_the_cost_model_gate_blocks_candidate_but_not_null():
    """未声明成本模型挡的是可交易主张。

    断言「该机制与标的没有统计关系」不需要交易成本模型。若它同时挡住 null，
    则在 M5 完成之前 null 结构性不可达，而 M6/M7 的出口判据要求 null 可覆盖。
    """
    from arad.evaluation.kernel import REASON_INVALIDATES

    assert REASON_INVALIDATES["cost_model_missing"] == frozenset({"candidate"})


def test_cluster_degeneracy_invalidates_candidate_only():
    """标准误被低估只会**高估**显著性，因此只可能推翻 candidate。

    真实标准误更大只会让 |t| 更小，null 反而更强；且置换检验根本不使用标准误。
    """
    from arad.evaluation.kernel import REASON_INVALIDATES

    assert REASON_INVALIDATES["cluster_structure_insufficient"] == frozenset({"candidate"})


def test_single_point_influence_is_direction_aware():
    """一个点能制造效应，也能遮蔽效应，但两者的判据不同。

    守 candidate：这一点是否撑起了效应。守 null：删掉它之后 |t| 能否够到显著性。
    对称地把两者都判为「什么都断言不了」，会让每一个干净的 null 都自己把自己作废。
    """
    from arad.evaluation.kernel import REASON_INVALIDATES

    assert REASON_INVALIDATES["single_point_influence_candidate_only"] == frozenset(
        {"candidate"}
    )
    assert REASON_INVALIDATES["single_point_influence_both"] == frozenset(
        {"candidate", "null"}
    )
    rows, labels = make_rows(n=60, seed=3)
    bad = rows[0]
    rows[0] = EvaluationRow(**{**bad.__dict__, "prediction": 50.0})
    labels[bad.row_key] = 50.0
    result = evaluate(a_request(rows), labels, role="evaluator")
    kind = next(k for k in result["blocked_reason_kinds"] if k.startswith("single_point"))
    t = abs(result["effects"]["t_stat"])
    d = result["diagnostics"]["influence"]["max_abs_dfbetas"]
    expected = "both" if t + d >= 2.8 else "candidate_only"
    assert kind.endswith(expected)


def test_the_verdict_reads_only_reason_kinds_never_the_numbers_in_them():
    """判决只能是封闭种类表的函数。

    一旦推导条件化到任何未经预注册闸门表达的效应数值（例如「|t| < 0.5 才算 null」，
    或把 null 分成强弱两档），判决词就开始编码一次新的量级比较，那才是泄漏。
    强度差异只能留在证据里给评价机与人看。
    """
    from arad.evaluation.kernel import REASON_INVALIDATES, derive_verdict

    for kinds, expected in [
        (["placebo_failed", "cost_model_missing", "cluster_structure_insufficient"], "null"),
        (["placebo_failed", "single_point_influence_candidate_only"], "null"),
        (["placebo_failed", "single_point_influence_both"], "blocked"),
        (["placebo_failed", "not_identified"], "blocked"),
        (["cost_model_missing"], "blocked"),
        (["insufficient_sample", "placebo_failed"], "underpowered"),
        ([], "candidate"),
    ]:
        assert derive_verdict(kinds) == expected, kinds
    # 未登记的种类必须报错而不是静默地当作无害
    with pytest.raises(ValueError):
        derive_verdict(["something_new"])
    assert set(REASON_INVALIDATES) >= {"placebo_failed", "cost_model_missing"}


def test_the_verdict_classification_no_longer_reaches_the_proposer():
    """判决分类不再进提案器上下文（决定 0006）。

    M7 把它定价为安全，前提是它指向一个**匿名总体** —— 提案器每轮由独立子进程
    承载，跨轮不带上下文，因此「9 个 null」指的是哪 9 条它无从知道。
    M9 的具名清单取消了匿名，两者一联合就能做减法：`null` 只可能在读过 outcome
    之后产生，故 `#null <= tests_spent`；实测 run4 上 `#null = tests_spent = 9`，
    等式成立即推出「全部被度量过的具名规格都是 null」，而 null 的充要条件是
    置换检验未通过 = 实际斜率未超出其置换分布，那是一条关于量级的陈述。

    `blinded_history` 本身保留：Atlas 与人工复核要用它。
    """
    import json
    import tempfile

    from arad.harness.context import (
        DeclaredBias,
        assemble_proposer_context,
        blinded_history,
    )
    from arad.memory.ledger import EvidenceLedger

    with tempfile.TemporaryDirectory() as tmp, EvidenceLedger(f"{tmp}/l.db") as ledger:
        for i, verdict in enumerate(["null", "null", "blocked"]):
            ledger.append("verdict_recorded",
                          {"study_id": f"s{i}", "verdict": verdict,
                           "next_action": "archive_evidence", "rationale": "r"},
                          study_id=f"s{i}")
        bundle = assemble_proposer_context(
            ledger=ledger, family="fam", data_facts={}, targets=[{"name": "t"}],
            menu=[{"family_id": "c"}],
            menu_biases=[DeclaredBias("a", "b", "c")],
            budget_facts={}, blockers=[],
        )
        # 视图本身仍在，供 Atlas 与人工复核
        assert blinded_history(ledger, "fam")["verdict_taxonomy"] == {"null": 2, "blocked": 1}

    dumped = json.dumps(bundle.facts, ensure_ascii=False)
    assert "verdict_taxonomy" not in dumped
    assert "verdict" not in dumped
    for word in ("null", "blocked", "underpowered", "candidate"):
        assert f'"{word}"' not in dumped, word
    # 两本分母保留：它们由读 outcome 之前的纯函数决定，不是结果信息
    assert bundle.facts["denominators"]["statistical_denominator"] == 0
    for study_id in ("s0", "s1", "s2"):
        assert study_id not in bundle.prompt
