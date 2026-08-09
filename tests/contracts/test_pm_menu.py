"""M12：资格筛与分层轮换菜单的合同。"""

from arad.harness.pm_menu import (
    build_menu,
    qualify_families,
    unresolvedness,
)


def _stats(n=40, notional=1e6):
    return {
        f"cand:f{i:02d}": {"buckets": 1000, "span_days": 400,
                           "mean_unresolved": 0.1,
                           "notional": notional - i * 1000, "from": "2023-01-01"}
        for i in range(n)
    }


def _tokens(n=40):
    out = {}
    for i in range(n):
        toks = ["misc"]
        if i in (5, 6):
            toks = ["nba", "finals"]          # 安慰剂
        if i in (7, 8):
            toks = ["iran", "strike"]         # 有先验主题
        out[f"cand:f{i:02d}"] = {"family_id": f"cand:f{i:02d}",
                                 "head_tokens": toks, "markets": 3, "trades": 100}
    return out


PRIORS = {"mideast_conflict": {"tier": "primary", "theme_axis": "+1 = 冲突升级"}}


def test_qualification_rule_screens_on_pm_side_only():
    stats = _stats(4)
    stats["cand:f00"]["mean_unresolved"] = 0.001    # 钉死在 0/1 的死族
    stats["cand:f01"]["span_days"] = 30             # 短命族
    out = qualify_families(stats)
    assert "cand:f00" not in out["qualified"]
    assert "cand:f01" not in out["qualified"]
    assert "cand:f02" in out["qualified"]


def test_menu_is_deterministic_and_quota_stratified():
    q = qualify_families(_stats())
    m1 = build_menu(round_index=3, qualification=q, priors=PRIORS,
                    tokens_meta=_tokens())
    m2 = build_menu(round_index=3, qualification=q, priors=PRIORS,
                    tokens_meta=_tokens())
    assert m1 == m2                                  # 同轮重放得同菜单
    strata = {e["stratum"] for e in m1}
    assert {"top", "prior", "placebo", "rotation"} <= strata
    ids = [e["family_id"] for e in m1]
    assert len(ids) == len(set(ids))                 # 无重复
    placebo = [e for e in m1 if e["stratum"] == "placebo"]
    assert placebo                                   # 安慰剂层永远在
    prior = [e for e in m1 if e["stratum"] == "prior"]
    assert all("declared_prior" in e for e in prior)
    assert all(e["declared_prior"]["tier"] == "primary" for e in prior)


def test_rotation_gives_every_qualified_family_a_turn():
    q = qualify_families(_stats(60))
    seen = set()
    for rnd in range(12):
        menu = build_menu(round_index=rnd, qualification=q, priors=None,
                          tokens_meta=_tokens(60), width=20)
        seen |= {e["family_id"] for e in menu if e["stratum"] == "rotation"}
    # 12 轮 × 若干轮换位后，轮换层应覆盖大部分非头部族
    assert len(seen) > 30


def test_unresolvedness_is_bernoulli_variance_mean():
    assert abs(unresolvedness([0.5, 0.5]) - 0.25) < 1e-12
    assert unresolvedness([0.0, 1.0]) == 0.0
