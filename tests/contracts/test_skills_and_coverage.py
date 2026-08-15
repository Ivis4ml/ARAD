"""方法说明与搜索覆盖的合同测试（M17）。

三件事要钉住：

1. 进入模型上下文的**每一段文本**都过盲化闸门、都进内容寻址。
   走命令行参数或工作目录的通道等于不存在于账本，也扫不到（这正是被修的洞）。
2. 方法说明只承载机械失败的教训。承载判决即成为结果回流通道（决定 0006）。
3. 覆盖表只数提案，不数判决。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from arad.harness.coverage import search_coverage
from arad.harness.skills import SkillError, load_skill, render_system_prompt
from arad.providers.base import ContextLeak, ProviderRequest, Role
from arad.providers.claude_cli import DEFAULT_ARGS, ClaudeCliProvider

SKILL_TEXT = """---
skill_id: t_skill
version: 3
role: proposer
update_rule: mechanical_failures_only
---

# 方法说明

只写方法，不写任何判决。
"""


def _write(tmp_path: Path, text: str, name: str = "t_skill") -> Path:
    path = tmp_path / f"{name}.md"
    path.write_text(text, encoding="utf-8")
    return tmp_path


def test_skill_loads_with_identity(tmp_path):
    skill = load_skill("t_skill", skill_dir=_write(tmp_path, SKILL_TEXT))
    assert skill.version == 3
    assert skill.describe()["content_id"]
    assert "只写方法" in render_system_prompt(skill)


def test_skill_content_id_changes_with_the_body(tmp_path):
    first = load_skill("t_skill", skill_dir=_write(tmp_path, SKILL_TEXT)).content_id
    second = load_skill(
        "t_skill", skill_dir=_write(tmp_path, SKILL_TEXT + "\n多一句。\n")).content_id
    assert first != second


def test_skill_carrying_an_effect_field_is_refused(tmp_path):
    leaky = SKILL_TEXT.replace("只写方法，不写任何判决。", "上一轮的 t_stat 偏低，换个族。")
    with pytest.raises(ContextLeak):
        load_skill("t_skill", skill_dir=_write(tmp_path, leaky))


def test_skill_must_declare_the_mechanical_only_update_rule(tmp_path):
    loosened = SKILL_TEXT.replace("mechanical_failures_only", "anything_goes")
    with pytest.raises(SkillError, match="update_rule"):
        load_skill("t_skill", skill_dir=_write(tmp_path, loosened))


def test_shipped_proposer_skill_passes_the_gate():
    """仓库里真正会被发出去的那一份，必须自己过闸门。"""
    skill = load_skill("arad-proposer")
    assert skill.role == "proposer"
    assert skill.version >= 1


def test_system_prompt_is_part_of_the_request_identity():
    base = {"role": Role.PROPOSER, "prompt": "x", "schema_name": "ProposalOutput"}
    without = ProviderRequest(**base)
    with_skill = ProviderRequest(**base, system_prompt="方法说明")
    assert without.request_id != with_skill.request_id


def test_cli_provider_is_hermetic_by_default():
    """研究员进程不得拿到工具、MCP 服务器、skill 或任何设置来源。"""
    provider = ClaudeCliProvider()
    assert provider.require_hermetic is True
    args = provider.command()
    for flag in ("--disallowed-tools", "--strict-mcp-config",
                 "--disable-slash-commands", "--setting-sources"):
        assert flag in args, f"缺少封闭参数 {flag}"
    for tool in ("Bash", "Read", "Write", "Edit", "Grep", "Glob", "WebFetch"):
        assert tool in args, f"{tool} 未被拒绝"
    assert "--setting-sources" in DEFAULT_ARGS


def test_system_prompt_reaches_the_command_line_only_through_the_gated_field():
    provider = ClaudeCliProvider()
    assert "--append-system-prompt" not in provider.command()
    args = provider.command("方法说明")
    assert args[-2:] == ["--append-system-prompt", "方法说明"]


def test_coverage_counts_proposals_and_never_verdicts(tmp_path):
    from arad.memory.ledger import EvidenceLedger

    with EvidenceLedger(str(tmp_path / "t.db")) as ledger:
        ledger.append("feature_spec_locked", {"steps": [{"field": "mech:FED_HIKE:p"}]},
                      study_id="s1")
        ledger.append("proposal_locked",
                      {"universe": "sc_dominant_t1", "target": "sc_rv_next_session"},
                      study_id="s1")
        ledger.append("verdict_recorded", {"verdict": "null"}, study_id="s1")
        coverage = search_coverage(ledger)

    assert coverage["proposals_counted"] == 1
    assert coverage["by_pm_family"] == {"mech:FED_HIKE": 1}
    key = "mech:FED_HIKE|sc_dominant_t1|sc_rv_next_session"
    assert coverage["visited_combinations"][key] == 1
    # 判决一个字都不能出现在覆盖表里
    blob = str(coverage)
    for word in ("null", "verdict", "candidate", "blocked"):
        assert word not in blob


# ---------------------------------------------------------------- 机制族进菜单


def _qualification(*family_ids):
    return {
        "families": {f: {"notional": 1e6, "buckets": 900, "span_days": 400,
                         "mean_unresolved": 0.1, "from": "2023-01-01T00:00:00"}
                     for f in family_ids},
        "qualified": list(family_ids),
    }


def _families_manifest(*names):
    return {"families": {
        n: {"series_id": f"mech:{n}", "name_cn": n, "driver_channel": "地缘-冲突",
            "mechanism_cn": "说明", "counts": {"member_pos": 5, "member_neg": 2},
            "by_segment": {"discovery": 9}, "themes": []}
        for n in names
    }}


def test_a_mechanism_family_that_replays_its_predecessor_is_kept_out_of_the_menu():
    """重合度高的族是同一次检验的重放，不该换个名字再问一遍。"""
    from arad.harness.pm_menu import mechanism_rows

    rows = mechanism_rows(
        qualification=_qualification("mech:NEW", "mech:OLD"),
        families_manifest=_families_manifest("NEW", "OLD"),
        overlap_manifest={"mechanism_vs_lexical_predecessor": {
            "NEW": {"verdict": "distinct_object", "lexical_predecessor": "cand:x"},
            "OLD": {"verdict": "replay_of_predecessor", "lexical_predecessor": "cand:y"},
        }},
        tested_predecessors=frozenset({"cand:y"}),
    )
    assert [r["family_id"] for r in rows] == ["mech:NEW"]


def test_a_replay_of_an_untested_predecessor_is_not_permanently_excluded():
    """重放判定回答「是不是同一个东西」，不回答「问过没有」。

    前身零引用时，那条轴仍是没问过的问题；按重放永久排除等于因为
    「像一条同样没被检验过的序列」而放弃它。它仍进旧族账户的菜单
    （账户路由是另一条规则，见 test_family_routing_and_permanent_exclusion_are_separate_rules）。
    """
    from arad.harness.pm_menu import mechanism_rows

    rows = mechanism_rows(
        qualification=_qualification("mech:OLD"),
        families_manifest=_families_manifest("OLD"),
        overlap_manifest={"mechanism_vs_lexical_predecessor": {
            "OLD": {"verdict": "replay_of_predecessor", "lexical_predecessor": "cand:y"},
        }},
        admit=frozenset({"distinct_object", "replay_of_predecessor"}),
        tested_predecessors=frozenset(),
    )
    assert [r["family_id"] for r in rows] == ["mech:OLD"]
    assert rows[0]["vs_lexical_predecessor"]["predecessor_was_tested"] is False
    assert "旧族账户" in rows[0]["vs_lexical_predecessor"]["account_note"]


def test_mechanism_rows_claim_slots_before_the_volume_ranked_strata():
    """先验层与安慰剂层曾因让头部层先挑而配额落空；机制族不重蹈。"""
    from arad.harness.pm_menu import build_menu

    lexical = _qualification(*[f"cand:{i}" for i in range(20)])
    mech = mechanism_rows_fixture()
    menu = build_menu(round_index=0, qualification=lexical, priors=None,
                      tokens_meta={}, mechanism=mech, width=10)
    assert [r["family_id"] for r in menu[:2]] == ["mech:A", "mech:B"]
    assert len(menu) <= 10


def mechanism_rows_fixture():
    from arad.harness.pm_menu import mechanism_rows

    return mechanism_rows(
        qualification=_qualification("mech:A", "mech:B"),
        families_manifest=_families_manifest("A", "B"),
        overlap_manifest={"mechanism_vs_lexical_predecessor": {
            "A": {"verdict": "distinct_object"},
            "B": {"verdict": "distinct_object"},
        }},
    )


def test_mechanism_series_fields_include_the_composition_controlled_change():
    rows = mechanism_rows_fixture()
    fields = rows[0]["fields"]
    assert any(f.endswith(":dp") for f in fields)
    assert any(f.endswith(":conditions") for f in fields)


def test_partially_overlapping_family_is_kept_out_when_admit_narrows():
    """决定 0011：新族运行只见 distinct_object，部分重合的族属旧族账户。"""
    from arad.harness.pm_menu import mechanism_rows

    rows = mechanism_rows(
        qualification=_qualification("mech:A", "mech:B"),
        families_manifest=_families_manifest("A", "B"),
        overlap_manifest={"mechanism_vs_lexical_predecessor": {
            "A": {"verdict": "distinct_object"},
            "B": {"verdict": "partially_overlapping", "lexical_predecessor": "cand:b"},
        }},
        admit=frozenset({"distinct_object"}),
        tested_predecessors=frozenset({"cand:b"}),
    )
    assert [r["family_id"] for r in rows] == ["mech:A"]


def test_family_floors_report_both_accounts(tmp_path):
    """决定 0011：族地板与合并地板并列 —— 分族的正当性以合并账可读为前提。"""
    from arad.harness.episode import family_floors
    from arad.memory.ledger import EvidenceLedger

    with EvidenceLedger(str(tmp_path / "t.db")) as ledger:
        for i in range(3):
            ledger.record_outcome_read(f"old-{i}:main", "old_family", f"old-{i}")
        ledger.record_outcome_read("new-0:main", "new_family", "new-0")
        floors = family_floors(ledger, "new_family")

    assert floors["family_tests"] == 1
    assert floors["all_families_tests"] == 4
    # 合并地板必须高于族地板：它对着更大的极大值集合
    assert floors["merged_floor"] > floors["family_floor"]


def test_qualified_set_covers_both_family_layers(monkeypatch, tmp_path):
    """菜单与准入必须同源：菜单列出 mech: 族而准入名单没有，规格会一律判 blocked。

    run27 前三版实测即此形态，理由都是「没有为 (pm_market, 'mech:X:dp') 提供数据序列」。
    """
    import json

    from arad.harness import demo

    lex = tmp_path / "lex.json"
    mech = tmp_path / "mech.json"
    lex.write_text(json.dumps({"qualified": ["cand:iran"]}), encoding="utf-8")
    mech.write_text(json.dumps({"qualified": ["mech:FED_HIKE"]}), encoding="utf-8")
    monkeypatch.setattr(demo, "PM_QUALIFICATION_PATH", str(lex))
    monkeypatch.setattr(demo, "PM_MECH_QUALIFICATION_PATH", str(mech))
    assert demo._qualified_families() == {"cand:iran", "mech:FED_HIKE"}


def test_family_routing_and_permanent_exclusion_are_separate_rules():
    """两条规则不可揉成一条（M18.3 曾揉成一条，部分重合与重放的族漏进新族）。

    永久排除：与前身重放**且**前身被检验过 —— 重复消耗预算。
    账户路由：只有 distinct_object 进新族的账，其余属旧族账户。
    """
    from arad.harness.pm_menu import MECHANISM_ADMITS, mechanism_rows

    manifest = _families_manifest("NEW", "PARTIAL", "REPLAY_TESTED", "REPLAY_UNTESTED")
    overlaps = {"mechanism_vs_lexical_predecessor": {
        "NEW": {"verdict": "distinct_object", "lexical_predecessor": "cand:a"},
        "PARTIAL": {"verdict": "partially_overlapping", "lexical_predecessor": "cand:b"},
        "REPLAY_TESTED": {"verdict": "replay_of_predecessor",
                          "lexical_predecessor": "cand:tested"},
        "REPLAY_UNTESTED": {"verdict": "replay_of_predecessor",
                            "lexical_predecessor": "cand:fresh"},
    }}
    qual = _qualification("mech:NEW", "mech:PARTIAL",
                          "mech:REPLAY_TESTED", "mech:REPLAY_UNTESTED")
    tested = frozenset({"cand:tested"})

    new_family = mechanism_rows(
        qualification=qual, families_manifest=manifest, overlap_manifest=overlaps,
        admit=frozenset({"distinct_object"}), tested_predecessors=tested)
    assert [r["family_id"] for r in new_family] == ["mech:NEW"]

    old_family = mechanism_rows(
        qualification=qual, families_manifest=manifest, overlap_manifest=overlaps,
        admit=MECHANISM_ADMITS, tested_predecessors=tested)
    got = {r["family_id"] for r in old_family}
    assert "mech:PARTIAL" in got            # 部分重合属旧族账户
    assert "mech:REPLAY_TESTED" not in got  # 前身测过，永久排除
    assert "mech:NEW" in got


def test_universe_menu_states_the_consequence_not_only_the_mechanism():
    """只说「品种维退化」不够：要说清它使 candidate 失效这个后果。"""
    from arad.harness.demo import universe_menu

    menu = universe_menu()
    single = next(u for u in menu if u["universe"].endswith("_dominant_t1"))
    panel = next(u for u in menu if u["universe"] == "full_coverage_panel")
    assert "candidate" in single["note"]
    assert "candidate" in panel["note"]


def test_shipped_skill_carries_the_prescreen_lesson_and_stays_gated():
    """事前功效筛属机械失败，可以入方法说明；入了仍须过闸门。"""
    skill = load_skill("arad-proposer")
    assert skill.version >= 2
    assert "事前功效筛" in skill.body
    assert "defined_share_on_decision_grid" in skill.body
