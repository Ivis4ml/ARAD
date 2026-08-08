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
from ..atlas.runs import write_run
from ..atlas.sources import data_freshness
from ..evaluation.kernel import EvaluationRequest, EvaluationRow, evaluate
from ..features.interpreter import INTERPRETER_VERSION, BarSeries, NotInterpretable, evaluate_series
from ..features.spec import FeatureSpec, Source, Step
from ..harness.audit import AuditInput
from ..harness.beam import Beam, Candidate, greedy_ensemble
from ..harness.context import DeclaredBias, assemble_proposer_context
from ..harness.episode import run_episode
from ..memory.ledger import EvidenceLedger
from ..memory.ledger import Role as LedgerRole
from ..orchestrator.queue import DurableQueue
from ..providers.base import EpisodeBudget, Provider
from ..providers.claude_cli import ClaudeCliProvider
from ..providers.mock import MockProvider
from ..registry.specs import TaxonomyContamination
from ..temporal.targets import TARGET_SPECS, specs_for


class UnknownTarget(RuntimeError):
    """提案声明的 target 没有已物化的目标表。"""


class UnknownUniverse(RuntimeError):
    """提案声明的 universe 解析不出品种清单。拒绝猜测。"""


def _label_target_record() -> dict:
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


#: `product` 是 `product_cluster` 的正确来源。原本切 `contract[:2]`，对单字母品种
#: 是错的（'a2601'[:2] == 'a2'）；'sc'[:2] == 'sc' 恰好正确，因此单品种下从未暴露。
_COLUMNS = ["product", "contract", "trading_day", "session_name", "decision_time",
            "label_start", "label_end", "value", "no_trade", "episode_id",
            "sample_segment"]


def _key(row: dict) -> str:
    return f"{row['contract']}:{row['trading_day']}:{row['session_name']}"


def _read_target(path: str, segment: str = SEGMENT) -> list[dict]:
    table = pq.read_table(path, columns=_COLUMNS)
    rows = [
        r for r in table.to_pylist()
        if r["sample_segment"] == segment and not r["no_trade"] and r["value"] is not None
    ]
    rows.sort(key=lambda r: r["label_end"])
    return rows


def built_products() -> list[str]:
    """已物化 spine 的品种，按品种名排序。

    只看盘面上真有的东西：M8.1 登记了 72 个品种，实际建成 51 个
    （21 个郑商所卡在交易所 TradingDay 约定差异上，见阻塞事项 10）。
    菜单必须反映真实可用的东西，否则「自主选择」变成在一张有一半是空头支票的表上选。
    """
    root = Path("data/spine")
    if not root.exists():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name == "controls":
            continue
        if (d / f"target_{d.name}_{LABEL_TARGET[3:]}.parquet").exists():
            out.append(d.name)
    return out


def _product_target_path(product: str, target_name: str) -> str:
    return str(Path("data/spine") / product / f"target_{target_name}.parquet")


def universe_members(universe: str) -> list[str]:
    """把 universe 名解析成品种清单。**不认识的名字直接报错，不猜。**

    两种形态：
    - `<品种>_dominant_t1`：单品种。`sc_dominant_t1` 是既有的那一个，取值不变；
    - `full_coverage_panel`：样本期内目标表满行的全部品种。成员资格是**数据可得性**
      规则，与任何结果无关，因此不构成结果依赖的选择；但它排除了样本期内退市或
      中途上市的品种，这一条是幸存者性质的，必须在证据里读得出来。
    """
    built = built_products()
    if universe == "full_coverage_panel":
        full = []
        for product in built:
            path = _product_target_path(product, f"{product}_{LABEL_TARGET[3:]}")
            if not os.path.exists(path):
                continue
            if pq.read_metadata(path).num_rows >= _FULL_COVERAGE_ROWS:
                full.append(product)
        return full
    if universe.endswith("_dominant_t1"):
        product = universe[: -len("_dominant_t1")]
        if product in built:
            return [product]
    raise UnknownUniverse(
        f"不认识的 universe {universe!r}；可用：full_coverage_panel 与 "
        f"{[p + '_dominant_t1' for p in built[:6]]}… 共 {len(built)} 个单品种"
    )


#: 「满覆盖」的行数门槛。sc 与 au 的目标表都是 1816 行（909 个交易日 × 2 个 session
#: 减去缺口），样本期内全程挂牌的品种都落在这个数上。
_FULL_COVERAGE_ROWS = 1816


def _load_sc(target_path: str, segment: str = SEGMENT) -> tuple[list[dict], dict, dict]:
    """读 M2 目标表的 discovery 段，构造 bar 序列、决策点与标签。

    **特征序列与标签来自两张不同的表**：特征用已实现波动（正的量级，取对数），
    标签用收益型 target（有符号）。两者按 (合约, 交易日, session) 对齐，
    只保留两边都有取值的行 —— 这个交集不依赖标签取值本身，因此不是结果依赖过滤。

    序列的可用时刻取每个 session 的 `label_end`：已实现波动只有在其窗口结束后才可知。
    决策时点严格晚于所用序列点，PIT 由构造保证，不靠检查。
    """
    feature_rows = [r for r in _read_target(target_path, segment) if r["value"] > 0]
    # **全部**已物化的 target 都载入，由模型在提案里选。此前只载 LABEL_TARGET，
    # 而菜单又只告诉模型 FEATURE_TARGET，于是模型预注册的是波动幅度的假设，
    # 系统检验的是收益方向（实测 12 条 Study 全部如此，两者秩相关 −0.05）。
    # 兄弟目标表按**品种**推路径，不按字符串替换。替换法只在 sc 上碰巧成立：
    # au 的表叫 `target_au_rv_next_session.parquet`，其中不含 `sc_rv_next_session`，
    # 于是三个 spec 会全部指向同一个文件而不报错。
    product = Path(target_path).parent.name
    labels_by_target: dict[str, dict] = {}
    for spec in specs_for(product):
        path = _product_target_path(product, spec.name)
        if os.path.exists(path):
            labels_by_target[spec.name] = {_key(r): r for r in _read_target(path, segment)}
    label_target = next(
        t.name for t in specs_for(product) if t.name.endswith(LABEL_TARGET[2:])
    )
    if label_target not in labels_by_target:
        raise FileNotFoundError(
            f"缺少收益型目标表 {_product_target_path(product, label_target)}；"
            "请先运行 `arad spine build`"
        )
    label_by_key = labels_by_target[label_target]

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
        "segment": segment,
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
                  "labels_by_target": labels_by_target,
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


#: 目标菜单允许出现的字段。**不含 `description`。**
#:
#: 目标描述是写给人看的散文，而散文正是效应词的老家：`sc_ret_next_session` 的描述里
#: 有「Sharpe 因此才有定义」，`sc_open_gap_absorption` 的描述里有「不作可交易 alpha
#: 主张」。M8.2 把菜单改成 `t.record()` 全量列出，于是这两个词进了提示词，
#: 盲化检查在**一次调用都没发出去之前**把整轮拦下（实测 run5 连续两轮 context_blocked）。
#: 模型选目标需要的是 label 语义，不是这段散文。
TARGET_MENU_FIELDS = (
    "name", "kind", "label_rule", "label_is_return", "tradable_claim",
    "execution_lag_seconds", "min_observations",
)


def _target_menu_entry(spec) -> dict:
    record = spec.record()
    entry = {k: record[k] for k in TARGET_MENU_FIELDS if k in record}
    entry.update({"horizon": "next_session", "segment": SEGMENT})
    return entry


def universe_menu() -> list[dict]:
    """可选的 universe。**只列真有 spine 的**，与机制族菜单同一条原则。

    每一项带够形成判断的信息：成员数、样本行数、以及成员资格是怎么定的。
    面板与单品种不是同一个研究对象：面板上一次评价是**一次**检验（判决由单一汇总
    估计量导出），逐品种各评一次是 N 次 —— 两者不得混用，先跑面板再看逐品种、
    报告其中最好的那个，是事后检验。
    """
    built = built_products()
    panel = universe_members("full_coverage_panel")
    out = [{
        "universe": "full_coverage_panel",
        "products": len(panel),
        "members": panel,
        "membership_rule": (
            f"目标表满 {_FULL_COVERAGE_ROWS} 行的品种。这是**数据可得性**规则，"
            "与任何结果无关；但它排除了样本期内退市或中途上市的品种，"
            "这一条是幸存者性质的"
        ),
        "note": (
            "唯一能做截面推断的形态：截面统计量要求同一时点上有多个可排序标的。"
            "双向 cluster 的品种维在这里才有内容 —— 单品种下它恒为一组并退化"
        ),
    }]
    out += [{
        "universe": f"{p}_dominant_t1",
        "products": 1,
        "members": [p],
        "membership_rule": "单品种主力视图",
        "note": "截面统计量无定义；双向 cluster 的品种维退化为一组",
    } for p in built]
    return out


def _load_product(product: str, segment: str = SEGMENT):
    """按品种装载一份 spine。返回 (pack, rows)，与 `_load_sc` 的形状一致。"""
    feature_target = next(
        t.name for t in specs_for(product) if t.name.endswith(FEATURE_TARGET[2:])
    )
    rows, pack, _visible = _load_sc(_product_target_path(product, feature_target), segment)
    return pack, rows


def _collect(spec, rows, values, times, eval_rows, authoritative, exclusions) -> None:
    """把一个品种的求值结果并入面板。逐行的 PIT 由构造保证，不靠检查。"""
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
                # 多品种下这一维才有内容。单品种时它恒为一组，双向 cluster 退化，
                # 而那条理由出现在此前**每一条**判决里。
                product_cluster=row["product"],
                decision_time=row["decision_time"],
                label_start=row["label_start"],
                availability_times={"commodity_bar": times[idx]},
                prediction=value,
                controls={"trading_day_parity": float(int(row["trading_day"]) % 2)},
            )
        )


def _build_evaluation(sc: dict, rows: list[dict], visible: dict,
                      loader=None, default_universe: str = "sc_dominant_t1"):
    """返回 harness 需要的 build_evaluation 回调。

    `loader(product)` 按品种装载 spine，缺省时只有 `default_universe` 那一个品种，
    即传进来的 `sc` 与 `rows`。提案声明多品种 universe 时，特征**逐品种**求值 ——
    每个品种有自己的 session 表、自己的决策时点、自己的 bar 序列，
    把它们混在一条序列上求值会算出一个不属于任何品种的数。求值之后再汇集成面板。
    """
    packs = {default_universe.replace("_dominant_t1", ""): (sc, rows)}

    def _pack(product: str):
        if product not in packs:
            if loader is None:
                raise UnknownUniverse(
                    f"未提供多品种装载器，无法求值品种 {product!r}"
                )
            packs[product] = loader(product)
        return packs[product]

    def build(spec: FeatureSpec, study_id: str, proposal=None):
        # **标签由提案声明的 target 决定。**此前写死用 LABEL_TARGET，而菜单又只告诉
        # 模型 FEATURE_TARGET，于是预注册的是波动幅度的假设、检验的是收益方向。
        # 目标名带品种（`sc_ret_next_session`），而面板要跨品种，因此这里按**后缀**
        # 解析：`ret_next_session` 是目标族名，每个品种贡献自己的那张表。
        # 不这样做，面板会用 sc 的键去查其余品种的标签，把它们全部过滤掉 ——
        # 实测面板与单品种给出**同样的 926 行、同样的 1 个品种簇**，看起来像在工作。
        target_name = (getattr(proposal, "target", None) or LABEL_TARGET)
        suffix = target_name.split("_", 1)[1] if "_" in target_name else target_name
        record = next(
            (t.record() for t in TARGET_SPECS if t.name.endswith(suffix)), None
        )
        if record is None:
            raise UnknownTarget(
                f"提案声明的 target {target_name!r} 解析不出目标族；"
                f"可用后缀：{[t.name.split('_', 1)[1] for t in TARGET_SPECS]}"
            )
        universe = getattr(proposal, "universe", None) or default_universe
        members = universe_members(universe)
        eval_rows, authoritative, exclusions = [], [], {}
        coverage: dict = {}
        chosen_labels: dict[str, float] = {}
        for product in members:
            pack, prows = _pack(product)
            per_product_target = f"{product}_{suffix}"
            table = pack.get("labels_by_target", {}).get(per_product_target)
            if table is None:
                raise UnknownTarget(
                    f"品种 {product!r} 没有已物化的 {per_product_target!r}；"
                    f"可用：{sorted(pack.get('labels_by_target', {}))}"
                )
            chosen_labels.update(
                {k: v["value"] for k, v in table.items() if v.get("value") is not None}
            )
            pseries = pack["series"]
            times = pseries[(Source.COMMODITY_BAR, "realised_volatility")].times
            decision_times = [r["decision_time"] for r in prows]
            values, cov = evaluate_series(spec, decision_times, pseries)
            coverage[product] = cov
            _collect(spec, prows, values, times, eval_rows, authoritative, exclusions)
        coverage = coverage.get(members[0], {}) if len(members) == 1 else {
            "per_product": coverage, "products": len(members)
        }
        eval_rows = [r for r in eval_rows if r.row_key in chosen_labels]
        authoritative = [k for k in authoritative if k in chosen_labels]
        detail = {**visible, "feature_coverage": coverage,
                  "evaluated_target": target_name}
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
            label_is_return=bool(record and record.get("label_is_return")),
            target_name=target_name,
            label_rule=(record or {}).get("label_rule", ""),
            periods_per_year=sc.get("periods_per_year") or 485.3,
        )
        return request, chosen_labels, detail

    return build


def _assembler(ledger: EvidenceLedger, manifest_dir: str, visible: dict, sc: dict):
    menu = _menu(manifest_dir, visible)

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
            # **全部已物化的 target 都列出来，由模型自己选。**
            # 此前只列 sc_rv_next_session，而评价机用的是 sc_ret_next_session：
            # 模型预注册的是波动幅度的假设，系统检验的是收益方向。
            # 每一项如实带上 label 语义，选哪个是模型的经济判断。
            targets=[_target_menu_entry(t) for t in TARGET_SPECS
                     if t.name in sc.get("labels_by_target", {})],
            menu=menu,
            universes=universe_menu(),
            menu_biases=MENU_BIASES,
            budget_facts={"note": "预算耗尽只结束 Episode，Research Service 不停"},
            blockers=[
                # 这条此前写着「pm_market 尚未接入」，而它在 M5.2 就接入了，
                # 菜单同时列着 30 个族 —— 提示词自相矛盾。陈述现状，不留旧话。
                "已接入 commodity_bar 与 pm_market；cls_telegraph 尚未接入",
                "无成本与容量模型（属 M5），因此本轮不可能取 candidate",
                "residualise 的控制序列目前只有 brent 与 own_realised_volatility 两条",
            ],
            # 累积的语义错配码。任务载荷是唯一对所有 provider 都成立的通路：
            # provider 属性那条路只有确定性变异器走得通
            learned_mismatches=tuple(task["payload"].get("learned_mismatches") or ()),
        )

    return assemble


def _menu(manifest_dir: str, visible: dict | None = None) -> list[dict]:
    """候选机制族的菜单。

    **只列实际有序列的族。**此前按 manifest 的成交量取前 N 个，其中有些根本没有物化
    序列，模型提了也求不了值 —— 菜单必须反映真实可用的东西，否则「自主选择」变成
    在一张有一半是空头支票的表上选。

    每一项带够形成经济假设的信息：token（这个族在讲什么）、市场数与名义额（有多少人
    在上面下注）、覆盖起点（多早开始有数据）。**不做任何「哪个族关联原油」的暗示** ——
    那是提案器要下的判断，也是它要被证伪的地方。菜单里同时有体育与加密族，
    它们是天然的安慰剂对照：若某支球队的关注度「预测」了原油，整个信号都该被怀疑。
    """
    path = Path(manifest_dir) / "pm_candidate_families.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    tokens = {f["family_id"]: f for f in doc.get("families", [])}
    available = {f["family_id"]: f for f in (visible or {}).get("pm_families", [])}
    out = []
    for family_id, series in available.items():
        meta = tokens.get(family_id, {})
        out.append({
            "family_id": family_id,
            "head_tokens": meta.get("head_tokens", []),
            "markets": meta.get("markets"),
            "trades": meta.get("trades"),
            "notional_usdc": round(series.get("notional", 0.0)),
            "series_from": series.get("from", "")[:10],
            "buckets": series.get("buckets"),
            "fields": [f"{family_id}:{k}" for k in ("p", "notional", "trades")],
        })
    out.sort(key=lambda f: -(f["notional_usdc"] or 0))
    return out


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
    """构造语义审计员的输入。**逐字段从类型化对象取，不是过滤某个 payload。**

    `target_record` 按**提案声明的** target 取，不是按装配方写死的那一个。
    否则审计员比对的是特征与另一个目标的语义：实测中模型被告知目标是已实现波动、
    据此提出幅度型特征（对波动目标完全正确），却因为审计员拿的是收益型目标的记录
    而被判「幅度对方向」，连续七轮。模型是对的，是框架在目标上对它说了假话。
    """
    wired = frozenset({Source.COMMODITY_BAR.value, Source.PM_MARKET.value})
    span = None
    if visible.get("from") and visible.get("to"):
        span = int(
            (datetime.fromisoformat(visible["to"]) - datetime.fromisoformat(visible["from"]))
            .total_seconds()
        )

    def build(feature, proposal):
        record = target_record
        declared = getattr(proposal, "target", None)
        if declared:
            record = next(
                (t.record() for t in TARGET_SPECS if t.name == declared), target_record
            )
        return AuditInput(
            feature=feature,
            target_record=record,
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


def _alpha_cards(ledger, beam_members: list[dict], sealed: list[dict],
                 projection) -> list[dict]:
    """把束里的候选做成因子卡。代码由规格生成，因此说明与代码不可能各说各话。"""
    from ..features.spec import FeatureSpec
    from ..registry.alpha_card import AlphaCard

    sealed_by = {e["feature_id"]: e for e in sealed if "t_stat" in e}
    specs: dict[str, FeatureSpec] = {}
    spec_study: dict[str, str] = {}
    for event in ledger.read_events(role=LedgerRole.HUMAN):
        if event["event_type"] != "feature_spec_locked":
            continue
        payload = event["payload"]
        usable = {k: v for k, v in payload.items() if k in FeatureSpec.model_fields}
        usable["steps"] = [Step(**st) for st in payload["steps"]]
        specs.setdefault(payload["feature_id"], FeatureSpec(**usable))
        spec_study.setdefault(payload["feature_id"], event["study_id"] or "")

    by_study = {st["study_id"]: st for st in projection.studies}
    cards: list[dict] = []
    for member in beam_members:
        spec = specs.get(member["feature_id"])
        if spec is None:
            continue
        study = by_study.get(spec_study.get(spec.feature_id, ""), {})
        metrics = study.get("metrics", {})
        seal = sealed_by.get(spec.feature_id)
        card = AlphaCard(
            spec=spec,
            mechanism=(study.get("mechanism") or spec.mechanism),
            discovery={"t_stat": metrics.get("t_stat"),
                       "ic_spearman": metrics.get("ic_spearman"),
                       "rows": metrics.get("rows_submitted"),
                       "study_id": study.get("study_id")},
            sealed=({"t_stat": seal["t_stat"], "ic_spearman": seal["ic_spearman"],
                     "rows": seal["rows"], "segment": seal["segment"]} if seal else None),
            taxonomy_clean=bool(seal and seal.get("taxonomy_clean")),
            family=FAMILY,
        )
        cards.append(card.payload())
    return cards


def _write_cards(cards: list[dict], atlas_dir: str) -> None:
    """卡片另存一份可直接拿走的产物：说明是 markdown，代码是可运行的 .py。"""
    root = os.path.join(atlas_dir, "cards")
    os.makedirs(root, exist_ok=True)
    for card in cards:
        stem = card["feature_id"][:80]
        Path(os.path.join(root, f"{stem}.py")).write_text(card["code"], encoding="utf-8")
        lines = [
            f"# {card['feature_id']}", "",
            f"- 状态：`{card['status']}`　分类法干净：{card['taxonomy_clean']}",
            f"- 数据源：{', '.join(card['sources'])}",
            f"- 内容身份：`{card['content_id']}`", "",
            "## 这个因子意味着什么", "", card["meaning"], "",
            "## 公式", "", "```",
            *card["formula"], "```", "",
            "## 失败条件", "", card["failure_condition"], "",
            "## 代码", "",
            (f"见同目录 `{stem}.py`，由 `arad.features.codegen` 从冻结规格确定性生成；"
             "有合同测试钉死它与解释器逐位相同。"),
        ]
        Path(os.path.join(root, f"{stem}.md")).write_text(
            "\n".join(lines) + "\n", encoding="utf-8")


def _signal_values(ledger, sc: dict, rows: list[dict],
                   feature_ids: list[str]) -> dict[str, list[float]]:
    """把指定特征在同一批决策时点上求值。不碰标签。"""
    from ..features.spec import FeatureSpec

    want = set(feature_ids)
    specs: dict[str, FeatureSpec] = {}
    for event in ledger.read_events(role=LedgerRole.HUMAN):
        if event["event_type"] != "feature_spec_locked":
            continue
        payload = event["payload"]
        if payload["feature_id"] not in want:
            continue
        usable = {k: v for k, v in payload.items() if k in FeatureSpec.model_fields}
        usable["steps"] = [Step(**st) for st in payload["steps"]]
        specs.setdefault(payload["feature_id"], FeatureSpec(**usable))
    decision_times = [r["decision_time"] for r in rows]
    out: dict[str, list[float]] = {}
    for name, spec in specs.items():
        try:
            values, _ = evaluate_series(spec, decision_times, sc["series"])
        except NotInterpretable:
            continue
        out[name] = [v if v is not None else float("nan") for v in values]
    return out


def sealed_pass(
    ledger, *, target_path: str, families_manifest: str, top_features: list[str],
    segment: str = "historical_validation",
) -> list[dict]:
    """封闭段评估：**每个特征只开一次**。

    取自 LBG 的纪律 —— 预算用尽后封闭段恰好开启一次，提案器全程不接触它。
    这里把它变成结构性的：同一个 (规格, 段) 想开第二次会被账本拒绝。

    并列记两件事而不是一件：时间上的样本外（任何 target 都成立）与分类法上的干净
    （对 PM 族当前**不成立**，归纳切点 2026-08-01 覆盖了手上全部三段）。
    """
    from ..evaluation.sealed import SealedAlreadyOpened, open_sealed
    from ..features.spec import FeatureSpec

    rows, sc, visible = _load_sc(target_path, segment)
    build = _build_evaluation(sc, rows, visible)
    contaminate = _contamination(visible, families_manifest)

    specs: dict[str, FeatureSpec] = {}
    for event in ledger.read_events(role=LedgerRole.HUMAN):
        if event["event_type"] != "feature_spec_locked":
            continue
        payload = event["payload"]
        usable = {k: v for k, v in payload.items() if k in FeatureSpec.model_fields}
        usable["steps"] = [Step(**st) for st in payload["steps"]]
        spec = FeatureSpec(**usable)
        specs.setdefault(spec.feature_id, spec)

    out: list[dict] = []
    for feature_id in top_features:
        spec = specs.get(feature_id)
        if spec is None:
            continue
        try:
            request, labels, detail = build(spec, f"sealed:{feature_id}")
        except NotInterpretable as exc:
            out.append({"feature_id": feature_id, "skipped": str(exc)[:120]})
            continue
        if request is None:
            out.append({"feature_id": feature_id, "skipped": "封闭段上定义点过少",
                        "coverage": detail.get("feature_coverage")})
            continue
        result = evaluate(request, labels, role="evaluator")
        try:
            verdict = open_sealed(
                ledger, feature_id=feature_id, segment=segment,
                result={k: result[k] for k in ("coverage", "effects", "blocked_reasons",
                                               "suggested_verdict")},
                contamination=contaminate(spec),
            )
        except SealedAlreadyOpened as exc:
            out.append({"feature_id": feature_id, "refused": str(exc)[:120]})
            continue
        out.append({
            "feature_id": feature_id,
            "segment": segment,
            "t_stat": result["effects"]["t_stat"] if result["effects"] else None,
            "ic_spearman": (result["effects"] or {}).get("ic", {}).get("ic_spearman"),
            "rows": result["coverage"]["rows_submitted"],
            "out_of_sample_in_time": verdict.out_of_sample_in_time,
            "taxonomy_clean": verdict.taxonomy_clean,
        })
    return out


def run_service_demo(
    *,
    ledger_path: str,
    queue_path: str,
    target_path: str,
    atlas_dir: str,
    manifest_dir: str = "artifacts/manifests",
    max_rounds: int = 24,
    runs_root: str = "runs",
    run_id: str | None = None,
    provider_kind: str = "mutator",
    model: str = "claude-opus-5",
) -> dict:
    """连续研究：一轮接一轮，直到到达外部边界或停滞。不靠任何写死的变体表。"""
    from ..harness.service import AutoProposer, run_service

    if not os.path.exists(target_path):
        raise FileNotFoundError(f"缺少 SC 目标表 {target_path}；请先运行 spine build")
    for path in (ledger_path, queue_path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    # 运行标识必须在 run_service 之前定下来。时间戳兜底原本写在函数末尾（只为 Atlas
    # 的运行目录命名），于是 `--run-id` 缺省时 run_service 拿到的是 None，
    # 任务标识变成恒定的 "None-task-0"，M7.2 要修的冲突原样回来。
    run_id = run_id or datetime.now(UTC).strftime("run_%Y%m%d_%H%M%S")
    rows, sc, visible = _load_sc(target_path)
    record = next(t.record() for t in TARGET_SPECS if t.name == LABEL_TARGET)
    now = datetime.now(UTC)
    with EvidenceLedger(ledger_path) as ledger, DurableQueue(queue_path) as queue:
        provider = (
            AutoProposer(target_name=LABEL_TARGET) if provider_kind == "mutator"
            else ClaudeCliProvider(model_id=model)
        )
        result = run_service(
            ledger=ledger, queue=queue,
            provider=provider,
            family=FAMILY, owner="auto-worker",
            assemble=_assembler(ledger, manifest_dir, visible, sc),
            build_evaluation=_build_evaluation(sc, rows, visible, loader=_load_product),
            audit_input=_audit_input(sc, visible, record),
            contamination=_contamination(visible, FAMILIES_MANIFEST),
            seed_task={}, max_rounds=max_rounds, now=now,
            # 队列与账本跨运行持久，标识必须带上运行 id：否则第二次运行的
            # `auto-task-1` 在上一次里已经是 done，入队成空操作，服务一轮就停
            run_id=run_id,
        )
        # 相关矩阵：只比信号之间，不读 outcome
        correlations = signal_correlations(ledger, sc, rows)
        ledger.append("signal_correlation", correlations)

        # 束：按 reward（越过噪声地板多少）排，不按原始 |t| 排
        beam = Beam(width=4)
        proj = project(ledger, family=FAMILY)
        tests_at = {c["study_id"]: c["tests_so_far"]
                    for chain in proj.lineage for c in chain["curves"]["abs_t"]}
        by_study = {st["study_id"]: st for st in proj.studies}
        for study_id, study in by_study.items():
            spec_id = next(
                (e["payload"]["feature_id"]
                 for e in ledger.read_events(role=LedgerRole.HUMAN, study_id=study_id)
                 if e["event_type"] == "feature_spec_locked"), None,
            )
            if spec_id is None:
                continue
            beam.offer(Candidate(
                feature_id=spec_id, study_id=study_id,
                value=study["metrics"].get("abs_t"),
                tests_at_evaluation=tests_at.get(study_id, 1),
                source=study.get("source", ""),
            ))
        ledger.append("beam_state", beam.summary())

        # 封闭段：每个特征只开一次，提案器全程不接触
        sealed = sealed_pass(
            ledger, target_path=target_path, families_manifest=FAMILIES_MANIFEST,
            top_features=[m["feature_id"] for m in beam.summary()["members"]],
        )
        ledger.append("sealed_pass", {"entries": sealed})

        # 组合：在**发现段**上贪心前向选（低相关约束），这一步是选择，不是验证
        members = [m["feature_id"] for m in beam.summary()["members"]]
        signals = {
            name: values for name, values in _signal_values(ledger, sc, rows, members).items()
        }
        ensemble = greedy_ensemble(
            signals, [sc["labels"][_key(r)] for r in rows], max_size=3,
        ) if len(signals) >= 2 else {"constituents": [], "note": "可求值特征少于两个"}
        ledger.append("ensemble_selected", ensemble)

        # 因子卡：公式、意义、证据、以及由规格确定性生成的代码
        cards = _alpha_cards(ledger, beam.summary()["members"], sealed, proj)
        ledger.append("alpha_cards", {"cards": [c["feature_id"] for c in cards]})
        _write_cards(cards, atlas_dir)
        projection = project(ledger, family=FAMILY, service=queue.service_state())
        fresh = data_freshness(manifest_dir)
        paths = render_app(projection, atlas_dir, freshness=fresh)
        # 同一次运行同时落成 runs/<id>/：单文件那条路保留（不需要服务器），
        # 运行目录让独立 app 能看历史、能并排比较
        paths["run"] = write_run(
            projection, runs_root, run_id,
            events=ledger.read_events(role=LedgerRole.HUMAN),
            cards=cards, freshness=fresh,
        )["run_id"]
        return {
            "service": {**result.summary(), "provider": provider_kind},
            "beam": beam.summary()["members"],
            "cards": [{k: c[k] for k in ("feature_id", "status", "taxonomy_clean")}
                      for c in cards],
            "ensemble": {k: ensemble.get(k) for k in
                         ("constituents", "trajectory", "score", "rejected_for_correlation")},
            "sealed": sealed,
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
            assemble=_assembler(ledger, manifest_dir, visible, sc),
            build_evaluation=_build_evaluation(sc, rows, visible, loader=_load_product),
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
