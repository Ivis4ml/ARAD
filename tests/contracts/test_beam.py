

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
