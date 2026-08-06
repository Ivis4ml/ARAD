"""durable queue 的合同测试（M3 第三块）。

M6 的活性出口条件在这里预先固定：空计划不丢任务、kill -9 后幂等恢复、
无工作时不 busy loop、模型无权写顶层终态。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from arad.orchestrator.queue import (
    DurableQueue,
    LeaseLost,
    ServiceControlDenied,
    ServiceState,
    TaskNotFound,
    TaskState,
)

T0 = datetime(2026, 8, 5, 12, 0, tzinfo=UTC)


@pytest.fixture
def queue(tmp_path):
    with DurableQueue(str(tmp_path / "q.db"), backoff_seconds=60) as q:
        yield q


def seed(q, n=1, **kw):
    for i in range(n):
        q.enqueue(f"t{i}", "study", {"i": i}, now=T0, **kw)


# ---------------------------------------------------------------- 入队与认领


def test_enqueue_is_idempotent(queue):
    queue.enqueue("t1", "study", {"a": 1}, now=T0)
    queue.enqueue("t1", "study", {"a": 999}, now=T0)
    assert queue.stats() == {TaskState.READY.value: 1}
    assert queue.get("t1")["payload"] == {"a": 1}


def test_claim_returns_none_when_nothing_is_runnable(queue):
    """没有可运行任务时返回 None，**不返回"研究完成"**。"""
    assert queue.claim("w1", now=T0) is None


def test_claim_respects_priority_then_age(queue):
    queue.enqueue("low", "study", {}, priority=0, now=T0)
    queue.enqueue("high", "study", {}, priority=5, now=T0)
    assert queue.claim("w1", now=T0)["task_id"] == "high"


def test_a_claimed_task_is_not_handed_to_a_second_worker(queue):
    seed(queue)
    assert queue.claim("w1", lease_seconds=300, now=T0)["task_id"] == "t0"
    assert queue.claim("w2", lease_seconds=300, now=T0) is None


# ---------------------------------------------------------------- 租约与恢复


def test_expired_lease_is_reclaimable_after_a_crash(queue):
    """kill -9 后租约到期即可重新认领，任务不丢。"""
    seed(queue)
    queue.claim("dead", lease_seconds=60, now=T0)
    assert queue.claim("alive", now=T0 + timedelta(seconds=30)) is None
    revived = queue.claim("alive", now=T0 + timedelta(seconds=61))
    assert revived["task_id"] == "t0"
    assert revived["attempts"] == 2  # 认领次数被如实记录


def test_the_crashed_worker_cannot_write_after_losing_its_lease(queue):
    seed(queue)
    queue.claim("dead", lease_seconds=60, now=T0)
    queue.claim("alive", now=T0 + timedelta(seconds=61))
    with pytest.raises(LeaseLost):
        queue.checkpoint("t0", "dead", {"step": 1}, now=T0 + timedelta(seconds=62))


def test_heartbeat_extends_the_lease(queue):
    seed(queue)
    queue.claim("w1", lease_seconds=60, now=T0)
    queue.heartbeat("t0", "w1", lease_seconds=600, now=T0 + timedelta(seconds=30))
    assert queue.claim("w2", now=T0 + timedelta(seconds=90)) is None


def test_checkpoint_survives_reclaim(queue):
    """恢复时从检查点继续，不从头重跑。"""
    seed(queue)
    queue.claim("dead", lease_seconds=60, now=T0)
    queue.checkpoint("t0", "dead", {"rows_done": 500}, now=T0 + timedelta(seconds=10))
    revived = queue.claim("alive", now=T0 + timedelta(seconds=61))
    assert revived["checkpoint"] == {"rows_done": 500}


# ---------------------------------------------------------------- 幂等副作用


def test_completing_twice_records_the_side_effect_once(queue):
    seed(queue)
    queue.claim("w1", now=T0)
    first = queue.complete("t0", "w1", {"verdict": "null"}, idempotency_key="k1", now=T0)
    assert first["duplicate"] is False
    queue.enqueue("t0b", "study", {}, now=T0)
    queue.claim("w1", now=T0)
    second = queue.complete(
        "t0b", "w1", {"verdict": "candidate"}, idempotency_key="k1", now=T0
    )
    assert second["duplicate"] is True
    assert second["result"] == {"verdict": "null"}  # 第一次的结果不被覆盖


def test_side_effects_are_append_only(queue):
    import sqlite3

    seed(queue)
    queue.claim("w1", now=T0)
    queue.complete("t0", "w1", {"ok": True}, idempotency_key="k1", now=T0)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        queue._conn.execute("DELETE FROM side_effects")
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        queue._conn.execute("UPDATE side_effects SET result = '{}'")


# ---------------------------------------------------------------- 不丢任务


@pytest.mark.parametrize(
    "reason", ["空计划", "坏 JSON：解析失败", "provider 超时"]
)
def test_failures_requeue_with_backoff_instead_of_losing_the_task(queue, reason):
    seed(queue)
    queue.claim("w1", now=T0)
    state = queue.fail("t0", "w1", reason, now=T0)
    assert state == TaskState.READY.value
    task = queue.get("t0")
    assert task["last_error"] == reason
    assert task["wake_at"] is not None            # 退避，不是立刻重试
    assert queue.claim("w2", now=T0) is None       # 退避期内不可认领
    assert queue.claim("w2", now=T0 + timedelta(seconds=61))["task_id"] == "t0"


def test_exhausting_attempts_goes_to_human_review_not_to_a_failed_terminal(queue):
    queue.enqueue("t0", "study", {}, max_attempts=2, now=T0)
    now = T0
    for _ in range(2):
        queue.claim("w1", now=now)
        state = queue.fail("t0", "w1", "provider 超时", now=now)
        now += timedelta(seconds=300)
    assert state == TaskState.HUMAN_REVIEW_REQUIRED.value
    assert TaskState.HUMAN_REVIEW_REQUIRED.value in TaskState.waitable()
    # 仍在队列里，没有被丢弃
    assert queue.get("t0")["state"] == TaskState.HUMAN_REVIEW_REQUIRED.value


# ---------------------------------------------------------------- 持久等待


def test_waiting_for_data_is_a_wakeable_state_not_a_failure(queue):
    seed(queue)
    queue.claim("w1", now=T0)
    wake = T0 + timedelta(hours=6)
    queue.wait_for_data("t0", "w1", "source manifest fingerprint changes", wake, now=T0)
    task = queue.get("t0")
    assert task["state"] == TaskState.WAITING_FOR_DATA.value
    assert task["wake_condition"] == "source manifest fingerprint changes"
    assert queue.claim("w2", now=T0 + timedelta(hours=1)) is None
    assert queue.claim("w2", now=wake)["task_id"] == "t0"


def test_next_wakeup_lets_the_caller_sleep_instead_of_busy_looping(queue):
    seed(queue)
    queue.claim("w1", now=T0)
    wake = T0 + timedelta(hours=6)
    queue.wait_for_data("t0", "w1", "forward reservation due", wake, now=T0)
    assert queue.claim("w2", now=T0 + timedelta(minutes=1)) is None
    assert queue.next_wakeup(now=T0 + timedelta(minutes=1)) == wake


def test_next_wakeup_is_none_when_everything_is_done(queue):
    seed(queue)
    queue.claim("w1", now=T0)
    queue.complete("t0", "w1", {}, idempotency_key="k", now=T0)
    assert queue.next_wakeup(now=T0) is None
    assert queue.claim("w1", now=T0) is None


# ---------------------------------------------------------------- 顶层状态


@pytest.mark.parametrize("role", ["research_worker", "proposer", "orchestrator", "evaluator"])
def test_only_a_human_may_change_the_service_state(queue, role):
    """模型的 stop 只能结束 Search Episode，不能停服务。"""
    with pytest.raises(ServiceControlDenied):
        queue.set_service_state(ServiceState.SHUTDOWN, role=role, now=T0)


def test_human_can_pause_and_resume(queue):
    assert queue.service_state()["state"] == ServiceState.RUNNING.value
    queue.set_service_state(ServiceState.PAUSED, role="human", reason="人工检查", now=T0)
    assert queue.service_state()["state"] == ServiceState.PAUSED.value
    queue.set_service_state(ServiceState.RUNNING, role="human", now=T0)
    assert queue.service_state()["state"] == ServiceState.RUNNING.value


def test_there_is_no_completed_service_state():
    """顶层没有"研究完成"这个状态。"""
    assert {s.value for s in ServiceState} == {"running", "paused", "shutdown"}
    assert "completed" not in {s.value for s in ServiceState}
    assert "done" not in {s.value for s in ServiceState}


# ---------------------------------------------------------------- 杂项


def test_unknown_task_raises(queue):
    with pytest.raises(TaskNotFound):
        queue.get("nope")


def test_state_survives_reopening_the_database(tmp_path):
    path = str(tmp_path / "q.db")
    with DurableQueue(path) as q:
        q.enqueue("t0", "study", {"a": 1}, now=T0)
        q.claim("w1", lease_seconds=60, now=T0)
        q.checkpoint("t0", "w1", {"step": 3}, now=T0)
    with DurableQueue(path) as q:
        assert q.get("t0")["checkpoint"] == {"step": 3}
        assert q.claim("w2", now=T0 + timedelta(seconds=61))["task_id"] == "t0"
