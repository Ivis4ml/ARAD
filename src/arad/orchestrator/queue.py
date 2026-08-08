"""SQLite 上的 durable queue（M3 第三块）。

Merge-Plan-2 §6 的三层活性在这里落到实处：**顶层不存在模型可写的终态**。
`WAITING_FOR_DATA` 与 `HUMAN_REVIEW_REQUIRED` 是持久、可唤醒状态，不是失败，
也不应 busy loop —— 没有可运行任务时 `next_wakeup()` 给出下次唤醒时刻，
调用方据此休眠，而不是返回"研究完成"。

四条边界：

1. **租约**：任务被认领后带过期时刻。进程被 kill 后租约到期即可重新认领，
   任务不会丢，也不会被两个 worker 同时持有。
2. **幂等**：每个副作用带幂等键，重复完成同一任务只记录一次结果。
   这是"kill -9 后幂等恢复"的实现，不是靠 worker 自觉。
3. **不丢任务**：空计划、坏 JSON、provider 超时都走 `fail()`，
   attempt 加一并按退避重新排队；达到上限转 `HUMAN_REVIEW_REQUIRED`，仍不丢。
4. **能力边界**：Research Service 的 pause/resume/shutdown 只接受 human 角色。
   worker 与 proposer 调用即被拒，模型无法写顶层终态。

时间显式注入（`now` 参数），使租约过期、退避与唤醒都可确定性测试。
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Self

QUEUE_VERSION = "0.1.0"


class TaskState(str, Enum):
    READY = "ready"
    LEASED = "leased"
    WAITING_FOR_DATA = "waiting_for_data"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    DONE = "done"

    @classmethod
    def waitable(cls) -> set[str]:
        return {cls.WAITING_FOR_DATA.value, cls.HUMAN_REVIEW_REQUIRED.value}


class ServiceState(str, Enum):
    """Research Service 的顶层状态。只有 human 可以改。"""

    RUNNING = "running"
    PAUSED = "paused"
    SHUTDOWN = "shutdown"


class LeaseLost(RuntimeError):
    """租约已被他人接管或已过期。写入被拒绝。"""


class ServiceControlDenied(RuntimeError):
    """非 human 角色试图改写 Research Service 的顶层状态。"""


class TaskNotFound(RuntimeError):
    """任务不存在。"""


_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    kind             TEXT NOT NULL,
    payload          TEXT NOT NULL,
    state            TEXT NOT NULL,
    priority         INTEGER NOT NULL DEFAULT 0,
    attempts         INTEGER NOT NULL DEFAULT 0,
    max_attempts     INTEGER NOT NULL DEFAULT 3,
    lease_owner      TEXT,
    lease_expires_at TEXT,
    wake_at          TEXT,
    wake_condition   TEXT,
    checkpoint       TEXT,
    last_error       TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS side_effects (
    idempotency_key TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL,
    result          TEXT NOT NULL,
    recorded_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS service_state (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    state      TEXT NOT NULL,
    reason     TEXT NOT NULL DEFAULT '',
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS side_effects_no_update
BEFORE UPDATE ON side_effects
BEGIN SELECT RAISE(ABORT, 'side effects are append-only: UPDATE denied'); END;

CREATE TRIGGER IF NOT EXISTS side_effects_no_delete
BEFORE DELETE ON side_effects
BEGIN SELECT RAISE(ABORT, 'side effects are append-only: DELETE denied'); END;
"""


def _iso(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat()


class DurableQueue:
    """持久任务队列。所有状态转换都在一个 SQLite 事务里完成。"""

    def __init__(self, path: str, *, backoff_seconds: int = 60):
        self.path = path
        self.backoff_seconds = backoff_seconds
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------ 入队

    def enqueue(
        self,
        task_id: str,
        kind: str,
        payload: dict,
        *,
        priority: int = 0,
        max_attempts: int = 3,
        now: datetime | None = None,
    ) -> str:
        """入队。同一 task_id 重复入队是幂等的，不会产生第二个任务。"""
        stamp = _iso(now or datetime.now(UTC))
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO tasks (task_id, kind, payload, state, priority,"
                " max_attempts, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (task_id, kind, json.dumps(payload, ensure_ascii=False, sort_keys=True),
                 TaskState.READY.value, priority, max_attempts, stamp, stamp),
            )
        return task_id

    # ------------------------------------------------------------ 认领

    def claim(
        self, owner: str, *, lease_seconds: int = 300, now: datetime | None = None,
        prefix: str | None = None,
    ) -> dict | None:
        """认领一个可运行任务。没有可运行任务时返回 None，**不返回"完成"**。

        可运行 = READY，或租约已过期的 LEASED，或唤醒时刻已到的等待状态。
        过期租约可被重新认领，这就是 kill -9 之后任务不丢的机制。

        `prefix` 把认领限制在本次运行的任务上。**没有它，一次新运行会先去替上一次
        运行干活**：队列是持久的，上一次被停掉时留下的 ready 任务排在更前面，
        而认领按 created_at 升序取最早的一个。实测 run8 启动后写出的第一条事件
        是 `run6-study-9` —— M7.2 让**标识**唯一了，但没让**认领**按运行范围隔离，
        于是 24 轮预算会花在陈旧任务上，而它们的载荷带着旧的错配码与旧的谱系。
        """
        current = datetime.now(UTC) if now is None else now
        stamp = _iso(current)
        scope = " AND task_id LIKE ?" if prefix else ""
        with self._conn:
            row = self._conn.execute(
                "SELECT * FROM tasks WHERE ("
                # READY 也要尊重退避：失败重排的任务在 wake_at 之前不可认领
                " (state = ? AND (wake_at IS NULL OR wake_at <= ?))"
                " OR (state = ? AND lease_expires_at <= ?)"
                " OR (state IN (?, ?) AND wake_at IS NOT NULL AND wake_at <= ?)"
                f" ){scope}"
                " ORDER BY priority DESC, created_at ASC, task_id ASC LIMIT 1",
                (
                    TaskState.READY.value, stamp,
                    TaskState.LEASED.value, stamp,
                    TaskState.WAITING_FOR_DATA.value,
                    TaskState.HUMAN_REVIEW_REQUIRED.value, stamp,
                    *((f"{prefix}%",) if prefix else ()),
                ),
            ).fetchone()
            if row is None:
                return None
            expires = _iso(current + timedelta(seconds=lease_seconds))
            self._conn.execute(
                "UPDATE tasks SET state = ?, lease_owner = ?, lease_expires_at = ?,"
                " attempts = attempts + 1, updated_at = ? WHERE task_id = ?",
                (TaskState.LEASED.value, owner, expires, stamp, row["task_id"]),
            )
        return self.get(row["task_id"])

    def _require_lease(self, task_id: str, owner: str, now: datetime) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise TaskNotFound(task_id)
        if row["lease_owner"] != owner:
            raise LeaseLost(f"{task_id} 的租约属于 {row['lease_owner']!r}，不是 {owner!r}")
        if row["lease_expires_at"] and row["lease_expires_at"] <= _iso(now):
            raise LeaseLost(f"{task_id} 的租约已于 {row['lease_expires_at']} 过期")
        return row

    def heartbeat(
        self, task_id: str, owner: str, *, lease_seconds: int = 300,
        now: datetime | None = None,
    ) -> str:
        current = datetime.now(UTC) if now is None else now
        self._require_lease(task_id, owner, current)
        expires = _iso(current + timedelta(seconds=lease_seconds))
        with self._conn:
            self._conn.execute(
                "UPDATE tasks SET lease_expires_at = ?, updated_at = ? WHERE task_id = ?",
                (expires, _iso(current), task_id),
            )
        return expires

    def checkpoint(
        self, task_id: str, owner: str, data: dict, *, now: datetime | None = None
    ) -> None:
        """保存进度。恢复时从检查点继续，不从头重跑。"""
        current = datetime.now(UTC) if now is None else now
        self._require_lease(task_id, owner, current)
        with self._conn:
            self._conn.execute(
                "UPDATE tasks SET checkpoint = ?, updated_at = ? WHERE task_id = ?",
                (json.dumps(data, ensure_ascii=False, sort_keys=True), _iso(current), task_id),
            )

    # ------------------------------------------------------------ 终结与等待

    def complete(
        self, task_id: str, owner: str, result: dict, *, idempotency_key: str,
        now: datetime | None = None,
    ) -> dict:
        """完成任务并记录副作用。同一幂等键重复完成只留第一次的结果。"""
        current = datetime.now(UTC) if now is None else now
        self._require_lease(task_id, owner, current)
        stamp = _iso(current)
        with self._conn:
            existing = self._conn.execute(
                "SELECT result FROM side_effects WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is None:
                self._conn.execute(
                    "INSERT INTO side_effects (idempotency_key, task_id, result, recorded_at)"
                    " VALUES (?,?,?,?)",
                    (idempotency_key, task_id,
                     json.dumps(result, ensure_ascii=False, sort_keys=True), stamp),
                )
                stored, duplicate = result, False
            else:
                stored, duplicate = json.loads(existing["result"]), True
            self._conn.execute(
                "UPDATE tasks SET state = ?, lease_owner = NULL, lease_expires_at = NULL,"
                " updated_at = ? WHERE task_id = ?",
                (TaskState.DONE.value, stamp, task_id),
            )
        return {"result": stored, "duplicate": duplicate}

    def fail(
        self, task_id: str, owner: str, reason: str, *, now: datetime | None = None
    ) -> str:
        """任务失败。空计划、坏 JSON、provider 超时都走这里，任务不丢。

        未达上限则按退避重新排队；达到上限转 HUMAN_REVIEW_REQUIRED，
        它是持久可唤醒状态，不是失败终态。
        """
        current = datetime.now(UTC) if now is None else now
        row = self._require_lease(task_id, owner, current)
        stamp = _iso(current)
        if row["attempts"] >= row["max_attempts"]:
            state, wake = TaskState.HUMAN_REVIEW_REQUIRED.value, None
        else:
            state = TaskState.READY.value
            wake = _iso(current + timedelta(seconds=self.backoff_seconds * row["attempts"]))
        with self._conn:
            self._conn.execute(
                "UPDATE tasks SET state = ?, lease_owner = NULL, lease_expires_at = NULL,"
                " wake_at = ?, wake_condition = ?, last_error = ?, updated_at = ?"
                " WHERE task_id = ?",
                (state, wake, "retry_backoff" if wake else "human_review", reason,
                 stamp, task_id),
            )
        return state

    def wait_for_data(
        self, task_id: str, owner: str, condition: str, wake_at: datetime,
        *, now: datetime | None = None,
    ) -> None:
        """转入持久等待。这不是失败，也不占用租约。"""
        current = datetime.now(UTC) if now is None else now
        self._require_lease(task_id, owner, current)
        with self._conn:
            self._conn.execute(
                "UPDATE tasks SET state = ?, lease_owner = NULL, lease_expires_at = NULL,"
                " wake_at = ?, wake_condition = ?, updated_at = ? WHERE task_id = ?",
                (TaskState.WAITING_FOR_DATA.value, _iso(wake_at), condition,
                 _iso(current), task_id),
            )

    # ------------------------------------------------------------ 查询

    def get(self, task_id: str) -> dict:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise TaskNotFound(task_id)
        out = dict(row)
        out["payload"] = json.loads(out["payload"])
        out["checkpoint"] = json.loads(out["checkpoint"]) if out["checkpoint"] else None
        return out

    def next_wakeup(self, now: datetime | None = None) -> datetime | None:
        """没有可运行任务时的下次唤醒时刻。用于休眠而不是 busy loop。"""
        current = datetime.now(UTC) if now is None else now
        stamp = _iso(current)
        row = self._conn.execute(
            "SELECT MIN(t) AS t FROM ("
            " SELECT lease_expires_at AS t FROM tasks WHERE state = ? AND lease_expires_at > ?"
            " UNION ALL"
            " SELECT wake_at AS t FROM tasks WHERE wake_at IS NOT NULL AND wake_at > ?"
            "   AND state != ?)",
            (TaskState.LEASED.value, stamp, stamp, TaskState.DONE.value),
        ).fetchone()
        return datetime.fromisoformat(row["t"]) if row and row["t"] else None

    def stats(self) -> dict:
        rows = self._conn.execute(
            "SELECT state, COUNT(*) n FROM tasks GROUP BY state"
        ).fetchall()
        return {r["state"]: r["n"] for r in rows}

    # ------------------------------------------------------------ 顶层状态

    def service_state(self) -> dict:
        row = self._conn.execute("SELECT * FROM service_state WHERE id = 1").fetchone()
        if row is None:
            return {"state": ServiceState.RUNNING.value, "reason": "", "changed_by": ""}
        return dict(row)

    def set_service_state(
        self, state: ServiceState, *, role: str, reason: str = "",
        now: datetime | None = None,
    ) -> None:
        """只有 human 可以 pause/resume/shutdown。模型无权写顶层终态。"""
        if role != "human":
            raise ServiceControlDenied(
                f"角色 {role!r} 无权改写 Research Service 顶层状态；"
                "模型的 stop 只能结束当前 Search Episode，不能停服务"
            )
        stamp = _iso(now or datetime.now(UTC))
        with self._conn:
            self._conn.execute(
                "INSERT INTO service_state (id, state, reason, changed_by, changed_at)"
                " VALUES (1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET"
                " state = excluded.state, reason = excluded.reason,"
                " changed_by = excluded.changed_by, changed_at = excluded.changed_at",
                (state.value, reason, role, stamp),
            )
