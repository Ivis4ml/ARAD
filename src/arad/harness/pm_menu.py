"""Polymarket 族的资格筛与分层轮换菜单（M12）。

此前的「起点选择」是两级默认：物化时按成交量取前 30，菜单只列已物化的。
规则结果无关（好），但战争与政治垄断菜单、1,998 族里 98% 永远没有出场机会、
经济先验从未被声明（坏）。本模块把选择规则本身变成预注册的、版本化的对象：

一、资格筛（qualify_families）：纯 PM 侧统计，与期货结果无关 ——
    覆盖跨度、桶数、未决性（p 的时均伯努利方差：钉死在 0/1 的族没有信息流）、
    活动度。阈值声明在 QUALIFICATION_RULE 里，改阈值就换版本号。

二、分层轮换菜单（build_menu）：每轮 width 个名额按四层配额组装 ——
    头部层（成交量前列）、先验层（事前经济映射标注的族，映射验证只用外部
    ETF 证据，永远不碰期货收益）、安慰剂层（体育/加密/娱乐，任何在它们身上
    「发现」的信号都该使整族方法被怀疑）、轮换层（确定性轮换，让全部合格族
    在长期运行中都有出场机会）。轮换种子取轮次号：同轮重放得同菜单。

刻意不做的两件事：不按「哪个族历史上跑分好」调菜单（结果反馈进提案侧，
决定 0006 封的门）；先验只标注不过滤（证伪机会留给模型）。
"""

from __future__ import annotations

import math
from typing import Any

MENU_RULE_VERSION = "menu-v3"

#: 机制族层的配额（M17）。机制族（`mech:`，见 data_catalog/pm_mechanism_families）
#: 按机制与极性定义成员，与词汇族并列而不是取代它 —— 两者是不同的研究对象，
#: 实测其中两族与各自的词汇前身在决策网格上高度重合（属重放），其余不重合。
#: 重放的族不进本层：把同一次检验换个名字再问一遍，既浪费预算也污染分母。
QUOTA_MECHANISM = 6

#: 重合度裁断到菜单资格的映射。判据取自 Polymarket 一侧的序列比较，
#: 与期货结果无关（见 scripts/measure_series_overlap.py）。
MECHANISM_ADMITS = frozenset({"distinct_object", "partially_overlapping"})

QUALIFICATION_RULE = {
    "version": "qualify-v1",
    "min_span_days": 180,
    "min_buckets": 500,
    "min_mean_unresolved": 0.02,   # 时均 p(1-p)：0.02 对应 p 长期在 [0.02, 0.98] 之外
    "min_notional_usdc": 50_000.0,
    "note": (
        "全部判据取自 Polymarket 侧序列本身，与期货结果无关。"
        "未决性筛掉钉死在 0 或 1 的死族：没有未决概率质量就没有信息流。"
    ),
}

#: 安慰剂词表：命中即归安慰剂层。体育/加密/娱乐与商品盘面无机制通路，
#: 在它们身上「发现」信号说明方法而不是市场出了问题。
PLACEBO_TOKENS = frozenset({
    "nba", "nfl", "mlb", "nhl", "soccer", "premier", "ufc", "boxing",
    "bitcoin", "ethereum", "solana", "crypto", "dogecoin",
    "oscars", "grammys", "album", "movie", "spotify", "gta",
})

#: 主题 → 头部词的声明映射。用于把 tier registry 的 (主题, 品种) 先验
#: 标注到族上。词表是人的判断，冻结在此；命中多个主题的族全部标注。
THEME_TOKENS: dict[str, frozenset[str]] = {
    "oil_price": frozenset({"oil", "opec", "crude", "wti", "brent"}),
    "mideast_conflict": frozenset({
        "iran", "israel", "hamas", "ceasefire", "hezbollah", "gaza",
        "hormuz", "houthi", "yemen", "lebanon", "syria", "strike",
    }),
    "russia_ukraine": frozenset({
        "russia", "ukraine", "putin", "zelensky", "kyiv", "moscow", "crimea",
    }),
    "fed_policy": frozenset({
        "fed", "rate", "rates", "powell", "fomc", "inflation", "cpi", "recession",
    }),
    "us_china_trade": frozenset({"china", "tariff", "tariffs", "trade", "xi"}),
    "taiwan_risk": frozenset({"taiwan", "invasion", "blockade"}),
    "metal_price": frozenset({"gold", "silver", "copper"}),
    "us_shutdown": frozenset({"shutdown", "government"}),
}

_TIER_RANK = {"primary": 0, "secondary": 1, "exploratory": 2}


def qualify_families(stats: dict[str, dict]) -> dict:
    """按 QUALIFICATION_RULE 出资格名单。

    `stats[family_id]` 需含 span_days / buckets / mean_unresolved / notional。
    返回 {"rule": ..., "families": stats, "qualified": [...]}，供菜单与
    惰性装载共用 —— 不合格的族即使被规格引用也不装载。
    """
    rule = QUALIFICATION_RULE
    qualified = sorted(
        fid for fid, s in stats.items()
        if s.get("span_days", 0) >= rule["min_span_days"]
        and s.get("buckets", 0) >= rule["min_buckets"]
        and (s.get("mean_unresolved") or 0.0) >= rule["min_mean_unresolved"]
        and (s.get("notional") or 0.0) >= rule["min_notional_usdc"]
    )
    return {"rule": rule, "families": stats, "qualified": qualified}


def annotate_themes(head_tokens: list[str]) -> list[str]:
    toks = {t.lower() for t in head_tokens}
    return sorted(theme for theme, kw in THEME_TOKENS.items() if toks & kw)


def build_menu(
    *,
    round_index: int,
    qualification: dict,
    priors: dict[str, dict] | None,
    tokens_meta: dict[str, dict],
    width: int = 30,
    quota_top: int = 8,
    quota_prior: int = 4,
    quota_placebo: int = 3,
    mechanism: list[dict[str, Any]] | None = None,
    quota_mechanism: int = QUOTA_MECHANISM,
) -> list[dict[str, Any]]:
    """组装一轮的候选族菜单。确定性：同 (round_index, 输入) 得同菜单。

    机制族层（M17）先认领名额：它们是本轮唯一带机制叙述的选项，
    若让成交量排序的头部层先挑，机制族会被词汇族挤掉（先验层与安慰剂层
    此前正是这样落空的，那次实测形态记在下面）。
    """
    stats = qualification["families"]
    qualified = [f for f in qualification["qualified"] if f in stats]
    mech_rows = list(mechanism or [])[:quota_mechanism]
    if not qualified:
        return mech_rows

    def entry(fid: str, stratum: str) -> dict:
        meta = tokens_meta.get(fid, {})
        s = stats[fid]
        themes = annotate_themes(meta.get("head_tokens", []))
        row: dict[str, Any] = {
            "family_id": fid,
            "head_tokens": meta.get("head_tokens", []),
            "markets": meta.get("markets"),
            "trades": meta.get("trades"),
            "notional_usdc": round(s.get("notional") or 0.0),
            "series_from": (s.get("from") or "")[:10],
            "buckets": s.get("buckets"),
            "fields": [f"{fid}:{k}" for k in ("p", "notional", "trades")],
            "stratum": stratum,
        }
        if priors and themes:
            tiers = [priors[t] for t in themes if t in priors]
            if tiers:
                best = min(tiers, key=lambda p: _TIER_RANK.get(p.get("tier", ""), 9))
                row["declared_prior"] = {
                    "themes": themes,
                    "tier": best.get("tier"),
                    "axis": best.get("theme_axis"),
                    "note": "事前经济映射（外部 ETF 证据验证，从未接触期货收益）",
                }
        return row

    by_notional = sorted(
        qualified, key=lambda f: (-(stats[f].get("notional") or 0.0), f))
    picked: list[tuple[str, str]] = []
    seen: set[str] = set()

    def take(pool, stratum, quota):
        for fid in pool:
            if len([p for p in picked if p[1] == stratum]) >= quota:
                break
            if fid in seen:
                continue
            seen.add(fid)
            picked.append((fid, stratum))

    # 有意设计的层先认领：安慰剂与先验族常常本身就在成交量前列，
    # 让 top 层先挑会把它们吃掉，配额落空（实测形态）。
    prior_pool = [
        f for f in by_notional
        if priors and any(t in priors for t in
                          annotate_themes(tokens_meta.get(f, {}).get("head_tokens", [])))
    ]
    take(prior_pool, "prior", quota_prior)

    placebo_pool = [
        f for f in by_notional
        if {t.lower() for t in tokens_meta.get(f, {}).get("head_tokens", [])}
        & PLACEBO_TOKENS
    ]
    take(placebo_pool, "placebo", quota_placebo)

    take(by_notional, "top", quota_top)

    # 轮换层：对合格名单按 family_id 排序后取确定性切片。步长取剩余名额，
    # 偏移随轮次前进 —— 长期运行中每个合格族都会轮到。
    remaining = width - len(picked) - len(mech_rows)
    if remaining > 0:
        pool = [f for f in sorted(qualified) if f not in seen]
        if pool:
            offset = (round_index * remaining) % len(pool)
            rotation = (pool[offset:] + pool[:offset])[:remaining]
            for fid in rotation:
                seen.add(fid)
                picked.append((fid, "rotation"))

    return mech_rows + [entry(fid, stratum) for fid, stratum in picked]


def mechanism_rows(
    *,
    qualification: dict,
    families_manifest: dict,
    overlap_manifest: dict | None = None,
    admit: frozenset[str] = MECHANISM_ADMITS,
) -> list[dict[str, Any]]:
    """机制族的菜单行。

    每行带机制叙述与驱动通道（这是它相对词汇族的全部意义：模型能据此形成经济假设
    而不是从一个词猜内容），带成员构成（正向/反向各几个市场），
    也带重合度裁断 —— 后者只由 Polymarket 侧序列算出，与期货结果无关。
    """
    stats = qualification.get("families", {})
    qualified = set(qualification.get("qualified", []))
    overlaps = (overlap_manifest or {}).get("mechanism_vs_lexical_predecessor", {})
    rows: list[dict[str, Any]] = []
    for name, info in (families_manifest.get("families") or {}).items():
        series_id = info.get("series_id") or f"mech:{name}"
        if series_id not in qualified:
            continue
        verdict = (overlaps.get(name) or {}).get("verdict")
        if verdict is not None and verdict not in admit:
            continue
        stat = stats.get(series_id, {})
        counts = info.get("counts", {})
        rows.append({
            "family_id": series_id,
            "stratum": "mechanism",
            "name_cn": info.get("name_cn"),
            "driver_channel": info.get("driver_channel"),
            "mechanism_cn": info.get("mechanism_cn"),
            "members": {
                "positive": counts.get("member_pos"),
                "reverse": counts.get("member_neg"),
                "discovery": (info.get("by_segment") or {}).get("discovery"),
            },
            "notional_usdc": round(stat.get("notional") or 0.0),
            "buckets": stat.get("buckets"),
            "series_from": (stat.get("from") or "")[:10],
            "fields": [f"{series_id}:{k}"
                       for k in ("p", "notional", "trades", "conditions", "dp")],
            "series_note": (
                "p 已按机制极性同号化，是「该机制发生」的概率而不是某个具体问题的"
                "Yes 价；dp 是构成受控的分桶变化（新入族成员不贡献电平跳变）；"
                "conditions 是当桶活跃成员市场数。p 的电平不可跨时期比较"
            ),
            "vs_lexical_predecessor": {
                "predecessor": (overlaps.get(name) or {}).get("lexical_predecessor"),
                "verdict": verdict,
                "note": "重合度只由 Polymarket 侧序列算出，不含任何期货侧结果",
            },
            "themes": info.get("themes") or [],
        })
    rows.sort(key=lambda r: (-(r["notional_usdc"] or 0), r["family_id"]))
    return rows


def unresolvedness(p_values: list[float]) -> float:
    """时均伯努利方差 mean(p·(1−p))。空序列无定义。"""
    vals = [p * (1.0 - p) for p in p_values if p is not None and math.isfinite(p)]
    return sum(vals) / len(vals) if vals else float("nan")
