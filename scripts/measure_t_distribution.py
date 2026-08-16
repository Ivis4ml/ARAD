"""实测 |t| 的分布，对照同样本量的标准正态噪声（报告第十版 §基准线）。

解析地板 E₂(n) 的推导前提是每次检验抽到一个标准正态随机数。这份测量核对该前提。

三条必须与结论同印的限定：

1. **左列不是纯零样本**。它混着可能真实但与另类数据无关的效应（最大的那条是
   波动率聚集假象：分母是已实现波动，目标也是已实现波动）。因此本测量只作提示，
   严格的零参照要由置换与 decoy 两条经验零分布给出。
2. **分位定义只用一种**，全表一致。混用 exclusive 与线性插值两种定义会让同一张表
   里的两列不可比 —— 这正是本表前身犯过的错。
3. **正态参照列有种子**，可复现。前身那一列是一次没记种子的模拟，构造上无法复现。
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

_DRAWS = 2000
_SEED = 20260815


def _quantile_linear(values: list[float], q: float) -> float:
    """线性插值分位。全表统一用这一种定义。"""
    if not values:
        return float("nan")
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (position - low)


def measure(ledger_path: str = "data/ledger/service.db") -> dict:
    import numpy as np

    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

    observed = []
    undefined = 0
    for event in events:
        if event["event_type"] != "evaluation_result":
            continue
        t = (event["payload"].get("effects") or {}).get("t_stat")
        if isinstance(t, (int, float)) and math.isfinite(t):
            observed.append(abs(t))
        else:
            undefined += 1
    observed.sort()
    n = len(observed)

    rng = np.random.default_rng(_SEED)
    sims = np.abs(rng.standard_normal((_DRAWS, n)))
    sims.sort(axis=1)
    ref = {
        "median": float(np.mean([_quantile_linear(list(row), 0.5) for row in sims])),
        "mean": float(np.mean(sims.mean(axis=1))),
        "p90": float(np.mean([_quantile_linear(list(row), 0.9) for row in sims])),
        "max": float(np.mean(sims[:, -1])),
    }

    return {
        "measurement": "t-distribution/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "quantile_definition": "线性插值（全表统一）",
        "reference": {
            "kind": "标准正态的绝对值，样本量与实测相同",
            "draws": _DRAWS, "seed": _SEED,
        },
        "n_finite": n,
        "n_undefined": undefined,
        "observed": {
            "median": _quantile_linear(observed, 0.5),
            "mean": sum(observed) / n if n else None,
            "p90": _quantile_linear(observed, 0.9),
            "max": observed[-1] if observed else None,
        },
        "normal_reference": ref,
        "caveats": [
            ("左列不是纯零样本：混着可能真实但与另类数据无关的效应，"
             "最大的那条是波动率聚集假象"),
            "因此本测量只作提示；严格的零参照由置换与 decoy 两条经验零分布给出",
        ],
    }


def main() -> None:
    doc = measure()
    out = Path("artifacts/manifests/t_distribution.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    o, r = doc["observed"], doc["normal_reference"]
    print(f"实测 |t| 有限 {doc['n_finite']} 条（无定义 {doc['n_undefined']} 条），"
          f"对照 {doc['reference']['draws']} 次标准正态模拟（种子 "
          f"{doc['reference']['seed']}，{doc['quantile_definition']}）")
    print(f"{'量':>8s} {'实测':>10s} {'正态参照':>10s} {'倍数':>8s}")
    for key, label in (("median", "中位"), ("mean", "均值"),
                       ("p90", "90 分位"), ("max", "最大值")):
        print(f"{label:>8s} {o[key]:10.4f} {r[key]:10.4f} {o[key] / r[key]:8.2f}")
    print("\n限制：")
    for line in doc["caveats"]:
        print(f"  {line}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
