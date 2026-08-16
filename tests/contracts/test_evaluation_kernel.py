

# ---------------------------------------------------------------- 方向核对（决定 0012）


def _directional_request(direction: int, slope_sign: int, **kw):
    """造一批线性数据：prediction 与 label 的关系符号由 slope_sign 决定。"""
    from datetime import UTC, datetime, timedelta

    from arad.evaluation.kernel import EvaluationRequest, EvaluationRow

    base = datetime(2024, 1, 2, 9, 0, tzinfo=UTC)
    rows, labels = [], {}
    for i in range(200):
        x = (i % 20) - 10 + (i * 0.013)
        key = f"p{i % 4}:{i}"
        rows.append(EvaluationRow(
            row_key=key, episode_id=f"e{i}", date_cluster=f"d{i // 2}",
            product_cluster=f"p{i % 4}",
            decision_time=base + timedelta(hours=i),
            label_start=base + timedelta(hours=i, minutes=1),
            availability_times={"pm": base + timedelta(hours=i, minutes=-5)},
            prediction=x, controls={},
        ))
        labels[key] = slope_sign * x * 0.01 + ((i % 7) - 3) * 0.0005
    return EvaluationRequest(
        study_id="s", confirmatory_id="c", family="f", rows=rows,
        authoritative_keys=list(labels), declared_direction=direction,
        label_is_return=False, cost_model_declared=True,
        cost_model={"version": "t", "round_trip_cost_ret": 1e-9}, **kw,
    ), labels


def test_a_sign_opposite_to_the_declared_direction_invalidates_candidate():
    """预注册方向与实得符号相反：所主张的机制未被支持，不可为 candidate。

    这条判据本就写在每份提案自己的证否条件里，此前没有任何东西执行它 ——
    实测全史 188 条有方向的 Study 里 103 条符号相反。
    """
    from arad.evaluation.kernel import evaluate

    request, labels = _directional_request(direction=-1, slope_sign=+1)
    result = evaluate(request, labels, role="evaluator")
    assert "direction_mismatch" in result["blocked_reason_kinds"]
    assert result["suggested_verdict"] != "candidate"


def test_a_sign_matching_the_declared_direction_does_not_block():
    from arad.evaluation.kernel import evaluate

    request, labels = _directional_request(direction=+1, slope_sign=+1)
    result = evaluate(request, labels, role="evaluator")
    assert "direction_mismatch" not in result["blocked_reason_kinds"]


def test_an_undeclared_direction_is_not_judged():
    """未声明方向就不判方向 —— 不能替提案补一个它没写的预注册。"""
    from arad.evaluation.kernel import evaluate

    request, labels = _directional_request(direction=0, slope_sign=-1)
    result = evaluate(request, labels, role="evaluator")
    assert "direction_mismatch" not in result["blocked_reason_kinds"]


def test_direction_mismatch_does_not_invalidate_null():
    """反号且幅度很小仍是一条合法的否定。"""
    from arad.evaluation.kernel import REASON_INVALIDATES

    assert REASON_INVALIDATES["direction_mismatch"] == frozenset({"candidate"})


def test_declared_direction_enters_the_request_digest():
    """同一批预测配不同的声明方向不是同一次检验。"""
    a, _ = _directional_request(direction=+1, slope_sign=+1)
    b, _ = _directional_request(direction=-1, slope_sign=+1)
    assert a.digest() != b.digest()


# ---------------------------------------------------------------- decoy 校准（决定 0014）


def test_decoy_is_disclosure_only_and_never_blocks():
    """decoy 只披露，不作判据。升格为闸门需另一份决定。"""
    from arad.evaluation.kernel import REASON_INVALIDATES, evaluate

    request, labels = _directional_request(direction=+1, slope_sign=+1)
    result = evaluate(request, labels, role="evaluator")
    assert "decoy" in result["diagnostics"]
    assert "decoy_exceed_rate" in result["diagnostics"]["decoy"]
    # 没有任何以 decoy 为名的失效理由
    assert not [k for k in REASON_INVALIDATES if "decoy" in k]
    assert not [k for k in result["blocked_reason_kinds"] if "decoy" in k]


def test_decoy_separates_a_real_relationship_from_none():
    """有真实关系时伪因子比不过；无关系时伪因子与真因子难分。"""
    from arad.evaluation.stats import decoy_slope_distribution

    n = 400
    x = [((i * 7919) % 101) / 101.0 - 0.5 for i in range(n)]
    linked = [3.0 * xi for xi in x]
    unlinked = [((i * 4111) % 97) / 97.0 - 0.5 for i in range(n)]

    strong = decoy_slope_distribution(linked, x, draws=99, seed=0)
    weak = decoy_slope_distribution(unlinked, x, draws=99, seed=0)
    assert strong["decoy_exceed_rate"] < 0.05
    assert weak["decoy_exceed_rate"] > strong["decoy_exceed_rate"]


def test_decoy_preserves_the_factor_series_marginal():
    """循环平移逐点保留因子的边际分布与自相关；打乱会毁掉后者。"""
    from arad.evaluation.stats import decoy_slope_distribution

    x = [float(i % 13) for i in range(200)]
    y = [float((i * 3) % 7) for i in range(200)]
    out = decoy_slope_distribution(y, x, draws=20, seed=1, min_shift=5)
    assert out["draws"] > 0
    assert out["min_shift"] == 5


def test_sealed_openings_are_counted_as_their_own_denominator(tmp_path):
    """一次性规则挡不住「开很多条不同构造的封再报最好的」，那同样要按次数记账。"""
    from arad.evaluation.sealed import sealed_denominator
    from arad.memory.ledger import EvidenceLedger

    with EvidenceLedger(str(tmp_path / "t.db")) as ledger:
        assert sealed_denominator(ledger) == 0
        for i in range(3):
            ledger.append("sealed_segment_opened",
                          {"feature_id": f"f{i}", "segment": "historical_validation"})
        ledger.append("sealed_segment_opened",
                      {"feature_id": "g", "segment": "forward_confirmation"})
        assert sealed_denominator(ledger) == 4
        assert sealed_denominator(ledger, "historical_validation") == 3
