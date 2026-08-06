"""从真实 spine 数据构造一个合成 Study，走完账本全流程并渲染快照。

这是 M3 第一块的出口演示：不是回测，不产生任何效果估计，也不读取 forward 数据。
它证明的是账本 schema 足以把一次判决完整回放 —— 包括两次冻结、两本分母、
当时可见的数据范围与判决理由。Verdict 固定为 `blocked`：evaluator 尚未建成，
任何"有效应"的结论此刻都不可能成立，把它写成别的值就是伪造证据。
"""

from __future__ import annotations

import json
import os

import pyarrow.parquet as pq

from ..registry.specs import (
    ConfirmatoryLock,
    HypothesisLock,
    NextAction,
    ProposalSpec,
    StudySpec,
    StudyVerdict,
    Verdict,
)
from .ledger import EvidenceLedger, Role
from .snapshot import collect_snapshot, render_markdown, require_complete

FAMILY = "sc_rv_geopolitical_innovation"


def _visible_range(target_path: str) -> dict:
    """当时可见的数据范围取自 M2 目标表的 discovery 段，不含任何 forward 数据。"""
    if not os.path.exists(target_path):
        return {"note": "SC 目标表不可用", "segment": "discovery"}
    table = pq.read_table(target_path, columns=["label_end", "sample_segment"])
    rows = [
        r for r in table.to_pylist() if r["sample_segment"] == "discovery"
    ]
    ends = sorted(r["label_end"] for r in rows)
    return {
        "segment": "discovery",
        "rows": len(rows),
        "from": ends[0].isoformat() if ends else None,
        "to": ends[-1].isoformat() if ends else None,
        "forward_data": "not read (per-Study forward eligibility 未到期)",
    }


def run_demo(ledger_path: str, target_path: str, out_path: str) -> dict:
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with EvidenceLedger(ledger_path) as ledger:
        study_id = "demo-sc-rv-geopolitical-innovation"

        # 一整批提案都进 proposal denominator，包括被预检挡下的
        accepted = ProposalSpec(
            mechanism="闭市期间地缘政治概率创新",
            source="polymarket",
            target="sc_rv_next_session",
            horizon="next_session",
            universe="sc_dominant_t1",
            direction=1,
            falsifiable_condition="概率创新与下一 session 已实现波动无关则证伪",
            proposed_by="demo",
            rationale="M2.5 词表显示 iran/israel/russia 是数据中最密集的地缘实体",
        )
        screened = ProposalSpec(
            mechanism="Brent 相关市场的概率创新",
            source="polymarket",
            target="sc_rv_next_session",
            horizon="next_session",
            universe="sc_dominant_t1",
            direction=1,
            falsifiable_condition="同上",
            proposed_by="demo",
        )
        ledger.record_proposal(accepted.content_id, FAMILY)
        ledger.record_proposal(
            screened.content_id, FAMILY, screened_out=True,
            reason="功效预检不足：全史仅 3 个市场含 brent（M2.5 词表实测），MDE 不可达",
        )

        hypothesis = HypothesisLock(
            proposal_id=accepted.content_id,
            experiment_family=FAMILY,
            controls=["sc_own_information", "cls_public_news"],
            sample_segments=["discovery"],
        )
        confirmatory = ConfirmatoryLock(
            hypothesis_id=hypothesis.content_id,
            formula="rv_next_session ~ residualised_probability_innovation + controls",
            transforms=["log", "winsorise_none"],
            controls=["sc_own_information", "cls_public_news"],
            statistics=["two_way_cluster", "block_bootstrap"],
            preregistered_diagnostics=[
                "leakage", "pseudo_replication", "influence_points",
                "classical_factor_proxy", "single_regime", "cost",
            ],
            cost_model="placeholder",
            economic_bound="待人工冻结",
            test_family=FAMILY,
        )
        study = StudySpec(
            study_id=study_id,
            proposal_id=accepted.content_id,
            hypothesis_id=hypothesis.content_id,
            confirmatory_id=confirmatory.content_id,
        )

        ledger.append("proposal_locked", accepted.payload(), study_id=study_id)
        ledger.append("hypothesis_locked", hypothesis.payload(), study_id=study_id)
        ledger.append("confirmatory_locked", confirmatory.payload(), study_id=study_id)
        ledger.append("study_created", study.payload(), study_id=study_id)
        ledger.append("visible_data_range", _visible_range(target_path), study_id=study_id)

        verdict = StudyVerdict(
            study_id=study_id,
            verdict=Verdict.BLOCKED,
            next_action=NextAction.WAIT_FOR_DATA,
            rationale=(
                "评价机尚未建成，且 Polymarket 侧缺机制分族（Decision Map #12）。"
                "本 Study 未读取任何 outcome，statistical denominator 为 0；"
                "在这两项就绪之前，任何非 blocked 的判决都不可能有证据支撑。"
            ),
            evidence_refs=[study.content_id],
        )
        ledger.append("verdict_recorded", verdict.payload(), study_id=study_id)

        events = ledger.read_events(role=Role.EVALUATOR, study_id=study_id)
        snapshot = require_complete(collect_snapshot(events, ledger.denominators(FAMILY)))
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_markdown(snapshot))
        with open(out_path.replace(".md", ".json"), "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2, default=str)
        return {
            "study_id": study_id,
            "events": ledger.require_intact(),
            "denominators": ledger.denominators(FAMILY),
            "snapshot": out_path,
        }
