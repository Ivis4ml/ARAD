"""运行目录：把一次研究的全部产物落成可被独立 app 读取的结构（M9.5）。

此前 Atlas 是「把投影注入单文件 HTML」，一次运行只能看一次、看不了历史、也没法并排
比较。改成 `runs/<run_id>/` 之后，app 变成读运行目录的独立应用，而单文件那条路保留 ——
它不需要服务器，把一次运行整个带走只要一个文件，这是真实的优点，不是遗留包袱。

目录结构（参照人类 minute_factor_agent 的 runs/ 约定）：

    runs/<run_id>/
      manifest.json     这次运行是什么：族、轮数、判决、账本指纹
      atlas.json        完整投影（与单文件里注入的是同一份）
      events.jsonl      账本事件流，供逐拍回放与增量拉取
      cards/*.md|.py    因子卡：给人看的说明，与可直接运行的代码

`manifest.json` 刻意只放**索引级**的字段：列表页要能在不读 atlas.json 的前提下渲染。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .project import AtlasProjection

RUNS_VERSION = "0.1.0"


@dataclass(frozen=True)
class RunSummary:
    """列表页需要的最少信息。"""

    run_id: str
    created_at: str
    family: str | None
    studies: int
    statistical_denominator: int
    proposal_denominator: int
    headline: str
    exceeded_band: bool
    cards: int
    chain_intact: bool

    def payload(self) -> dict:
        return {**self.__dict__, "runs_version": RUNS_VERSION}


def write_run(
    projection: AtlasProjection,
    root: str,
    run_id: str,
    *,
    events: list[dict],
    cards: list[dict] | None = None,
    freshness: list[dict] | None = None,
) -> dict:
    """落一次运行。**只写不改**：同一个 run_id 重复写会覆盖，因此调用方负责给新 id。"""
    base = Path(root) / run_id
    (base / "cards").mkdir(parents=True, exist_ok=True)

    payload = projection.to_dict()
    payload["data_freshness"] = freshness or []
    (base / "atlas.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    with (base / "events.jsonl").open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

    written = 0
    for card in cards or []:
        stem = str(card["feature_id"])[:80]
        (base / "cards" / f"{stem}.py").write_text(card["code"], encoding="utf-8")
        (base / "cards" / f"{stem}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        written += 1

    verdict = projection.search_verdict or {}
    summary = RunSummary(
        run_id=run_id,
        created_at=datetime.now(UTC).isoformat(),
        family=projection.denominators.get("family"),
        studies=len(projection.studies),
        statistical_denominator=projection.denominators.get("statistical_denominator", 0),
        proposal_denominator=projection.denominators.get("proposal_denominator", 0),
        headline=verdict.get("headline", "这份账本里还没有走到判决的研究。"),
        exceeded_band=bool(verdict.get("exceeded_band")),
        cards=written,
        chain_intact=bool(projection.chain.get("intact")),
    )
    (base / "manifest.json").write_text(
        json.dumps(summary.payload(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary.payload()


def list_runs(root: str) -> list[dict]:
    """列出运行，最新的在前。读不动的目录如实跳过，不猜。"""
    base = Path(root)
    if not base.is_dir():
        return []
    out: list[dict] = []
    for entry in sorted(base.iterdir()):
        manifest = entry / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            out.append(json.loads(manifest.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(out, key=lambda r: r.get("created_at", ""), reverse=True)


def read_artifact(root: str, run_id: str, name: str) -> dict | list | None:
    """读一次运行的产物。`run_id` 与 `name` 都做过路径约束，不接受穿越。"""
    if not _safe(run_id) or not _safe(name):
        return None
    base = Path(root) / run_id
    if name == "events":
        path = base / "events.jsonl"
        if not path.is_file():
            return None
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    if name == "cards":
        folder = base / "cards"
        if not folder.is_dir():
            return []
        return [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(folder.glob("*.json"))]
    path = base / f"{name}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _safe(name: str) -> bool:
    """只允许普通的名字。路径穿越在这里挡掉，不指望上游。"""
    return bool(name) and "/" not in name and "\\" not in name and not name.startswith(".") \
        and os.pardir not in name
