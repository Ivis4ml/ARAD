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

#: label 规则 → 说明。**必须用映射派发**：原实现是两分支 if/else 且 else 落在已实现波动上，
#: 新规则只加进校验元组而忘了加分支时，会静默地以新 target 的名义物化 RV。
LABEL_RULES: dict[str, str] = {
    "full_session": "整个 session 作为 label 窗口",
    "first_k_minutes": "开盘后 K 分钟",
    "entry_to_close": "入场时刻到 session 收盘",
}

#: label 值本身就是一条**有符号收益**的规则。Sharpe 只有在这些规则下才有定义。
RETURN_LABEL_RULES = frozenset({"entry_to_close"})

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
        ("entry_price", pa.float64()),
        ("exit_price", pa.float64()),
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
        if self.label_rule not in LABEL_RULES:
            raise ValueError(
                f"未知的 label_rule {self.label_rule!r}；可选 {sorted(LABEL_RULES)}"
            )
        if self.label_is_return and not self.tradable_claim:
            raise ValueError(
                f"{self.name}：label 是收益却不声明 tradable_claim，两者必须一致"
            )

    def decision_time(self, window: SessionWindow) -> datetime:
        return window.open - timedelta(seconds=self.execution_lag_seconds)

    @property
    def entry_offset_minutes(self) -> int:
        return int(self.params.get("entry_offset_minutes", 0))

    @property
    def label_is_return(self) -> bool:
        """label 值是否本身就是一条有符号收益。"""
        return self.label_rule in RETURN_LABEL_RULES

    def execution_time(self, window: SessionWindow) -> datetime:
        """真正成交的时刻。

        `entry_to_close` 下它是 `open + entry_offset`，而不是开盘 —— 开盘价来自
        集合竞价，对决策时点不可执行（`sc_open_gap_absorption` 已记录这条假设）。
        """
        return window.open + timedelta(minutes=self.entry_offset_minutes)

    def label_window(self, window: SessionWindow) -> tuple[datetime, datetime]:
        if self.label_rule == "first_k_minutes":
            k = int(self.params.get("k_minutes", 30))
            return window.open, min(window.open + timedelta(minutes=k), window.close)
        if self.label_rule == "entry_to_close":
            # label 窗口自**入场时刻**起：收益是从这一刻捕获的，开盘跳空不在其中
            return self.execution_time(window), window.close
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
            "label_is_return": self.label_is_return,
        }


RV_NEXT_SESSION = TargetSpec(
    name="sc_rv_next_session",
    kind="primary",
    description=(
        "决策 cutoff（session 开盘前 execution_lag 秒）之后，下一个 SC session 的"
        "已实现波动：同一连续竞价 segment 内相邻 1 分钟 bar 对数收益的平方和开方。"
        "集合竞价 bar 与跨 segment、跨 session 的价格变化不计入。"
        "**tradable_claim=False**：本数据集里没有 SC 的波动率工具，"
        "已实现波动是一个正的量级而不是可捕获的收益，因此它不承载可交易主张。"
        "原值为 True 属记录错误，2026-08-06 更正。"
    ),
    execution_lag_seconds=60,
    tradable_claim=False,
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

RET_NEXT_SESSION = TargetSpec(
    name="sc_ret_next_session",
    kind="primary",
    description=(
        "决策 cutoff 之后，下一个 SC session 从**入场时刻到收盘**的对数收益。"
        "入场时刻为开盘后 1 分钟，入场价取该分钟最后一笔（约 09:00:59），"
        "不是这一分钟的第一笔 —— 决策到成交需要时间，取本分钟最后一笔是保守的一侧。"
        "集合竞价成交价不参与，因此**开盘跳空不在本目标的主张之内**。"
        "入场或收盘价落在涨跌停上时判为无定义：那一刻买不进或卖不出。"
        "这是本数据集中第一个 label 本身即有符号收益的目标，Sharpe 因此才有定义。"
    ),
    execution_lag_seconds=60,
    tradable_claim=True,
    params={"entry_offset_minutes": 1},
    label_rule="entry_to_close",
)

TARGET_SPECS = (RV_NEXT_SESSION, RET_NEXT_SESSION, OPEN_GAP_ABSORPTION)


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
    #: 最小变动价位。涨跌停判据要用它做容差，交易所给出的限价与成交价之间
    #: 存在浮点噪声（实测 2.7e-13），精确相等会漏判。
    tick_size: float | None = None

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

    def returns(self, *, until: datetime | None = None) -> list[float]:
        """同一 segment 内相邻 bar 的对数收益。跨 segment 不产生收益。

        until 给出时只保留右端点不晚于该时刻的收益，用于窗口短于整个 session
        的目标（例如开盘后 K 分钟）。
        """
        out: list[float] = []
        for seg in self.segments:
            for a, b in pairwise(seg):
                if until is not None and b["bar_end"] > until:
                    continue
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

    def at_price_limit(self, price: float | None) -> bool:
        """该价格是否落在涨跌停上（按半个 tick 容差）。

        **不能用精确相等。**实测 sc2604 在 20260303 夜盘整段 330 根 bar 收于 572.3，
        而交易所限价字段是 572.3000000000002，差 2.7e-13；`price in (upper, lower)`
        返回 False，于是一个一手都买不到的 session 被物化成 `value=0.0, no_trade=False`，
        直接违反本模块假设 5「no-trade 一律是 NULL 加原因，绝不写 0.0」。
        """
        if price is None:
            return False
        tol = (self.tick_size or 0.0) / 2 or 1e-9
        return any(
            limit is not None and abs(price - limit) <= tol
            for limit in (self.upper_limit, self.lower_limit)
        )

    def is_limit_locked(self) -> bool:
        bars = self.segment_bars
        if not bars:
            return False
        closes = {b["close"] for b in bars}
        if len(closes) != 1:
            return False
        return self.at_price_limit(next(iter(closes)))


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
                    tick_size=product.tick_size,
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


def entry_to_close_return(
    session: SessionBars, *, entry_offset_minutes: int
) -> tuple[float | None, str | None, dict]:
    """从入场时刻到 session 收盘的对数收益。

    **入场价是开盘后第 `entry_offset_minutes` 分钟那根 bar 的收盘价**，也就是
    大约 09:00:59 的最后一笔，而不是这一分钟的第一笔（两者实测中位相差 11.5 个基点）。
    这样取是因为「决策 → 下单 → 成交」需要时间，取本分钟最后一笔是保守的一侧。
    集合竞价的成交价不参与：它对决策时点不可执行（本模块 OPEN_GAP_ABSORPTION 已记录
    这条假设），因此开盘跳空**不在本目标的主张之内**。

    涨跌停按**逐价**判断而非整段判断：入场那一刻锁在涨停上就买不进，收盘锁在跌停上
    就卖不出，两者都使这条收益无法捕获，与整段是否锁死无关。
    """
    extra: dict = {"entry_price": None, "exit_price": None, "open_price": session.open_price}
    if session.n_bars == 0:
        return None, "no_ticks", extra
    if session.total_volume == 0:
        return None, "zero_volume", extra
    entry = session.price_at(entry_offset_minutes)
    exit_price = session.close_price
    extra["entry_price"], extra["exit_price"] = entry, exit_price
    if entry is None or entry <= 0:
        return None, "no_entry_price", extra
    if exit_price is None or exit_price <= 0:
        return None, "no_exit_price", extra
    if session.at_price_limit(entry):
        return None, "entry_at_price_limit", extra
    if session.at_price_limit(exit_price):
        return None, "exit_at_price_limit", extra
    return math.log(exit_price / entry), None, extra


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
            entry_price = exit_price = None
            if spec.label_rule == "first_k_minutes":
                value, reason, extra = open_gap_absorption(
                    sb,
                    prev_sb,
                    k_minutes=int(spec.params["k_minutes"]),
                    min_abs_gap=float(spec.params["min_abs_gap"]),
                )
                n_returns = len(sb.returns(until=label_end))
                gap, move_k = extra["gap"], extra["move_k"]
                open_price, prev_close = extra["open_price"], extra["prev_close"]
            elif spec.label_rule == "entry_to_close":
                value, reason, extra = entry_to_close_return(
                    sb, entry_offset_minutes=spec.entry_offset_minutes
                )
                n_returns = len(sb.returns(until=label_end))
                entry_price, exit_price = extra["entry_price"], extra["exit_price"]
                open_price = extra["open_price"]
            elif spec.label_rule == "full_session":
                value, reason, n_returns = realized_volatility(sb)
                open_price = sb.open_price
            else:                                     # pragma: no cover - 由构造保证
                raise ValueError(f"label_rule {spec.label_rule!r} 没有物化分支")

            if value is not None and spec.label_is_return:
                # 建表期后置条件：有取值就必须有正的入场与出场价，且取值确实是它们的对数比
                assert entry_price and exit_price and entry_price > 0 and exit_price > 0
                assert abs(value - math.log(exit_price / entry_price)) < 1e-12

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
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                }
            )
    table = pa.Table.from_pylist(rows, schema=TARGET_SCHEMA)
    return table.sort_by([("contract", "ascending"), ("label_start", "ascending")])


def segment_counts(targets: pa.Table, *, valued_only: bool = False) -> dict[str, int]:
    """按样本段计数。缺省数**行**（含 no-trade 行）；valued_only 只数有取值的行。

    计数列取 target_name（恒非空）：用可空的 value 列计数会把 no-trade 行漏掉，
    使各段之和小于总行数。
    """
    table = targets
    if valued_only:
        table = table.filter(pc.equal(table.column("no_trade"), False))
    if table.num_rows == 0:
        return {}
    grouped = pa.TableGroupBy(table, ["sample_segment"]).aggregate([("target_name", "count")])
    return {
        r["sample_segment"]: int(r["target_name_count"]) for r in grouped.to_pylist()
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
