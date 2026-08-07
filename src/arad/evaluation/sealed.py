"""封闭段评估：只开一次（M7）。

取自 LBG-Agent 的纪律：LLM 永不接触封闭窗口，预算用尽后封闭段**恰好开启一次**。
本模块把它变成结构性的而不是约定性的 —— 同一个 (规格, 段) 想开第二次会被账本拒绝，
因为"再看一眼"正是把封闭段变成第二个发现段的那一步。

**封闭不等于干净。**两件事必须分开记：

- **时间上的样本外**：该段的 label 窗口全部晚于发现段。任何 target 都成立。
- **分类法上的干净**：机制的**选择**没有看过该段发生了什么。这一条对 pm_market 族
  当前**不成立** —— 候选族的归纳切点是 2026-08-01，覆盖了手上全部三个段，
  因此族的选择在每一段上都不独立于结果（决定 0004）。

对纯量价特征两者同时成立；对 PM 族特征只有前者成立，后者要等归纳切点之后的数据。
把两者混为一谈，等于用一个仍被污染的段给出"已验证"的结论。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ..memory.ledger import EvidenceLedger
from ..registry.specs import TaxonomyContamination, content_id

SEALED_VERSION = "0.1.0"

SEALED_OPENED = "sealed_segment_opened"


class SealedAlreadyOpened(RuntimeError):
    """该 (规格, 段) 的封闭评估已经做过。再看一眼就不是封闭段了。"""


@dataclass(frozen=True)
class SealedVerdict:
    """封闭评估的结果。**它不能改写发现段的判决**，只在它旁边并列。"""

    feature_id: str
    segment: str
    out_of_sample_in_time: bool
    taxonomy_clean: bool
    result: dict

    def payload(self) -> dict:
        return {
            "sealed_version": SEALED_VERSION,
            "feature_id": self.feature_id,
            "segment": self.segment,
            "out_of_sample_in_time": self.out_of_sample_in_time,
            "taxonomy_clean": self.taxonomy_clean,
            "result": self.result,
            "note": (
                "封闭不等于干净：时间上的样本外与分类法上的干净是两件事。"
                "机制选择若看过该段发生了什么，样本外也救不了它"
            ),
        }


def seal_key(feature_id: str, segment: str) -> str:
    return content_id({"feature_id": feature_id, "segment": segment,
                       "sealed_version": SEALED_VERSION})


def assert_unopened(ledger: EvidenceLedger, feature_id: str, segment: str) -> str:
    """检查这把封条有没有被揭过。揭过就拒绝，不是警告。"""
    key = seal_key(feature_id, segment)
    rows = ledger._conn.execute(
        "SELECT payload FROM events WHERE event_type = ?", (SEALED_OPENED,)
    ).fetchall()
    for row in rows:
        if json.loads(row["payload"]).get("seal_key") == key:
            raise SealedAlreadyOpened(
                f"特征 {feature_id!r} 在段 {segment!r} 上的封闭评估已经做过。"
                "再开一次就是把封闭段当成第二个发现段"
            )
    return key


def open_sealed(
    ledger: EvidenceLedger,
    *,
    feature_id: str,
    segment: str,
    result: dict,
    contamination: TaxonomyContamination | None,
) -> SealedVerdict:
    """开封一次并入账。**写一次即封死**，由账本的追加式触发器保证。"""
    key = assert_unopened(ledger, feature_id, segment)
    verdict = SealedVerdict(
        feature_id=feature_id,
        segment=segment,
        out_of_sample_in_time=True,
        taxonomy_clean=not (contamination and contamination.overlaps_outcome_window),
        result=result,
    )
    ledger.append(SEALED_OPENED, {"seal_key": key, **verdict.payload()})
    return verdict
