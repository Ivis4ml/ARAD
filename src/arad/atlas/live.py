"""运行中的进度投影（M9.3）。

运行目录只在 `run_service` 返回之后写一次，因此运行期间应用里什么都看不到 ——
实测 run6 跑到第 4 轮时 `runs/` 里仍然没有 run6，只能去查账本才知道进度。

**账本本来就是实时写的**，所以这里不重写运行目录，只读账本投影当前状态。
把 `write_run` 挪进循环每轮调一次是最省事的做法，但它每轮重算整个投影并重写目录，
随账本变大越来越慢，而且会拖慢研究本身 —— 观测不该改变被观测的过程。

**本模块只用 SQL 聚合，不把事件读进内存。**投影的代价必须与账本大小无关，
否则轮询会随运行时间变慢，而那正是最需要它的时候。

它是给**人**看的（Atlas 一直是只读的人类视图），因此不受提案器盲化边界约束。

**它返回逐次检验的 |t| 与零假设带，但两者永远成对。**先前这里写着「不返回任何效应量」，
理由是运行期间盯着效应看会让「要不要继续找」变成事后选择。那条顾虑是真的，
但用错了地方：这个决定按设计本来就归人（M6：「该不该继续找」是人的判断），
不能用一条设计原则挡住那个被指定要做判断的人。

**形态上有一条硬约束：曲线绝不单独出现。**一条随迭代上升的曲线，本身就是选择在纯噪声上
必然产出的形状；单画它会系统性地骗人。因此 `curve` 的每一点都同时带 `running_best` 与
`null_threshold`，缺一不可，前端也据此渲染。

残余风险如实记下：看着结果决定何时停，会让停止时点与结果相关。零假设带按**已花掉的**
检验次数计价，早停不会把已花的退回来，因此它不制造额外的多重检验偏差；
真正的风险是「看着不错就停」——而缓解手段正是把地板画在旁边，
使「不错」是相对于那根同步抬高的横杠判断的，不是相对于零。
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from ..evaluation.selection import expected_max_abs_z

LIVE_VERSION = "0.1.0"

#: 一个 Study 固定走这 11 步，顺序即账本 seq 的顺序。因此「第 k / 11 步」有确切
#: 含义，不是一个编出来的百分比。缺步本身也是信息：语义审计拦下的 Study 在
#: `semantic_audit` 之后直接跳到 `verdict_recorded`，**根本不读 outcome**，
#: 于是 `outcome_read` 与 `evaluation_result` 两步缺席 —— 那正是它没消耗
#: 多重检验预算的证据。
STUDY_PIPELINE = (
    "context_assembled", "proposal_locked", "hypothesis_locked",
    "confirmatory_locked", "study_created", "feature_spec_locked",
    "semantic_audit", "visible_data_range", "outcome_read",
    "evaluation_result", "verdict_recorded",
)

#: 判决词以外，进度需要的事件类型。逐个列出而不是排除法：
#: 新增事件类型默认不进进度，避免哪天某个带效应量的事件被顺手加进来。
PROGRESS_EVENTS = (
    "episode_started", "context_assembled", "study_created", "feature_spec_locked",
    "semantic_audit", "outcome_read", "verdict_recorded", "parse_failure",
    "context_blocked", "provider_repair", "service_stopped", "human_review_required",
)

#: 超过这个秒数没有新事件，就认为服务不在跑了。真实一轮约 3 到 8 分钟，
#: 取 15 分钟留足余量：宁可把已停的报成在跑，也不要把在跑的报成已停 ——
#: 后者会让人以为出事了而去干预一个正常的运行。
STALE_AFTER_SECONDS = 900


def live_state(ledger_path: str, family: str, *, now: datetime | None = None) -> dict:
    """当前进度。只走 SQL 聚合，代价与账本大小无关。"""
    conn = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        return _project(conn, family, now or datetime.now(UTC))
    finally:
        conn.close()


def live_beats(ledger_path: str, since: int = 0, limit: int = 400) -> dict:
    """增量拉取回放节拍。**代价与 since 之后的新事件数成正比，不与账本大小成正比。**

    节拍带两个累计量（提案分母、统计分母），因此不能只看新事件就算出来。
    做法是先用两条聚合查询取 `since` 处的计数，再在新事件上往后累加 ——
    每次从头重算会让轮询随运行时间变慢，而那正是最需要它的时候。
    """
    from .project import BEAT_STAGES, _beat_detail

    conn = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        # 提案分母按**内容去重**计数（record_proposal 是 INSERT OR IGNORE），
        # 数事件次数会与账本对不上：参数扫描的多个变体共用一个提案内容身份。
        proposals = {
            r["pid"]
            for r in conn.execute(
                "SELECT DISTINCT json_extract(payload, '$.proposal_id') pid FROM events"
                " WHERE event_type = 'proposal_recorded' AND seq <= ?", (since,)
            )
            if r["pid"] is not None
        }
        tests = conn.execute(
            "SELECT COUNT(*) n FROM events WHERE event_type = 'outcome_read'"
            " AND seq <= ?", (since,)
        ).fetchone()["n"]
        rows = conn.execute(
            "SELECT seq, study_id, event_type, payload, created_at FROM events"
            " WHERE seq > ? ORDER BY seq LIMIT ?", (since, limit)
        ).fetchall()
        head = conn.execute("SELECT MAX(seq) m FROM events").fetchone()["m"] or 0
    finally:
        conn.close()

    import json as _json

    beats: list[dict] = []
    for row in rows:
        payload = _json.loads(row["payload"])
        stage, headline = BEAT_STAGES.get(
            row["event_type"], ("other", row["event_type"])
        )
        if row["event_type"] == "proposal_recorded":
            pid = payload.get("proposal_id")
            if pid is not None:
                proposals.add(pid)
        if row["event_type"] == "outcome_read":
            tests += 1
        beats.append({
            "seq": row["seq"], "at": row["created_at"],
            "event_type": row["event_type"], "study_id": row["study_id"],
            "stage": stage, "headline": headline,
            "detail": _beat_detail(row["event_type"], payload),
            "pending_point": row["event_type"] == "proposal_locked",
            "reveal_point": row["event_type"] == "evaluation_result",
            "proposals_so_far": len(proposals), "tests_so_far": tests,
        })
    return {"since": since, "head": head, "beats": beats,
            "more": bool(beats) and beats[-1]["seq"] < head}


def study_detail(ledger_path: str, study_id: str) -> dict:
    """一个 Study 的全部细节，给右侧产物台。人类视图，因此含评价效应。"""
    conn = sqlite3.connect(f"file:{ledger_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    import json as _json

    try:
        rows = conn.execute(
            "SELECT seq, event_type, payload, created_at FROM events"
            " WHERE study_id = ? ORDER BY seq", (study_id,)
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return {"error": f"没有 Study {study_id!r}"}
    out: dict = {"study_id": study_id, "timeline": []}
    for row in rows:
        payload = _json.loads(row["payload"])
        kind = row["event_type"]
        out["timeline"].append({"seq": row["seq"], "event_type": kind,
                                "at": row["created_at"]})
        if kind == "proposal_locked":
            out["proposal"] = {k: payload.get(k) for k in (
                "mechanism", "target", "universe", "direction",
                "falsifiable_condition", "rationale")}
        elif kind == "feature_spec_locked":
            out["feature"] = {
                "feature_id": payload.get("feature_id"),
                "mechanism": payload.get("mechanism"),
                "failure_condition": payload.get("failure_condition"),
                "content_id": payload.get("content_id"),
                "steps": payload.get("steps", []),
            }
        elif kind == "semantic_audit":
            out["audit"] = payload.get("mismatches", [])
        elif kind == "evaluation_result":
            eff = payload.get("effects") or {}
            perf = (eff.get("performance") or {})
            ic = (eff.get("ic") or {})
            out["evaluation"] = {
                "t_stat": eff.get("t_stat"),
                "ic_spearman": ic.get("ic_spearman"),
                "sharpe_annualised": perf.get("sharpe_annualised"),
                "coverage": payload.get("coverage"),
                "blocked_reasons": payload.get("blocked_reasons", []),
            }
        elif kind == "verdict_recorded":
            out["verdict"] = {k: payload.get(k) for k in
                              ("verdict", "rationale", "next_action", "decided_at")}
    return out


def all_studies(conn: sqlite3.Connection) -> list[dict]:
    """全部 Study 的轻量摘要，给左栏导航。倒序（最新在上）。"""
    import json as _json

    rows = conn.execute(
        "SELECT study_id, event_type, payload FROM events"
        " WHERE study_id IS NOT NULL AND event_type IN"
        "   ('proposal_locked','feature_spec_locked','verdict_recorded','outcome_read')"
        " ORDER BY seq"
    ).fetchall()
    acc: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        sid = row["study_id"]
        if sid not in acc:
            acc[sid] = {"study_id": sid}
            order.append(sid)
        payload = _json.loads(row["payload"])
        if row["event_type"] == "proposal_locked":
            acc[sid]["target"] = payload.get("target")
            acc[sid]["universe"] = payload.get("universe")
        elif row["event_type"] == "feature_spec_locked":
            acc[sid]["feature_id"] = payload.get("feature_id")
        elif row["event_type"] == "outcome_read":
            acc[sid]["read_outcome"] = True
        elif row["event_type"] == "verdict_recorded":
            acc[sid]["verdict"] = payload.get("verdict")
    return [acc[s] for s in reversed(order)]


def _thinking() -> dict:
    """模型正在写的东西（在途观察窗）。

    provider 把 stream-json 的文本增量落到 INFLIGHT_PATH，调用结束即删。
    这是给人看的：单次调用 3 至 8 分钟，等待期间一个字都看不到是实测里
    最难受的一段。只取尾部 —— 人要看的是"它正在想什么"，不是全文。
    """
    from pathlib import Path

    path = Path("data/ledger/inflight_proposer.txt")
    if not path.exists():
        return {"active": False}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"active": False}
    return {"active": True, "chars": len(text), "tail": text[-3000:]}


def _curve(conn: sqlite3.Connection) -> list[dict]:
    """逐次检验的 |t| 与同一时刻的零假设带。**两者永远成对。**

    只取真正读过 outcome 的那些 —— 被语义审计拦下的 Study 没有 evaluation_result，
    也不该出现在这条曲线上：它没消耗多重检验预算，地板不因它抬高。
    """
    rows = conn.execute(
        "SELECT study_id,"
        "       json_extract(payload, '$.effects.t_stat') t,"
        "       json_extract(payload, '$.suggested_verdict') verdict"
        "  FROM events WHERE event_type = 'evaluation_result' ORDER BY seq"
    ).fetchall()
    out: list[dict] = []
    best = 0.0
    for i, row in enumerate(rows, start=1):
        raw = row["t"]
        value = abs(raw) if isinstance(raw, (int, float)) else None
        if value is not None and value > best:
            best = value
        out.append({
            "index": i,
            "study_id": row["study_id"],
            "value": value,
            "running_best": best if out or value is not None else None,
            # 地板按**这一点为止**已花的检验次数算，因此它随曲线一起长
            "null_threshold": round(expected_max_abs_z(i), 4),
            "verdict": row["verdict"],
        })
    return out


def _recent(conn: sqlite3.Connection, limit: int = 8) -> list[dict]:
    """最近几版的**中间结论**：模型提了什么、审计说了什么、判决是什么。

    此前这些只有在服务跑完写进运行目录之后才看得到，而运行期间恰恰最想看它们。
    账本本来就是实时写的，这里直接读。

    这一段是给**人**看的，因此可以带机制全文。它不进提案器上下文 ——
    提案器那一侧的记忆走 `memory/induction.py`，且判决分类已按决定 0006 退出。
    """
    ids = [
        r["study_id"]
        for r in conn.execute(
            "SELECT DISTINCT study_id FROM events WHERE study_id IS NOT NULL"
            " ORDER BY study_id DESC LIMIT ?", (limit,)
        )
    ]
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT study_id, event_type, payload FROM events"
        f" WHERE study_id IN ({marks})"
        f"   AND event_type IN ('proposal_locked','semantic_audit','verdict_recorded',"
        f"                      'feature_spec_locked')"
        f" ORDER BY seq", tuple(ids)
    ).fetchall()
    import json as _json

    by_study: dict[str, dict] = {}
    for row in rows:
        entry = by_study.setdefault(row["study_id"], {"study_id": row["study_id"]})
        payload = _json.loads(row["payload"])
        if row["event_type"] == "proposal_locked":
            entry.update({
                "mechanism": payload.get("mechanism", ""),
                "target": payload.get("target", ""),
                "universe": payload.get("universe", ""),
                "direction": payload.get("direction"),
                "falsifiable_condition": payload.get("falsifiable_condition", ""),
            })
        elif row["event_type"] == "feature_spec_locked":
            entry["feature_id"] = payload.get("feature_id", "")
            entry["shape"] = " -> ".join(
                f"{st.get('kind')}({st.get('field') or ','.join(st.get('inputs') or [])})"
                for st in payload.get("steps", [])
            )
        elif row["event_type"] == "semantic_audit":
            # 封闭词表的码。**审计拦下的那些根本没读 outcome**，
            # 因此它们不抬高地板 —— 这一条是审计在替我们省预算的证据。
            entry["audit_codes"] = [m["code"] for m in payload.get("mismatches", [])]
        elif row["event_type"] == "verdict_recorded":
            entry["verdict"] = payload.get("verdict", "")
            entry["rationale"] = payload.get("rationale", "")
    return [by_study[i] for i in sorted(by_study, reverse=True)]


def _project(conn: sqlite3.Connection, family: str, now: datetime) -> dict:
    last = conn.execute(
        "SELECT seq, event_type, study_id, created_at FROM events"
        " ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    if last is None:
        return {"live_version": LIVE_VERSION, "running": False, "events": 0,
                "note": "账本还是空的"}

    counts = {
        row["event_type"]: row["n"]
        for row in conn.execute(
            "SELECT event_type, COUNT(*) n FROM events GROUP BY event_type"
        )
    }
    verdicts = {
        row["v"]: row["n"]
        for row in conn.execute(
            "SELECT json_extract(payload, '$.verdict') v, COUNT(*) n FROM events"
            " WHERE event_type = 'verdict_recorded' GROUP BY v"
        )
        if row["v"]
    }
    tests = conn.execute(
        "SELECT COUNT(*) n FROM statistical_denominator WHERE family = ?", (family,)
    ).fetchone()["n"]
    proposals = conn.execute(
        "SELECT COUNT(*) n FROM proposal_denominator WHERE family = ?", (family,)
    ).fetchone()["n"]

    # 当前这一轮：最后一个 study_id 非空的事件属于哪个 Study
    current = conn.execute(
        "SELECT study_id FROM events WHERE study_id IS NOT NULL"
        " ORDER BY seq DESC LIMIT 1"
    ).fetchone()
    study_id = current["study_id"] if current else None
    run_id = study_id.rsplit("-study-", 1)[0] if study_id and "-study-" in study_id else None

    # 当前 Study 走到第几步。缺步不补：跳过的步骤本身是证据。
    steps: list[dict] = []
    if study_id:
        done = {
            r["event_type"]: r["seq"]
            for r in conn.execute(
                "SELECT event_type, MIN(seq) seq FROM events WHERE study_id = ?"
                " GROUP BY event_type", (study_id,)
            )
        }
        steps = [{"step": name, "seq": done.get(name), "done": name in done}
                 for name in STUDY_PIPELINE]

    age = (now - datetime.fromisoformat(last["created_at"])).total_seconds()
    stopped = counts.get("service_stopped", 0) > 0 and last["event_type"] in (
        "service_stopped", "human_review_required",
    )
    return {
        "live_version": LIVE_VERSION,
        # 「在跑」按**最后一个事件的年龄**判断，不按进程状态：账本是唯一的事实来源，
        # 而进程可能在另一台机器上，也可能已经被杀掉却没来得及写停止事件。
        "running": (not stopped) and age < STALE_AFTER_SECONDS,
        "seconds_since_last_event": round(age, 1),
        "run_id": run_id,
        "current_study": study_id,
        "last_event": last["event_type"],
        "pipeline": steps,
        "step_index": sum(1 for x in steps if x["done"]),
        "step_total": len(STUDY_PIPELINE),
        "seq": last["seq"],
        "events": sum(counts.values()),
        "stage_counts": {k: counts.get(k, 0) for k in PROGRESS_EVENTS},
        "verdicts": verdicts,
        "denominators": {
            "family": family, "proposal_denominator": proposals,
            "statistical_denominator": tests,
        },
        # 报价，与提案器看到的同一口径：多问一个问题要付多少
        "price": {
            "tests_spent": tests,
            "floor_now": round(expected_max_abs_z(tests), 4) if tests else 0.0,
            "floor_after_one_more": round(expected_max_abs_z(tests + 1), 4),
        },
        "curve": _curve(conn),
        "thinking": _thinking(),
        "recent": _recent(conn),
        "studies": all_studies(conn),
        "note": (
            "|t| 与零假设带成对返回，缺一不可：一条随迭代上升的曲线本身就是选择在"
            "纯噪声上必然产出的形状，单看它会系统性地骗人"
        ),
    }
