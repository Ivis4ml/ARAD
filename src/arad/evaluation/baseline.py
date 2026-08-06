"""最小 Baseline Control：SC 自身波动持续性（M3 第二块）。

这是 Merge-Plan-2 §3.1 的 **Baseline Control Library** 成员，不是 Alternative
Factor：它只用 SC 自身量价，不含任何另类数据，**不计入另类因子库存**。
它的用途是数据与评价的 sanity check、残差化与正交性对照。

预测量是同一合约、**同一 session 类型**的上一个已实现波动，标签是当前 session 的
已实现波动。必须同类型配对：夜盘与日盘的时长与波动水平系统性不同，用相邻 session
配对会在构造上造成负相关，把 session 类型效应误读成波动反转。首版实现犯过这个错，
实测斜率 -0.108 且置换检验 100% 超越，改为同类型配对后修正。

PIT 关系由构造保证：上一同类型 session 的 RV 在其 label 窗口结束时才可用，
该时刻严格早于当前 session 的决策时点。
"""

from __future__ import annotations

import math
import os
from datetime import timedelta

import pyarrow.parquet as pq

from .kernel import EvaluationRequest, EvaluationRow, evaluate

BASELINE_ID = "baseline_sc_rv_persistence"
INVENTORY = "baseline_control"  # 明确不计入 Alternative Factor Inventory


def build_rows(target_path: str, segment: str = "discovery") -> tuple[list, dict]:
    """从 M2 目标表构造评价行。只用同一合约相邻 session，且严格保持 PIT。"""
    table = pq.read_table(
        target_path,
        columns=[
            "contract", "trading_day", "session_name", "decision_time", "label_start",
            "label_end", "value", "no_trade", "episode_id", "sample_segment",
        ],
    )
    rows = [r for r in table.to_pylist() if r["sample_segment"] == segment]
    rows.sort(key=lambda r: (r["contract"], r["label_start"]))

    out, labels = [], {}
    previous: dict[tuple[str, str], dict] = {}
    for cur in rows:
        pair_key = (cur["contract"], cur["session_name"])
        prev = previous.get(pair_key)
        previous[pair_key] = cur
        if prev is None:
            continue
        if prev["no_trade"] or cur["no_trade"]:
            continue                      # no-trade 是 NULL 加原因，不是 0
        if prev["value"] is None or cur["value"] is None or prev["value"] <= 0:
            continue
        if prev["label_end"] >= cur["decision_time"]:
            continue                      # 上一 session 尚未结束就不可用
        key = f"{cur['contract']}:{cur['trading_day']}:{cur['session_name']}"
        out.append(
            EvaluationRow(
                row_key=key,
                episode_id=cur["episode_id"],
                date_cluster=str(cur["trading_day"]),
                product_cluster=cur["contract"][:2],
                decision_time=cur["decision_time"],
                label_start=cur["label_start"],
                availability_times={"prev_same_session_rv": prev["label_end"]},
                prediction=math.log(prev["value"]),
                # 同类型配对后 session 类型不再是混淆源；保留一个有变异的完整性哨兵
                controls={"trading_day_parity": float(int(cur["trading_day"]) % 2)},
            )
        )
        labels[key] = math.log(cur["value"])
    return out, labels


def run_baseline(target_path: str, *, segment: str = "discovery") -> dict:
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"缺少 SC 目标表 {target_path}；请先运行 spine build")
    rows, labels = build_rows(target_path, segment)
    if len(rows) < 3:
        raise ValueError(f"{segment} 段可用观测过少（{len(rows)}），无法评价")
    request = EvaluationRequest(
        study_id=BASELINE_ID,
        confirmatory_id="baseline-v1",
        family=BASELINE_ID,
        rows=rows,
        authoritative_keys=[r.row_key for r in rows],
        cost_model_declared=True,   # 对照集不承诺可交易，成本占位视为已声明
        placebo_draws=200,
        hac_lag=5,
        min_returns=100,
        min_clusters=50,
    )
    result = evaluate(request, labels, role="evaluator")
    result["inventory"] = INVENTORY
    result["inventory_note"] = (
        "Baseline Control，只用 SC 自身量价，不计入 Alternative Factor Inventory；"
        "纯量价因子不能被统计为另类因子（Merge-Plan-2 §3.1）"
    )
    result["sample_segment"] = segment
    span = sorted(r.decision_time for r in rows)
    result["coverage"]["decision_time_from"] = span[0].isoformat()
    result["coverage"]["decision_time_to"] = span[-1].isoformat()
    result["coverage"]["min_lead_seconds"] = min(
        int((r.decision_time - a).total_seconds())
        for r in rows
        for a in r.availability_times.values()
    )
    assert result["coverage"]["min_lead_seconds"] > 0
    assert timedelta(seconds=result["coverage"]["min_lead_seconds"]) > timedelta(0)
    return result
