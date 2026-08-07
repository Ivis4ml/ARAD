"""运行中的进度投影（M9.3）。

运行目录只在 `run_service` 返回之后写一次，因此运行期间应用里什么都看不到 ——
实测 run6 跑到第 4 轮时 `runs/` 里仍然没有 run6，只能去查账本才知道进度。

**账本本来就是实时写的**，所以这里不重写运行目录，只读账本投影当前状态。
把 `write_run` 挪进循环每轮调一次是最省事的做法，但它每轮重算整个投影并重写目录，
随账本变大越来越慢，而且会拖慢研究本身 —— 观测不该改变被观测的过程。

**本模块只用 SQL 聚合，不把事件读进内存。**投影的代价必须与账本大小无关，
否则轮询会随运行时间变慢，而那正是最需要它的时候。

它是给**人**看的（Atlas 一直是只读的人类视图），因此不受提案器盲化边界约束；
但它同样不返回任何效应量 —— 进度是「跑到哪了」，不是「结果如何」。
让进度条泄漏效应，会把「盯着它看」变成一种事后选择。
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
        "note": (
            "进度是「跑到哪了」，不是「结果如何」：本视图不返回任何效应量。"
            "让进度泄漏效应，会把盯着它看变成一种事后选择"
        ),
    }
