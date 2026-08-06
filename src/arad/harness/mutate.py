"""确定性变异器（M6 第二块）：离线跑连续研究时的提案器替身。

真正的执行者是 LLM。但把整条服务的**机制**验证到位，不该每次都花真钱与真时间，
也不该因为网络波动而中断。这里给出一个确定性的变异器：它读父版的冻结规格与
盲化反馈，产出下一版规格。

**它不是在爬结果的山。**它看不到任何效应量 —— 输入只有父版规格、语义错配码与
覆盖统计。变异方向由错配码决定（例如"幅度对方向"就换一个带符号的特征），
没有错配时按一个固定的参数网格推进。因此它跑出来的链形状是"搜索过程本身"的形状，
正是零假设带要度量的那个东西。

同一个 (父规格, 错配码, 第几步) 必然给出同一个子规格：可回放，进 content id。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ..features.spec import FeatureSpec

MUTATOR_VERSION = "0.1.0"

#: 参数网格。没有语义错配时按这条网格推进 —— 顺序固定，因此整条链可回放。
_WINDOW_GRID = (259200, 432000, 864000, 1728000)
_BASELINE_GRID = (1728000, 2592000, 5184000)
_ZWINDOW_GRID = (7776000, 15552000, 23328000)
_ZSTEP_GRID = (86400, 172800, 259200)


@dataclass(frozen=True)
class MutationPlan:
    """一次变异：改了什么，以及为什么改。理由只引用错配码，不引用任何结果。"""

    change_summary: str
    reason_code: str


def _signed_feature(step_index: int) -> tuple[list[dict], str, str]:
    """把幅度特征换成带符号的动量特征：这是「幅度对方向」错配的唯一正解。"""
    window = _WINDOW_GRID[step_index % len(_WINDOW_GRID)]
    # 基线必须**严格长于**观测窗：两者相等时 difference 恒为零，评价机会正确地
    # 报「回归元没有变异」，但那一轮就白花了。实测踩过。
    longer = [b for b in _BASELINE_GRID if b > window] or [window * 3]
    baseline = longer[step_index % len(longer)]
    steps = [
        {"name": "px_recent", "kind": "window", "source": "commodity_bar",
         "field": "log_return", "op": "sum", "window_seconds": window},
        {"name": "px_baseline", "kind": "window", "source": "commodity_bar",
         "field": "log_return", "op": "sum", "window_seconds": baseline},
        {"name": "momentum", "kind": "difference",
         "inputs": ["px_recent", "px_baseline"]},
    ]
    return (
        steps,
        "momentum",
        (f"改用带符号的动量特征（{window // 86400} 日累计对 {baseline // 86400} 日基线）："
         "标签是有符号收益，幅度类特征在方向上不可证伪"),
    )


def _magnitude_feature(step_index: int) -> tuple[list[dict], str, str]:
    """幅度特征的参数推进：观测窗、基线窗、标准化窗、采样步长轮流走一格。"""
    window = _WINDOW_GRID[step_index % len(_WINDOW_GRID)]
    baseline = _BASELINE_GRID[(step_index // 2) % len(_BASELINE_GRID)]
    zwindow = _ZWINDOW_GRID[(step_index // 3) % len(_ZWINDOW_GRID)]
    zstep = _ZSTEP_GRID[(step_index // 4) % len(_ZSTEP_GRID)]
    steps = [
        {"name": "rv_recent", "kind": "window", "source": "commodity_bar",
         "field": "realised_volatility", "op": "mean", "window_seconds": window},
        {"name": "rv_baseline", "kind": "window", "source": "commodity_bar",
         "field": "realised_volatility", "op": "mean", "window_seconds": baseline},
        {"name": "rv_innovation", "kind": "difference",
         "inputs": ["rv_recent", "rv_baseline"]},
        {"name": "rv_innovation_z", "kind": "zscore", "inputs": ["rv_innovation"],
         "window_seconds": zwindow, "sample_every_seconds": zstep, "min_samples": 20},
    ]
    return (
        steps,
        "rv_innovation_z",
        (f"观测窗 {window // 86400} 日、基线 {baseline // 86400} 日、"
         f"标准化窗 {zwindow // 86400} 日、采样步长 {zstep // 86400} 日"),
    )


def next_proposal(
    *,
    step_index: int,
    mismatch_codes: tuple[str, ...],
    target_name: str,
    parent: FeatureSpec | None = None,
) -> tuple[str, MutationPlan]:
    """产出下一版提案的 JSON 与变异说明。

    `mismatch_codes` 来自语义审计员，是封闭词表里的码，不含任何数字。
    """
    if "magnitude_vs_signed_label" in mismatch_codes:
        steps, output, why = _signed_feature(step_index)
        reason = "magnitude_vs_signed_label"
        mechanism = "价格动量：短期累计收益相对长期基线为正时，下一 session 收益方向偏正"
        failure = "若动量与下一 session 收益无关，则本特征被证伪"
    else:
        steps, output, why = _magnitude_feature(step_index)
        reason = "parameter_sweep" if parent is not None else "seed"
        mechanism = "波动状态：短期已实现波动相对自身分布异常抬升时，下一 session 收益方向偏正"
        failure = "若标准化后的创新量与下一 session 收益无关，则本特征被证伪"

    feature_id = "auto_" + "_".join(
        f"{s['name']}{s.get('window_seconds') or ''}" for s in steps
    )[:72]
    payload = {
        "mechanism": mechanism,
        "source": "commodity_bar",
        "target": target_name,
        "horizon": "next_session",
        "universe": "sc_dominant_t1",
        "direction": 1,
        "falsifiable_condition": failure,
        "rationale": "确定性变异器产出；它看不到任何效应量",
        "change_summary": "" if parent is None else why,
        "feature_spec": {
            "feature_id": feature_id,
            "mechanism": mechanism,
            "steps": steps,
            "output_step": output,
            "failure_condition": failure,
            "authored_by": f"deterministic_mutator/{MUTATOR_VERSION}",
        },
    }
    return json.dumps(payload, ensure_ascii=False), MutationPlan(why, reason)


__all__ = ["MUTATOR_VERSION", "MutationPlan", "next_proposal"]
