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

from ..memory.ledger import EvidenceLedger, Role
from ..memory.snapshot import collect_snapshot, require_complete
from ..registry.specs import Verdict

ATLAS_VERSION = "0.1.0"

#: 不属于任何 Study、但必须出现在 Episode 层的事件。
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
    "source_gap": "所需数据源尚未接入解释器",
    "primitive_gap_declared": "声明原语缺口",
    "provider_error": "provider 调用故障",
    "invalid_proposal": "提案缺必填字段",
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
    return {
        "study_id": study_id,
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

    return AtlasProjection(
        chain=chain,
        denominators=denominators,
        verdicts=verdicts,
        coverage=_coverage(studies),
        episodes=episodes,
        studies=sorted(studies, key=lambda s: s["study_id"]),
        aborted_rounds=sorted(aborted, key=lambda s: s["study_id"]),
        service=service,
    )
