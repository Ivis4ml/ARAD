

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
