"""Atlas 投影：把账本折叠成可渲染的结构（M9 第一部分）。

决定 0003 的三条边界在这一层就要成立，渲染层只是把结构变成 HTML：

1. **只读投影。**这里只有 SELECT，没有任何写入路径；产物是静态文件。
   HTML 写不了账本 —— 与 events 表上的 UPDATE/DELETE 触发器是同一种论证：
   边界是物理的，不是承诺出来的。
2. **尊重能力隔离。**forward 段的数据与标签在 Atlas 里同样不可见，
   只显示"预约待裁决"。
3. **不重算。**每个数字都从账本里存着的 payload 原样读出。这一层没有 import 任何
   统计模块，因此"前端偷偷算一个 t 值"在结构上做不到。

三个容易踩空的映射问题，都在这里处理掉：

- **没有 study_id 的事件不能被丢掉。**原语缺口声明与 Episode 起讫本来就不属于任何
  Study。按 study_id 分组会让它们整批消失，而第一版恰恰以缺口声明为主要产出。
  它们进 Episode 层，单独成节。
- **有 study_id 不等于存在 Study。**解析失败的那一轮带着 study_id 入账，
  但它没有 `study_created`、没有提案、没有判决。用 `study_created` 判别，
  否则这些本属预期的中止轮会被当成账本缺口报出来。
- **以 human 角色读账本。**proposer 视图会递归遮蔽效果字段，而快照层的存在意义
  正是呈现逐项结果。Atlas 要守的边界是 forward 不可见，不是效果字段遮蔽。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..evaluation.selection import selection_band
from ..memory.ledger import EvidenceLedger, Role
from ..memory.snapshot import collect_snapshot, require_complete
from ..registry.specs import Verdict

ATLAS_VERSION = "0.1.0"

#: 不属于任何 Study、但必须出现在 Episode 层的事件。
#: `proposal_recorded` 刻意不在其中：它是分母的记账副本，总览层的两本分母已经完整
#: 呈现同一信息，逐条列出只会淹没真正需要人看的缺口声明与故障。
EPISODE_SCOPED_EVENTS = ("primitive_gap_declared", "provider_error", "invalid_proposal")

#: 事件类型到时间线标签的映射。渲染层不认识事件类型，只认识标签。
TIMELINE_LABELS = {
    "context_assembled": "组装盲化上下文",
    "proposal_locked": "提案入账（计入 proposal denominator）",
    "hypothesis_locked": "Hypothesis Lock 冻结（读 outcome 之前）",
    "confirmatory_locked": "Confirmatory Lock 冻结（预注册对抗诊断）",
    "study_created": "Study 建立",
    "feature_spec_locked": "特征规格冻结",
    "visible_data_range": "记录当时可见的数据范围",
    "outcome_read": "读取 outcome（计入 statistical denominator）",
    "evaluation_result": "评价机出具结构化结果",
    "verdict_recorded": "判决入账",
    "parse_failure": "输出无法解析为结构化提案",
    "interpretation_gap": "解释器尚不能求值该规格（数据源或步骤类型缺口）",
    "primitive_gap_declared": "声明原语缺口",
    "provider_error": "provider 调用故障",
    "invalid_proposal": "提案缺必填字段",
    "context_blocked": "上下文组装泄漏效果字段，调用被拒绝",
    "provider_repair": "模型首次输出不合规，已按修复提示重试",
}


@dataclass
class AtlasProjection:
    """一次投影的全部内容。渲染层不再回头读账本。"""

    chain: dict
    denominators: dict
    verdicts: dict[str, int]
    coverage: list[dict]
    episodes: list[dict] = field(default_factory=list)
    studies: list[dict] = field(default_factory=list)
    aborted_rounds: list[dict] = field(default_factory=list)
    lineage: list[dict] = field(default_factory=list)
    service: dict | None = None
    atlas_version: str = ATLAS_VERSION

    def to_dict(self) -> dict:
        return {
            "atlas_version": self.atlas_version,
            "chain": self.chain,
            "service": self.service,
            "denominators": self.denominators,
            "verdicts": self.verdicts,
            "coverage": self.coverage,
            "episodes": self.episodes,
            "studies": self.studies,
            "aborted_rounds": self.aborted_rounds,
            "lineage": self.lineage,
            "curve_metrics": list(CURVE_METRICS),
        }

    @property
    def totals(self) -> dict:
        return {
            "studies": len(self.studies),
            "episodes": len(self.episodes),
            "aborted_rounds": len(self.aborted_rounds),
            "primitive_gaps": sum(
                1
                for ep in self.episodes
                for e in ep["events"]
                if e["event_type"] == "primitive_gap_declared"
            ),
        }


def _timeline(events: list[dict]) -> list[dict]:
    return [
        {
            "seq": e["seq"],
            "at": e["created_at"],
            "event_type": e["event_type"],
            "label": TIMELINE_LABELS.get(e["event_type"], e["event_type"]),
        }
        for e in events
    ]


def _group_by_study(events: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for event in events:
        if event["study_id"]:
            grouped.setdefault(event["study_id"], []).append(event)
    return grouped


def _project_episodes(events: list[dict]) -> tuple[list[dict], list[dict]]:
    """按 episode_started / episode_ended 切段。无归属的事件不丢，进 orphan 段。"""
    episodes: list[dict] = []
    orphans: list[dict] = []
    current: dict | None = None
    for event in events:
        kind = event["event_type"]
        if kind == "episode_started":
            current = {
                "episode_id": event["payload"].get("episode_id", "unknown"),
                "family": event["payload"].get("family", ""),
                "started_at": event["created_at"],
                "budget_at_start": event["payload"].get("budget", {}),
                "ended_at": None,
                "summary": None,
                "events": [],
                "studies": [],
            }
            episodes.append(current)
            continue
        if kind == "episode_ended":
            if current is not None:
                current["ended_at"] = event["created_at"]
                current["summary"] = event["payload"]
                current = None
            continue
        if event["study_id"]:
            if current is not None and event["study_id"] not in current["studies"]:
                current["studies"].append(event["study_id"])
            continue
        if kind not in EPISODE_SCOPED_EVENTS:
            continue
        record = {
            "seq": event["seq"],
            "at": event["created_at"],
            "event_type": kind,
            "label": TIMELINE_LABELS.get(kind, kind),
            "payload": event["payload"],
        }
        (current["events"] if current is not None else orphans).append(record)
    return episodes, orphans


def _project_study(
    study_id: str, events: list[dict], denominators: dict, *, strict: bool
) -> dict:
    snapshot = collect_snapshot(events, denominators)
    if strict:
        # 决定 0003 的附带价值：拼不出完整快照即账本缺口，按 bug 处理。
        # 这里刻意不捕获 SnapshotIncomplete —— 吞掉它就等于把账本缺口渲染成半页。
        require_complete(snapshot)
    verdict = snapshot.get("verdict") or {}
    proposal = snapshot.get("proposal") or {}
    hypothesis = snapshot.get("hypothesis_lock") or {}
    study = snapshot.get("study") or {}
    return {
        "study_id": study_id,
        "parent_study_id": study.get("parent_study_id"),
        "change_summary": study.get("change_summary", ""),
        "created_at": study.get("created_at", ""),
        "metrics": _metrics(snapshot),
        "verdict": verdict.get("verdict", ""),
        "next_action": verdict.get("next_action", ""),
        "rationale": verdict.get("rationale", ""),
        "decided_at": verdict.get("decided_at", ""),
        "family": hypothesis.get("experiment_family", ""),
        "source": proposal.get("source", ""),
        "horizon": proposal.get("horizon", ""),
        "mechanism": proposal.get("mechanism", ""),
        "forward_reserved": verdict.get("next_action") == "queue_forward",
        "timeline": _timeline(events),
        "snapshot": snapshot,
    }


#: 只组装了上下文就结束的轮次：它的产出不属于任何 Study，记在 Episode 层。
_CONTEXT_ONLY = {"context_assembled"}


#: 曲线上可选的纵轴。全部来自评价机存下的 payload，Atlas 不重算。
CURVE_METRICS = ("abs_t", "ic_spearman", "sharpe")


def _metrics(snapshot: dict) -> dict:
    """从判决快照里取出曲线要用的量。取不到就是 None，不补默认值。"""
    evaluation = snapshot.get("evaluation") or {}
    effects = evaluation.get("effects") or {}
    ic = effects.get("ic") or {}
    performance = effects.get("performance") or {}
    coverage = evaluation.get("coverage") or {}
    diagnostics = evaluation.get("diagnostics") or {}
    t_stat = effects.get("t_stat")
    return {
        "abs_t": abs(t_stat) if isinstance(t_stat, (int, float)) else None,
        "t_stat": t_stat,
        "slope": effects.get("slope"),
        "mde_at_2p8_se": effects.get("mde_at_2p8_se"),
        "ic_spearman": ic.get("ic_spearman"),
        "ic_kind": ic.get("kind"),
        "sharpe": performance.get("sharpe"),
        "sharpe_annualised": performance.get("sharpe_annualised"),
        "sharpe_undefined_reason": performance.get("sharpe_undefined_reason"),
        "skew": performance.get("skew"),
        "excess_kurtosis": performance.get("excess_kurtosis"),
        "periods_per_year": performance.get("periods_per_year"),
        "rows_submitted": coverage.get("rows_submitted"),
        "episodes": coverage.get("episodes"),
        "placebo_exceed_rate": (diagnostics.get("placebo") or {}).get("placebo_exceed_rate"),
        "outcome_reads": len(snapshot.get("outcome_reads") or []),
    }


def _lineage(studies: list[dict]) -> list[dict]:
    """按 parent_study_id 把 Study 串成演化链。

    没有父子关系时每个 Study 自成一条长度为 1 的链 —— 那是如实的："它们之间
    没有继承关系"。把它们按时间连成一条线会让读图的人以为看到了演化。
    """
    by_id = {s["study_id"]: s for s in studies}
    children: dict[str | None, list[str]] = {}
    for study in studies:
        parent = study["parent_study_id"] if study["parent_study_id"] in by_id else None
        children.setdefault(parent, []).append(study["study_id"])

    chains: list[dict] = []

    def walk(node: str, path: list[str]) -> None:
        path = [*path, node]
        kids = sorted(children.get(node, []))
        if not kids:
            chains.append({"chain_id": path[0], "study_ids": path})
            return
        for kid in kids:
            walk(kid, path)

    for root in sorted(children.get(None, [])):
        walk(root, [])
    return chains


def _curve(chain: list[dict], metric: str) -> list[dict]:
    """一条链的曲线数据：每点的值、running best、零假设带。"""
    points = [
        {
            "study_id": s["study_id"],
            "verdict": s["verdict"],
            "change_summary": s["change_summary"],
            "value": s["metrics"].get(metric),
            "counts_toward_denominator": bool(s["metrics"].get("outcome_reads")),
            "skew": s["metrics"].get("skew"),
            "excess_kurtosis": s["metrics"].get("excess_kurtosis"),
        }
        for s in chain
    ]
    rows = [s["metrics"].get("rows_submitted") for s in chain]
    defined = [r for r in rows if isinstance(r, int)]
    return selection_band(
        points, metric=metric, n_periods=min(defined) if defined else None
    )


def _project_aborted(study_id: str, events: list[dict]) -> dict:
    last = events[-1]
    kinds = {e["event_type"] for e in events}
    reason = (
        "未建立 Study：本轮产出不属于任何 Study，记在 Episode 层（如原语缺口声明）"
        if kinds <= _CONTEXT_ONLY
        else TIMELINE_LABELS.get(last["event_type"], last["event_type"])
    )
    return {
        "study_id": study_id,
        "reason": reason,
        "event_type": last["event_type"],
        "at": last["created_at"],
        "detail": last["payload"],
        "timeline": _timeline(events),
    }


def _coverage(studies: list[dict]) -> list[dict]:
    """库存覆盖：机制族 × 数据源 × 时域。计数来自判决，不重算任何东西。"""
    cells: dict[tuple[str, str, str], dict] = {}
    for study in studies:
        key = (study["family"], study["source"], study["horizon"])
        cell = cells.setdefault(
            key,
            {
                "family": key[0],
                "source": key[1],
                "horizon": key[2],
                "studies": 0,
                "verdicts": {},
            },
        )
        cell["studies"] += 1
        v = study["verdict"] or "unknown"
        cell["verdicts"][v] = cell["verdicts"].get(v, 0) + 1
    return sorted(cells.values(), key=lambda c: (c["family"], c["source"], c["horizon"]))


def project(
    ledger: EvidenceLedger,
    *,
    family: str | None = None,
    service: dict | None = None,
    strict: bool = True,
) -> AtlasProjection:
    """把账本折叠成 Atlas 投影。

    `strict=True` 时，真实 Study 拼不出完整快照会抛 `SnapshotIncomplete` ——
    那是账本缺口，应当刺眼，不应当被渲染成一页残缺的证据。
    """
    events = ledger.read_events(role=Role.HUMAN)
    count, broken = ledger.verify_chain()
    chain = {
        "events": count,
        "intact": not broken,
        "broken_at": broken[:20],
        "note": "Atlas 每次渲染都重算整条哈希链；断链即证据不可信",
    }
    denominators = ledger.denominators(family)
    episodes, orphans = _project_episodes(events)

    studies: list[dict] = []
    aborted: list[dict] = []
    for study_id, study_events in _group_by_study(events).items():
        kinds = {e["event_type"] for e in study_events}
        if "study_created" in kinds:
            studies.append(_project_study(study_id, study_events, denominators,
                                          strict=strict))
        else:
            aborted.append(_project_aborted(study_id, study_events))

    verdicts = dict.fromkeys((v.value for v in Verdict), 0)
    for study in studies:
        if study["verdict"]:
            verdicts[study["verdict"]] = verdicts.get(study["verdict"], 0) + 1

    if orphans:
        episodes.append(
            {
                "episode_id": "（无 Episode 归属）",
                "family": "",
                "started_at": "",
                "ended_at": None,
                "budget_at_start": {},
                "summary": None,
                "events": orphans,
                "studies": [],
            }
        )

    ordered = sorted(studies, key=lambda s: (s["created_at"] or "", s["study_id"]))
    by_id = {s["study_id"]: s for s in ordered}
    lineage = []
    for entry in _lineage(ordered):
        members = [by_id[i] for i in entry["study_ids"]]
        lineage.append({
            **entry,
            "family": members[0]["family"],
            "curves": {m: _curve(members, m) for m in CURVE_METRICS},
        })

    return AtlasProjection(
        chain=chain,
        lineage=lineage,
        denominators=denominators,
        verdicts=verdicts,
        coverage=_coverage(studies),
        episodes=episodes,
        studies=sorted(studies, key=lambda s: s["study_id"]),
        aborted_rounds=sorted(aborted, key=lambda s: s["study_id"]),
        service=service,
    )
