"""判决时刻快照渲染（决定 0003 的 schema 合同）。

M3 的出口条件之一：任意 Study 的账本事件必须**足以**渲染为自包含的判决时刻快照。
渲染器本身可以是最简单的 Markdown 导出 —— 验证的是账本 schema 的完整性，
不是界面。拼不出完整快照即账本缺口，按 bug 处理。

快照只呈现**判决当时可见**的内容，不用后见数据回填；forward 数据与标签不可见，
只显示预约状态。
"""

from __future__ import annotations

from ..registry.specs import Verdict

#: 一个自包含快照必须能回答的问题。缺任一项即账本缺口。
REQUIRED_SECTIONS = (
    "proposal",
    "hypothesis_lock",
    "confirmatory_lock",
    "outcome_reads",
    "verdict",
    "denominators",
    "visible_data_range",
)


class SnapshotIncomplete(RuntimeError):
    """账本事件不足以渲染自包含快照。这是账本缺口，不是渲染器缺陷。"""


#: 快照的可选切片。缺失不算账本缺口 —— blocked 的 Study 本来就没有评价结果 ——
#: 但只要有就必须呈现：决定 0003 快照层要求五关逐项结果、腿分解、红队诊断与工件哈希。
OPTIONAL_SECTIONS = ("evaluation", "feature_spec")


def collect_snapshot(events: list[dict], denominators: dict) -> dict:
    """把一个 Study 的事件流折叠成判决时刻快照。"""
    snap: dict = {s: None for s in REQUIRED_SECTIONS}
    snap.update(dict.fromkeys(OPTIONAL_SECTIONS))
    snap["outcome_reads"] = []
    snap["denominators"] = denominators
    for event in events:
        kind, payload = event["event_type"], event["payload"]
        if kind == "evaluation_result":
            snap["evaluation"] = payload
        elif kind == "feature_spec_locked":
            snap["feature_spec"] = payload
        elif kind == "proposal_locked":
            snap["proposal"] = payload
        elif kind == "hypothesis_locked":
            snap["hypothesis_lock"] = payload
        elif kind == "confirmatory_locked":
            snap["confirmatory_lock"] = payload
        elif kind == "outcome_read":
            snap["outcome_reads"].append(payload)
        elif kind == "verdict_recorded":
            snap["verdict"] = payload
        elif kind == "visible_data_range":
            snap["visible_data_range"] = payload
    return snap


def require_complete(snapshot: dict) -> dict:
    missing = [s for s in REQUIRED_SECTIONS if snapshot.get(s) in (None, [])]
    # outcome_reads 允许为空：blocked 与 underpowered 的 Study 可能一次 outcome 都没读
    verdict = (snapshot.get("verdict") or {}).get("verdict")
    if verdict in (Verdict.BLOCKED.value, Verdict.UNDERPOWERED.value):
        missing = [m for m in missing if m != "outcome_reads"]
    if missing:
        raise SnapshotIncomplete(
            f"账本不足以渲染自包含快照，缺少 {missing}；按 bug 处理并回补回归测试"
        )
    return snapshot


def render_markdown(snapshot: dict) -> str:
    require_complete(snapshot)
    v = snapshot["verdict"]
    lines = [
        f"# Study {v['study_id']} 判决快照",
        "",
        f"- Verdict：`{v['verdict']}`　下一步动作：`{v['next_action']}`",
        f"- 理由：{v['rationale']}",
        f"- 当时可见数据范围：{snapshot['visible_data_range']}",
        "",
        "## 分母",
        "",
        (
            f"- proposal denominator：{snapshot['denominators']['proposal_denominator']}"
            f"（其中预检挡下 {snapshot['denominators']['proposals_screened_out']}）"
        ),
        f"- statistical denominator：{snapshot['denominators']['statistical_denominator']}",
        "",
        "## 冻结的假设",
        "",
        f"- 提案：{snapshot['proposal']}",
        f"- Hypothesis Lock：{snapshot['hypothesis_lock']}",
        f"- Confirmatory Lock：{snapshot['confirmatory_lock']}",
        "",
        f"## 读过 outcome 的检验（{len(snapshot['outcome_reads'])} 次）",
        "",
    ]
    lines.extend(f"- {r}" for r in snapshot["outcome_reads"])
    lines.append("")
    lines.append("> 快照只呈现判决当时可见的内容；forward 数据与标签不可见。")
    return "\n".join(lines)
