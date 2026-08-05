"""t-1 信息主力合约选择与换月事件。

规则只使用**前一交易日收盘后已知**的成交量与持仓；把当日数据喂进选择器
必须立即失败。来源归档自带的 `主力连续` 文件是当日口径的事后别名，
只用于报告一致率，不参与选择，也不用于调参。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pyarrow as pa
import pyarrow.compute as pc

from ..data_catalog.schema import QualityFinding, Severity
from .contracts import ContractCode
from .errors import LookaheadError

DOMINANT_SERIES_SCHEMA = pa.schema(
    [
        ("trading_day", pa.int32()),
        ("information_day", pa.int32()),
        ("contract", pa.string()),
        ("delivery_key", pa.int32()),
        ("volume_tm1", pa.int64()),
        ("open_interest_tm1", pa.float64()),
        ("prev_contract", pa.string()),
        ("is_roll", pa.bool_()),
        ("has_data_on_day", pa.bool_()),
        ("alias_contract", pa.string()),
        ("rule_version", pa.string()),
        ("reason", pa.string()),
    ]
)


@dataclass(frozen=True)
class DominantRule:
    """主力选择规则。version 随参数变化，使产物可追溯到确切规则。"""

    metric: str = "volume"
    tie_break: str = "open_interest"
    monotone_delivery: bool = True

    @property
    def version(self) -> str:
        mono = "monotone" if self.monotone_delivery else "free"
        return f"t1-{self.metric}-{self.tie_break}-{mono}-v1"


@dataclass(frozen=True)
class DominantSelection:
    trading_day: date
    information_day: date | None
    contract: str | None
    delivery_key: int | None
    volume_tm1: int | None
    open_interest_tm1: float | None
    rule_version: str
    reason: str


def _as_date(value: int) -> date:
    s = str(int(value))
    return date(int(s[:4]), int(s[4:6]), int(s[6:]))


def select_dominant(
    panel: pa.Table,
    trading_day: date,
    *,
    rule: DominantRule,
    previous: DominantSelection | None = None,
) -> DominantSelection:
    """从只含 t-1 及更早信息的日频面板中选出交易日 T 的主力合约。

    panel 至少包含 `trading_day`(YYYYMMDD int)、`contract`、`volume`、
    `open_interest` 四列。panel 含有 >= T 的任何一行都视为前视并报错：
    调用方必须先按信息可用性裁剪，而不是依赖本函数忽略多余的行。
    """
    td_int = int(trading_day.strftime("%Y%m%d"))
    if panel.num_rows:
        future = pc.unique(
            panel.filter(pc.greater_equal(panel.column("trading_day"), td_int)).column(
                "trading_day"
            )
        ).to_pylist()
        if future:
            raise LookaheadError(
                f"主力选择只允许使用 {td_int} 之前的信息，但面板含有交易日 "
                f"{sorted(int(d) for d in future)}"
            )
    if panel.num_rows == 0:
        return DominantSelection(
            trading_day=trading_day,
            information_day=None,
            contract=None,
            delivery_key=None,
            volume_tm1=None,
            open_interest_tm1=None,
            rule_version=rule.version,
            reason="no_prior_information",
        )

    info_day_int = int(pc.max(panel.column("trading_day")).as_py())
    latest = panel.filter(pc.equal(panel.column("trading_day"), info_day_int))
    rows = latest.to_pylist()

    floor_key = None
    if rule.monotone_delivery and previous is not None and previous.delivery_key is not None:
        floor_key = previous.delivery_key

    def key(row):
        return (row["volume"], row["open_interest"], _neg_code(row["contract"]))

    eligible = []
    for row in rows:
        code = ContractCode.parse(row["contract"])
        if floor_key is not None and code.delivery_key < floor_key:
            continue
        eligible.append((row, code))

    reason = "t1_max_volume"
    if not eligible:
        eligible = [(row, ContractCode.parse(row["contract"])) for row in rows]
        reason = "t1_max_volume_monotone_floor_unreachable"
    elif floor_key is not None and len(eligible) < len(rows):
        reason = "t1_max_volume_monotone_delivery_floor"

    best_row, best_code = max(eligible, key=lambda rc: key(rc[0]))
    return DominantSelection(
        trading_day=trading_day,
        information_day=_as_date(info_day_int),
        contract=best_row["contract"],
        delivery_key=best_code.delivery_key,
        volume_tm1=int(best_row["volume"]),
        open_interest_tm1=float(best_row["open_interest"]),
        rule_version=rule.version,
        reason=reason,
    )


def _neg_code(contract: str) -> tuple[int, ...]:
    """合约代码的确定性次级排序键：代码越小越优先（与 max 语义配合取负序）。"""
    return tuple(-ord(c) for c in contract)


def build_dominant_series(
    daily_panel: pa.Table,
    trading_days: list[date],
    *,
    rule: DominantRule,
    alias: dict[date, str] | None = None,
) -> tuple[pa.Table, list[QualityFinding]]:
    """逐日构造主力序列。每一日只把该日之前的面板喂给选择器。"""
    alias = alias or {}
    findings: list[QualityFinding] = []
    days_present: dict[int, set[str]] = {}
    for row in daily_panel.select(["trading_day", "contract"]).to_pylist():
        days_present.setdefault(int(row["trading_day"]), set()).add(row["contract"])

    rows = []
    previous: DominantSelection | None = None
    for day in sorted(trading_days):
        td_int = int(day.strftime("%Y%m%d"))
        prior = daily_panel.filter(pc.less(daily_panel.column("trading_day"), td_int))
        sel = select_dominant(prior, day, rule=rule, previous=previous)
        has_data = sel.contract is not None and sel.contract in days_present.get(td_int, set())
        is_roll = (
            previous is not None
            and previous.contract is not None
            and sel.contract is not None
            and sel.contract != previous.contract
        )
        if sel.contract is not None and not has_data:
            findings.append(
                QualityFinding(
                    severity=Severity.WARNING,
                    code="dominant.selected_contract_absent_on_day",
                    message=(
                        "按 t-1 信息选出的主力合约在当日没有数据；按 no-trade 记录，"
                        "不用当日信息替换选择"
                    ),
                    evidence={"trading_day": day.isoformat(), "contract": sel.contract},
                )
            )
        rows.append(
            {
                "trading_day": td_int,
                "information_day": (
                    int(sel.information_day.strftime("%Y%m%d")) if sel.information_day else None
                ),
                "contract": sel.contract,
                "delivery_key": sel.delivery_key,
                "volume_tm1": sel.volume_tm1,
                "open_interest_tm1": sel.open_interest_tm1,
                "prev_contract": previous.contract if previous else None,
                "is_roll": bool(is_roll),
                "has_data_on_day": bool(has_data),
                "alias_contract": alias.get(day),
                "rule_version": sel.rule_version,
                "reason": sel.reason,
            }
        )
        if sel.contract is not None:
            previous = sel
    table = pa.Table.from_pylist(rows, schema=DOMINANT_SERIES_SCHEMA)
    return table, findings


def alias_agreement_finding(series: pa.Table) -> QualityFinding:
    """报告本地 t-1 规则与来源 `主力连续` 别名的一致率。

    别名是当日口径的事后结果，与只用 t-1 信息的规则在换月前后本就应当不同；
    这里只报告，不据此调参，否则别名会从 QA 对照变成事实上的依赖。
    """
    rows = series.select(["trading_day", "contract", "alias_contract"]).to_pylist()
    compared = [r for r in rows if r["contract"] and r["alias_contract"]]
    agree = [r for r in compared if r["contract"] == r["alias_contract"]]
    disagree_days = [int(r["trading_day"]) for r in compared if r["contract"] != r["alias_contract"]]
    rate = len(agree) / len(compared) if compared else 0.0
    return QualityFinding(
        severity=Severity.INFO,
        code="dominant.alias_agreement",
        message="t-1 主力规则与来源主力连续别名的一致率（QA 对照，不作依赖）",
        evidence={
            "compared": len(compared),
            "agreed": len(agree),
            "agreement_rate": rate,
            "first_disagreement_days": sorted(disagree_days)[:20],
        },
    )
