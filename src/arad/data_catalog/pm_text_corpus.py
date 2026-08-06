"""Polymarket 市场文本语料与模板归纳（Decision Map #12，自下而上第一层）。

2026-08-05 人类裁决：机制族**从数据自下而上重新归纳**，不沿用旧系统的 8 个主题
（那 8 个主题是看过结果之后写成的规则表，继承它等于继承选择偏差）。

本层完全确定性，不使用任何模型：

1. slug 归一化为跨抓取稳定的基名（规则与证据见 `pm_metadata_audit`）；
2. 基名按 `-` 切词后，把数字、月份、年份替换为占位符，得到**模板**。
   Polymarket 的市场标题高度模板化（`will-<X>-hit-low-<N>-by-end-of-<MONTH>`），
   模板是语法层的天然分组，无需模型即可复现。

模板不是机制族。它是给后续命名与人工金标用的候选分组；机制族的语义命名、
跨模型一致性审计与金标裁决属本票的后续阶段。

**归纳期切点是冻结参数**：用全史文本归纳分类法，等于用后见的市场宇宙定义分组。
因此每个映射版本记录 `induction_cutoff`，并实测该切点之外市场的模板覆盖率，
使"用多晚的语料换多高的覆盖"成为可测量的量，而不是判断题。
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.parquet as pq

from .pm_census import Heartbeat
from .pm_metadata_audit import normalize_slug
from .schema import QualityFinding, Severity

CORPUS_VERSION = "0.1.0"

MARKET_TEXT_SCHEMA = pa.schema(
    [
        ("condition_id", pa.string()),
        ("slug_raw", pa.string()),
        ("slug_base", pa.string()),
        ("template", pa.string()),
        ("distinct_raw_slugs", pa.int64()),
    ]
)

_MONTHS = {
    "jan", "january", "feb", "february", "mar", "march", "apr", "april", "may",
    "jun", "june", "jul", "july", "aug", "august", "sep", "sept", "september",
    "oct", "october", "nov", "november", "dec", "december",
}
_NUMBER = re.compile(r"^\d+(?:\.\d+)?[kmb]?$")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")


def slug_template(slug_base: str | None) -> str | None:
    """把归一化基名变成模板：数字、年份、月份替换为占位符。

    年份先于数字判定（`2026` 既是四位数也是年份，作为年份更有信息量）。
    """
    if not slug_base:
        return slug_base
    out = []
    for token in slug_base.split("-"):
        low = token.lower()
        if _YEAR.match(low):
            out.append("<YEAR>")
        elif _NUMBER.match(low):
            out.append("<N>")
        elif low in _MONTHS:
            out.append("<MONTH>")
        else:
            out.append(low)
    return "-".join(out)


@dataclass(frozen=True)
class InductionSpec:
    """冻结的归纳参数。任何一项变化都产生一个新的映射版本。"""

    induction_cutoff: str
    min_markets_per_template: int = 3
    version: str = CORPUS_VERSION

    def describe(self) -> dict:
        return {
            "version": self.version,
            "induction_cutoff": self.induction_cutoff,
            "min_markets_per_template": self.min_markets_per_template,
            "rule": (
                "只用首笔公开成交早于 induction_cutoff 的市场归纳模板；"
                "该切点之后的市场只用于测量覆盖率，不参与归纳"
            ),
        }


def _partition_market_text(path: str) -> pa.Table:
    table = pq.read_table(path, columns=["condition_id", "market_slug"])
    if table.num_rows == 0:
        return pa.table({"condition_id": pa.array([], pa.string()),
                         "market_slug": pa.array([], pa.string())})
    return pa.TableGroupBy(table, ["condition_id", "market_slug"]).aggregate(
        [("condition_id", "count")]
    ).select(["condition_id", "market_slug"])


def build_market_text(
    roots: dict[str, str], *, heartbeat: Heartbeat | None = None
) -> pa.Table:
    """全史扫描出每个市场见过的 slug，归一化为基名与模板。

    同一市场可能有多个原始 slug（实测跨抓取会追加消歧数字段）：`slug_raw` 取
    字典序最小者以保证确定性，`distinct_raw_slugs` 记录见过几个，
    `slug_base` 与 `template` 由基名派生，跨抓取稳定。
    """
    paths = []
    for root in roots.values():
        paths.extend(sorted(glob.glob(os.path.join(root, "*.parquet"))))
    paths.sort()
    if heartbeat is not None:
        heartbeat.stage("market_text", total=len(paths))
    seen: dict[str, set[str]] = {}
    for i, path in enumerate(paths, start=1):
        table = _partition_market_text(path)
        for cid, slug in zip(
            table.column("condition_id").to_pylist(), table.column("market_slug").to_pylist()
        ):
            seen.setdefault(cid, set()).add(slug)
        if heartbeat is not None:
            heartbeat.progress(i, os.path.basename(path))

    cids = sorted(seen)
    raws = [min(s for s in seen[c] if s is not None) if any(seen[c]) else None for c in cids]
    bases = [normalize_slug(r) for r in raws]
    return pa.table(
        {
            "condition_id": pa.array(cids, pa.string()),
            "slug_raw": pa.array(raws, pa.string()),
            "slug_base": pa.array(bases, pa.string()),
            "template": pa.array([slug_template(b) for b in bases], pa.string()),
            "distinct_raw_slugs": pa.array([len(seen[c]) for c in cids], pa.int64()),
        },
        schema=MARKET_TEXT_SCHEMA,
    )


def _cutoff_epoch(cutoff: str) -> int:
    return int(datetime.fromisoformat(cutoff).replace(tzinfo=UTC).timestamp())


def induce_templates(
    market_text: pa.Table, presence: pa.Table, spec: InductionSpec
) -> tuple[pa.Table, dict]:
    """只用归纳期内的市场产生模板集合，并实测期外覆盖率。"""
    cutoff = _cutoff_epoch(spec.induction_cutoff)
    first = dict(
        zip(
            presence.column("condition_id").to_pylist(),
            presence.column("first_trade_ts").to_pylist(),
        )
    )
    in_period: dict[str, int] = {}
    out_period: dict[str, int] = {}
    for cid, template in zip(
        market_text.column("condition_id").to_pylist(),
        market_text.column("template").to_pylist(),
    ):
        ts = first.get(cid)
        if ts is None or template is None:
            continue
        bucket = in_period if ts < cutoff else out_period
        bucket[template] = bucket.get(template, 0) + 1

    kept = {t: n for t, n in in_period.items() if n >= spec.min_markets_per_template}
    covered = sum(n for t, n in out_period.items() if t in kept)
    total_out = sum(out_period.values())
    singleton = sum(1 for n in in_period.values() if n == 1)
    table = pa.table(
        {
            "template": pa.array(sorted(kept), pa.string()),
            "markets_in_induction_period": pa.array(
                [kept[t] for t in sorted(kept)], pa.int64()
            ),
            "markets_after_cutoff": pa.array(
                [out_period.get(t, 0) for t in sorted(kept)], pa.int64()
            ),
        }
    )
    stats = {
        "spec": spec.describe(),
        "markets_in_induction_period": sum(in_period.values()),
        "templates_in_induction_period": len(in_period),
        "templates_kept": len(kept),
        "singleton_templates": singleton,
        "markets_after_cutoff": total_out,
        "markets_after_cutoff_covered": covered,
        "coverage_after_cutoff": (covered / total_out) if total_out else 0.0,
    }
    return table, stats


def coverage_curve(
    market_text: pa.Table, presence: pa.Table, cutoffs: list[str], min_markets: int
) -> list[dict]:
    """不同归纳期切点下的期外覆盖率。把"用多晚的语料"变成可测量的量。"""
    out = []
    for cutoff in cutoffs:
        _, stats = induce_templates(
            market_text, presence, InductionSpec(cutoff, min_markets_per_template=min_markets)
        )
        out.append(
            {
                "induction_cutoff": cutoff,
                "markets_in_period": stats["markets_in_induction_period"],
                "templates_kept": stats["templates_kept"],
                "markets_after_cutoff": stats["markets_after_cutoff"],
                "coverage_after_cutoff": round(stats["coverage_after_cutoff"], 4),
            }
        )
    return out


def corpus_findings(market_text: pa.Table, curve: list[dict]) -> list[QualityFinding]:
    findings = [
        QualityFinding(
            severity=Severity.INFO,
            code="pm_text.template_induction",
            message=(
                "模板由确定性规则归纳，不使用任何模型；模板是候选分组，不是机制族。"
                "机制族的语义命名、跨模型一致性审计与金标裁决属后续阶段"
            ),
            evidence={"markets": market_text.num_rows, "coverage_curve": curve},
        )
    ]
    multi = sum(
        1 for n in market_text.column("distinct_raw_slugs").to_pylist() if n > 1
    )
    if multi:
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="pm_text.multiple_raw_slugs",
                message=(
                    "部分市场见过多个原始 slug（跨抓取追加消歧数字段）；"
                    "基名与模板取自归一化结果，原始 slug 只作观测记录"
                ),
                evidence={"markets_with_multiple_raw_slugs": multi},
            )
        )
    weak = [c for c in curve if c["coverage_after_cutoff"] < 0.5]
    if weak:
        findings.append(
            QualityFinding(
                severity=Severity.WARNING,
                code="pm_text.low_out_of_period_coverage",
                message=(
                    "部分归纳期切点下，期外市场被已知模板覆盖的比例低于一半；"
                    "以该切点冻结的映射版本对后续市场解释力有限，"
                    "选择切点是 PIT 诚实度与覆盖率之间的权衡，须由 Study 显式声明"
                ),
                evidence={"cutoffs_below_half": weak},
            )
        )
    return findings
