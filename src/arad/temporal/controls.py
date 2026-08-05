"""控制数据源的可用时间合同与 PIT 序列构造。

三个控制源都以**声明式** SourceManifest 登记：它们不是 M1 扫描出来的来源，
但同样必须先有可用时间合同才能被消费（M1 出口条件：没有合同的字段不可消费）。

- 财联社电报：走 M1 的 CLS manifest，热度字段在合同层被硬拒绝；
  可用时间 = 文件名日期 + Time（Asia/Shanghai）+ 声明的采集延迟。
- 国际油价（Alpha-Data intl/brent_daily.csv）：只有日期与数值，没有发布时刻。
  发布时点未经来源方核实，因此 `value` 标为 provisional，采用保守规则
  "D 的收盘价在 D+1 06:00 Asia/Shanghai 可用"，消费需受审计 override。
- Polymarket 市场登记表（冻结的 cn_registry_v3.parquet）：只用 admit_ts 与市场
  元数据；`usdc_win`/`n_win`/`sigma`/`orientation`/`resolved_at`/`exploratory`
  都由结果推导，一律 banned。tape 逐笔序列不在本票范围（需要 M5 的
  venue/relay/negRisk 审计后才能物化）。
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
PM_BANNED_FIELDS = {
    "usdc_win": "按结果侧统计的成交额，含结算信息",
    "n_win": "按结果侧统计的笔数，含结算信息",
    "resolved_at": "结算时间，M1 合同已禁用",
    "sigma": "方向标注由历史结果推导，属 outcome-exposed",
    "orientation": "方向标注由历史结果推导，属 outcome-exposed",
    "exploratory": "筛选标记由既往研究结果推导",
}

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
                "市场只有在 admit_ts 之后才被视为已进入研究可见集合；"
                "登记表由既往系统冻结产出，theme/product 映射只作机制种子，"
                "必须在 Decision Map #5 重新通过语义与 provenance 审计"
            ),
            timezone="UTC（epoch 秒）",
            unit_notes="admit_ts/first_ts/last_ts 为 epoch 秒；毫秒量级应触发单位断言失败",
        ),
        fields=fields,
        partitions=[],
    )


def load_pm_registry_series(path: str, *, product: str) -> PitSeries:
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


def pm_registry_contract(path: str, *, product: str, rows: int, themes: dict[str, int]) -> ControlContract:
    m = pm_registry_manifest(path)
    return ControlContract(
        source_id="pm_cn_registry_v3",
        root_uri=path,
        availability_rule=m.time_semantics.availability_rule,
        timezone=m.time_semantics.timezone,
        banned_fields=sorted(m.banned_fields()),
        provisional_fields=sorted(m.provisional_fields()),
        notes=(
            f"切片：product=={product}，{rows} 个市场，主题分布 {themes}。"
            "只登记市场元数据与 admit_ts；逐笔 belief 序列不在 M2 范围，"
            "需 M5 完成 venue/relay/negRisk 审计后才能物化。"
        ),
    )
