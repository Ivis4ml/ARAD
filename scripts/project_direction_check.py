"""按更正后的方向判据重投影全部历史判决（决定 0012）。

账本只追加、不可回写，因此已入账的判决**原样保留**。本脚本回答的是另一个问题：
「若当时评价机就核对方向，判决会是什么」——与成本模型建成后的回溯投影
（决定 0007）同一形态、同一纪律。

投影规则与新实现逐字一致：预注册方向为 ±1、斜率非零且符号相反时，
追加阻断理由 `direction_mismatch`，该理由按失效表只使 candidate 失效。
因此投影只可能把 candidate 降为 blocked，不可能把任何否定翻成肯定。
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from arad.evaluation.kernel import REASON_INVALIDATES
from arad.memory.ledger import EvidenceLedger, Role


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
    return {
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
