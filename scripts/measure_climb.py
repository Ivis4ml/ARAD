"""逐轮的合格构造最好成绩：爬升到底有没有发生（报告第十版）。

先前报告里印过一条十个数的序列，并附了一段自我更正。核对发现那条序列**仍然
不完整**：有合格构造的运行不止十个，更正也只补了其中五个。一段以「对趋势诚实」
为主题的正文里留一个不完整的序列，是最不该留的那种缺口。本脚本因此一次给全，
不再手抄。

三条约定，一处写明、全篇执行：

1. **地板取当次的本族地板**，即读取该次 outcome 时该族已读次数 n 对应的 E₂(n)。
   这是评价机当时真正施加的那条线，也是 `qualifying_climb.png` 画的那条。
   报告另有「合并地板」口径（把三本账并成一个分母），两者都真但不可混用；
   本脚本只出本族口径。

   n **按 `outcome_read` 事件计数**：一次读取消耗一次分母，与那次读取最终有没有
   算出有限的 t 无关。理由是分母记的是「看了几次」，不是「看成了几次」——
   若把算不出 t 的那次从分母里摘掉，等于让一次失败的读取免费。
   账本里近期评价载荷的 `floors.family_tests` 用的正是这个口径
   （run31-study-0 记 43，与本脚本重建一致）。报告既有的 `tab:crossed`
   用的是「只计 t 有限」的另一口径，因此同一条 Study 的地板会低一档
   （run16-study-3：2.5998 对 2.5941），差值不影响任何结论，但口径须声明。
2. **奖励 = |t| − 当次本族地板**。地板随分母单调上升，因此维持同样的 |t|
   等于奖励在下降。
3. **合格 = 另类数据（源为 `pm_market`）且斜率符号与预注册方向一致**。
   量价构造属基线对照，不计入另类清单；符号相反的读数不支持它自己主张的机制。
   t 无定义的读数（双向 cluster 方差非正）不进极值统计，但**单独计数**，
   否则读者会以为每次检验都产出了可比的 t。
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

import build_report


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def measure(ledger_path: str = "data/ledger/service.db") -> dict:
    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

    def family_of(study: str) -> str:
        run = study.split("-study-")[0]
        if run in build_report.EVENT_RUNS:
            return "event"
        if run in build_report.MECH_RUNS:
            return "mech"
        return "old"

    # 地板必须自己按族内已读次数重建：`floors.family_floor` 只在近期运行的
    # 评价载荷里有，早期运行没有该字段。按账本顺序数每族的 outcome_read，
    # 第 k 次读取对应的地板即 E₂(k) —— 与评价机、与搜索曲线同一条定义。
    from arad.evaluation.selection import expected_max_abs_z

    rows: dict[str, dict] = {}
    family_reads: dict[str, int] = {}
    for event in events:
        study = event.get("study_id")
        if not study:
            continue
        payload = event["payload"]
        row = rows.setdefault(study, {"study_id": study})
        if event["event_type"] == "outcome_read":
            family = family_of(study)
            family_reads[family] = family_reads.get(family, 0) + 1
            row["family_tests"] = family_reads[family]
            row["family_floor"] = expected_max_abs_z(family_reads[family])
        elif event["event_type"] == "proposal_locked":
            spec = payload.get("proposal") or payload
            if spec.get("direction") in (1, -1):
                row["declared_direction"] = int(spec["direction"])
            source = spec.get("sources") or spec.get("source") or ""
            row["source"] = source if isinstance(source, str) else str(source)
        elif event["event_type"] == "evaluation_result":
            effects = payload.get("effects") or {}
            row["evaluated"] = True
            row["t_stat"] = effects.get("t_stat")
            row["slope"] = effects.get("slope")
        elif event["event_type"] == "verdict_recorded":
            row["verdict"] = payload.get("verdict")

    per_run: dict[str, dict] = {}
    for study, row in rows.items():
        if "verdict" not in row:
            continue
        run = study.split("-study-")[0]
        bucket = per_run.setdefault(run, {
            "run": run,
            "family": ("event" if run in build_report.EVENT_RUNS
                       else "mech" if run in build_report.MECH_RUNS else "old"),
            "n_decided": 0, "n_not_evaluated": 0, "n_t_undefined": 0,
            "n_qualified": 0,
            "best_abs_t": None, "best_reward": None, "best_study": None,
        })
        bucket["n_decided"] += 1
        if not row.get("evaluated"):
            # 没走到评价的（读取之前即被拦下）不是「t 无定义」，它们没消耗分母，
            # 单独计数。把两者混为一谈会虚报「无定义」的次数。
            bucket["n_not_evaluated"] += 1
            continue
        if not _finite(row.get("t_stat")):
            bucket["n_t_undefined"] += 1
            continue
        want = row.get("declared_direction")
        slope = row.get("slope")
        agrees = (want in (1, -1) and _finite(slope) and slope != 0
                  and (1 if slope > 0 else -1) == want)
        if "pm" not in (row.get("source") or "") or not agrees:
            continue
        bucket["n_qualified"] += 1
        floor = row.get("family_floor")
        if not _finite(floor):
            continue
        reward = abs(row["t_stat"]) - floor
        if bucket["best_reward"] is None or reward > bucket["best_reward"]:
            bucket["best_reward"] = reward
            bucket["best_abs_t"] = abs(row["t_stat"])
            bucket["best_study"] = study
            bucket["best_floor"] = floor

    order = [r for r in build_report.RUN_ORDER if r in per_run]
    unknown = sorted(set(per_run) - set(build_report.RUN_ORDER))
    series = [per_run[r] for r in order]
    with_reward = [s for s in series if s["best_reward"] is not None]
    positive = [s for s in with_reward if s["best_reward"] > 0]

    return {
        "measurement": "climb/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "floor_convention": (
            "当次本族地板 E₂(n)，n 为读取该次 outcome 时该族已读次数。"
            "报告另有合并地板口径，两者不可混用"
        ),
        "qualify_rule": (
            "源为 pm_market（另类数据）且斜率符号与预注册方向一致；"
            "t 无定义者不进极值统计但单独计数"
        ),
        "runs_unregistered_in_run_order": unknown,
        "n_runs_with_qualified": len(with_reward),
        "n_runs_with_positive_reward": len(positive),
        "positive_runs": [
            {"run": s["run"], "reward": s["best_reward"],
             "study": s["best_study"], "abs_t": s["best_abs_t"]}
            for s in positive
        ],
        "best_reward_overall": (
            max(s["best_reward"] for s in with_reward) if with_reward else None),
        "worst_reward_overall": (
            min(s["best_reward"] for s in with_reward) if with_reward else None),
        "series": series,
    }


def main() -> None:
    doc = measure()
    out = Path("artifacts/manifests/climb.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    if doc["runs_unregistered_in_run_order"]:
        print(f"警告：账本里有未登记在 RUN_ORDER 的运行 "
              f"{doc['runs_unregistered_in_run_order']}，它们未进序列")
    print("逐轮合格构造最好成绩（地板口径：当次本族地板）")
    print(f"{'运行':8s} {'族':6s} {'判决':>4s} {'未评价':>6s} {'t无定义':>7s} {'合格':>4s} "
          f"{'最好|t|':>8s} {'地板':>7s} {'奖励':>8s}  最好的那条")
    for s in doc["series"]:
        if s["best_reward"] is None:
            print(f"{s['run']:8s} {s['family']:6s} {s['n_decided']:4d} "
                  f"{s['n_not_evaluated']:6d} {s['n_t_undefined']:7d} "
                  f"{s['n_qualified']:4d} "
                  f"{'—':>8s} {'—':>7s} {'—':>8s}")
            continue
        print(f"{s['run']:8s} {s['family']:6s} {s['n_decided']:4d} "
              f"{s['n_not_evaluated']:6d} {s['n_t_undefined']:7d} "
              f"{s['n_qualified']:4d} "
              f"{s['best_abs_t']:8.3f} {s['best_floor']:7.3f} "
              f"{s['best_reward']:+8.3f}  {s['best_study']}")
    print(f"\n有合格构造的运行 {doc['n_runs_with_qualified']} 个，"
          f"其中奖励为正的 {doc['n_runs_with_positive_reward']} 个：")
    for row in doc["positive_runs"]:
        print(f"  {row['run']:8s} |t|={row['abs_t']:.3f} "
              f"奖励 {row['reward']:+.3f}  {row['study']}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
