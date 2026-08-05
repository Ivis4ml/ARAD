"""控制数据源的可用时间合同与 PIT 序列构造。

三个控制源都以**声明式** SourceManifest 登记：它们不是 M1 扫描出来的来源，
但同样必须先有可用时间合同才能被消费（M1 出口条件：没有合同的字段不可消费）。

- 财联社电报：走 M1 的 CLS manifest，热度字段在合同层被硬拒绝；
  可用时间 = 文件名日期 + Time（Asia/Shanghai）+ 声明的采集延迟。
- 国际油价（Alpha-Data intl/brent_daily.csv）：只有日期与数值，没有发布时刻。
  发布时点未经来源方核实，因此 `value` 标为 provisional，采用保守规则
  "D 的收盘价在 D+1 06:00 Asia/Shanghai 可用"，消费需受审计 override。
- Polymarket 市场登记表（cn_registry_v3.parquet）：**已弃用并隔离**（2026-08-05
  人类裁决）。ARAD 不再以它作为市场来源、市场映射或研究输入。其替代是从原始 tape
  推导的 PIT Market Index（存在性由首笔公开成交决定，流动性资格由过去窗口决定，
  见 `temporal/pm_market_index.py`）。本模块保留一个会主动报错的加载函数，
  使任何残留调用路径显式失败，而不是靠提示词约束（Merge-Plan-2 §7.2：
  提示词不是安全边界）。
"""

from __future__ import annotations

import csv
import glob
import os
import re
from datetime import date, datetime, timedelta

import pyarrow as pa
import pyarrow.parquet as pq

from ..data_catalog.schema import (
    FieldAvailability,
    SourceManifest,
    TimeSemantics,
)
from ..data_catalog.timeguard import require_epoch_seconds
from .asof import PitSeries
from .manifest import ControlContract
from .sessions import SHANGHAI

CLS_POLL_DELAY_SECONDS = 60
BRENT_AVAILABLE_AT_HOUR = 6  # D+1 06:00 Asia/Shanghai
BRENT_OVERRIDE_REASON = (
    "M2 as-of 演示：brent_daily.csv 只有日期与数值，发布时点未经来源方核实；"
    "采用保守规则 D+1 06:00 Asia/Shanghai，晚于 ICE 结算与美市收盘的任何合理时点。"
    "核实来源与发布时刻属于 acquisition 流程，需人工授权。"
)

PM_ALLOWED_FIELDS = (
    "condition_id",
    "slug",
    "category",
    "theme",
    "product",
    "first_ts",
    "last_ts",
    "admit_ts",
)
# 禁用理由以来源构造脚本 Alpha-Data/scripts/select_polymarket_markets.py 为准。
# 注意 usdc_win/n_win 的 win 指 window 而非 winning：它们是**全窗口**累计量，
# 不含结算信息，但对窗口内任一决策时点都是前视。
# sigma/orientation 来自事前注册的规则表（docs/mapping_taxonomy.md），
# 不是由历史结果拟合；它们被门禁的理由是 Merge-Plan-2 §8.9 的映射种子条款。
PM_BANNED_FIELDS = {
    "usdc_win": "窗口内累计名义额（全窗口聚合），对窗口内任一决策时点均为前视",
    "n_win": "窗口内累计成交笔数（全窗口聚合），对窗口内任一决策时点均为前视",
    "resolved_at": "结算时间，M1 合同已禁用",
    "sigma": "前一代系统事前注册的方向先验，属映射种子，未过 PIT/语义/provenance 审计",
    "orientation": "sigma × 品种符号，同为未审计的映射种子",
    "exploratory": "前一代系统规则表的探索性标记，属未审计的选样标注",
}

#: 登记表的成员资格筛选：窗口内累计名义额需达到该门槛（来源脚本默认值）。
PM_ADMISSION_MIN_USDC = 100_000.0

PM_REGISTRY_DEPRECATION = (
    "cn_registry_v3.parquet 已于 2026-08-05 由人类裁决弃用并隔离，不得作为市场来源、"
    "市场映射或任何研究输入，也不得进入 M3 evaluator 或 M4 Study。三条理由："
    "(1) 成员资格是全窗口筛选（累计名义额需达 10 万美元），在决策时点不可知，"
    "存在幸存者偏差；(2) theme/product/sigma 是前一代系统的语义映射种子，"
    "未过 PIT、语义与 provenance 审计；(3) 覆盖仅 2026-01-04 至 2026-07-13，"
    "整段位于 contaminated audit 区间。替代方案是从原始 tape 推导的 PIT Market Index。"
    "如需把它当作被隔离的 QA 参照，必须显式传入 quarantine_ack 并把理由记入账本。"
)


class DeprecatedSourceError(RuntimeError):
    """访问了已弃用并隔离的数据源。这是硬边界，不是提醒。"""

_CLS_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


# ---------------------------------------------------------------- CLS


def load_cls_series(
    output_dir: str,
    pattern: str,
    manifest: SourceManifest,
    *,
    start: date,
    end: date,
    poll_delay_seconds: int = CLS_POLL_DELAY_SECONDS,
) -> PitSeries:
    """把区间内的财联社日 CSV 读成按可用时间升序的 PIT 序列。

    只保留 manifest 允许的分析字段；热度三列从物理上不进入本序列。
    """
    allowed = [c for c in manifest.analysis_fields() if c != "Index"]
    files = sorted(glob.glob(os.path.join(output_dir, pattern)))
    rows: dict[str, list] = {c: [] for c in allowed}
    rows["natural_date"] = []
    rows["available_time"] = []
    for path in files:
        m = _CLS_DATE_RE.search(os.path.basename(path))
        if not m:
            continue
        day = date.fromisoformat(m.group(1))
        if not (start <= day <= end):
            continue
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                t = (row.get("Time") or "").strip()
                if len(t) < 8:
                    continue
                published = datetime(
                    day.year, day.month, day.day,
                    int(t[0:2]), int(t[3:5]), int(t[6:8]), tzinfo=SHANGHAI,
                )
                rows["natural_date"].append(day.isoformat())
                rows["available_time"].append(
                    published + timedelta(seconds=poll_delay_seconds)
                )
                for c in allowed:
                    rows[c].append(row.get(c))
    table = pa.table(
        {
            "natural_date": pa.array(rows["natural_date"], pa.string()),
            "available_time": pa.array(
                rows["available_time"], pa.timestamp("us", tz="Asia/Shanghai")
            ),
            **{c: pa.array(rows[c], pa.string()) for c in allowed},
        }
    )
    table = table.sort_by([("available_time", "ascending")])
    return PitSeries(name="cls_telegraph", table=table, manifest=manifest)


def cls_contract(manifest: SourceManifest, output_dir: str, poll_delay: int) -> ControlContract:
    return ControlContract(
        source_id="cls_telegraph",
        root_uri=output_dir,
        availability_rule=(
            f"{manifest.time_semantics.availability_rule}；本票采用采集延迟 {poll_delay} 秒"
        ),
        timezone=manifest.time_semantics.timezone,
        banned_fields=sorted(manifest.banned_fields()),
        provisional_fields=sorted(manifest.provisional_fields()),
        notes="热度三列在合同层硬拒绝，物化视图中也不存在该列",
    )


# ---------------------------------------------------------------- Brent


def brent_manifest(path: str) -> SourceManifest:
    return SourceManifest(
        source_id="intl_brent",
        root_uri=path,
        scanner_version="declared-0.1.0",
        time_semantics=TimeSemantics(
            event_time="报价日 D（无日内时刻）",
            publication_time="未经来源方核实",
            availability_time=f"D+1 {BRENT_AVAILABLE_AT_HOUR:02d}:00 Asia/Shanghai（保守下界）",
            availability_rule=(
                "日 D 的收盘价在 D+1 "
                f"{BRENT_AVAILABLE_AT_HOUR:02d}:00 Asia/Shanghai 之后才可用；"
                "该规则晚于 ICE 结算（伦敦 19:30）与美市收盘的任何合理换算时点"
            ),
            timezone="Asia/Shanghai（由报价日推导，原文件无时区）",
            unit_notes="美元/桶",
        ),
        fields=[
            FieldAvailability(name="timestamp", dtype="str", semantic="报价日", unit="YYYY-MM-DD"),
            FieldAvailability(
                name="value",
                dtype="float64",
                semantic="布伦特原油日收盘/现货价",
                unit="美元/桶",
                provisional=True,
            ),
        ],
        partitions=[],
    )


def load_brent_series(path: str, *, start: date, end: date) -> PitSeries:
    manifest = brent_manifest(path)
    days: list[str] = []
    values: list[float] = []
    available: list[datetime] = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                day = date.fromisoformat(row["timestamp"])
                value = float(row["value"])
            except (KeyError, ValueError):
                continue
            if not (start <= day <= end):
                continue
            days.append(day.isoformat())
            values.append(value)
            available.append(
                datetime(day.year, day.month, day.day, tzinfo=SHANGHAI)
                + timedelta(days=1, hours=BRENT_AVAILABLE_AT_HOUR)
            )
    table = pa.table(
        {
            "timestamp": pa.array(days, pa.string()),
            "value": pa.array(values, pa.float64()),
            "available_time": pa.array(available, pa.timestamp("us", tz="Asia/Shanghai")),
        }
    ).sort_by([("available_time", "ascending")])
    return PitSeries(
        name="intl_brent",
        table=table,
        manifest=manifest,
        allow_provisional={"value"},
        override_reason=BRENT_OVERRIDE_REASON,
    )


def brent_contract(path: str) -> ControlContract:
    m = brent_manifest(path)
    return ControlContract(
        source_id="intl_brent",
        root_uri=path,
        availability_rule=m.time_semantics.availability_rule,
        timezone=m.time_semantics.timezone,
        banned_fields=sorted(m.banned_fields()),
        provisional_fields=sorted(m.provisional_fields()),
        audited_override_reason=BRENT_OVERRIDE_REASON,
        notes="声明式合同，非扫描产物；发布时点核实属 acquisition 流程",
    )


# ---------------------------------------------------------------- PM 市场登记


def pm_registry_manifest(path: str) -> SourceManifest:
    fields = [
        FieldAvailability(name="condition_id", dtype="str", semantic="市场键"),
        FieldAvailability(name="slug", dtype="str", semantic="市场 slug"),
        FieldAvailability(name="category", dtype="str", semantic="市场类别（元数据）"),
        FieldAvailability(name="theme", dtype="str", semantic="人工机制主题（种子，非真值）"),
        FieldAvailability(name="product", dtype="str", semantic="映射到的商品品种（种子，非真值）"),
        FieldAvailability(name="first_ts", dtype="int64", semantic="首笔成交链上时间", unit="epoch s"),
        FieldAvailability(name="last_ts", dtype="int64", semantic="末笔成交链上时间", unit="epoch s"),
        FieldAvailability(name="admit_ts", dtype="int64", semantic="市场进入登记表的时间", unit="epoch s"),
    ]
    for name, reason in PM_BANNED_FIELDS.items():
        fields.append(
            FieldAvailability(
                name=name, dtype="mixed", semantic=reason, banned=True, banned_reason=reason
            )
        )
    return SourceManifest(
        source_id="pm_cn_registry_v3",
        root_uri=path,
        scanner_version="declared-0.1.0",
        time_semantics=TimeSemantics(
            event_time="市场首笔成交链上时间 first_ts",
            publication_time="admit_ts（登记表判定该市场可用的时间）",
            availability_time="admit_ts",
            availability_rule=(
                "市场只有在 admit_ts 之后才被视为已进入研究可见集合。"
                "admit_ts 是窗口内累计名义额首次达到 "
                f"{PM_ADMISSION_MIN_USDC:.0f} 美元的链上时刻，构造上是点时化的；"
                "但**成员资格本身是全窗口筛选**（要求全窗口累计额达到同一门槛），"
                "在任一决策时点不可知，因此市场选择存在幸存者偏差，admit_ts 修不掉。"
                "登记表由既往系统冻结产出，theme/product/sigma 映射只作机制种子，"
                "必须在 Decision Map #5 重新通过 PIT、语义与 provenance 审计"
        ),
            timezone="UTC（epoch 秒）",
            unit_notes="admit_ts/first_ts/last_ts 为 epoch 秒；毫秒量级应触发单位断言失败",
        ),
        fields=fields,
        partitions=[],
    )


def load_pm_registry_series(
    path: str, *, product: str, quarantine_ack: str = ""
) -> PitSeries:
    """**已弃用**。默认拒绝加载；仅在显式给出隔离理由时放行，供只读 QA 对照。"""
    if not quarantine_ack:
        raise DeprecatedSourceError(PM_REGISTRY_DEPRECATION)
    manifest = pm_registry_manifest(path)
    table = pq.read_table(path, columns=list(PM_ALLOWED_FIELDS))
    rows = [r for r in table.to_pylist() if r["product"] == product]
    for r in rows:
        require_epoch_seconds(r["admit_ts"], field="admit_ts")
    rows.sort(key=lambda r: (r["admit_ts"], r["condition_id"]))
    out = {c: pa.array([r[c] for r in rows]) for c in PM_ALLOWED_FIELDS}
    out["available_time"] = pa.array(
        [datetime.fromtimestamp(r["admit_ts"], tz=SHANGHAI) for r in rows],
        pa.timestamp("us", tz="Asia/Shanghai"),
    )
    return PitSeries(name="pm_cn_registry_v3", table=pa.table(out), manifest=manifest)


def pm_registry_deprecation_record(path: str) -> dict:
    """弃用记录。写进 spine manifest，使"这个来源被移除过"本身可追溯。"""
    return {
        "source_id": "pm_cn_registry_v3",
        "root_uri": path,
        "status": "deprecated_quarantined",
        "decided_at": "2026-08-05",
        "decided_by": "human",
        "reason": PM_REGISTRY_DEPRECATION,
        "replacement": (
            "从原始 Polymarket tape 推导的 PIT Market Index："
            "存在性由首笔公开成交决定，流动性资格由过去窗口决定，两者分离"
        ),
        "allowed_use": "仅可作为被隔离的只读 QA 对照，且必须显式传入 quarantine_ack 并记入账本",
        "forbidden_use": "市场来源、市场语义映射、任何研究输入、M3 evaluator、M4 Study",
    }
