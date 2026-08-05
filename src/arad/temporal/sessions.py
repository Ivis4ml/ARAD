"""品种时段表与 session 窗口。

时段表按 Merge-Plan-2 §8.6 采用"版本化权威参照"：时间来自交易所公布的合约
与交易时间规则，代码只负责校验实测 tick 是否与声明一致，不从数据反推时段。
不一致产生 QualityFinding，由人工裁决，不自动改写声明。

一个 session 内部可以有休息（10:15-10:30、11:30-13:30）。休息不是 session
中断：它不切分 session，也不切分交易日归属；但它切分**连续竞价 segment**，
因此跨 segment 的相邻 bar 之间不存在 1 分钟收益。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import Enum
from functools import cached_property
from zoneinfo import ZoneInfo

from ..data_catalog.schema import QualityFinding, Severity
from ..data_catalog.timeguard import natural_date_of_tick
from .errors import SessionTableError

SHANGHAI = ZoneInfo("Asia/Shanghai")

DAY_SECONDS = 86_400


def to_sod(t: time) -> int:
    return t.hour * 3600 + t.minute * 60 + t.second


class Placement(str, Enum):
    """一条 tick 相对时段表的位置。"""

    AUCTION = "auction"      # 集合竞价窗口
    SEGMENT = "segment"      # 连续竞价
    BREAK = "break"          # session 内部休息
    OUTSIDE = "outside"      # 时段表之外（例如 15:17 结算快照）


@dataclass(frozen=True)
class Segment:
    """一个连续竞价区间。end 为含端点（收盘打印属于本段）。"""

    name: str
    start: time
    end: time
    end_next_day: bool = False


@dataclass(frozen=True)
class Session:
    name: str
    seq: int
    anchor: str                      # "trading_day" | "prev_trading_day"
    open: time
    close: time
    segments: tuple[Segment, ...]
    auction_start: time | None = None
    close_next_day: bool = False


@dataclass(frozen=True)
class Classification:
    session_seq: int
    session_name: str
    segment_idx: int
    placement: Placement


@dataclass(frozen=True)
class SessionWindow:
    """某个交易日某个 session 的具体自然时间窗口（带时区）。"""

    product: str
    trading_day: date
    name: str
    seq: int
    open: datetime
    close: datetime
    segments: tuple[tuple[datetime, datetime], ...]
    auction_start: datetime | None

    def contains(self, ts: datetime) -> bool:
        return self.open <= ts <= self.close


# (起始秒, 结束秒（含）, session_seq, session_name, segment_idx, placement)
_Range = tuple[int, int, int, str, int, Placement]


@dataclass(frozen=True)
class SessionTable:
    product: str
    sessions: tuple[Session, ...]
    reference: str

    def __post_init__(self) -> None:
        if not self.sessions:
            raise SessionTableError(f"{self.product} 时段表为空")
        if not self.reference:
            raise SessionTableError(f"{self.product} 时段表缺少权威参照出处")

    def session(self, name: str) -> Session:
        for s in self.sessions:
            if s.name == name:
                return s
        raise SessionTableError(f"{self.product} 没有名为 {name!r} 的 session")

    # ------------------------------------------------------------ 归类

    @cached_property
    def _ranges(self) -> tuple[_Range, ...]:
        out: list[_Range] = []
        for s in self.sessions:
            if s.auction_start is not None:
                lo, hi = to_sod(s.auction_start), to_sod(s.open) - 1
                out.append((lo, hi, s.seq, s.name, -1, Placement.AUCTION))
            prev_end: int | None = None
            for idx, seg in enumerate(s.segments):
                lo, hi = to_sod(seg.start), to_sod(seg.end)
                if seg.end_next_day:
                    out.append((lo, DAY_SECONDS - 1, s.seq, s.name, idx, Placement.SEGMENT))
                    out.append((0, hi, s.seq, s.name, idx, Placement.SEGMENT))
                else:
                    out.append((lo, hi, s.seq, s.name, idx, Placement.SEGMENT))
                    if prev_end is not None and lo - 1 >= prev_end + 1:
                        out.append(
                            (prev_end + 1, lo - 1, s.seq, s.name, -1, Placement.BREAK)
                        )
                    prev_end = hi
        return tuple(sorted(out))

    def ranges(self) -> tuple[_Range, ...]:
        """展开为按秒的归类区间；跨零点的区间被拆成两段。区间端点均为含端点。"""
        return self._ranges

    def classify(self, seconds_of_day: int) -> Classification:
        for lo, hi, seq, name, idx, placement in self.ranges():
            if lo <= seconds_of_day <= hi:
                return Classification(seq, name, idx, placement)
        return Classification(-1, "", -1, Placement.OUTSIDE)

    # ------------------------------------------------------------ 自然日归属

    def natural_date_windows(self) -> tuple[tuple[int, int, str, int], ...]:
        """自然日归属窗口，覆盖全天 0 至 86400 秒。

        边界取在 08:00 与 20:00，与 M1 `timeguard.natural_date_of_tick` 的缺省
        规则在其定义域上逐点一致（见 test_sessions 的交叉校验）；本表额外覆盖
        缺省规则拒绝归属的死区（03:00-07:59 归夜盘次自然日，16:00-19:59 归当日），
        使盘后快照等 session 外行也能获得确定的时间戳后再被隔离。
        """
        return (
            (0, 8 * 3600, "prev_trading_day", 1),
            (8 * 3600, 20 * 3600, "trading_day", 0),
            (20 * 3600, DAY_SECONDS, "prev_trading_day", 0),
        )

    def requires_predecessor(self, seconds_of_day: int) -> bool:
        for lo, hi, anchor, _ in self.natural_date_windows():
            if lo <= seconds_of_day < hi:
                return anchor == "prev_trading_day"
        return False

    # ------------------------------------------------------------ 窗口

    def windows(
        self, trading_day: date, *, prev_trading_day: date | None
    ) -> tuple[SessionWindow, ...]:
        out: list[SessionWindow] = []
        for s in self.sessions:
            if s.anchor == "prev_trading_day":
                if prev_trading_day is None:
                    continue
                base = prev_trading_day
            else:
                base = trading_day
            open_ts = datetime.combine(base, s.open, tzinfo=SHANGHAI)
            close_base = base + timedelta(days=1) if s.close_next_day else base
            close_ts = datetime.combine(close_base, s.close, tzinfo=SHANGHAI)
            segs = []
            for seg in s.segments:
                seg_base = base + timedelta(days=1) if seg.end_next_day else base
                segs.append(
                    (
                        datetime.combine(base, seg.start, tzinfo=SHANGHAI),
                        datetime.combine(seg_base, seg.end, tzinfo=SHANGHAI),
                    )
                )
            auction = (
                datetime.combine(base, s.auction_start, tzinfo=SHANGHAI)
                if s.auction_start is not None
                else None
            )
            out.append(
                SessionWindow(
                    product=self.product,
                    trading_day=trading_day,
                    name=s.name,
                    seq=s.seq,
                    open=open_ts,
                    close=close_ts,
                    segments=tuple(segs),
                    auction_start=auction,
                )
            )
        return tuple(sorted(out, key=lambda w: w.open))

    def describe(self) -> dict:
        return {
            "product": self.product,
            "reference": self.reference,
            "sessions": [
                {
                    "name": s.name,
                    "seq": s.seq,
                    "anchor": s.anchor,
                    "auction_start": s.auction_start.isoformat() if s.auction_start else None,
                    "open": s.open.isoformat(),
                    "close": s.close.isoformat(),
                    "close_next_day": s.close_next_day,
                    "segments": [
                        {
                            "name": seg.name,
                            "start": seg.start.isoformat(),
                            "end": seg.end.isoformat(),
                            "end_next_day": seg.end_next_day,
                        }
                        for seg in s.segments
                    ],
                }
                for s in self.sessions
            ],
        }


def natural_date_for(
    table: SessionTable, trading_day: date, seconds_of_day: int, *, prev_trading_day: date | None
) -> date:
    """按时段表把 (TradingDay, 秒) 归属到自然日；实际计算复用 M1 的 timeguard。"""
    sod = seconds_of_day % DAY_SECONDS
    tick_time = time(sod // 3600, sod % 3600 // 60, sod % 60)
    if prev_trading_day is None and table.requires_predecessor(sod):
        raise SessionTableError(
            f"{trading_day.isoformat()} 的 {tick_time} 需要前一交易日才能归属自然日"
        )
    return natural_date_of_tick(
        trading_day,
        tick_time,
        prev_trading_day=prev_trading_day or trading_day,
        windows=table.natural_date_windows(),
    )


def verify_session_table(
    table: SessionTable, observed: dict[str, tuple[int, int]]
) -> list[QualityFinding]:
    """把实测的 session 首尾时刻与声明时段表比对。

    observed 的每个值是 (该 session 的首个 tick 秒, 末个 tick 秒)，按 session
    时间顺序而非数值大小给出（夜盘跨零点时末秒小于首秒）。
    """
    findings: list[QualityFinding] = []
    for name, (first, last) in sorted(observed.items()):
        for label, sod in (("first", first), ("last", last)):
            got = table.classify(sod)
            if got.placement is Placement.OUTSIDE or got.session_name != name:
                findings.append(
                    QualityFinding(
                        severity=Severity.WARNING,
                        code="sessions.observed_outside_declared",
                        message=(
                            f"{table.product} 的 {name} session 实测 {label} tick 落在"
                            "声明时段表之外；需人工裁决是交易所规则变化还是数据异常"
                        ),
                        evidence={
                            "product": table.product,
                            "session": name,
                            "which": label,
                            "seconds_of_day": sod,
                            "classified_as": got.placement.value,
                            "classified_session": got.session_name,
                        },
                    )
                )
    return findings


# ---------------------------------------------------------------------------
# SC（上海国际能源交易中心 原油期货）
# ---------------------------------------------------------------------------

SC_SESSIONS = SessionTable(
    product="sc",
    reference=(
        "上海国际能源交易中心《原油期货合约》与交易时间规则：日盘 09:00-10:15、"
        "10:30-11:30、13:30-15:00，连续交易（夜盘）21:00-次日 02:30；"
        "日盘集合竞价 08:55-08:59，夜盘集合竞价 20:55-20:59。"
        "版本：2026-08-05 人工录入的权威参照，未由数据反推。"
    ),
    sessions=(
        Session(
            name="night",
            seq=0,
            anchor="prev_trading_day",
            auction_start=time(20, 55),
            open=time(21, 0),
            close=time(2, 30),
            close_next_day=True,
            segments=(Segment(name="n0", start=time(21, 0), end=time(2, 30), end_next_day=True),),
        ),
        Session(
            name="day",
            seq=1,
            anchor="trading_day",
            auction_start=time(8, 55),
            open=time(9, 0),
            close=time(15, 0),
            segments=(
                Segment(name="d0", start=time(9, 0), end=time(10, 15)),
                Segment(name="d1", start=time(10, 30), end=time(11, 30)),
                Segment(name="d2", start=time(13, 30), end=time(15, 0)),
            ),
        ),
    ),
)


@dataclass(frozen=True)
class ProductReference:
    """品种的版本化权威参照：合约乘数、最小变动价位、交易所与时段表。"""

    product: str
    exchange: str
    multiplier: float
    tick_size: float
    sessions: SessionTable
    reference: str

    @property
    def reference_tick_return(self) -> float:
        """一个最小变动价位在典型价位上的相对幅度，用于跳空阈值等参数的量纲参照。"""
        return self.tick_size


SC = ProductReference(
    product="sc",
    exchange="INE",
    multiplier=1000.0,
    tick_size=0.1,
    sessions=SC_SESSIONS,
    reference=(
        "上海国际能源交易中心《原油期货合约》：交易单位 1000 桶/手，"
        "报价单位 元(人民币)/桶，最小变动价位 0.1 元/桶。"
        "M1 实测校验：Turnover = LastPrice × 1000 × Volume（含合约乘数）。"
    ),
)

PRODUCTS: dict[str, ProductReference] = {"sc": SC}
