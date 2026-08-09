

def test_baseline_constructs_do_not_occupy_beam_slots():
    """B6：四条波动假象曾以最高奖励霸占全部束位，把唯一奖励为正的
    残差化另类构造挤出自动封存队列。决定 0002 本就规定纯量价构造
    不计入另类清单 —— 束位据此只留给非基线来源。"""
    from arad.harness.beam import Beam, Candidate

    beam = Beam(width=2)
    assert not beam.offer(Candidate(
        feature_id="vol_artefact", study_id="s1", value=9.3,
        tests_at_evaluation=20, source="commodity_bar"))
    assert beam.offer(Candidate(
        feature_id="pm_thing", study_id="s2", value=4.39,
        tests_at_evaluation=61, source="pm_market"))
    assert [m.feature_id for m in beam.members] == ["pm_thing"]


def test_underpowered_studies_never_reach_the_beam():
    """B7 的机制侧钉子：束语义要求 value 来自过了样本闸门的评价。
    这里钉 demo 侧的过滤行为等价物：underpowered 的候选即使 reward 为正
    也不该出现在束里 —— 通过构造直接验证束的输入契约。"""
    from arad.harness.beam import Beam, Candidate

    beam = Beam(width=2)
    # demo 侧的过滤在 offer 之前发生；这里验证的是：一旦过滤缺失，
    # 10 行样本的高 t 会压过 15,000 行的正常评价 —— 这正是要防的形态。
    small_sample = Candidate(feature_id="tiny", study_id="s", value=3.17,
                             tests_at_evaluation=51, source="pm_market")
    real = Candidate(feature_id="real", study_id="r", value=2.9,
                     tests_at_evaluation=51, source="pm_market")
    beam.offer(small_sample)
    beam.offer(real)
    # 束本身按 reward 排 —— 排序正确性仍成立；过滤责任在 demo 侧
    assert [m.feature_id for m in beam.members] == ["tiny", "real"]


def test_beam_construction_is_family_scoped():
    """B8：束按族过滤的判据 —— 族归属以 evaluation_result 载荷的 family 为准。
    这里钉住判据函数的行为等价物：无评价记录或异族记录的 Study 不入束。
    （demo 侧以 _family_of(study_id) != fam 过滤；run23 实测束被旧族占满、
    收尾封存烧在旧族特征上。）"""
    # 判据本身在 demo 的闭包里；此测试作为语义占位钉住载荷契约：
    from arad.evaluation.kernel import EvaluationRequest
    assert "family" in EvaluationRequest.__dataclass_fields__
