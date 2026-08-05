"""temporal 层的硬边界异常。

这些异常是研究完整性边界，不是可选提醒：触发时必须让流程失败，
不允许降级为警告后继续产出目标值。
"""

from __future__ import annotations


class LookaheadError(RuntimeError):
    """使用了决策时点之后才可获得的信息。"""


class CalendarBoundaryError(RuntimeError):
    """交易日历无法回答该查询（越界或该日不在日历中）。拒绝猜测。"""


class SessionTableError(ValueError):
    """品种时段表定义或校验失败。"""
