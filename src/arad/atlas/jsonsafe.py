"""JSON 边界的数值净化。

Python 的 `json.dumps` 默认允许 NaN/Infinity（非标准扩展），浏览器的 `JSON.parse`
按 RFC 8259 拒绝。实测形态：账本里一条 `abs_t: NaN` 让 `/api/live/projection`
产出非法 JSON，整个 app 打不开 —— 而**单文件模式一直没事**，因为它把同一份数据
注入成 JS 字面量，`NaN` 在 JS 里合法。同一份数据、两条通路、一条炸，
这类缺陷只能在边界统一杀掉。

非有限值一律变 None：前端把 null 显示为「—」，这与解释器「无定义返回 None
绝不返回 0」是同一条纪律。
"""

from __future__ import annotations

import math
from typing import Any


def finite(value: Any) -> Any:
    """递归替换非有限浮点为 None。dict/list/tuple 之外原样返回。"""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: finite(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite(v) for v in value]
    return value
