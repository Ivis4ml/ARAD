"""在真实 SC 数据上跑一次 Search Episode，并把账本渲染成 Atlas（M4 出口演示）。

这不是回测，也不承诺发现任何因子。它验证的是 M4 的出口条件：一次 Episode 能在
无人干预下走完「提案 → 冻结 → 特征 → 评价 → 判决 → 入账」，且全过程可从账本
回放为自包含快照并被 Atlas 讲清楚。

provider 可选。默认 `MockProvider`：演示要可重复、零调用成本，且不因网络波动而失败；
脚本刻意覆盖四种结局，因为它们都是第一版预期会大量出现的状态：

1. 一个用商品量价原语表达的提案 —— 走完整评价，判决由评价机出具；
2. 一条原语缺口声明 —— 现有语言表达不了某机制，这是有价值的产出；
3. 一个引用 `pm_market` 的提案 —— 解释器尚未接入该源，判 blocked 并请求人工复核。
   这正是当前真实状态：另类数据侧的取数尚未接通，把它演示成"能跑"才是伪造；
4. 连续三次无法解析的输出 —— 重试用尽后降级为 ParseFailure，任务退避重排不丢。

第一个提案是**量价**特征，属 Baseline Control，不计入 Alternative Factor Inventory
（Merge-Plan-2 §3.1）。之所以用它，是因为解释器目前只接了 `commodity_bar`；
用它演示环路，同时用第三个提案把真实缺口暴露出来。

`--provider claude` 走真实 `claude -p`。脚本可以让环转起来，但**它证明不了真实模型的
产出能通过本系统的合同** —— 盲化检查、`extra="forbid"` 的 schema、PIT 原语约束都只有
真实产出能检验。真实调用只跑一轮：它花的是真钱与真时间，而要回答的问题只有一个。
"""

from __future__ import annotations

import json
import math
import os
from bisect import bisect_left
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

from ..atlas.app import render_app
from ..atlas.project import project
from ..atlas.sources import data_freshness
from ..evaluation.kernel import EvaluationRequest, EvaluationRow
from ..features.interpreter import INTERPRETER_VERSION, BarSeries, NotInterpretable, evaluate_series
from ..features.spec import FeatureSpec, Source, Step
from ..harness.audit import AuditInput
from ..harness.context import DeclaredBias, assemble_proposer_context
from ..harness.episode import run_episode
from ..memory.ledger import EvidenceLedger
from ..memory.ledger import Role as LedgerRole
from ..orchestrator.queue import DurableQueue
from ..providers.base import EpisodeBudget, Provider
from ..providers.claude_cli import ClaudeCliProvider
from ..providers.mock import MockProvider
from ..registry.specs import TaxonomyContamination


def _label_target_record() -> dict:
    from ..temporal.targets import TARGET_SPECS

    return next(t.record() for t in TARGET_SPECS if t.name == LABEL_TARGET)


FAMILY = "demo_sc_price_volume"
SEGMENT = "discovery"

#: 标签取收益型 target：只有它的 label 是有符号收益，Sharpe 才有定义。
#: 特征仍用已实现波动序列 —— 波动可以预测收益的**幅度**，本演示检验的是它能否
#: 预测收益的**方向**（sign_unit 仓位规则下 Sharpe 度量的正是方向）。
LABEL_TARGET = "sc_ret_next_session"
FEATURE_TARGET = "sc_rv_next_session"
#: 候选机制族的 PIT 序列（M5.2）。族的选择是各 Study 冻结的经济假设，不是映射表。
PM_SERIES_PATH = "data/pm_series/family_hourly.parquet"
FAMILIES_MANIFEST = "artifacts/manifests/pm_candidate_families.json"

#: 菜单偏差是实测过的（#12 taxonomy hindsight audit）。藏起来它会原样传导成提案偏差。
MENU_BIASES = [
    DeclaredBias(
        name="后见暴露",
        measurement="候选机制族的归纳语料有 83.7% 的市场创建于其自身裁决区间之后",
        consequence="菜单里的机制不是从无偏宇宙抽出的；依赖高暴露族的提案需在 rationale 中说明",
    ),
    DeclaredBias(
        name="晚涌现族的结果邻接",
        measurement="晚涌现族在大波动日上的活动份额高出 10.4 个百分点（p<0.002，效应 0.41 SD）",
        consequence="分类法与结果并非独立，重叠区间的 verdict 上限为 candidate",
    ),
]


def _proposal_json() -> str:
    """一个可被现有原语表达的提案：SC 自身波动的短期创新。"""
    spec = {
        "feature_id": "sc_rv_innovation_z_3d_vs_20d",
        "mechanism": "SC 自身已实现波动的短期创新，相对其自身过去 90 天分布标准化",
        "steps": [
            {"name": "rv_recent", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": 259200},
            {"name": "rv_baseline", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": 1728000},
            {"name": "rv_innovation", "kind": "difference",
             "inputs": ["rv_recent", "rv_baseline"]},
            {"name": "rv_innovation_z", "kind": "zscore", "inputs": ["rv_innovation"],
             "window_seconds": 7776000, "sample_every_seconds": 86400,
             "min_samples": 30},
        ],
        "output_step": "rv_innovation_z",
        "failure_condition": (
            "若标准化后的创新量与下一 session 已实现波动无关，则本特征被证伪；"
            "参考分布被长假截断到少于 30 个互异取值时该点无定义"
        ),
        "authored_by": "llm_proposer",
    }
    return json.dumps(
        {
            "mechanism": "波动状态：短期已实现波动相对自身分布异常抬升时，下一 session 收益方向偏正",
            "source": "commodity_bar",
            "target": "sc_ret_next_session",
            "horizon": "next_session",
            "universe": "sc_dominant_t1",
            "direction": 1,
            "falsifiable_condition": "斜率不显著异于零，或置换检验不能把实际值与置换分布区分开",
            "rationale": "量价对照集：解释器当前只接入 commodity_bar，先用它检验环路本身",
            "feature_spec": spec,
        },
        ensure_ascii=False,
    )


#: 一条演化链：同一机制的连续变体。每一版只改一处，且把改了什么写进 change_summary ——
#: 「策略在演化」要能被查证，靠的是父子关系与这句话，不是时间上的先后。
LINEAGE_VARIANTS = [
    {"window": 259200, "baseline": 1728000, "z_window": 7776000, "z_step": 86400,
     "min_samples": 30, "change": ""},
    {"window": 432000, "baseline": 1728000, "z_window": 7776000, "z_step": 86400,
     "min_samples": 30, "change": "观测窗口 3 日→5 日：3 日窗在长假后常整段落空"},
    {"window": 432000, "baseline": 2592000, "z_window": 7776000, "z_step": 86400,
     "min_samples": 30, "change": "基线窗口 20 日→30 日：让创新量的参照更稳"},
    {"window": 432000, "baseline": 2592000, "z_window": 15552000, "z_step": 86400,
     "min_samples": 45, "change": "标准化窗口 90 日→180 日，最小互异样本 30→45"},
    {"window": 432000, "baseline": 2592000, "z_window": 15552000, "z_step": 172800,
     "min_samples": 30, "change": "采样步长 1 日→2 日：相邻日的 5 日均值高度重叠"},
]


def _variant_json(v: dict) -> str:
    """把一个变体渲染成提案。同一机制，只改参数。"""
    spec = {
        "feature_id": (
            f"sc_rv_innovation_z_w{v['window']}_b{v['baseline']}"
            f"_z{v['z_window']}_s{v['z_step']}"
        ),
        "mechanism": "SC 自身已实现波动的短期创新，相对其自身过去分布标准化",
        "steps": [
            {"name": "rv_recent", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": v["window"]},
            {"name": "rv_baseline", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": v["baseline"]},
            {"name": "rv_innovation", "kind": "difference",
             "inputs": ["rv_recent", "rv_baseline"]},
            {"name": "rv_innovation_z", "kind": "zscore", "inputs": ["rv_innovation"],
             "window_seconds": v["z_window"], "sample_every_seconds": v["z_step"],
             "min_samples": v["min_samples"]},
        ],
        "output_step": "rv_innovation_z",
        "failure_condition": (
            "若标准化后的创新量与下一 session 已实现波动无关，则本特征被证伪；"
            "参考分布被长假截断到少于声明的互异取值数时该点无定义"
        ),
        "authored_by": "llm_proposer",
    }
    return json.dumps(
        {
            "mechanism": "波动状态：短期已实现波动相对自身分布异常抬升时，下一 session 收益方向偏正",
            "source": "commodity_bar",
            "target": "sc_ret_next_session",
            "horizon": "next_session",
            "universe": "sc_dominant_t1",
            "direction": 1,
            "falsifiable_condition": "斜率不显著异于零，或置换检验不能把实际值与置换分布区分开",
            "rationale": "量价对照集：解释器当前只接入 commodity_bar；标签为收益型 target",
            "change_summary": v["change"],
            "feature_spec": spec,
        },
        ensure_ascii=False,
    )


def _gap_json() -> str:
    return json.dumps(
        {
            "unsupported_mechanism": {
                "mechanism": "闭市期间地缘政治概率的跳变强度",
                "missing_primitive": "event_count_since_last_session_close",
                "why_existing_primitives_insufficient": (
                    "现有 window 算子以固定秒数回看，无法表达"
                    "「自上一次 session 收盘以来」这种由交易日历定义的边界"
                ),
            }
        },
        ensure_ascii=False,
    )


def _pm_proposal_json() -> str:
    """引用尚未接入的数据源。判 blocked 是正确结果，不是缺陷。"""
    spec = {
        "feature_id": "pm_probability_innovation_overnight",
        "mechanism": "地缘政治市场概率在夜间的创新量",
        "steps": [
            {"name": "p_recent", "kind": "window", "source": "pm_market",
             "field": "mid_price", "op": "last", "window_seconds": 3600},
        ],
        "output_step": "p_recent",
        "failure_condition": "概率创新与下一 session 已实现波动无关则证伪",
        "authored_by": "llm_proposer",
    }
    return json.dumps(
        {
            "mechanism": "闭市期间 Polymarket 地缘政治概率创新驱动开盘波动",
            "source": "polymarket",
            "target": "sc_rv_next_session",
            "horizon": "next_session",
            "universe": "sc_dominant_t1",
            "direction": 1,
            "falsifiable_condition": "概率创新与下一 session 已实现波动无关则证伪",
            "rationale": "另类数据侧的主线机制",
            "feature_spec": spec,
        },
        ensure_ascii=False,
    )


_COLUMNS = ["contract", "trading_day", "session_name", "decision_time", "label_start",
            "label_end", "value", "no_trade", "episode_id", "sample_segment"]


def _key(row: dict) -> str:
    return f"{row['contract']}:{row['trading_day']}:{row['session_name']}"


def _read_target(path: str) -> list[dict]:
    table = pq.read_table(path, columns=_COLUMNS)
    rows = [
        r for r in table.to_pylist()
        if r["sample_segment"] == SEGMENT and not r["no_trade"] and r["value"] is not None
    ]
    rows.sort(key=lambda r: r["label_end"])
    return rows


def _load_sc(target_path: str) -> tuple[list[dict], dict, dict]:
    """读 M2 目标表的 discovery 段，构造 bar 序列、决策点与标签。

    **特征序列与标签来自两张不同的表**：特征用已实现波动（正的量级，取对数），
    标签用收益型 target（有符号）。两者按 (合约, 交易日, session) 对齐，
    只保留两边都有取值的行 —— 这个交集不依赖标签取值本身，因此不是结果依赖过滤。

    序列的可用时刻取每个 session 的 `label_end`：已实现波动只有在其窗口结束后才可知。
    决策时点严格晚于所用序列点，PIT 由构造保证，不靠检查。
    """
    feature_rows = [r for r in _read_target(target_path) if r["value"] > 0]
    label_path = target_path.replace(FEATURE_TARGET, LABEL_TARGET)
    if not os.path.exists(label_path):
        raise FileNotFoundError(
            f"缺少收益型目标表 {label_path}；请先运行 `arad spine build`"
        )
    label_by_key = {_key(r): r for r in _read_target(label_path)}

    rows = [r for r in feature_rows if _key(r) in label_by_key]
    return_rows = sorted(label_by_key.values(), key=lambda r: r["label_end"])
    series = {
        (Source.COMMODITY_BAR, "realised_volatility"): BarSeries(
            field="realised_volatility",
            times=[r["label_end"] for r in feature_rows],
            values=[math.log(r["value"]) for r in feature_rows],
        ),
        # 收益型 target 的取值本身就是逐 session 的对数收益，且只有在 label_end
        # 之后才可知。语义审计诊断出「幅度对方向」之后，变异器要换成带符号特征，
        # 那条路径需要这条序列才走得通。
        (Source.COMMODITY_BAR, "log_return"): BarSeries(
            field="log_return",
            times=[r["label_end"] for r in return_rows],
            values=[r["value"] for r in return_rows],
        ),
    }
    labels = {_key(r): label_by_key[_key(r)]["value"] for r in rows}
    spans = [r["decision_time"] for r in rows]
    years = (
        (spans[-1] - spans[0]).total_seconds() / (365.2425 * 86400) if len(spans) > 1 else 0
    )
    visible = {
        "segment": SEGMENT,
        "feature_target": FEATURE_TARGET,
        "label_target": LABEL_TARGET,
        "label_is_return": True,
        "feature_rows": len(feature_rows),
        "rows": len(rows),
        "dropped_no_label": len(feature_rows) - len(rows),
        "sessions_per_year": round(len(rows) / years, 2) if years > 0 else None,
        "from": rows[0]["label_end"].isoformat() if rows else None,
        "to": rows[-1]["label_end"].isoformat() if rows else None,
        "forward_data": "未读取：forward 段按 Study 逐个到期，Atlas 中只显示预约状态",
    }
    pm = _load_pm_series(PM_SERIES_PATH)
    series.update(pm["series"])
    visible["pm_families"] = pm["families"]
    visible["pm_note"] = pm["note"]
    return rows, {"series": series, "labels": labels,
                  "periods_per_year": visible["sessions_per_year"]}, visible


def _load_pm_series(path: str) -> dict:
    """把候选族的小时序列接成解释器可用的形态。

    字段名形如 `cand:iran:p`：族在字段名里，因此「用哪个族」是**规格的一部分**，
    会进 content id、进冻结锁、进快照 —— 而不是藏在某张映射表里。

    `coverage_start` 显式取该族第一个分桶：族的市场是逐步出现的，早于它的决策点
    必须判为无定义，而不是拿一段更短的历史硬算。
    """
    if not os.path.exists(path):
        return {"series": {}, "families": [], "note": f"缺少 {path}，pm_market 不可用"}
    table = pq.read_table(path)
    buckets: dict[str, list[dict]] = {}
    for row in table.to_pylist():
        buckets.setdefault(row["family_id"], []).append(row)
    series: dict[tuple[Source, str], BarSeries] = {}
    families: list[dict] = []
    for family_id, rows in sorted(buckets.items()):
        rows.sort(key=lambda r: r["bucket_end"])
        times = [r["bucket_end"] for r in rows]
        start = times[0]
        for field in ("p", "notional", "trades"):
            values = [float(r[field]) for r in rows if r[field] is not None]
            keep = [r["bucket_end"] for r in rows if r[field] is not None]
            if len(values) < 2:
                continue
            series[(Source.PM_MARKET, f"{family_id}:{field}")] = BarSeries(
                field=f"{family_id}:{field}", times=keep, values=values,
                coverage_start=start,
            )
        families.append({
            "family_id": family_id, "buckets": len(rows),
            "from": start.isoformat(), "to": times[-1].isoformat(),
            "notional": sum(r["notional"] or 0.0 for r in rows),
        })
    return {
        "series": series,
        "families": families,
        "note": (
            "概率已归一到 outcome_seq==1 一侧；可用时刻取小时桶右端，"
            "比 block_timestamp（撮合时刻的保守下界）还要晚一档"
        ),
    }


def _build_evaluation(sc: dict, rows: list[dict], visible: dict):
    """返回 harness 需要的 build_evaluation 回调。"""
    series = sc["series"]
    labels = sc["labels"]
    times = series[(Source.COMMODITY_BAR, "realised_volatility")].times

    def build(spec: FeatureSpec, study_id: str):
        decision_times = [r["decision_time"] for r in rows]
        values, coverage = evaluate_series(spec, decision_times, series)
        eval_rows, authoritative, exclusions = [], [], {}
        for row, value in zip(rows, values, strict=True):
            key = _key(row)
            authoritative.append(key)
            idx = bisect_left(times, row["decision_time"]) - 1
            if value is None or idx < 0:
                exclusions[key] = (
                    "特征在该决策时点无定义（回看窗口内无数据）。"
                    "定义与否只取决于特征与历史数据，与标签无关，因此不是结果依赖过滤"
                )
                continue
            eval_rows.append(
                EvaluationRow(
                    row_key=key,
                    episode_id=row["episode_id"],
                    date_cluster=str(row["trading_day"]),
                    product_cluster=row["contract"][:2],
                    decision_time=row["decision_time"],
                    label_start=row["label_start"],
                    availability_times={"commodity_bar": times[idx]},
                    prediction=value,
                    controls={"trading_day_parity": float(int(row["trading_day"]) % 2)},
                )
            )
        detail = {**visible, "feature_coverage": coverage}
        if len(eval_rows) < 3:
            return None, {}, detail
        request = EvaluationRequest(
            study_id=study_id,
            confirmatory_id=spec.content_id,
            family=FAMILY,
            rows=eval_rows,
            authoritative_keys=authoritative,
            preregistered_exclusions=exclusions,
            cost_model_declared=False,   # M5 之前没有成本模型；声明为 True 就是伪造
            interpreter_version=INTERPRETER_VERSION,
            label_is_return=True,
            target_name=LABEL_TARGET,
            label_rule="entry_to_close",
            periods_per_year=sc.get("periods_per_year") or 485.3,
        )
        return request, labels, detail

    return build


def _assembler(ledger: EvidenceLedger, manifest_dir: str, visible: dict):
    menu = _menu(manifest_dir)

    def assemble(task: dict):
        return assemble_proposer_context(
            ledger=ledger,
            family=FAMILY,
            data_facts={
                "sources": data_freshness(manifest_dir),
                "visible": visible,
                "available_series": {
                    "commodity_bar": ["realised_volatility", "log_return"],
                    "pm_market": sorted(
                        f"{f['family_id']}:{k}" for f in visible.get("pm_families", [])
                        for k in ("p", "notional", "trades")
                    ),
                    "note": (
                        "解释器当前只提供这些序列；引用其他 field 会判 blocked。"
                        "pm_market 的字段名含族 id —— 用哪个族是本提案的经济假设"
                    ),
                },
            },
            targets=[{"target": "sc_rv_next_session", "horizon": "next_session",
                      "universe": "sc_dominant_t1", "segment": SEGMENT}],
            menu=menu,
            menu_biases=MENU_BIASES,
            budget_facts={"note": "预算耗尽只结束 Episode，Research Service 不停"},
            blockers=[
                "解释器目前只接入 commodity_bar；pm_market 与 cls_telegraph 尚未接入",
                "无成本与容量模型（属 M5），因此本轮不可能取 candidate",
            ],
        )

    return assemble


def _menu(manifest_dir: str, limit: int = 8) -> list[dict]:
    path = Path(manifest_dir) / "pm_candidate_families.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    families = [f for f in doc.get("families", []) if not f.get("screened_out")]
    families.sort(key=lambda f: f.get("trades", 0), reverse=True)
    return [
        {"family_id": f["family_id"], "head_tokens": f["head_tokens"],
         "markets": f["markets"], "trades": f["trades"]}
        for f in families[:limit]
    ]


def make_provider(kind: str, model: str = "claude-opus-5") -> tuple[Provider, int]:
    """选 provider。mock 走脚本，claude 走真实 `claude -p`。

    返回 (provider, 任务数)：真实调用只跑一轮，因为它花的是真钱与真时间，
    而这一轮要回答的问题只有一个 —— 真实模型的产出能否通过本系统的合同。
    """
    if kind == "mock":
        return MockProvider(scripts={"proposer": [
            _proposal_json(), _gap_json(), _pm_proposal_json(),
            "这不是 JSON", "还是不是 JSON", "仍然不是 JSON",
        ]}), 4
    if kind == "lineage":
        # 一条演化链：五个变体依次提出，每一版由上一版的判决触发
        return MockProvider(scripts={
            "proposer": [_variant_json(v) for v in LINEAGE_VARIANTS]
        }), 1
    if kind == "claude":
        return ClaudeCliProvider(model_id=model), 1
    raise ValueError(f"未知的 provider {kind!r}")


def _lineage_scheduler(limit: int = len(LINEAGE_VARIANTS)):
    """判决之后的调度：还有变体没试就排下一版，并记下它的父版。

    这是环真正闭上的那一段。`next_action` 写进账本却没有东西执行它的时候，
    每个 Study 都是孤立的一次性尝试。
    """
    state = {"n": 1}

    def schedule(outcome, queue, now):
        if outcome.study_id is None or state["n"] >= limit:
            return
        child = f"demo-study-{state['n']}"
        queue.enqueue(
            f"demo-task-{state['n']}", "study",
            {"study_id": child, "parent_study_id": outcome.study_id},
            now=now,
        )
        state["n"] += 1

    return schedule


def _contamination(visible: dict, families_manifest: str):
    """只有用到 pm_market 的特征才带分类法污染记录。

    候选机制族是从市场标题归纳出来的，而市场的创建对真实事件内生 —— 那些事件正是
    推动商品价格的事件。归纳语料若覆盖本 Study 读 outcome 的区间，族的选择就不独立
    于结果（决定 0004）。`cand:israel` 排进头部，正是因为以色列相关市场被创建并被
    大量交易，而它们被创建恰恰是在回应那些同时推动油价的事件。
    """
    if not os.path.exists(families_manifest):
        return lambda spec: None
    doc = json.loads(Path(families_manifest).read_text(encoding="utf-8"))
    cutoff = doc["spec"]["induction"]["induction_cutoff"]
    interval = (str(visible.get("from") or "")[:10], str(visible.get("to") or "")[:10])

    def build(spec):
        if not any(step.source is Source.PM_MARKET for step in spec.steps):
            return None
        return TaxonomyContamination(
            taxonomy_id=f"pm_candidate_families/{doc['spec']['version']}",
            taxonomy_freeze_at=cutoff,
            induction_corpus_max_date=cutoff,
            outcome_read_intervals=[interval],
        )

    return build


def _audit_input(sc: dict, visible: dict, target_record: dict):
    """构造语义审计员的输入。**逐字段从类型化对象取，不是过滤某个 payload。**"""
    wired = frozenset({Source.COMMODITY_BAR.value, Source.PM_MARKET.value})
    span = None
    if visible.get("from") and visible.get("to"):
        span = int(
            (datetime.fromisoformat(visible["to"]) - datetime.fromisoformat(visible["from"]))
            .total_seconds()
        )

    def build(feature, proposal):
        return AuditInput(
            feature=feature,
            target_record=target_record,
            proposal_direction=proposal.direction,
            falsifiable_condition=proposal.falsifiable_condition,
            wired_sources=wired,
            visible_span_seconds=span,
        )

    return build


def signal_correlations(ledger, sc: dict, rows: list[dict]) -> dict:
    """把这一族试过的全部特征放在同一批决策时点上两两求相关。

    **这一步不碰任何标签，因此不读 outcome，不进统计分母。**它回答的是
    「这些想法是不是同一个想法」—— 而同族变体高度相关时，零假设带的独立性假设
    最不成立。这张表就是「带偏严」那句告诫的量化形式。
    """
    from ..evaluation import stats
    from ..features.spec import FeatureSpec

    seen: dict[str, FeatureSpec] = {}
    for event in ledger.read_events(role=LedgerRole.HUMAN):
        if event["event_type"] != "feature_spec_locked":
            continue
        payload = event["payload"]
        usable = {k: v for k, v in payload.items() if k in FeatureSpec.model_fields}
        usable["steps"] = [Step(**step) for step in payload["steps"]]
        spec = FeatureSpec(**usable)
        seen.setdefault(spec.feature_id, spec)

    decision_times = [r["decision_time"] for r in rows]
    series: dict[str, list[float]] = {}
    for name, spec in seen.items():
        try:
            values, _ = evaluate_series(spec, decision_times, sc["series"])
        except NotInterpretable:
            continue
        defined = [v if v is not None else float("nan") for v in values]
        if any(math.isfinite(v) for v in defined):
            series[name] = defined
    if len(series) < 2:
        return {"defined": False, "reason": "可求值的特征少于两个", "features": len(series)}
    out = stats.correlation_matrix(series)
    out["defined"] = True
    out["decision_points"] = len(decision_times)
    out["effective_signals"] = stats.effective_independent_signals(out["matrix"])
    return out


def run_service_demo(
    *,
    ledger_path: str,
    queue_path: str,
    target_path: str,
    atlas_dir: str,
    manifest_dir: str = "artifacts/manifests",
    max_rounds: int = 24,
) -> dict:
    """连续研究：一轮接一轮，直到到达外部边界或停滞。不靠任何写死的变体表。"""
    from ..harness.service import AutoProposer, run_service
    from ..temporal.targets import TARGET_SPECS

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"缺少 SC 目标表 {target_path}；请先运行 spine build")
    for path in (ledger_path, queue_path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    rows, sc, visible = _load_sc(target_path)
    record = next(t.record() for t in TARGET_SPECS if t.name == LABEL_TARGET)
    now = datetime.now(UTC)
    with EvidenceLedger(ledger_path) as ledger, DurableQueue(queue_path) as queue:
        result = run_service(
            ledger=ledger, queue=queue,
            provider=AutoProposer(target_name=LABEL_TARGET),
            family=FAMILY, owner="auto-worker",
            assemble=_assembler(ledger, manifest_dir, visible),
            build_evaluation=_build_evaluation(sc, rows, visible),
            audit_input=_audit_input(sc, visible, record),
            contamination=_contamination(visible, FAMILIES_MANIFEST),
            seed_task={}, max_rounds=max_rounds, now=now,
        )
        # 相关矩阵：只比信号之间，不读 outcome
        correlations = signal_correlations(ledger, sc, rows)
        ledger.append("signal_correlation", correlations)
        projection = project(ledger, family=FAMILY, service=queue.service_state())
        paths = render_app(projection, atlas_dir, freshness=data_freshness(manifest_dir))
        return {
            "service": result.summary(),
            "signal_correlation": {
                k: correlations.get(k) for k in ("defined", "method", "names",
                                                 "mean_abs_offdiagonal")
            },
            "denominators": ledger.denominators(FAMILY),
            "ledger_events": ledger.require_intact(),
            "atlas": paths,
        }


def run_episode_demo(
    *,
    ledger_path: str,
    queue_path: str,
    target_path: str,
    atlas_dir: str,
    manifest_dir: str = "artifacts/manifests",
    provider_kind: str = "mock",
    model: str = "claude-opus-5",
) -> dict:
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"缺少 SC 目标表 {target_path}；请先运行 spine build")
    for path in (ledger_path, queue_path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    rows, sc, visible = _load_sc(target_path)
    now = datetime.now(UTC)
    provider, tasks = make_provider(provider_kind, model)
    with EvidenceLedger(ledger_path) as ledger, DurableQueue(queue_path) as queue:
        for i in range(tasks):
            queue.enqueue(f"demo-task-{i}", "study",
                          {"study_id": f"demo-study-{i}"}, now=now)
        result = run_episode(
            episode_id="demo-episode-1",
            schedule_next=_lineage_scheduler() if provider_kind == "lineage" else None,
            queue=queue,
            ledger=ledger,
            provider=provider,
            budget=EpisodeBudget(max_calls=12),
            family=FAMILY,
            owner="demo-worker",
            assemble=_assembler(ledger, manifest_dir, visible),
            build_evaluation=_build_evaluation(sc, rows, visible),
            audit_input=_audit_input(sc, visible, _label_target_record()),
            now=now,
        )
        projection = project(ledger, family=FAMILY, service=queue.service_state())
        paths = render_app(
            projection, atlas_dir, freshness=data_freshness(manifest_dir)
        )
        return {
            "episode": result.summary(),
            "rounds": [
                {"task": r.task_id, "outcome": r.outcome, "verdict": r.verdict}
                for r in result.rounds
            ],
            "provider": {"kind": provider_kind, "model": getattr(provider, "model_id", "")},
            "denominators": ledger.denominators(FAMILY),
            "ledger_events": ledger.require_intact(),
            "atlas": paths,
        }
