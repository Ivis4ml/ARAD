"""Evidence Ledger：SQLite WAL 上的追加式哈希链账本（M3 第一块）。

三条边界都由**数据库**强制，不由提示词或约定：

1. **只能追加**：events 表上的 UPDATE 与 DELETE 触发器直接 ABORT。
   Merge-Plan-2 §5.3 禁止用 KILL 删除证据；这里让删除在物理上失败。
2. **哈希链**：每个事件链接前一事件的哈希，任何篡改都会使 `verify_chain()` 失败。
3. **能力边界**：proposer 角色的查询路径不返回效果字段（β/t/p/IC/Sharpe），
   由 `read_events()` 强制（§7.2：提示词与 pre-commit 不是安全边界）。

两本分母分开记：proposal denominator 计入**全部**提案（含被预检挡下的），
statistical denominator 只计入真正读过 outcome 的检验，且只增不减。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from typing import Self

from ..registry.specs import (
    EFFECT_CONTAINERS,
    canonical_json,
    content_id,
    is_effect_field,
    utc_now,
)

LEDGER_VERSION = "0.1.0"

GENESIS_HASH = "0" * 64


class Role(str, Enum):
    """能力角色。决定查询层能看到什么，不是提醒。"""

    ORCHESTRATOR = "orchestrator"
    EVALUATOR = "evaluator"
    PROPOSER = "proposer"
    HUMAN = "human"


class LedgerIntegrityError(RuntimeError):
    """哈希链校验失败：账本被改动过。"""


class CapabilityDenied(RuntimeError):
    """角色越权访问。"""


class DenominatorShrink(RuntimeError):
    """统计分母被缩小。只要读过 outcome 就必须计入，筛掉也不能回缩。"""


_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS events (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id    TEXT,
    event_type  TEXT NOT NULL,
    payload     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    prev_hash   TEXT NOT NULL,
    event_hash  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS proposal_denominator (
    proposal_id TEXT PRIMARY KEY,
    family      TEXT NOT NULL,
    screened_out INTEGER NOT NULL,
    reason      TEXT NOT NULL DEFAULT '',
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS statistical_denominator (
    test_id     TEXT PRIMARY KEY,
    family      TEXT NOT NULL,
    study_id    TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS events_no_update
BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'evidence ledger is append-only: UPDATE denied'); END;

CREATE TRIGGER IF NOT EXISTS events_no_delete
BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'evidence ledger is append-only: DELETE denied'); END;

CREATE TRIGGER IF NOT EXISTS statistical_denominator_no_delete
BEFORE DELETE ON statistical_denominator
BEGIN SELECT RAISE(ABORT, 'statistical denominator cannot shrink: DELETE denied'); END;

CREATE TRIGGER IF NOT EXISTS statistical_denominator_no_update
BEFORE UPDATE ON statistical_denominator
BEGIN SELECT RAISE(ABORT, 'statistical denominator cannot shrink: UPDATE denied'); END;

CREATE TRIGGER IF NOT EXISTS proposal_denominator_no_delete
BEFORE DELETE ON proposal_denominator
BEGIN SELECT RAISE(ABORT, 'proposal denominator cannot shrink: DELETE denied'); END;
"""


def event_hash(prev_hash: str, seq: int, study_id: str | None, event_type: str,
               payload: dict, created_at: str) -> str:
    return content_id(
        {
            "prev_hash": prev_hash,
            "seq": seq,
            "study_id": study_id,
            "event_type": event_type,
            "payload": payload,
            "created_at": created_at,
        }
    )


#: 盲化角色**能看到**的字段，按事件类型逐项列出。没列的一律丢弃，不是遮蔽。
#:
#: **黑名单在这里是错的形状，这已经被证伪两次。**第一次是 `EFFECT_FIELDS` 漏了
#: 评价机实际输出的 `slope` 与 `intercept`；补上名字、前缀与 `effects` 容器之后，
#: 第二次从 `diagnostics` 漏出来 —— `placebo.actual_slope` 除以
#: `two_way_cluster.se` 就是带符号的 t 值，实测与评价机的 `t_stat` 逐位相同。
#: 只要评价机新增一个统计量，黑名单就又开一个口子。白名单反过来：
#: 没被显式允许的东西不可能出现在盲化视图里，新增统计量默认不可见。
#:
#: `evaluation_result` **整条不在名单里**：提案器不该看到评价结果的任何部分。
PROPOSER_VISIBLE_FIELDS: dict[str, tuple[str, ...]] = {
    "verdict_recorded": ("study_id", "verdict"),
    "proposal_recorded": ("family", "screened_out", "reason"),
    "outcome_read": ("family",),
    "parse_failure": ("role", "schema_name", "attempts"),
    "provider_repair": ("attempts", "model_id"),
    "primitive_gap_declared": (
        "mechanism", "missing_primitive", "why_existing_primitives_insufficient",
    ),
    "study_created": ("study_id", "parent_study_id", "change_summary"),
    "episode_started": ("episode_id", "family"),
    "episode_ended": ("episode_id", "rounds", "ended_because"),
}

WITHHELD = "<withheld:not-on-blinded-allowlist>"

def _project_for_role(event_type: str, payload: dict) -> dict:
    """按事件类型取白名单字段。整条不在名单里的事件只留一个标记。"""
    allowed = PROPOSER_VISIBLE_FIELDS.get(event_type)
    if allowed is None:
        return {"withheld": WITHHELD}
    kept = {k: v for k, v in payload.items() if k in allowed}
    if len(kept) != len(payload):
        kept["withheld"] = WITHHELD
    return kept


def _redact(payload: dict) -> dict:
    """去掉效果字段。递归处理嵌套结构，避免把 β 藏在子字典里绕过边界。

    整个 `effects` 子对象一律遮蔽：逐字段挡只能挡住已经想到的名字，
    而评价机每加一个统计量都会开一个新口子。
    """
    out: dict = {}
    for key, value in payload.items():
        if key.lower() in EFFECT_CONTAINERS:
            out[key] = "<redacted:effect-container>"
        elif is_effect_field(key):
            out[key] = "<redacted:effect-field>"
        elif isinstance(value, dict):
            out[key] = _redact(value)
        elif isinstance(value, list):
            out[key] = [_redact(v) if isinstance(v, dict) else v for v in value]
        else:
            out[key] = value
    return out


class EvidenceLedger:
    """追加式哈希链账本。构造即建表；同一路径可重复打开。"""

    def __init__(self, path: str):
        self.path = path
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

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """跨对象更新必须在一个事务里完成（Merge-Plan-2 §7.1）。"""
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # ------------------------------------------------------------ 追加

    def _last(self) -> tuple[int, str]:
        row = self._conn.execute(
            "SELECT seq, event_hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return (row["seq"], row["event_hash"]) if row else (0, GENESIS_HASH)

    def append(self, event_type: str, payload: dict, *, study_id: str | None = None) -> str:
        """追加一个事件，返回其哈希。这是账本唯一的写入路径。"""
        if not event_type or not event_type.strip():
            raise ValueError("event_type 不能为空")
        prev_seq, prev_hash = self._last()
        seq = prev_seq + 1
        created_at = utc_now()
        digest = event_hash(prev_hash, seq, study_id, event_type, payload, created_at)
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO events (seq, study_id, event_type, payload, created_at,"
                " prev_hash, event_hash) VALUES (?,?,?,?,?,?,?)",
                (seq, study_id, event_type, canonical_json(payload), created_at,
                 prev_hash, digest),
            )
        return digest

    # ------------------------------------------------------------ 读取

    def read_events(self, *, role: Role, study_id: str | None = None) -> list[dict]:
        """按角色读取事件。proposer 拿不到效果字段。"""
        if role is Role.PROPOSER and study_id is None:
            # 提案器只能按 Study 取盲化视图，不能全量拉账本
            raise CapabilityDenied("proposer 只能按 study_id 读取盲化事件，不能全量读取账本")
        sql = "SELECT * FROM events"
        args: tuple = ()
        if study_id is not None:
            sql += " WHERE study_id = ?"
            args = (study_id,)
        sql += " ORDER BY seq"
        rows = self._conn.execute(sql, args).fetchall()
        out = []
        for row in rows:
            import json as _json

            payload = _json.loads(row["payload"])
            if role is Role.PROPOSER:
                # 先按白名单裁剪，再让黑名单兜一道底：白名单字段本应安全，
                # 但两道比一道好，且第二道的失败已经有实测记录
                payload = _redact(_project_for_role(row["event_type"], payload))
            out.append(
                {
                    "seq": row["seq"],
                    "study_id": row["study_id"],
                    "event_type": row["event_type"],
                    "payload": payload,
                    "created_at": row["created_at"],
                    "prev_hash": row["prev_hash"],
                    "event_hash": row["event_hash"],
                }
            )
        return out

    def verify_chain(self) -> tuple[int, list[int]]:
        """重算整条链。返回 (事件数, 断链处的 seq 列表)。"""
        import json as _json

        broken: list[int] = []
        prev = GENESIS_HASH
        rows = self._conn.execute("SELECT * FROM events ORDER BY seq").fetchall()
        for row in rows:
            expected = event_hash(
                prev, row["seq"], row["study_id"], row["event_type"],
                _json.loads(row["payload"]), row["created_at"],
            )
            if expected != row["event_hash"] or row["prev_hash"] != prev:
                broken.append(row["seq"])
            prev = row["event_hash"]
        return len(rows), broken

    def require_intact(self) -> int:
        count, broken = self.verify_chain()
        if broken:
            raise LedgerIntegrityError(f"账本哈希链在 seq {broken[:5]} 处断裂；证据不可信")
        return count

    # ------------------------------------------------------------ 两本分母

    def record_proposal(
        self, proposal_id: str, family: str, *, screened_out: bool = False, reason: str = ""
    ) -> None:
        """计入 proposal denominator。被预检挡下的提案同样必须计入。"""
        if screened_out and not reason:
            raise ValueError("被挡下的提案必须给出理由，否则无法审计选择偏差")
        with self.transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO proposal_denominator"
                " (proposal_id, family, screened_out, reason, recorded_at) VALUES (?,?,?,?,?)",
                (proposal_id, family, int(screened_out), reason, utc_now()),
            )
        self.append(
            "proposal_recorded",
            {"proposal_id": proposal_id, "family": family,
             "screened_out": screened_out, "reason": reason},
        )

    def record_outcome_read(self, test_id: str, family: str, study_id: str) -> None:
        """计入 statistical denominator。只要读过 outcome 就必须计入。"""
        with self.transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO statistical_denominator"
                " (test_id, family, study_id, recorded_at) VALUES (?,?,?,?)",
                (test_id, family, study_id, utc_now()),
            )
        self.append(
            "outcome_read", {"test_id": test_id, "family": family}, study_id=study_id
        )

    def denominators(self, family: str | None = None) -> dict:
        where = " WHERE family = ?" if family else ""
        args = (family,) if family else ()
        proposals = self._conn.execute(
            f"SELECT COUNT(*) n, SUM(screened_out) s FROM proposal_denominator{where}", args
        ).fetchone()
        tests = self._conn.execute(
            f"SELECT COUNT(*) n FROM statistical_denominator{where}", args
        ).fetchone()
        return {
            "family": family,
            "proposal_denominator": proposals["n"],
            "proposals_screened_out": proposals["s"] or 0,
            "statistical_denominator": tests["n"],
        }
