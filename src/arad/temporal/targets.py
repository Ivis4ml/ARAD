"""目标（label）定义与物化。

primary：`sc_rv_next_session` —— 决策 cutoff 后下一个 SC session 的已实现波动。
diagnostic-only：`sc_open_gap_absorption` —— 同期开盘跳空在开盘后 K 分钟内被
吸收的比例，只用于验证信息是否到达，明确不作可交易 alpha 主张。

已记录的可逆假设：
1. RV 的收益序列只取**同一连续竞价 segment 内**相邻 1 分钟 bar 的对数收益。
   跨 segment（10:15-10:30、11:30-13:30）与跨 session 的价格变化不是 1 分钟波动。
2. 集合竞价 bar 不进入 RV 的收益序列。开盘跳空由 diagnostic target 单独度量，
   若把竞价并入 RV，两个目标会在开盘处机械地度量同一件事。
3. session 开盘价：集合竞价有成交时取竞价成交价，否则取第一根连续竞价 bar 的开盘价。
4. 跳空的前一收盘价必须来自**同一合约**的上一个 session，避免换月价差被当成跳空。
5. no-trade 一律是 NULL 加原因，绝不写 0.0。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from itertools import pairwise

import pyarrow as pa
import pyarrow.compute as pc

from .asof import assert_decision_precedes_label
from .episode import SampleSegment, classify_segment, episode_id
from .sessions import Placement, ProductReference, SessionWindow

TARGET_KINDS = ("primary", "diagnostic_only")

TARGET_SCHEMA = pa.schema(
    [
        ("target_name", pa.string()),
        ("target_kind", pa.string()),
        ("tradable_claim", pa.bool_()),
        ("product", pa.string()),
        ("contract", pa.string()),
        ("trading_day", pa.int32()),
        ("session_name", pa.string()),
        ("session_seq", pa.int8()),
        ("decision_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("execution_time", pa.timestamp("us", tz="Asia/Shanghai")),
        ("label_start", pa.timestamp("us", tz="Asia/Shanghai")),
        ("label_end", pa.timestamp("us", tz="Asia/Shanghai")),
        ("value", pa.float64()),
        ("no_trade", pa.bool_()),
        ("no_trade_reason", pa.string()),
        ("n_returns", pa.int32()),
        ("session_volume", pa.int64()),
        ("episode_id", pa.string()),
        ("sample_segment", pa.string()),
        ("is_roll", pa.bool_()),
        ("gap", pa.float64()),
        ("move_k", pa.float64()),
        ("open_price", pa.float64()),
        ("prev_close", pa.float64()),
    ]
)


@dataclass(frozen=True)
class TargetSpec:
    name: str
    kind: str
    description: str
    execution_lag_seconds: int
    tradable_claim: bool
    params: dict
    label_rule: str = "full_session"

    def __post_init__(self) -> None:
        if self.kind not in TARGET_KINDS:
            raise ValueError(f"未知的 target kind {self.kind!r}，可选 {TARGET_KINDS}")
        if self.execution_lag_seconds <= 0:
            raise ValueError(
                "execution_lag_seconds 必须为正：决策时点等于 label 起点时，"
                "任何 feature 都无法严格早于标签"
            )
        if self.label_rule not in ("full_session", "first_k_minutes"):
            raise ValueError(f"未知的 label_rule {self.label_rule!r}")

    def decision_time(self, window: SessionWindow) -> datetime:
        return window.open - timedelta(seconds=self.execution_lag_seconds)

    def execution_time(self, window: SessionWindow) -> datetime:
        return window.open

    def label_window(self, window: SessionWindow) -> tuple[datetime, datetime]:
        if self.label_rule == "first_k_minutes":
            k = int(self.params.get("k_minutes", 30))
            return window.open, min(window.open + timedelta(minutes=k), window.close)
        return window.open, window.close

    def record(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "execution_lag_seconds": self.execution_lag_seconds,
            "tradable_claim": self.tradable_claim,
            "params": dict(self.params),
            "label_rule": self.label_rule,
        }


RV_NEXT_SESSION = TargetSpec(
    name="sc_rv_next_session",
    kind="primary",
    description=(
        "决策 cutoff（session 开盘前 execution_lag 秒）之后，下一个 SC session 的"
        "已实现波动：同一连续竞价 segment 内相邻 1 分钟 bar 对数收益的平方和开方。"
        "集合竞价 bar 与跨 segment、跨 session 的价格变化不计入。"
    ),
    execution_lag_seconds=60,
    tradable_claim=True,
    params={"min_returns": 2},
    label_rule="full_session",
)

OPEN_GAP_ABSORPTION = TargetSpec(
    name="sc_open_gap_absorption",
    kind="diagnostic_only",
    description=(
        "同期开盘跳空吸收：开盘跳空在开盘后 K 分钟内被反向抹去的比例。"
        "开盘价对决策时点而言不可执行，本目标只验证信息是否在开盘处到达，"
        "不作可交易 alpha 主张，也不得用于 Production 升级。"
    ),
    execution_lag_seconds=60,
    tradable_claim=False,
    params={"k_minutes": 30, "min_abs_gap": 0.0005},
    label_rule="first_k_minutes",
)

TARGET_SPECS = (RV_NEXT_SESSION, OPEN_GAP_ABSORPTION)


@dataclass
class SessionBars:
    """一个 (合约, 交易日, session) 的 bar 视图。"""

    product: str
    contract: str
    trading_day: date
    session_seq: int
    session_name: str
    window: SessionWindow
    auction: dict | None = None
    segments: list[list[dict]] = field(default_factory=list)
    upper_limit: float | None = None
    lower_limit: float | None = None

    @property
    def segment_bars(self) -> list[dict]:
        return [b for seg in self.segments for b in seg]

    @property
    def n_bars(self) -> int:
        return len(self.segment_bars)

    @property
    def open_price(self) -> float | None:
        if self.auction is not None and (self.auction.get("volume") or 0) > 0:
            return self.auction["close"]
        bars = self.segment_bars
        return bars[0]["open"] if bars else None

    @property
    def close_price(self) -> float | None:
        bars = self.segment_bars
        return bars[-1]["close"] if bars else None

    @property
    def total_volume(self) -> int:
        vol = sum(b["volume"] or 0 for b in self.segment_bars)
        if self.auction is not None:
            vol += self.auction.get("volume") or 0
        return int(vol)

    def returns(self) -> list[float]:
        """同一 segment 内相邻 bar 的对数收益。跨 segment 不产生收益。"""
        out: list[float] = []
        for seg in self.segments:
            for a, b in pairwise(seg):
                if a["close"] and b["close"] and a["close"] > 0 and b["close"] > 0:
                    out.append(math.log(b["close"] / a["close"]))
        return out

    def price_at(self, offset_minutes: int) -> float | None:
        """开盘后 offset 分钟时点的价格：右端点不晚于该时点的最后一根 bar 的收盘。"""
        cutoff = self.window.open + timedelta(minutes=offset_minutes)
        last = None
        for b in self.segment_bars:
            if b["bar_end"] <= cutoff:
                last = b["close"]
        return last

    def is_limit_locked(self) -> bool:
        bars = self.segment_bars
        if not bars:
            return False
        closes = {b["close"] for b in bars}
        if len(closes) != 1:
            return False
        only = next(iter(closes))
        return only in (self.upper_limit, self.lower_limit)


def build_session_bars(
    bars: pa.Table,
    *,
    product: ProductReference,
    prev_trading_day: date | None = None,
    prev_lookup=None,
) -> list[SessionBars]:
    """把 1 分钟 bar 表整理为按 (合约, session) 的视图。

    对每个出现过 bar 的 (合约, 交易日) 都产生时段表声明的全部 session，
    包括没有任何 bar 的 session：缺数据必须以 no-trade 记录，不能整段消失。
    """
    if bars.num_rows == 0:
        return []
    rows = bars.to_pylist()
    grouped: dict[tuple[str, int], list[dict]] = {}
    for r in rows:
        grouped.setdefault((r["contract"], r["trading_day"]), []).append(r)

    out: list[SessionBars] = []
    for (contract, td_int), group in sorted(grouped.items()):
        s = str(td_int)
        trading_day = date(int(s[:4]), int(s[4:6]), int(s[6:]))
        prev = prev_lookup(trading_day) if prev_lookup else prev_trading_day
        windows = product.sessions.windows(trading_day, prev_trading_day=prev)
        limits = [r for r in group if r["upper_limit"] is not None]
        upper = limits[-1]["upper_limit"] if limits else None
        lower = limits[-1]["lower_limit"] if limits else None
        for w in windows:
            in_window = sorted(
                (r for r in group if r["session_seq"] == w.seq),
                key=lambda r: r["bar_start"],
            )
            auction_rows = [r for r in in_window if r["placement"] == Placement.AUCTION.value]
            segments: list[list[dict]] = [[] for _ in w.segments]
            for r in in_window:
                if r["placement"] != Placement.SEGMENT.value:
                    continue
                idx = int(r["segment_idx"])
                if 0 <= idx < len(segments):
                    segments[idx].append(r)
            out.append(
                SessionBars(
                    product=product.product,
                    contract=contract,
                    trading_day=trading_day,
                    session_seq=w.seq,
                    session_name=w.name,
                    window=w,
                    auction=auction_rows[-1] if auction_rows else None,
                    segments=segments,
                    upper_limit=upper,
                    lower_limit=lower,
                )
            )
    return sorted(out, key=lambda sb: (sb.contract, sb.window.open))


def realized_volatility(session: SessionBars) -> tuple[float | None, str | None, int]:
    rets = session.returns()
    if session.n_bars == 0:
        return None, "no_ticks", 0
    if session.total_volume == 0:
        return None, "zero_volume", len(rets)
    if session.is_limit_locked():
        return None, "limit_locked", len(rets)
    if len(rets) < 2:
        return None, "insufficient_returns", len(rets)
    return math.sqrt(sum(r * r for r in rets)), None, len(rets)


def open_gap_absorption(
    session: SessionBars,
    prev_session: SessionBars | None,
    *,
    k_minutes: int,
    min_abs_gap: float,
) -> tuple[float | None, str | None, dict]:
    extra: dict = {"gap": None, "move_k": None, "open_price": None, "prev_close": None}
    if prev_session is None:
        return None, "no_prev_session", extra
    if prev_session.contract != session.contract:
        return None, "prev_session_contract_mismatch", extra
    open_price = session.open_price
    prev_close = prev_session.close_price
    extra["open_price"] = open_price
    extra["prev_close"] = prev_close
    if open_price is None or session.n_bars == 0:
        return None, "no_ticks", extra
    if prev_close is None or prev_close <= 0 or open_price <= 0:
        return None, "no_prev_close", extra
    gap = math.log(open_price / prev_close)
    extra["gap"] = gap
    if abs(gap) < min_abs_gap:
        return None, "gap_below_threshold", extra
    p_k = session.price_at(k_minutes)
    if p_k is None or p_k <= 0:
        return None, "no_price_at_horizon", extra
    move = math.log(p_k / open_price)
    extra["move_k"] = move
    return -move / gap, None, extra


def build_target_table(
    sessions: list[SessionBars],
    spec: TargetSpec,
    *,
    product: ProductReference,
    freeze_at: datetime | None = None,
    embargo: timedelta = timedelta(0),
    episode_grain: str = "trading_day",
    roll_days: set[date] | None = None,
) -> pa.Table:
    """把 session 视图物化为一张目标表（含 no-trade 行）。"""
    by_contract: dict[str, list[SessionBars]] = {}
    for sb in sorted(sessions, key=lambda s: (s.contract, s.window.open)):
        by_contract.setdefault(sb.contract, []).append(sb)

    rows = []
    for contract, seq in by_contract.items():
        for i, sb in enumerate(seq):
            window = sb.window
            decision = spec.decision_time(window)
            label_start, label_end = spec.label_window(window)
            assert_decision_precedes_label(decision, label_start)
            prev_sb = seq[i - 1] if i > 0 else None

            gap = move_k = open_price = prev_close = None
            if spec.label_rule == "first_k_minutes":
                value, reason, extra = open_gap_absorption(
                    sb,
                    prev_sb,
                    k_minutes=int(spec.params["k_minutes"]),
                    min_abs_gap=float(spec.params["min_abs_gap"]),
                )
                n_returns = len(sb.returns())
                gap, move_k = extra["gap"], extra["move_k"]
                open_price, prev_close = extra["open_price"], extra["prev_close"]
            else:
                value, reason, n_returns = realized_volatility(sb)
                open_price = sb.open_price

            rows.append(
                {
                    "target_name": spec.name,
                    "target_kind": spec.kind,
                    "tradable_claim": spec.tradable_claim,
                    "product": product.product,
                    "contract": contract,
                    "trading_day": int(sb.trading_day.strftime("%Y%m%d")),
                    "session_name": sb.session_name,
                    "session_seq": sb.session_seq,
                    "decision_time": decision,
                    "execution_time": spec.execution_time(window),
                    "label_start": label_start,
                    "label_end": label_end,
                    "value": value,
                    "no_trade": value is None,
                    "no_trade_reason": reason,
                    "n_returns": n_returns,
                    "session_volume": sb.total_volume,
                    "episode_id": episode_id(
                        product.product, sb.trading_day, sb.session_seq, grain=episode_grain
                    ),
                    "sample_segment": classify_segment(
                        label_start, label_end, freeze_at=freeze_at, embargo=embargo
                    ).value,
                    "is_roll": (sb.trading_day in roll_days) if roll_days is not None else None,
                    "gap": gap,
                    "move_k": move_k,
                    "open_price": open_price,
                    "prev_close": prev_close,
                }
            )
    table = pa.Table.from_pylist(rows, schema=TARGET_SCHEMA)
    return table.sort_by([("contract", "ascending"), ("label_start", "ascending")])


def segment_counts(targets: pa.Table) -> dict[str, int]:
    if targets.num_rows == 0:
        return {}
    grouped = pa.TableGroupBy(targets, ["sample_segment"]).aggregate([("value", "count")])
    return {
        r["sample_segment"]: int(r["value_count"]) for r in grouped.to_pylist()
    }


def no_trade_counts(targets: pa.Table) -> dict[str, int]:
    sub = targets.filter(pc.equal(targets.column("no_trade"), True))
    if sub.num_rows == 0:
        return {}
    grouped = pa.TableGroupBy(sub, ["no_trade_reason"]).aggregate([("no_trade", "count")])
    return {
        str(r["no_trade_reason"]): int(r["no_trade_count"]) for r in grouped.to_pylist()
    }


SampleSegmentValues = tuple(s.value for s in SampleSegment)
