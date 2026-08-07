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

#: 候选机制族。族的选择进入特征字段名，因而进 content id 与冻结锁 ——
#: 「用哪个族」是本提案的经济假设，不是藏在映射表里的常量。
_PM_FAMILIES = ("cand:iran", "cand:russia", "cand:israel")
#: 信念变化的回看跨度。SC 的两个闭市窗口约 6 与 6.5 小时，因此从 6 小时起步。
_PM_LAG_GRID = (21600, 43200, 86400, 172800)
_PM_OBS_GRID = (3600, 7200, 21600)


def _pm_belief_feature(step_index: int) -> tuple[list[dict], str, str]:
    """族的信念变化：现在的水平减去 Δ 之前的水平。

    这是 ADAR T2 的 `dp_terminal` 在本语言里的写法 —— 用 offset 取「Δ 之前那一段的
    最后取值」，再与当下作差。`dp_drift_run`（同号累积异号清零后最长的一段）
    现有原语表达不了，那是一个应当被声明的缺口，不是这里该绕过的东西。
    """
    family = _PM_FAMILIES[step_index % len(_PM_FAMILIES)]
    lag = _PM_LAG_GRID[(step_index // 3) % len(_PM_LAG_GRID)]
    obs = _PM_OBS_GRID[(step_index // 5) % len(_PM_OBS_GRID)]
    steps = [
        {"name": "p_now", "kind": "window", "source": "pm_market",
         "field": f"{family}:p", "op": "last", "window_seconds": obs},
        {"name": "p_lag", "kind": "window", "source": "pm_market",
         "field": f"{family}:p", "op": "last", "window_seconds": obs,
         "offset_seconds": lag},
        {"name": "dp", "kind": "difference", "inputs": ["p_now", "p_lag"]},
    ]
    return (
        steps, "dp",
        (f"改用 {family} 的信念变化（{lag // 3600} 小时跨度、{obs // 3600} 小时观测窗）："
         "另类数据侧的主线机制，标的是有符号收益"),
    )


def _pm_attention_feature(step_index: int) -> tuple[list[dict], str, str]:
    """族的资金关注度相对自身常态的抬升。名义额，不是笔数：一笔一美元与一笔十万
    美元对「市场在看这件事」的证据强度不同。"""
    family = _PM_FAMILIES[step_index % len(_PM_FAMILIES)]
    obs = _PM_OBS_GRID[(step_index // 3) % len(_PM_OBS_GRID)]
    base = _PM_LAG_GRID[(step_index // 4) % len(_PM_LAG_GRID)] * 4
    steps = [
        {"name": "flow_recent", "kind": "window", "source": "pm_market",
         "field": f"{family}:notional", "op": "sum", "window_seconds": obs},
        {"name": "flow_base", "kind": "window", "source": "pm_market",
         "field": f"{family}:notional", "op": "sum", "window_seconds": base},
        {"name": "attention", "kind": "ratio", "inputs": ["flow_recent", "flow_base"]},
    ]
    return (
        steps, "attention",
        (f"改用 {family} 的资金关注度（{obs // 3600} 小时成交额对 {base // 3600} 小时基线之比）："
         "信念未必变，但钱在往这件事上压"),
    )


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
    # 机制轮转：一条链不该只在一个想法里扫参数。轮转次序固定，因此整条链可回放。
    if "magnitude_vs_signed_label" in mismatch_codes:
        wheel = (
            (_pm_belief_feature,
             "闭市期间地缘族信念变化驱动开盘后的方向",
             "若该族信念变化与下一 session 收益无关，则本特征被证伪"),
            (_signed_feature,
             "价格动量：短期累计收益相对长期基线为正时，下一 session 收益方向偏正",
             "若动量与下一 session 收益无关，则本特征被证伪"),
            (_pm_attention_feature,
             "资金关注度：地缘族成交额相对自身基线抬升时，下一 session 方向可预测",
             "若关注度与下一 session 收益无关，则本特征被证伪"),
        )
        maker, mechanism, failure = wheel[step_index % len(wheel)]
        steps, output, why = maker(step_index)
        reason = "magnitude_vs_signed_label"
    else:
        steps, output, why = _magnitude_feature(step_index)
        reason = "parameter_sweep" if parent is not None else "seed"
        mechanism = "波动状态：短期已实现波动相对自身分布异常抬升时，下一 session 收益方向偏正"
        failure = "若标准化后的创新量与下一 session 收益无关，则本特征被证伪"

    feature_id = "auto_" + "_".join(
        f"{s['name']}{s.get('window_seconds') or ''}" for s in steps
    )[:72]
    # source 进 ProposalSpec 的 content id，也是 Atlas 覆盖表的分组依据：
    # 用了 pm_market 的特征必须如实报 polymarket，否则另类因子会被记成量价因子
    uses_pm = any(step.get("source") == "pm_market" for step in steps)
    payload = {
        "mechanism": mechanism,
        "source": "polymarket" if uses_pm else "commodity_bar",
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
