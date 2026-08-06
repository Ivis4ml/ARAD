"""在真实 SC 数据上跑一次 Search Episode，并把账本渲染成 Atlas（M4 出口演示）。

这不是回测，也不承诺发现任何因子。它验证的是 M4 的出口条件：一次 Episode 能在
无人干预下走完「提案 → 冻结 → 特征 → 评价 → 判决 → 入账」，且全过程可从账本
回放为自包含快照并被 Atlas 讲清楚。

provider 用 `MockProvider` 而非 `claude -p`：演示要可重复、零调用成本，且不因网络
波动而失败。脚本刻意覆盖四种结局，因为它们都是第一版预期会大量出现的状态：

1. 一个用商品量价原语表达的提案 —— 走完整评价，判决由评价机出具；
2. 一条原语缺口声明 —— 现有语言表达不了某机制，这是有价值的产出；
3. 一个引用 `pm_market` 的提案 —— 解释器尚未接入该源，判 blocked 并请求人工复核。
   这正是当前真实状态：另类数据侧的取数尚未接通，把它演示成"能跑"才是伪造；
4. 连续三次无法解析的输出 —— 重试用尽后降级为 ParseFailure，任务退避重排不丢。

第一个提案是**量价**特征，属 Baseline Control，不计入 Alternative Factor Inventory
（Merge-Plan-2 §3.1）。之所以用它，是因为解释器目前只接了 `commodity_bar`；
用它演示环路，同时用第三个提案把真实缺口暴露出来。
"""

from __future__ import annotations

import json
import math
import os
from bisect import bisect_left
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

from ..atlas.project import project
from ..atlas.render import render_site
from ..atlas.sources import data_freshness
from ..evaluation.kernel import EvaluationRequest, EvaluationRow
from ..features.interpreter import BarSeries, evaluate_series
from ..features.spec import FeatureSpec, Source
from ..harness.context import DeclaredBias, assemble_proposer_context
from ..harness.episode import run_episode
from ..memory.ledger import EvidenceLedger
from ..orchestrator.queue import DurableQueue
from ..providers.base import EpisodeBudget
from ..providers.mock import MockProvider

FAMILY = "demo_sc_price_volume"
SEGMENT = "discovery"

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
        "feature_id": "sc_rv_innovation_3d_vs_20d",
        "mechanism": "SC 自身已实现波动的短期创新相对长期基线",
        "steps": [
            {"name": "rv_recent", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": 259200},
            {"name": "rv_baseline", "kind": "window", "source": "commodity_bar",
             "field": "realised_volatility", "op": "mean", "window_seconds": 1728000},
            {"name": "rv_innovation", "kind": "difference",
             "inputs": ["rv_recent", "rv_baseline"]},
        ],
        "output_step": "rv_innovation",
        "failure_condition": "若创新量与下一 session 已实现波动无关，则本特征被证伪",
        "authored_by": "llm_proposer",
    }
    return json.dumps(
        {
            "mechanism": "波动聚集：短期已实现波动高于长期基线时，下一 session 波动偏高",
            "source": "commodity_bar",
            "target": "sc_rv_next_session",
            "horizon": "next_session",
            "universe": "sc_dominant_t1",
            "direction": 1,
            "falsifiable_condition": "斜率不显著异于零，或置换检验不能把实际值与置换分布区分开",
            "rationale": "量价对照集：解释器当前只接入 commodity_bar，先用它检验环路本身",
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


def _load_sc(target_path: str) -> tuple[list[dict], dict, dict]:
    """读 M2 目标表的 discovery 段，构造 bar 序列与决策点。

    序列的可用时刻取每个 session 的 `label_end` —— 已实现波动只有在其窗口结束后
    才可知。决策时点严格晚于所用序列点，PIT 由构造保证，不靠检查。
    """
    table = pq.read_table(
        target_path,
        columns=["contract", "trading_day", "session_name", "decision_time",
                 "label_start", "label_end", "value", "no_trade", "episode_id",
                 "sample_segment"],
    )
    rows = [
        r for r in table.to_pylist()
        if r["sample_segment"] == SEGMENT and not r["no_trade"]
        and r["value"] is not None and r["value"] > 0
    ]
    rows.sort(key=lambda r: r["label_end"])
    series = {
        (Source.COMMODITY_BAR, "realised_volatility"): BarSeries(
            field="realised_volatility",
            times=[r["label_end"] for r in rows],
            values=[math.log(r["value"]) for r in rows],
        )
    }
    labels = {
        f"{r['contract']}:{r['trading_day']}:{r['session_name']}": math.log(r["value"])
        for r in rows
    }
    visible = {
        "segment": SEGMENT,
        "rows": len(rows),
        "from": rows[0]["label_end"].isoformat() if rows else None,
        "to": rows[-1]["label_end"].isoformat() if rows else None,
        "forward_data": "未读取：forward 段按 Study 逐个到期，Atlas 中只显示预约状态",
    }
    return rows, {"series": series, "labels": labels}, visible


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
            key = f"{row['contract']}:{row['trading_day']}:{row['session_name']}"
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
        )
        return request, labels, detail

    return build


def _assembler(ledger: EvidenceLedger, manifest_dir: str, visible: dict):
    menu = _menu(manifest_dir)

    def assemble(task: dict):
        return assemble_proposer_context(
            ledger=ledger,
            family=FAMILY,
            data_facts={"sources": data_freshness(manifest_dir), "visible": visible},
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


def run_episode_demo(
    *,
    ledger_path: str,
    queue_path: str,
    target_path: str,
    atlas_dir: str,
    manifest_dir: str = "artifacts/manifests",
) -> dict:
    if not os.path.exists(target_path):
        raise FileNotFoundError(f"缺少 SC 目标表 {target_path}；请先运行 spine build")
    for path in (ledger_path, queue_path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    rows, sc, visible = _load_sc(target_path)
    now = datetime.now(UTC)
    scripts = [
        _proposal_json(), _gap_json(), _pm_proposal_json(),
        "这不是 JSON", "还是不是 JSON", "仍然不是 JSON",
    ]
    with EvidenceLedger(ledger_path) as ledger, DurableQueue(queue_path) as queue:
        for i in range(4):
            queue.enqueue(f"demo-task-{i}", "study",
                          {"study_id": f"demo-study-{i}"}, now=now)
        result = run_episode(
            episode_id="demo-episode-1",
            queue=queue,
            ledger=ledger,
            provider=MockProvider(scripts={"proposer": scripts}),
            budget=EpisodeBudget(max_calls=12),
            family=FAMILY,
            owner="demo-worker",
            assemble=_assembler(ledger, manifest_dir, visible),
            build_evaluation=_build_evaluation(sc, rows, visible),
            now=now,
        )
        projection = project(ledger, family=FAMILY, service=queue.service_state())
        paths = render_site(
            projection, atlas_dir, freshness=data_freshness(manifest_dir)
        )
        return {
            "episode": result.summary(),
            "rounds": [
                {"task": r.task_id, "outcome": r.outcome, "verdict": r.verdict}
                for r in result.rounds
            ],
            "denominators": ledger.denominators(FAMILY),
            "ledger_events": ledger.require_intact(),
            "atlas": paths,
        }
