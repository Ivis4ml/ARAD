"""机制族：按价格形成机制与极性定义 Polymarket 族成员（M16）。

现有候选族（`cand:`，见 pm_entity_clusters 与 pm_series.conditions_by_family）的成员
规则是「市场 slug 分词后与族词表有交集」。它是词汇聚类，不是机制聚类，实测后果：
`cand:oil` 的词表含 `per` 这个介词因而有 829 个成员（含电影《Sarah's Oil》的评分市场）；
`cand:blockade` 的词表是 {been, blockade, has, that}，其 discovery 段的 4,272 个小时桶
完全由「外星人是否存在」与「OpenAI 是否达成 AGI」的概率构成，零封锁内容。
噪声市场并非通过成交额进入构造（按成交额它们只占 16%），而是通过**桶占有**：
特征的 window 算子对小时桶等权，噪声市场独占 `cand:iran` discovery 段 6,098 个族桶中的
1,673 个，在这些桶上族 p 完全等于噪声 p。

本模块把族成员改由**冻结的、可复算的谓词**定义，并给每个成员标注机制极性：

- 成员资格只作用于 `market_text` 的 slug，不引用任何期货结果，也不枚举 token 清单
  （枚举清单是某个时点的存活性选择，会把「当时还活着的市场」误当成「当时的宇宙」）。
- 极性把同一机制的否定式提问（「封锁被解除」之于「封锁发生」）折成同号，
  折法是 q = p 或 q = 1 − p；不折会让两侧在族内相互抵消。
- 任何落在实体门内却无法归类的市场都记入 `excluded` 表并计数，不取默认值：
  默认值会让规则的盲区伪装成「族里没有这种市场」。

规则集本身是研究工件，内容寻址后写进 manifest；改一个字符就是另一个族版本。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

MECHANISM_RULE_VERSION = "mech-rules-v1"

#: 成员表的模式。polarity 与 yes_outcome_seq 是数据而不是注释：
#: 日后若出现 Up/Down 或多结果市场，可以逐条覆盖而不必推翻全局假设。
MEMBERSHIP_SCHEMA = pa.schema([
    ("family_id", pa.string()),
    ("condition_id", pa.string()),
    ("polarity", pa.int8()),
    ("yes_outcome_seq", pa.int8()),
    ("matched_stage", pa.string()),
    ("slug", pa.string()),
    ("first_trade_ts", pa.int64()),
    ("eligible_from", pa.timestamp("us", tz="UTC")),
    ("first_trade_segment", pa.string()),
])

EXCLUDED_SCHEMA = pa.schema([
    ("family_id", pa.string()),
    ("condition_id", pa.string()),
    ("reason", pa.string()),
    ("matched_stage", pa.string()),
    ("slug", pa.string()),
    ("first_trade_segment", pa.string()),
])

StageKind = Literal["exclude", "route_out", "member"]


class MechanismRuleError(ValueError):
    """规则集自身不合法。构建失败优于产出一个语义不明的族。"""


@dataclass(frozen=True)
class MechanismStage:
    """一条按序判定的规则。第一条命中的 stage 决定该市场的归属。

    `unless` 是同一条内的否决式：命中 pattern 但也命中 unless 时本条不算命中，
    继续往下判。飓风族的「季节总数市场路由给 HURRICANES_SEASON，除非它同时问了登陆」
    就是这个形状，拆成两条会改变判定次序。
    """

    kind: StageKind
    name: str
    pattern: str
    unless: str | None = None
    sign: int | None = None
    reason: str | None = None
    route_to: str | None = None

    def __post_init__(self) -> None:
        if self.kind == "member" and self.sign not in (1, -1):
            raise MechanismRuleError(f"member 段 {self.name} 必须声明 sign 为 +1 或 -1")
        if self.kind == "exclude" and not self.reason:
            raise MechanismRuleError(f"exclude 段 {self.name} 必须声明 reason")
        if self.kind == "route_out" and not self.route_to:
            raise MechanismRuleError(f"route_out 段 {self.name} 必须声明 route_to")
        for pat in (self.pattern, self.unless):
            if pat is None:
                continue
            try:
                re.compile(pat)
            except re.error as exc:  # pragma: no cover - 规则写错时的诊断
                raise MechanismRuleError(f"{self.name} 的正则不可编译：{exc}") from exc

    def matches(self, slug: str) -> bool:
        if not re.search(self.pattern, slug):
            return False
        return not (self.unless and re.search(self.unless, slug))


@dataclass(frozen=True)
class MechanismRule:
    """一个机制族的完整定义。

    `expected_discovery_markets` 是自检锚点：规则是在 discovery 段的 slug 语法上
    标定的，成员数偏离锚点说明数据或规则有一方变了，构建时会报出来。
    """

    family_id: str
    name_cn: str
    driver_channel: str
    mechanism_cn: str
    match_field: str
    scope: str
    stages: tuple[MechanismStage, ...]
    seed_family: str | None = None
    seed_pack: str | None = None
    themes: tuple[str, ...] = ()
    require_all: tuple[str, ...] = ()
    stratum: str = "mechanism"
    yes_outcome_seq: int = 1
    expected_discovery_markets: int | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.match_field not in ("slug_base", "slug_raw"):
            raise MechanismRuleError(
                f"{self.family_id}: match_field 只能是 slug_base 或 slug_raw")
        if not self.stages:
            raise MechanismRuleError(f"{self.family_id}: 至少要有一条 member 段")
        if not any(s.kind == "member" for s in self.stages):
            raise MechanismRuleError(f"{self.family_id}: 规则集没有任何 member 段")
        for pat in (self.scope, *self.require_all):
            try:
                re.compile(pat)
            except re.error as exc:  # pragma: no cover
                raise MechanismRuleError(
                    f"{self.family_id} 的正则不可编译：{exc}") from exc

    @property
    def series_id(self) -> str:
        return f"mech:{self.family_id}"

    def describe(self) -> dict[str, Any]:
        """进 manifest 与内容寻址的规范形。字段顺序固定，便于逐字符比对。"""
        return {
            "family_id": self.family_id,
            "name_cn": self.name_cn,
            "driver_channel": self.driver_channel,
            "mechanism_cn": self.mechanism_cn,
            "match_field": self.match_field,
            "scope": self.scope,
            "require_all": list(self.require_all),
            "seed_family": self.seed_family,
            "seed_pack": self.seed_pack,
            "themes": list(self.themes),
            "stratum": self.stratum,
            "yes_outcome_seq": self.yes_outcome_seq,
            "stages": [
                {
                    "kind": s.kind, "name": s.name, "pattern": s.pattern,
                    "unless": s.unless, "sign": s.sign, "reason": s.reason,
                    "route_to": s.route_to,
                }
                for s in self.stages
            ],
        }


@dataclass
class Classification:
    outcome: str          # member / excluded / routed_out / out_of_scope / unmatched
    stage: str
    sign: int | None = None
    reason: str | None = None
    route_to: str | None = None


def classify(rule: MechanismRule, slug: str) -> Classification:
    """按 stages 顺序判定一个市场的归属。第一条命中即返回。

    落在实体门内却走完全部 stage 都没命中的市场归 `unmatched` —— 它既不是成员
    也没有被显式排除，是规则的盲区，必须被计数而不是被静默丢弃。
    """
    s = slug.lower()
    if not re.search(rule.scope, s):
        return Classification(outcome="out_of_scope", stage="scope")
    for pat in rule.require_all:
        if not re.search(pat, s):
            return Classification(
                outcome="excluded", stage="require_all", reason="missing_required_form")
    for stage in rule.stages:
        if not stage.matches(s):
            continue
        if stage.kind == "exclude":
            return Classification(
                outcome="excluded", stage=stage.name, reason=stage.reason)
        if stage.kind == "route_out":
            return Classification(
                outcome="routed_out", stage=stage.name, route_to=stage.route_to)
        return Classification(outcome="member", stage=stage.name, sign=stage.sign)
    return Classification(outcome="unmatched", stage="-", reason="no_stage_matched")


def load_rules(rules_dir: str | Path) -> dict[str, MechanismRule]:
    """读一个目录下的全部族定义（每族一个 YAML）。"""
    out: dict[str, MechanismRule] = {}
    for path in sorted(Path(rules_dir).glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        stages = tuple(
            MechanismStage(
                kind=s["kind"], name=s["name"], pattern=s["pattern"],
                unless=s.get("unless"), sign=s.get("sign"),
                reason=s.get("reason"), route_to=s.get("route_to"),
            )
            for s in doc.get("stages", [])
        )
        rule = MechanismRule(
            family_id=doc["family_id"],
            name_cn=doc["name_cn"],
            driver_channel=doc["driver_channel"],
            mechanism_cn=doc["mechanism_cn"],
            match_field=doc.get("match_field", "slug_base"),
            scope=doc["scope"],
            stages=stages,
            seed_family=doc.get("seed_family"),
            seed_pack=doc.get("seed_pack"),
            themes=tuple(doc.get("themes", ())),
            require_all=tuple(doc.get("require_all", ())),
            stratum=doc.get("stratum", "mechanism"),
            yes_outcome_seq=int(doc.get("yes_outcome_seq", 1)),
            expected_discovery_markets=doc.get("expected_discovery_markets"),
            notes=doc.get("notes", ""),
        )
        if rule.family_id in out:
            raise MechanismRuleError(f"族 {rule.family_id} 重复定义")
        out[rule.family_id] = rule
    if not out:
        raise MechanismRuleError(f"{rules_dir} 下没有任何族定义")
    return out


def rules_content_id(rules: dict[str, MechanismRule]) -> str:
    """规则集的内容指纹。规则一变，族就是另一个族，序列与结论都不可混用。"""
    payload = {
        "version": MECHANISM_RULE_VERSION,
        "families": [rules[k].describe() for k in sorted(rules)],
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _segment_of(first_trade_ts: int | None, *, discovery_end: date,
                validation_end: date) -> str:
    """按首笔公开成交的日期归段。成员资格由首笔成交定义（PIT）。"""
    if first_trade_ts is None:
        return "no_trade"
    day = datetime.fromtimestamp(int(first_trade_ts), tz=UTC).date()
    if day <= discovery_end:
        return "discovery"
    if day <= validation_end:
        return "historical_validation"
    return "contaminated_audit"


@dataclass
class CompileResult:
    membership: pa.Table
    excluded: pa.Table
    stats: dict[str, Any] = field(default_factory=dict)


def compile_membership(
    market_text_path: str,
    market_presence_path: str,
    rules: dict[str, MechanismRule],
    *,
    discovery_end: date,
    validation_end: date,
    strict_unmatched_segment: str | None = "discovery",
) -> CompileResult:
    """把规则集编译成成员表。

    `strict_unmatched_segment` 指定在哪一段上要求盲区为空：规则是在 discovery 段的
    提问语法上标定的，该段出现 unmatched 说明标定没做完，构建应当失败；
    其他段出现 unmatched 是已知且如实记录的（2025-26 年的提问语法明显分化）。
    """
    text = pq.read_table(market_text_path,
                         columns=["condition_id", "slug_base", "slug_raw"])
    presence = pq.read_table(market_presence_path,
                             columns=["condition_id", "first_trade_ts", "eligible_from"])
    first = dict(zip(presence.column("condition_id").to_pylist(),
                     presence.column("first_trade_ts").to_pylist(), strict=True))
    eligible = dict(zip(presence.column("condition_id").to_pylist(),
                        presence.column("eligible_from").to_pylist(), strict=True))

    cids = text.column("condition_id").to_pylist()
    slugs = {
        "slug_base": text.column("slug_base").to_pylist(),
        "slug_raw": text.column("slug_raw").to_pylist(),
    }

    mem_rows: list[dict] = []
    exc_rows: list[dict] = []
    stats: dict[str, Any] = {}
    for family_id in sorted(rules):
        rule = rules[family_id]
        column = slugs[rule.match_field]
        counts = {"member_pos": 0, "member_neg": 0, "excluded": 0,
                  "routed_out": 0, "unmatched": 0}
        seg_counts: dict[str, int] = {}
        unmatched_examples: list[str] = []
        for cid, slug in zip(cids, column, strict=True):
            if not slug:
                continue
            verdict = classify(rule, slug)
            if verdict.outcome == "out_of_scope":
                continue
            segment = _segment_of(first.get(cid), discovery_end=discovery_end,
                                  validation_end=validation_end)
            if verdict.outcome == "member":
                counts["member_pos" if verdict.sign == 1 else "member_neg"] += 1
                seg_counts[segment] = seg_counts.get(segment, 0) + 1
                mem_rows.append({
                    "family_id": family_id,
                    "condition_id": cid,
                    "polarity": verdict.sign,
                    "yes_outcome_seq": rule.yes_outcome_seq,
                    "matched_stage": verdict.stage,
                    "slug": slug,
                    "first_trade_ts": first.get(cid),
                    "eligible_from": eligible.get(cid),
                    "first_trade_segment": segment,
                })
                continue
            if verdict.outcome == "unmatched":
                counts["unmatched"] += 1
                if segment == strict_unmatched_segment and len(unmatched_examples) < 12:
                    unmatched_examples.append(slug)
            else:
                counts[verdict.outcome if verdict.outcome != "excluded" else "excluded"] += 1
            exc_rows.append({
                "family_id": family_id,
                "condition_id": cid,
                "reason": verdict.reason or (f"routed_to:{verdict.route_to}"
                                             if verdict.route_to else verdict.outcome),
                "matched_stage": verdict.stage,
                "slug": slug,
                "first_trade_segment": segment,
            })
        if strict_unmatched_segment and unmatched_examples:
            raise MechanismRuleError(
                f"{family_id}: {strict_unmatched_segment} 段有 {len(unmatched_examples)} "
                f"个市场落在实体门内却无法归类，规则标定未完成。举例："
                + "；".join(unmatched_examples[:5]))
        got = seg_counts.get("discovery", 0)
        if (rule.expected_discovery_markets is not None
                and got != rule.expected_discovery_markets):
            raise MechanismRuleError(
                f"{family_id}: discovery 成员数 {got} 与自检锚点 "
                f"{rule.expected_discovery_markets} 不符")
        stats[family_id] = {
            "counts": counts,
            "by_segment": seg_counts,
            "series_id": rule.series_id,
            "driver_channel": rule.driver_channel,
            "stratum": rule.stratum,
            "seed_family": rule.seed_family,
        }

    membership = pa.Table.from_pylist(mem_rows, schema=MEMBERSHIP_SCHEMA).sort_by(
        [("family_id", "ascending"), ("condition_id", "ascending")])
    excluded = pa.Table.from_pylist(exc_rows, schema=EXCLUDED_SCHEMA).sort_by(
        [("family_id", "ascending"), ("condition_id", "ascending")])
    return CompileResult(membership=membership, excluded=excluded, stats=stats)


def membership_by_family(table: pa.Table) -> dict[str, dict[str, int]]:
    """成员表 → {family_id: {condition_id: polarity}}，供序列构建使用。"""
    out: dict[str, dict[str, int]] = {}
    for fid, cid, pol in zip(table.column("family_id").to_pylist(),
                             table.column("condition_id").to_pylist(),
                             table.column("polarity").to_pylist(), strict=True):
        out.setdefault(f"mech:{fid}", {})[cid] = int(pol)
    return out
