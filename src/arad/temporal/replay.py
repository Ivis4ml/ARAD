"""人工回放清单（出口条件 2）。

抽样带种子且按样本段分层，因此清单可复现且必然覆盖多个历史段。清单本身是
给人核对的产物；机器守卫在 `tests/contracts/test_spine_artifacts.py`：
每一条 feature 的 availability_time 必须严格早于决策时点，决策时点必须严格
早于 label 窗口起点。
"""

from __future__ import annotations

import random
from collections.abc import Callable
from datetime import datetime

SEGMENT_ORDER = (
    "discovery",
    "historical_validation",
    "contaminated_audit",
    "forward_confirmation",
)


def stratified_sample(rows: list[dict], *, seed: int, size: int) -> list[dict]:
    """按 sample_segment 分层的带种子抽样，输出按 label_start 升序。"""
    buckets: dict[str, list[dict]] = {}
    for r in rows:
        buckets.setdefault(r["sample_segment"], []).append(r)
    present = [s for s in SEGMENT_ORDER if s in buckets] + [
        s for s in sorted(buckets) if s not in SEGMENT_ORDER
    ]
    total = len(rows)
    quota = {s: max(1, round(size * len(buckets[s]) / total)) for s in present}
    while sum(quota.values()) > size:
        biggest = max(quota, key=lambda s: (quota[s], len(buckets[s])))
        if quota[biggest] <= 1:
            break
        quota[biggest] -= 1
    while sum(quota.values()) < size:
        biggest = max(present, key=lambda s: len(buckets[s]) - quota[s])
        quota[biggest] += 1

    rng = random.Random(seed)
    picked: list[dict] = []
    for segment in present:
        pool = sorted(buckets[segment], key=lambda r: (r["label_start"], r["contract"]))
        n = min(quota[segment], len(pool))
        picked.extend(rng.sample(pool, n))
    picked.sort(key=lambda r: (r["label_start"], r["contract"]))
    return picked[:size]


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def build_checklist(
    sampled: list[dict],
    probes: list[tuple[str, str, Callable[[dict], dict | None]]],
    *,
    seed: int,
    size: int,
    spine_fingerprint: str,
    target_name: str,
    product: str,
) -> dict:
    """probes: (feature 名, 来源 id, 取值函数)。取值函数返回含 availability_time 的字典。"""
    entries = []
    for i, row in enumerate(sampled):
        decision = row["decision_time"]
        features, unavailable = [], []
        for name, source_id, fn in probes:
            got = fn(row)
            if got is None or got.get("availability_time") is None:
                unavailable.append({"feature": name, "source": source_id})
                continue
            payload = {
                "feature": name,
                "source": source_id,
                "availability_time": _iso(got["availability_time"]),
                "lead_seconds": int(
                    (decision - got["availability_time"]).total_seconds()
                ),
            }
            payload.update(
                {k: v for k, v in got.items() if k != "availability_time"}
            )
            features.append(payload)
        entries.append(
            {
                "index": i,
                "product": product,
                "contract": row["contract"],
                "trading_day": int(row["trading_day"]),
                "session_name": row["session_name"],
                "decision_time": _iso(decision),
                "execution_time": _iso(row["execution_time"]),
                "label_start": _iso(row["label_start"]),
                "label_end": _iso(row["label_end"]),
                "episode_id": row["episode_id"],
                "sample_segment": row["sample_segment"],
                "target_value": row["value"],
                "no_trade": bool(row["no_trade"]),
                "no_trade_reason": row["no_trade_reason"],
                "n_returns": row["n_returns"],
                "features": features,
                "unavailable_sources": unavailable,
            }
        )
    return {
        "target_name": target_name,
        "product": product,
        "seed": seed,
        "sample_size": size,
        "spine_fingerprint": spine_fingerprint,
        "entries": entries,
    }


def render_markdown(checklist: dict) -> str:
    lines = [
        f"# SC Temporal Spine 人工回放清单（{checklist['target_name']}）",
        "",
        f"- 抽样种子：`{checklist['seed']}`（按样本段分层，结果可复现）",
        f"- 样本量：{checklist['sample_size']}",
        f"- spine 指纹：`{checklist['spine_fingerprint']}`",
        "",
        "核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，",
        "且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。",
        "",
    ]
    for e in checklist["entries"]:
        lines.append(
            f"## {e['index']:02d}. {e['contract']} {e['trading_day']} {e['session_name']} "
            f"（{e['sample_segment']}）"
        )
        lines.append("")
        lines.append(f"- Episode：`{e['episode_id']}`")
        lines.append(f"- 决策时点：`{e['decision_time']}`")
        lines.append(f"- 执行时点：`{e['execution_time']}`")
        lines.append(f"- label 窗口：`{e['label_start']}` → `{e['label_end']}`")
        if e["no_trade"]:
            lines.append(f"- 目标值：NULL（no-trade：{e['no_trade_reason']}）")
        else:
            lines.append(f"- 目标值：{e['target_value']:.8g}（{e['n_returns']} 个 1 分钟收益）")
        lines.append("")
        lines.append("| feature | 来源 | availability_time | 提前量(秒) | 取值 |")
        lines.append("|---|---|---|---:|---|")
        for f in e["features"]:
            extra = {
                k: v
                for k, v in f.items()
                if k not in ("feature", "source", "availability_time", "lead_seconds")
            }
            lines.append(
                f"| {f['feature']} | {f['source']} | `{f['availability_time']}` | "
                f"{f['lead_seconds']} | {extra} |"
            )
        if e["unavailable_sources"]:
            names = "、".join(u["source"] for u in e["unavailable_sources"])
            lines.append("")
            lines.append(f"> 该决策时点之前无可用观测的来源：{names}")
        lines.append("")
    return "\n".join(lines)
