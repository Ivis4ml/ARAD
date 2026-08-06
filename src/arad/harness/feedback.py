"""反馈格式化器（M4 第四块）。

评价结果要回灌给提案器，但**不能原样回灌**。评价机的 `blocked_reasons` 里带着
数字："置换检验未通过：1.000 的置换斜率不小于实际值"、"单点影响过大：最大 DFBETA
占斜率 0.62" —— 这些是效应结构的泄漏。原样回传等于让提案器看见结果。

因此反馈只回传**分类**与**功效/覆盖**：分类告诉它哪里错了，功效告诉它样本够不够，
两者都不揭示效应的方向与量级。分类映射是白名单式的：认不出的原因归入
`unclassified` 并原样丢弃文本，而不是"保险起见带上去"。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..providers.base import Role, assert_blinded

FEEDBACK_VERSION = "0.1.0"

#: 失败分类白名单。键是分类名，值是识别用的关键片段（不含任何数字）。
FAILURE_TAXONOMY: dict[str, tuple[str, ...]] = {
    "insufficient_sample": ("低于预注册下限",),
    "cost_model_missing": ("未声明成本模型",),
    "placebo_failed": ("置换检验未通过",),
    "single_point_influence": ("单点影响过大",),
    "cluster_structure_insufficient": ("cluster 方差非正", "只有一组"),
    "not_identified": ("回归不可识别",),
}

#: 允许回传的覆盖/功效字段。白名单，不是黑名单。
ALLOWED_COVERAGE_FIELDS = (
    "rows_submitted", "rows_authoritative", "rows_excluded_preregistered",
    "episodes", "date_clusters", "product_clusters",
)

_NUMBER = re.compile(r"\d")


@dataclass(frozen=True)
class Feedback:
    """回灌给提案器的盲化反馈。"""

    study_id: str
    verdict: str
    failure_categories: list[str] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)
    unclassified_count: int = 0
    guidance: str = ""
    version: str = FEEDBACK_VERSION

    def render(self) -> str:
        lines = [
            f"- Study `{self.study_id}` 的判决分类：`{self.verdict}`",
            f"- 失败分类：{self.failure_categories or ['无']}",
            f"- 覆盖与功效：{self.coverage}",
        ]
        if self.unclassified_count:
            lines.append(
                f"- 另有 {self.unclassified_count} 条未归类的阻断原因未回传"
                "（含数字，可能泄漏效应结构）"
            )
        if self.guidance:
            lines.append(f"- 建议方向：{self.guidance}")
        return "\n".join(lines)


def classify(reason: str) -> str | None:
    for name, fragments in FAILURE_TAXONOMY.items():
        if any(fragment in reason for fragment in fragments):
            return name
    return None


def _guidance(categories: list[str]) -> str:
    if "insufficient_sample" in categories:
        return "样本或 Episode 数不足：换更长的样本段、更宽的 universe，或更低频的 target"
    if "cluster_structure_insufficient" in categories:
        return "单品种样本识别不出横截面结构：需要多品种，或改为纯时序推断并声明限制"
    if "placebo_failed" in categories:
        return "置换检验未通过：该方向在本样本上与随机不可区分，换机制而不是换参数"
    if "single_point_influence" in categories:
        return "结论依赖极少数观测：极值不可删除，应换更稳健的构造或更宽的样本"
    if "cost_model_missing" in categories:
        return "缺成本模型：在 Confirmatory Lock 里声明成本口径"
    return "无阻断分类；若判决仍非 candidate，检查功效预检"


def format_feedback(result: dict, verdict: str) -> Feedback:
    """把评价结果压成盲化反馈。数字一律不出分类映射之外。"""
    categories, unclassified = [], 0
    for reason in result.get("blocked_reasons", []):
        name = classify(reason)
        if name is None:
            unclassified += 1
        elif name not in categories:
            categories.append(name)
    coverage = {
        k: v for k, v in (result.get("coverage") or {}).items()
        if k in ALLOWED_COVERAGE_FIELDS
    }
    feedback = Feedback(
        study_id=result.get("study_id", ""),
        verdict=verdict,
        failure_categories=sorted(categories),
        coverage=coverage,
        unclassified_count=unclassified,
        guidance=_guidance(categories),
    )
    assert_blinded(feedback.render(), Role.PROPOSER)
    return feedback


def assert_no_effect_leakage(feedback: Feedback) -> None:
    """反馈里不得出现效应量。覆盖计数可以有数字，分类与建议不行。"""
    for text in [*feedback.failure_categories, feedback.guidance, feedback.verdict]:
        if _NUMBER.search(text):
            raise ValueError(
                f"反馈文本 {text!r} 含数字；分类与建议不得带数值，否则可能泄漏效应结构"
            )
