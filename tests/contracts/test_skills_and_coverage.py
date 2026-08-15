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
    )
    assert [r["family_id"] for r in rows] == ["mech:NEW"]


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
