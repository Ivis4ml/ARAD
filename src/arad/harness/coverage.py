"""搜索覆盖表：哪些 (族, universe, target) 组合被提过，哪些一次都没有（M17）。

问题是实测出来的：192 条提案里 119 条落在 `sc_dominant_t1`，目标只用过三个，
1,998 个候选族里只有 23 个被引用过，其中 `cand:iran` 一族独占 96 条 Study。
菜单每轮给 30 个族，但选哪个是模型的自由，而模型在没有覆盖信息时会反复回到
同一条轴上 —— 这不是模型的毛病，是它看不见自己走过哪里。

**为什么这不违反决定 0006**：本表只数 `proposal_locked`，即「提过几次」。
它不看 `evaluation_result`，不看 `verdict_recorded`，也不按「有没有通过事前筛」过滤。
提案计数与判决计数是两回事：前者在读取任何结果之前就已确定，
后者才是 0006 关闭的那条通道。任何想给本表加一个「其中多少条成立」的字段的改动，
都是把它变成结果回流通道，必须拒绝。
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from ..memory.ledger import EvidenceLedger, Role

COVERAGE_VERSION = "coverage-v1"

#: 从特征规格里认族名的形态：`cand:<词>` 与 `mech:<机制>`。
_FAMILY_PATTERN = re.compile(r"\b((?:cand|mech):[A-Za-z0-9_]+)\b")


def _families_in(payload: Any) -> set[str]:
    return set(_FAMILY_PATTERN.findall(str(payload)))


def search_coverage(ledger: EvidenceLedger, *, family: str | None = None) -> dict:
    """按 (族, universe, target) 数提案次数。只读 proposal_locked 与 feature_spec_locked。

    `family` 是**统计族**（如 demo_sc_price_volume），与这里数的 Polymarket 族不是
    一回事；传入时只统计该统计族的运行。传 None 统计全部历史。
    """
    events = ledger.read_events(role=Role.HUMAN)
    specs: dict[str, set[str]] = {}
    for event in events:
        if event["event_type"] == "feature_spec_locked":
            study = event.get("study_id")
            if study:
                specs[study] = _families_in(event["payload"])

    combos: Counter = Counter()
    by_universe: Counter = Counter()
    by_target: Counter = Counter()
    by_family: Counter = Counter()
    proposals = 0
    for event in events:
        if event["event_type"] != "proposal_locked":
            continue
        payload = event["payload"]
        spec = payload.get("proposal") or payload
        universe = spec.get("universe") or "-"
        target = spec.get("target") or "-"
        study = event.get("study_id")
        pm_families = specs.get(study or "", set()) or {"-"}
        proposals += 1
        by_universe[universe] += 1
        by_target[target] += 1
        for pm in pm_families:
            by_family[pm] += 1
            combos[(pm, universe, target)] += 1
    return {
        "version": COVERAGE_VERSION,
        "statistical_family": family,
        "proposals_counted": proposals,
        "by_pm_family": dict(by_family.most_common()),
        "by_universe": dict(by_universe.most_common()),
        "by_target": dict(by_target.most_common()),
        "visited_combinations": {f"{a}|{b}|{c}": n for (a, b, c), n in combos.items()},
        "note": (
            "只统计提案次数，不含任何判决与统计量。次数为零的组合"
            "不代表它更有希望，只代表它没被问过"
        ),
    }


def coverage_menu(coverage: dict, *, families: list[str], universes: list[str],
                  targets: list[str], width: int = 12,
                  round_index: int = 0, universe_slots: int = 6) -> dict:
    """把覆盖表折成提案器能直接用的两段：走过的与没走过的。

    两处顺序必须是**设计**而不是巧合：

    一、族按**菜单自身的次序**排（机制族在最前），不按字母序。按字母序排会把
    `cand:11pt5` 这种词汇碎片族推到建议的第一位 —— 那不是广度，是噪声。

    二、universe 每轮只取一个确定性切片（面板恒在，单品种按轮次轮换）。
    51 个品种 × 30 个族 × 3 个目标是 4,600 多个组合，整张表塞给模型等于没给；
    轮换保证长期覆盖，切片保证每一轮的建议是可读的。同 round_index 得同切片。
    """
    visited = coverage.get("visited_combinations", {})
    panel = [u for u in universes if not u.endswith("_dominant_t1")]
    singles = sorted(u for u in universes if u.endswith("_dominant_t1"))
    take = max(0, universe_slots - len(panel))
    if singles and take:
        offset = (round_index * take) % len(singles)
        rotated = (singles[offset:] + singles[:offset])[:take]
    else:
        rotated = []
    universes_this_round = panel + rotated

    rank = {name: i for i, name in enumerate(families)}
    u_rank = {name: i for i, name in enumerate(universes_this_round)}
    unvisited: list[str] = []
    for fam in families:
        for universe in universes_this_round:
            for target in targets:
                key = f"{fam}|{universe}|{target}"
                if key not in visited:
                    unvisited.append(key)
    def _order(key: str) -> tuple:
        fam, universe, target = key.split("|")
        return (rank.get(fam, 999), u_rank.get(universe, 999), target)

    unvisited.sort(key=_order)
    most_visited = sorted(visited.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    return {
        "version": COVERAGE_VERSION,
        "universes_this_round": universes_this_round,
        "combination_space": len(families) * len(universes_this_round) * len(targets),
        "visited_combinations": len(visited),
        "unvisited_examples": unvisited[:width],
        "unvisited_total": len(unvisited),
        "most_asked": [{"combination": k, "proposals": n} for k, n in most_visited],
        "instruction": (
            "优先取 unvisited_examples 里的组合；确有理由重回已问过的组合时，"
            "在 change_summary 里写明这次与之前那些提案的差别。"
            "次数只反映提问历史，不含任何结果。"
            "本轮列出的 universe 是确定性切片（面板恒在，单品种按轮次轮换）；"
            "要提切片之外的品种也可以，直接写它的 universe 名"
        ),
    }
