"""两条经验零分布的对照：置换与 decoy，逐条取自账本（决定 0013 §六的更正）。

决定 0013 §六原本印了一张四行的对照表（`FED_HIKE:dp` 等四条构造的 exceed
比例）。核对时发现：仓库里没有任何脚本、manifest 或账本字段产出那四对数字，
它们出自一次临时计算，产物已不存在。一份声称「每个数字可复算」的报告不能
留这样一张表，因此本脚本用账本里真实记录的读数把它替换掉。

替换是严格的改善而不只是补一份出处：评价机自 M22 起在同一次评价里同时记下
`placebo_exceed_rate` 与 `decoy_exceed_rate`，因此每一条带 decoy 的 Study
本身就是一次配对观测，两个比例算在同一批预测、同一批标签上。

两条零分布切的是同一条链的两端：

- **置换**：按 Episode 整块打乱**标签**，保留真实因子序列。它条件于真实的 x，
  但 y 侧的序列结构与体制被打乱破坏，零分布可能过窄。
- **decoy**：循环平移**因子**，保留真实标签序列的肥尾、体制与序列相关，
  也逐点保留因子自身的边际分布与自相关（平移不改变这两者），只破坏 x 与 y
  的配对。不用打乱因子，因为打乱会毁掉因子的自相关，而自相关正是构造伪迹的
  主要来源。

**读数的精度必须一并印出**：decoy 只有 39 次平移，一个比例的蒙特卡洛标准误
约为 sqrt(p(1-p)/39)，在 p≈0.5 处约 0.08。因此单条构造上的两率之差多半落在
抽样误差之内，可读的信息是**方向在多少条上一致**，不是任何一对的差值大小。
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

#: decoy 的平移次数。经验分辨率为 1/(draws+1)。
_DECOY_DRAWS = 39


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def measure(ledger_path: str = "data/ledger/service.db") -> dict:
    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

    rows = []
    universe: dict[str, str] = {}
    for event in events:
        study = event.get("study_id")
        if not study:
            continue
        payload = event["payload"]
        if event["event_type"] == "proposal_locked":
            spec = payload.get("proposal") or payload
            universe[study] = spec.get("universe") or ""
        elif event["event_type"] == "evaluation_result":
            diagnostics = payload.get("diagnostics") or {}
            decoy = (diagnostics.get("decoy") or {}).get("decoy_exceed_rate")
            placebo = (diagnostics.get("placebo") or {}).get("placebo_exceed_rate")
            if not (_finite(decoy) and _finite(placebo)):
                continue
            rows.append({
                "study_id": study,
                "universe": universe.get(study, ""),
                "placebo_exceed": placebo,
                "decoy_exceed": decoy,
                "decoy_stricter": decoy > placebo,
                "gap": decoy - placebo,
            })

    stricter = [r for r in rows if r["decoy_stricter"]]
    exceptions = [r for r in rows if not r["decoy_stricter"]]
    # 单条比例的蒙特卡洛标准误上界（p=0.5 处取到）。
    se_at_half = math.sqrt(0.25 / _DECOY_DRAWS)
    # 若两条零分布同严，「decoy 更严」在每条上各半概率；用正态近似给个方向性检验。
    n = len(rows)
    p_sign = None
    if n:
        z = (len(stricter) - n / 2) / math.sqrt(n / 4)
        p_sign = math.erfc(abs(z) / math.sqrt(2))

    return {
        "measurement": "empirical-nulls/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "note": (
            "取代决定 0013 §六原有的四行对照表 —— 那四对数字无产出脚本，"
            "本表逐条取自账本 evaluation_result 的 diagnostics。"
        ),
        "decoy_draws": _DECOY_DRAWS,
        "decoy_resolution": 1.0 / (_DECOY_DRAWS + 1),
        "per_row_mc_se_upper_bound": se_at_half,
        "n_paired": n,
        "n_decoy_stricter": len(stricter),
        "share_decoy_stricter": (len(stricter) / n) if n else None,
        "sign_test_two_sided_p": p_sign,
        "exceptions": exceptions,
        "median_placebo_exceed": (
            sorted(r["placebo_exceed"] for r in rows)[n // 2] if n else None),
        "median_decoy_exceed": (
            sorted(r["decoy_exceed"] for r in rows)[n // 2] if n else None),
        "rows": rows,
    }


def main() -> None:
    doc = measure()
    out = Path("artifacts/manifests/empirical_nulls.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    n = doc["n_paired"]
    print(f"同时记有置换与 decoy 两率的 Study：{n} 条")
    if not n:
        print("账本中尚无配对读数。")
        return
    print(f"  decoy 更严 {doc['n_decoy_stricter']}/{n} "
          f"（{doc['share_decoy_stricter']:.1%}），"
          f"符号检验双侧 p={doc['sign_test_two_sided_p']:.4f}")
    print(f"  中位：置换 {doc['median_placebo_exceed']:.4f}，"
          f"decoy {doc['median_decoy_exceed']:.4f}")
    print(f"  单条比例的蒙特卡洛标准误上界 {doc['per_row_mc_se_upper_bound']:.4f}"
          f"（{doc['decoy_draws']} 次平移，分辨率 {doc['decoy_resolution']:.4f}）"
          " —— 单条上的两率之差多半落在此误差内，可读的是方向的一致性")
    if doc["exceptions"]:
        print("  例外（decoy 反而更松）：")
        for row in doc["exceptions"]:
            print(f"    {row['study_id']:20s} 置换 {row['placebo_exceed']:.4f} "
                  f"对 decoy {row['decoy_exceed']:.4f}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
