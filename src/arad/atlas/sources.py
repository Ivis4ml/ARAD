"""三源数据新鲜度：从 M1 manifest 读出，不重新扫描数据（决定 0003 层一）。

Atlas 不碰源数据目录。源仓库只读，且重新扫描属于采集流程；这里只读 manifest
本身写下的指纹与覆盖末日。manifest 不存在就如实显示"未生成"，不去猜。
"""

from __future__ import annotations

import json
from pathlib import Path

#: M1 扫描器产出的三源 manifest 文件名。
SOURCE_MANIFESTS = ("commodity_tick.json", "polymarket_tape.json", "cls_telegraph.json")

_END_KEYS = ("last_day", "last_date", "coverage_end", "max_date")


def _deep_max(node: object, keys: tuple[str, ...]) -> str:
    """在嵌套结构里取指定键的最大值。分区源的覆盖末日藏在子对象里。"""
    best = ""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in keys and isinstance(value, str):
                best = max(best, value)
            else:
                best = max(best, _deep_max(value, keys))
    elif isinstance(node, list):
        for item in node:
            best = max(best, _deep_max(item, keys))
    return best


def data_freshness(manifest_dir: str | Path) -> list[dict]:
    """读三源 manifest，返回指纹与覆盖末日。缺文件如实标注，不推断。"""
    root = Path(manifest_dir)
    out: list[dict] = []
    for name in SOURCE_MANIFESTS:
        path = root / name
        if not path.exists():
            out.append({"source_id": name.removesuffix(".json"), "status": "manifest 未生成"})
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        out.append(
            {
                "source_id": doc.get("source_id", name.removesuffix(".json")),
                "status": "已扫描",
                "fingerprint": doc.get("fingerprint", ""),
                "scanned_at": doc.get("generated_at", ""),
                "coverage_end": _deep_max(doc.get("facts", {}), _END_KEYS) or "未知",
                "findings": len(doc.get("findings", []) or []),
            }
        )
    return out
