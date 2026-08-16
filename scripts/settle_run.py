"""一次运行跑完后的结算（决定 0013 §八）。

结算一律**直接查账本**，不采信监视器的读数：监视器在运行中途读库没有写隔离，
曾报出过一个半写状态（{candidate 2, null 11}），而同一时刻账本里是 16 条互异
判决。账本是唯一权威。

本脚本回答四个问题：

1. 判决分布，以及其中有多少次检验**没有产出可比的 t 值**。
   双向 cluster 标准误可能算出负方差，此时 t 无定义（NaN）。这类检验消耗了分母，
   却不进「最好 |t|」一类统计，若不单列会让读者以为每次检验都给出了可比的读数。
2. 合格构造的最好成绩。合格的判据有三条，逐条收紧：
   来自另类数据（量价构造是基线对照，不算另类数据的成绩）、
   斜率符号与预注册方向一致、且没有使 candidate 失效的阻断理由。
3. 品种覆盖：本轮实际读到过哪些品种，还剩哪些从未被读过。
4. 预注册停止规则的三个条件是否同时满足。

用法：`python scripts/settle_run.py run31 sc_mechanism_prior_v1 82`
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.evaluation.selection import expected_max_abs_z


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _universe_products(universe: str | None) -> list[str]:
    """从 universe 串里取出品种。只认已知的三种形态，认不出的返回空表。"""
    if not universe:
        return []
    if universe.startswith("mech_panel:"):
        return sorted({p for p in universe.split(":", 1)[1].split("+") if p})
    if universe.startswith("product:"):
        return [universe.split(":", 1)[1]]
    return []


def _uncovered_breakdown(covered: set[str]) -> dict:
    """把「没被读到的品种」分成两类：目标表行数不足的，与满行却未被选中的。

    前者是数据可得性的事实，后者才是搜索行为的事实。报告若混为一谈，
    读者会把一条「这些品种没有足够历史」误读成「模型漏掉了这些品种」。
    """
    import pyarrow.parquet as pq

    from arad.harness.demo import (
        _FULL_COVERAGE_ROWS,
        LABEL_TARGET,
        _product_target_path,
        built_products,
    )

    thin, full_but_unread = [], []
    for product in sorted(built_products()):
        if product in covered:
            continue
        path = _product_target_path(product, f"{product}_{LABEL_TARGET[3:]}")
        rows = pq.read_metadata(path).num_rows if Path(path).exists() else 0
        (full_but_unread if rows >= _FULL_COVERAGE_ROWS else thin).append(
            {"product": product, "target_rows": rows})
    return {
        "full_coverage_rows": _FULL_COVERAGE_ROWS,
        "thin_history": thin,
        "full_history_but_unread": full_but_unread,
    }


def collect(run_prefix: str, ledger_path: str = "data/ledger/service.db") -> dict:
    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

    studies: dict[str, dict] = {}
    for event in events:
        study = event.get("study_id") or ""
        if not study.startswith(f"{run_prefix}-"):
            continue
        row = studies.setdefault(study, {"study_id": study})
        payload = event["payload"]
        if event["event_type"] == "proposal_locked":
            spec = payload.get("proposal") or payload
            row["universe"] = spec.get("universe")
            row["mechanism"] = spec.get("mechanism")
            row["target"] = spec.get("target")
            if spec.get("direction") in (1, -1):
                row["declared_direction"] = int(spec["direction"])
            sources = spec.get("sources") or spec.get("source") or []
            row["sources"] = sources if isinstance(sources, list) else [sources]
        elif event["event_type"] == "evaluation_result":
            effects = payload.get("effects") or {}
            row["t_stat"] = effects.get("t_stat")
            row["slope"] = effects.get("slope")
            row["blocked_reason_kinds"] = list(payload.get("blocked_reason_kinds") or [])
            diagnostics = payload.get("diagnostics") or {}
            row["decoy_exceed"] = (diagnostics.get("decoy") or {}).get("decoy_exceed_rate")
            row["placebo_exceed"] = (
                diagnostics.get("placebo") or {}).get("placebo_exceed_rate")
            row["product_clusters"] = (
                payload.get("coverage") or {}).get("product_clusters")
            row["two_way_variance_negative"] = (
                diagnostics.get("two_way_cluster") or {}).get("variance_negative")
        elif event["event_type"] == "verdict_recorded":
            row["verdict"] = payload.get("verdict")
    return studies


def settle(run_prefix: str, family: str, budget_denominator: int,
           ledger_path: str = "data/ledger/service.db") -> dict:
    studies = collect(run_prefix, ledger_path)
    decided = [s for s in studies.values() if s.get("verdict")]

    # 一、判决分布与「t 无定义」的单独计数。
    verdicts = Counter(s["verdict"] for s in decided)
    t_defined = [s for s in decided if _finite(s.get("t_stat"))]
    t_undefined = [s for s in decided if not _finite(s.get("t_stat"))]

    # 二、合格构造：三条判据逐条收紧。
    def is_alt_data(row: dict) -> bool:
        return any("pm" in str(src) for src in (row.get("sources") or []))

    def direction_agrees(row: dict) -> bool:
        want = row.get("declared_direction")
        slope = row.get("slope")
        if want not in (1, -1) or not _finite(slope) or slope == 0:
            return False
        return (1 if slope > 0 else -1) == want

    def unblocked(row: dict) -> bool:
        return not row.get("blocked_reason_kinds")

    tiers = {
        "全部有定义的构造": t_defined,
        "另类数据": [s for s in t_defined if is_alt_data(s)],
        "另类数据且符号一致": [
            s for s in t_defined if is_alt_data(s) and direction_agrees(s)],
        "另类数据、符号一致且无阻断": [
            s for s in t_defined
            if is_alt_data(s) and direction_agrees(s) and unblocked(s)],
    }
    floor = expected_max_abs_z(budget_denominator)
    best: dict[str, dict] = {}
    for label, rows in tiers.items():
        if not rows:
            best[label] = {"n": 0, "best_abs_t": None, "study_id": None,
                           "reward": None}
            continue
        top = max(rows, key=lambda r: abs(r["t_stat"]))
        best[label] = {
            "n": len(rows),
            "best_abs_t": abs(top["t_stat"]),
            "study_id": top["study_id"],
            "reward": abs(top["t_stat"]) - floor,
        }

    # 三、品种覆盖，以及**没被覆盖的那些为什么没被覆盖**。
    # 只报覆盖率而不区分「数据不够」与「模型没选」，会把一条数据可得性的事实
    # 说成一条搜索行为的事实。二者在结论上完全不同。
    covered: set[str] = set()
    for row in decided:
        covered.update(_universe_products(row.get("universe")))
    universe_forms = Counter(
        (row.get("universe") or "").split(":", 1)[0] for row in decided)
    uncovered = _uncovered_breakdown(covered)

    # 四、符号一致率（本轮内）。
    with_direction = [
        s for s in decided
        if s.get("declared_direction") in (1, -1) and _finite(s.get("slope"))
        and s["slope"] != 0
    ]
    agree = sum(1 for s in with_direction if direction_agrees(s))

    # 五、预注册停止规则的三个条件。
    best_qualified = best["另类数据且符号一致"]["best_abs_t"]
    stop_rule = {
        "candidate 为 0": verdicts.get("candidate", 0) == 0,
        f"合格最好 |t| 未越 E2({budget_denominator})={floor:.4f}": (
            best_qualified is None or best_qualified < floor),
        "符号一致率仍在 50% 的二项噪声内": None,  # 由下面的 p 值填
    }
    if with_direction:
        # 双侧二项检验，正态近似（n 已足够大）。
        n = len(with_direction)
        z = (agree - n / 2) / math.sqrt(n / 4)
        p = math.erfc(abs(z) / math.sqrt(2))
        stop_rule["符号一致率仍在 50% 的二项噪声内"] = p > 0.05
    else:
        p = None

    return {
        "settlement": "settle-run/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "run": run_prefix,
        "family": family,
        "budget_denominator": budget_denominator,
        "floor": floor,
        "verdicts": dict(verdicts.most_common()),
        "studies_decided": len(decided),
        "t_defined": len(t_defined),
        "t_undefined": len(t_undefined),
        "t_undefined_studies": [
            {"study_id": s["study_id"], "universe": s.get("universe"),
             "verdict": s.get("verdict"),
             "two_way_variance_negative": s.get("two_way_variance_negative")}
            for s in t_undefined
        ],
        "best_by_tier": best,
        "coverage": {
            "products_read": sorted(covered),
            "n_products_read": len(covered),
            "universe_forms": dict(universe_forms.most_common()),
            "uncovered": uncovered,
        },
        "direction": {
            "n_with_declared_direction": len(with_direction),
            "sign_agrees": agree,
            "sign_opposite": len(with_direction) - agree,
            "two_sided_p_vs_half": p,
        },
        "decoy_median": (
            sorted(s["decoy_exceed"] for s in decided
                   if _finite(s.get("decoy_exceed")))[
                len([s for s in decided if _finite(s.get("decoy_exceed"))]) // 2]
            if any(_finite(s.get("decoy_exceed")) for s in decided) else None),
        "stop_rule": stop_rule,
        "stop_rule_all_met": all(v is True for v in stop_rule.values()),
    }


def main() -> None:
    run_prefix = sys.argv[1] if len(sys.argv) > 1 else "run31"
    family = sys.argv[2] if len(sys.argv) > 2 else "sc_mechanism_prior_v1"
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 82

    doc = settle(run_prefix, family, budget)
    out = Path(f"artifacts/manifests/settlement_{run_prefix}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{run_prefix} 结算（族 {family}，预算末分母 {budget}，"
          f"证否线 E2={doc['floor']:.4f}）")
    print(f"  判决 {doc['studies_decided']} 条：{doc['verdicts']}")
    print(f"  其中 t 有定义 {doc['t_defined']}，"
          f"**因 cluster 结构不足而无定义 {doc['t_undefined']}**")
    for row in doc["t_undefined_studies"]:
        print(f"    {row['study_id']:20s} {row['verdict']:10s} {row['universe']}")
    print("\n  最好成绩（奖励 = |t| 减证否线）：")
    for label, item in doc["best_by_tier"].items():
        if item["best_abs_t"] is None:
            print(f"    {label:26s} n={item['n']:3d}  （无）")
        else:
            print(f"    {label:26s} n={item['n']:3d}  |t|={item['best_abs_t']:.4f} "
                  f"奖励 {item['reward']:+.4f}  {item['study_id']}")
    cov = doc["coverage"]
    print(f"\n  品种覆盖：{cov['n_products_read']} 个  {cov['universe_forms']}")
    print(f"    {' '.join(cov['products_read'])}")
    unc = cov["uncovered"]
    thin = unc["thin_history"]
    unread = unc["full_history_but_unread"]
    thin_text = ", ".join("{} {}".format(r["product"], r["target_rows"]) for r in thin)
    unread_text = ", ".join(r["product"] for r in unread) or "无"
    print(f"    未读到 {len(thin) + len(unread)} 个："
          f"目标表行数不足 {len(thin)} 个（{thin_text}；"
          f"满样本 {unc['full_coverage_rows']} 行），"
          f"满行却未被选中 {len(unread)} 个（{unread_text}）")
    d = doc["direction"]
    p_text = "n/a" if d["two_sided_p_vs_half"] is None else f"{d['two_sided_p_vs_half']:.4f}"
    print(f"\n  符号：一致 {d['sign_agrees']} / 相反 {d['sign_opposite']}，"
          f"对 50% 的双侧 p={p_text}")
    print(f"  decoy exceed 中位：{doc['decoy_median']}")
    print("\n  预注册停止规则：")
    for cond, met in doc["stop_rule"].items():
        mark = "满足" if met is True else ("不满足" if met is False else "无法判定")
        print(f"    [{mark}] {cond}")
    print(f"  → 三条{'同时满足，应宣告数据源级否定' if doc['stop_rule_all_met'] else '未同时满足'}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
