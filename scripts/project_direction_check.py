"""按更正后的方向判据重投影全部历史判决（决定 0012）。

账本只追加、不可回写，因此已入账的判决**原样保留**。本脚本回答的是另一个问题：
「若当时评价机就核对方向，判决会是什么」，与成本模型建成后的回溯投影
（决定 0007）同一形态、同一纪律。

投影规则与新实现逐字一致：预注册方向为 ±1、斜率非零且符号相反时，
追加阻断理由 `direction_mismatch`，该理由按失效表只使 candidate 失效。
因此投影只可能把 candidate 降为 blocked，不可能把任何否定翻成肯定。
"""

from __future__ import annotations

import itertools
import json
import math
import os
import random
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.evaluation.kernel import REASON_INVALIDATES
from arad.memory.ledger import EvidenceLedger, Role

#: |t| 分层的边界。分层是为了回答一个具体问题：**一致率随效应大小上升吗**。
#: 若模型的符号推理有内容、只是被噪声淹没，效应大的那些应当更容易对。
_STRATA_EDGES = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, float("inf"))


def _strata(rows: list[dict]) -> list[dict]:
    out = []
    for low, high in itertools.pairwise(_STRATA_EDGES):
        band = [r for r in rows
                if isinstance(r.get("t_stat"), (int, float))
                and math.isfinite(r["t_stat"])
                and low <= abs(r["t_stat"]) < high]
        agree = sum(1 for r in band if r["sign_agrees"])
        out.append({
            "low": low, "high": None if math.isinf(high) else high,
            "n": len(band), "sign_agrees": agree,
            "rate": (agree / len(band)) if band else None,
        })
    return out


def _spearman(xs: list[float], ys: list[float]) -> float:
    def rank(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
                j += 1
            average = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = average
            i = j + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def _rank_correlation(rows: list[dict], draws: int = 20000,
                      seed: int = 20260815) -> dict:
    """逐条秩相关（|t| 与符号一致指示变量）及其置换 p 值。

    先前流通过一组「+0.139 / p=0.155」的数字，复算不出来；本函数把它换成
    可复算的量并写进产物，付印一律以此为准。
    """
    usable = [r for r in rows
              if isinstance(r.get("t_stat"), (int, float))
              and math.isfinite(r["t_stat"])]
    if len(usable) < 3:
        return {"spearman": None, "permutation_p": None, "n": len(usable)}
    xs = [abs(r["t_stat"]) for r in usable]
    ys = [1.0 if r["sign_agrees"] else 0.0 for r in usable]
    rho = _spearman(xs, ys)
    rnd = random.Random(seed)
    hits = 0
    for _ in range(draws):
        shuffled = ys[:]
        rnd.shuffle(shuffled)
        if abs(_spearman(xs, shuffled)) >= abs(rho):
            hits += 1
    return {
        "spearman": rho, "permutation_p": hits / draws,
        "draws": draws, "seed": seed, "n": len(usable),
        "note": "取代先前无法复算的 +0.139 / p=0.155",
    }


def project(ledger_path: str = "data/ledger/service.db") -> dict:
    with EvidenceLedger(ledger_path) as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

    direction: dict[str, int] = {}
    universe: dict[str, str] = {}
    family: dict[str, str] = {}
    slope: dict[str, float] = {}
    tstat: dict[str, float] = {}
    kinds: dict[str, list[str]] = {}
    verdict: dict[str, str] = {}
    for event in events:
        study = event.get("study_id")
        payload = event["payload"]
        if not study:
            continue
        if event["event_type"] == "proposal_locked":
            spec = payload.get("proposal") or payload
            if spec.get("direction") in (1, -1):
                direction[study] = int(spec["direction"])
            if spec.get("universe"):
                universe[study] = spec["universe"]
        elif event["event_type"] == "evaluation_result":
            effects = payload.get("effects") or {}
            if isinstance(effects.get("slope"), (int, float)):
                slope[study] = effects["slope"]
            if isinstance(effects.get("t_stat"), (int, float)):
                tstat[study] = effects["t_stat"]
            kinds[study] = list(payload.get("blocked_reason_kinds") or [])
            if payload.get("family"):
                family[study] = payload["family"]
        elif event["event_type"] == "verdict_recorded":
            verdict[study] = payload.get("verdict")

    rows = []
    for study, want in sorted(direction.items()):
        got = slope.get(study)
        if got is None or got == 0:
            continue
        realised = 1 if got > 0 else -1
        mismatch = realised != want
        before = verdict.get(study)
        after = before
        if mismatch and before == "candidate":
            after = "blocked"
        rows.append({
            "study_id": study,
            "family": family.get(study),
            "universe": universe.get(study),
            "declared_direction": want,
            "realised_sign": realised,
            "t_stat": tstat.get(study),
            "sign_agrees": not mismatch,
            "verdict_as_recorded": before,
            "verdict_under_direction_check": after,
            "changed": after != before,
        })

    changed = [r for r in rows if r["changed"]]
    strata = _strata(rows)
    return {
        "strata": strata,
        "rank_correlation": _rank_correlation(rows),
        "projection": "direction_check/v1",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "rule": {
            "reason_kind": "direction_mismatch",
            "invalidates": sorted(REASON_INVALIDATES["direction_mismatch"]),
            "note": (
                "斜率符号与预注册方向相反时追加该阻断理由。它只使 candidate 失效，"
                "因此投影不可能把任何否定翻成肯定；能改变的只有 candidate → blocked。"
                "账本不回写，本表是读取侧的投影。"
            ),
        },
        "studies_with_declared_direction": len(rows),
        "sign_agrees": sum(1 for r in rows if r["sign_agrees"]),
        "sign_opposite": sum(1 for r in rows if not r["sign_agrees"]),
        "verdict_counts_as_recorded": dict(
            Counter(r["verdict_as_recorded"] for r in rows).most_common()),
        "verdict_counts_under_check": dict(
            Counter(r["verdict_under_direction_check"] for r in rows).most_common()),
        "changed": changed,
        "rows": rows,
    }


def main() -> None:
    out = Path("artifacts/manifests/direction_check_projection.json")
    doc = project()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"有预注册方向且斜率非零的 Study：{doc['studies_with_declared_direction']}")
    print(f"  符号一致 {doc['sign_agrees']}，符号相反 {doc['sign_opposite']}")
    print(f"  判决（如实入账）：{doc['verdict_counts_as_recorded']}")
    print(f"  判决（方向核对投影）：{doc['verdict_counts_under_check']}")
    if doc["changed"]:
        print("\n投影下发生变化的 Study：")
        for row in doc["changed"]:
            print(f"  {row['study_id']:18s} 声明 {row['declared_direction']:+d} "
                  f"实得 t={row['t_stat']:+.3f} | {row['verdict_as_recorded']} → "
                  f"{row['verdict_under_direction_check']}")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
