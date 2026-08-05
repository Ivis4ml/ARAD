"""PIT Market Index：Polymarket 市场的点时化身份与资格（M2.5）。

两层严格分开，这是消除幸存者偏差的关键：

- **存在性（Presence）**由**首笔公开成交**决定。市场在 `eligible_from` 之后才存在，
  `eligible_from = 首笔成交的 block_timestamp + 冻结的可得性延迟`。不使用全窗口
  成交量、最终活跃度、resolution 或 winner。
- **流动性资格（Eligibility）**只由**决策时点之前的窗口**决定，且**不**决定成员资格。
  它回答的是"某个 Study 此刻是否允许使用这个市场"，门槛由每个 Study 自己冻结后
  传入；本模块不产生任何全局"优质市场表"。

relay / venue 去重在现有数据上无法执行（两段 tape 都没有相应列），因此一切
名义额类指标都是 provisional，不得单独决定成员资格。
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .errors import LookaheadError

INDEX_VERSION = "pit-market-index-v1"

PRESENCE_SCHEMA = pa.schema(
    [
        ("condition_id", pa.string()),
        ("first_trade_ts", pa.int64()),
        ("eligible_from", pa.timestamp("us", tz="UTC")),
    ]
)

ASSET_PRESENCE_SCHEMA = pa.schema(
    [
        ("asset_id", pa.string()),
        ("condition_id", pa.string()),
        ("first_trade_ts", pa.int64()),
        ("eligible_from", pa.timestamp("us", tz="UTC")),
    ]
)


class OrphanCensusPartition(RuntimeError):
    """普查目录里存在来源已消失的孤儿产物。索引拒绝加载。"""


@dataclass(frozen=True)
class PitMarketIndexConfig:
    """冻结的索引参数。任何一项变化都必须体现在产物指纹里。"""

    availability_delay_seconds: int = 0
    version: str = INDEX_VERSION

    def describe(self) -> dict:
        return {
            "version": self.version,
            "availability_delay_seconds": self.availability_delay_seconds,
            "availability_rule": (
                "eligible_from = 首笔公开成交的 block_timestamp + "
                f"{self.availability_delay_seconds} 秒；block_timestamp 按 M1 合同"
                "是撮合时刻的保守下界，延迟为 0 时仍不构成前视"
            ),
            "membership_rule": (
                "成员资格只由首笔可见成交决定；滚动流动性不参与成员资格判定"
            ),
        }


def _require_utc(ts: datetime, what: str) -> datetime:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise ValueError(f"{what} 必须带时区：{ts!r}")
    return ts


def _day_bounds(date_str: str) -> tuple[datetime, datetime]:
    """分区日期覆盖 UTC 的 [d 00:00, d+1 00:00)。该日在 d+1 00:00 才完整。"""
    day = datetime.fromisoformat(date_str).replace(tzinfo=UTC)
    return day, day + timedelta(days=1)


def complete_days_before(cutoff: datetime, lookback_days: int) -> list[str]:
    """决策时点之前**最近 lookback_days 个已完整结束**的 UTC 分区日。

    这是滚动窗口的唯一定义，`eligibility_at` 与普查的 cutoff 统计共用它：
    此前两处各写一套（一处按"日起点落在窗口内"、一处按"往回数 N 个日期"），
    对非午夜 cutoff 会相差一天。
    """
    if lookback_days <= 0:
        raise ValueError("lookback_days 必须为正")
    cut = cutoff.astimezone(UTC)
    days: list[str] = []
    k = 0
    while len(days) < lookback_days:
        k += 1
        candidate = (cut - timedelta(days=k)).date()
        if datetime.combine(candidate, datetime.min.time(), tzinfo=UTC) + timedelta(days=1) <= cut:
            days.append(candidate.isoformat())
        if k > lookback_days + 2:
            break
    return sorted(days)


class PitMarketIndex:
    """由普查产物构造的点时化市场索引。"""

    def __init__(
        self,
        market_day: pa.Table,
        *,
        asset_day: pa.Table | None = None,
        config: PitMarketIndexConfig | None = None,
    ):
        self.config = config or PitMarketIndexConfig()
        self.market_day = self._collapse(market_day)
        self.asset_day = (
            self._collapse_assets(asset_day) if asset_day is not None else None
        )
        self._presence = self._build_presence(
            self.market_day, self.config, key="condition_id"
        )
        self._asset_presence = (
            self._build_presence(self.asset_day, self.config, key="asset_id")
            if self.asset_day is not None
            else None
        )

    # ------------------------------------------------------------ 构造

    @classmethod
    def from_census_dir(
        cls,
        root: str,
        *,
        config: PitMarketIndexConfig | None = None,
        expected_keys: set[str] | None = None,
    ) -> PitMarketIndex:
        """加载普查产物。给出 expected_keys 时拒绝孤儿分区（来源已删除的旧产物）。"""
        market_files = sorted(glob.glob(os.path.join(root, "market_day", "*.parquet")))
        if not market_files:
            raise FileNotFoundError(f"{root} 下没有普查产物；请先运行 pm-index build")
        if expected_keys is not None:
            found = {os.path.basename(p)[: -len(".parquet")] for p in market_files}
            orphans = sorted(found - expected_keys)
            if orphans:
                raise OrphanCensusPartition(
                    f"普查目录含 {len(orphans)} 个来源已消失的孤儿分区："
                    f"{orphans[:5]}；索引拒绝加载，请重跑 build 以清理"
                )
        asset_files = sorted(glob.glob(os.path.join(root, "asset_day", "*.parquet")))
        market = pa.concat_tables([pq.read_table(p) for p in market_files])
        asset = (
            pa.concat_tables([pq.read_table(p) for p in asset_files]) if asset_files else None
        )
        return cls(market, asset_day=asset, config=config)

    @staticmethod
    def _collapse_assets(asset_day: pa.Table) -> pa.Table:
        if asset_day.num_rows == 0:
            return asset_day
        g = pa.TableGroupBy(asset_day, ["date", "condition_id", "asset_id"]).aggregate(
            [("trades", "sum"), ("notional", "sum"), ("first_ts", "min"),
             ("last_ts", "max"), ("outcome_seq", "min")]
        )
        return pa.table(
            {
                "date": g.column("date"),
                "condition_id": g.column("condition_id"),
                "asset_id": g.column("asset_id"),
                "outcome_seq": pc.cast(g.column("outcome_seq_min"), pa.int64()),
                "trades": pc.cast(g.column("trades_sum"), pa.int64()),
                "notional": pc.cast(g.column("notional_sum"), pa.float64()),
                "first_ts": pc.cast(g.column("first_ts_min"), pa.int64()),
                "last_ts": pc.cast(g.column("last_ts_max"), pa.int64()),
            }
        ).sort_by([("date", "ascending"), ("asset_id", "ascending")])

    @staticmethod
    def _collapse(market_day: pa.Table) -> pa.Table:
        """两段 tape 在接缝日各有一个分区，同一 (日, 市场) 需要合并为一行。"""
        if market_day.num_rows == 0:
            return market_day
        grouped = pa.TableGroupBy(market_day, ["date", "condition_id"]).aggregate(
            [
                ("trades", "sum"),
                ("notional", "sum"),
                ("first_ts", "min"),
                ("last_ts", "max"),
                ("active_seconds", "sum"),
                ("price_changes", "sum"),
                ("max_gap_seconds", "max"),
            ]
        )
        return pa.table(
            {
                "date": grouped.column("date"),
                "condition_id": grouped.column("condition_id"),
                "trades": pc.cast(grouped.column("trades_sum"), pa.int64()),
                "notional": pc.cast(grouped.column("notional_sum"), pa.float64()),
                "first_ts": pc.cast(grouped.column("first_ts_min"), pa.int64()),
                "last_ts": pc.cast(grouped.column("last_ts_max"), pa.int64()),
                "active_seconds": pc.cast(grouped.column("active_seconds_sum"), pa.int64()),
                "price_changes": pc.cast(grouped.column("price_changes_sum"), pa.int64()),
                "max_gap_seconds": pc.cast(grouped.column("max_gap_seconds_max"), pa.int64()),
            }
        ).sort_by([("date", "ascending"), ("condition_id", "ascending")])

    @staticmethod
    def _build_presence(
        day_table: pa.Table, config: PitMarketIndexConfig, *, key: str
    ) -> pa.Table:
        schema = PRESENCE_SCHEMA if key == "condition_id" else ASSET_PRESENCE_SCHEMA
        if day_table is None or day_table.num_rows == 0:
            return schema.empty_table()
        keys = [key] if key == "condition_id" else ["asset_id", "condition_id"]
        grouped = pa.TableGroupBy(day_table, keys).aggregate([("first_ts", "min")])
        first = pc.cast(grouped.column("first_ts_min"), pa.int64())
        eligible = pc.cast(
            pc.multiply(pc.add(first, config.availability_delay_seconds), 1_000_000),
            pa.timestamp("us", tz="UTC"),
        )
        cols = {k: grouped.column(k) for k in keys}
        cols["first_trade_ts"] = first
        cols["eligible_from"] = eligible
        return pa.table(cols, schema=schema).sort_by(
            [("eligible_from", "ascending"), (key, "ascending")]
        )

    # ------------------------------------------------------------ 查询

    @property
    def presence(self) -> pa.Table:
        return self._presence

    @property
    def asset_presence(self) -> pa.Table:
        """asset 级点时化身份。与市场级同规则：首笔公开成交之后才存在。"""
        if self._asset_presence is None:
            raise ValueError("本索引未加载 asset_day 普查产物，无 asset 级身份")
        return self._asset_presence

    def assets_present_at(self, cutoff: datetime) -> pa.Table:
        _require_utc(cutoff, "cutoff")
        table = self.asset_presence
        cut = pa.scalar(cutoff.astimezone(UTC), pa.timestamp("us", tz="UTC"))
        return table.filter(pc.less(table.column("eligible_from"), cut))

    def present_at(self, cutoff: datetime) -> pa.Table:
        """在决策时点已存在的市场：eligible_from **严格早于** cutoff。"""
        _require_utc(cutoff, "cutoff")
        cut = pa.scalar(cutoff.astimezone(UTC), pa.timestamp("us", tz="UTC"))
        return self._presence.filter(pc.less(self._presence.column("eligible_from"), cut))

    def eligibility_at(self, cutoff: datetime, *, lookback_days: int) -> pa.Table:
        """决策时点之前 lookback_days 内的滚动流动性指标。

        只纳入**在 cutoff 之前已经完整结束**的分区日，因此结果对之后新到的成交
        完全不敏感。返回值不含任何门槛判定：`rolling_notional` 标为 provisional，
        门槛由调用方（Study）冻结后自行施加。
        """
        _require_utc(cutoff, "cutoff")
        days = complete_days_before(cutoff, lookback_days)
        window = self.market_day.filter(
            pc.is_in(self.market_day.column("date"), value_set=pa.array(days, pa.string()))
        )
        present = self.present_at(cutoff)
        if window.num_rows == 0:
            return _empty_eligibility(present)

        grouped = pa.TableGroupBy(window, ["condition_id"]).aggregate(
            [
                ("trades", "sum"),
                ("notional", "sum"),
                ("active_seconds", "sum"),
                ("price_changes", "sum"),
                ("max_gap_seconds", "max"),
                ("date", "count"),
            ]
        )
        rolling = pa.table(
            {
                "condition_id": grouped.column("condition_id"),
                "rolling_trades": pc.cast(grouped.column("trades_sum"), pa.int64()),
                "rolling_notional_provisional": pc.cast(
                    grouped.column("notional_sum"), pa.float64()
                ),
                "rolling_active_seconds": pc.cast(
                    grouped.column("active_seconds_sum"), pa.int64()
                ),
                "rolling_price_changes": pc.cast(
                    grouped.column("price_changes_sum"), pa.int64()
                ),
                "rolling_max_gap_seconds": pc.cast(
                    grouped.column("max_gap_seconds_max"), pa.int64()
                ),
                "rolling_active_days": pc.cast(grouped.column("date_count"), pa.int64()),
            }
        )
        # 只保留在 cutoff 已存在的市场；存在但窗口内无成交的市场保留并置零，
        # 不能因为最近没成交就把它从历史里抹掉。
        out = present.join(rolling, keys="condition_id", join_type="left outer")
        for col in (
            "rolling_trades",
            "rolling_active_seconds",
            "rolling_price_changes",
            "rolling_max_gap_seconds",
            "rolling_active_days",
        ):
            out = out.set_column(
                out.schema.get_field_index(col),
                col,
                pc.fill_null(out.column(col), 0),
            )
        idx = out.schema.get_field_index("rolling_notional_provisional")
        out = out.set_column(
            idx, "rolling_notional_provisional", pc.fill_null(out.column(idx), 0.0)
        )
        return out.sort_by([("condition_id", "ascending")])

    def assert_no_lookahead(self, cutoff: datetime) -> None:
        rows = self.present_at(cutoff)
        if rows.num_rows and pc.max(rows.column("eligible_from")).as_py() >= cutoff.astimezone(UTC):
            raise LookaheadError(f"present_at({cutoff}) 返回了 eligible_from 不早于 cutoff 的市场")

    def facts(self) -> dict:
        dates = self.market_day.column("date").to_pylist()
        return {
            "markets": self._presence.num_rows,
            "assets": self._asset_presence.num_rows if self._asset_presence is not None else None,
            "market_days": self.market_day.num_rows,
            "asset_days": self.asset_day.num_rows if self.asset_day is not None else None,
            "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None,
            "config": self.config.describe(),
        }


def _empty_eligibility(present: pa.Table) -> pa.Table:
    n = present.num_rows
    return pa.table(
        {
            "condition_id": present.column("condition_id"),
            "first_trade_ts": present.column("first_trade_ts"),
            "eligible_from": present.column("eligible_from"),
            "rolling_trades": pa.array([0] * n, pa.int64()),
            "rolling_notional_provisional": pa.array([0.0] * n, pa.float64()),
            "rolling_active_seconds": pa.array([0] * n, pa.int64()),
            "rolling_price_changes": pa.array([0] * n, pa.int64()),
            "rolling_max_gap_seconds": pa.array([0] * n, pa.int64()),
            "rolling_active_days": pa.array([0] * n, pa.int64()),
        }
    )


def kish_n_eff(weights: list[float]) -> float:
    """Kish 有效样本量。用于提醒：逐笔行数不是独立样本量。"""
    total = sum(weights)
    sq = sum(w * w for w in weights)
    return (total * total / sq) if sq > 0 else 0.0
