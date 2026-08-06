"""上下文组装器（M4 第三块）。

**给 LLM 看什么，决定它提什么。**因此这一层和评价机一样是研究完整性的一部分，
不是 prompt 工程。三条规则：

1. **事实优先于散文。**上下文先组装成结构化 `facts`，再渲染成 prompt。
   facts 内容寻址，所以"模型当时看到了什么"是可回放的证据，而不是一段丢失的字符串。
2. **菜单偏差必须写进上下文，不能藏起来。**候选机制族是提案器的菜单，
   而菜单的构造偏差是实测过的（#12：hindsight exposure 83.7%，
   晚涌现族在大波动日上的活动份额高出 10.4 个百分点）。把它藏起来，
   偏差会原样传导成提案偏差且无人知晓；写进去，提案器至少能据此自我约束。
3. **盲化在渲染之后、发送之前再检一次。**组装器自己也可能引入效果字段。

历史信息一律走账本的 proposer 视图（效果字段已被递归遮蔽），
组装器不自己去读评价结果。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..features.spec import Op, Source, StepKind
from ..memory.ledger import EvidenceLedger
from ..memory.ledger import Role as LedgerRole
from ..providers.base import Role, assert_blinded
from ..registry.specs import content_id

CONTEXT_VERSION = "0.1.0"


@dataclass(frozen=True)
class DeclaredBias:
    """上下文里一条已知且已量化的偏差。必须出现在 prompt 里。"""

    name: str
    measurement: str
    consequence: str

    def render(self) -> str:
        return f"- **{self.name}**：{self.measurement}　后果：{self.consequence}"


@dataclass(frozen=True)
class ContextBundle:
    """一次组装的结果。facts 是证据，prompt 是它的渲染。"""

    role: Role
    facts: dict[str, Any]
    prompt: str
    declared_biases: list[DeclaredBias] = field(default_factory=list)

    @property
    def context_id(self) -> str:
        return content_id(
            {
                "role": self.role.value,
                "facts": self.facts,
                "context_version": CONTEXT_VERSION,
            }
        )

    def ledger_payload(self) -> dict:
        """写进账本的记录：模型当时看到了什么，可回放。"""
        return {
            "context_id": self.context_id,
            "role": self.role.value,
            "context_version": CONTEXT_VERSION,
            "facts": self.facts,
            "declared_biases": [b.__dict__ for b in self.declared_biases],
            "prompt_chars": len(self.prompt),
        }


def primitive_catalogue() -> dict:
    """提案器能用的全部原语。窄是刻意的，缺口应被声明而不是绕过。"""
    return {
        "sources": sorted(s.value for s in Source),
        "step_kinds": sorted(k.value for k in StepKind),
        "aggregations": sorted(o.value for o in Op),
        "hard_rules": [
            "所有窗口结束于决策时点之前；offset_seconds 只能非负",
            "特征必须声明经济含义（mechanism）与失败条件（failure_condition）",
            "步骤按依赖顺序排列，不允许环",
            "原语不足以表达某机制时，产出 UnsupportedMechanism 而不是绕过语言",
        ],
    }


def blinded_history(ledger: EvidenceLedger, family: str, *, limit: int = 40) -> dict:
    """历史信息只走账本的 proposer 视图，效果字段已被递归遮蔽。"""
    denominators = ledger.denominators(family)
    rows = ledger._conn.execute(
        "SELECT study_id, event_type FROM events WHERE event_type IN"
        " ('verdict_recorded','proposal_recorded') ORDER BY seq DESC LIMIT ?",
        (limit,),
    ).fetchall()
    studies = sorted({r["study_id"] for r in rows if r["study_id"]})
    taxonomy: dict[str, int] = {}
    for study_id in studies:
        for event in ledger.read_events(role=LedgerRole.PROPOSER, study_id=study_id):
            if event["event_type"] != "verdict_recorded":
                continue
            verdict = event["payload"].get("verdict", "unknown")
            taxonomy[verdict] = taxonomy.get(verdict, 0) + 1
    return {
        "denominators": denominators,
        "verdict_taxonomy": taxonomy,
        "studies_seen": len(studies),
        "note": "只给判决分类与分母；效果方向与量级对提案器不可见",
    }


def assemble_proposer_context(
    *,
    ledger: EvidenceLedger,
    family: str,
    data_facts: dict,
    targets: list[dict],
    menu: list[dict],
    menu_biases: list[DeclaredBias],
    budget_facts: dict,
    blockers: list[str],
) -> ContextBundle:
    """组装提案器上下文。渲染后再过一次盲化检查。"""
    facts = {
        "task": "提出一个可证伪的研究提案",
        "data": data_facts,
        "targets": targets,
        "primitives": primitive_catalogue(),
        "menu": {
            "candidate_families": menu,
            "known_biases": [b.__dict__ for b in menu_biases],
        },
        "history": blinded_history(ledger, family),
        "budget": budget_facts,
        "blockers": blockers,
        "output_contract": {
            "required": [
                "mechanism", "source", "target", "horizon", "universe",
                "direction", "falsifiable_condition", "feature_spec",
            ],
            "note": "只输出 JSON。特征必须用上面列出的原语表达",
        },
    }
    prompt = render_proposer_prompt(facts, menu_biases)
    assert_blinded(prompt, Role.PROPOSER)
    return ContextBundle(
        role=Role.PROPOSER, facts=facts, prompt=prompt, declared_biases=list(menu_biases)
    )


def render_proposer_prompt(facts: dict, biases: list[DeclaredBias]) -> str:
    """把结构化事实渲染成 prompt。渲染是确定性的：同样的 facts 得到同样的字符串。"""
    lines = [
        "你是一个持续因子研究服务的提案器。你的任务是提出**一个**可证伪的研究提案。",
        "",
        "## 你能看到什么，看不到什么",
        "",
        "你能看到：数据覆盖、可用目标、原语清单、历史判决的**分类**与分母、预算。",
        "你看不到：任何效应的方向与量级。这是刻意的 —— 看过结果再提案就不是事前假设。",
        "",
        "## 这份菜单的已知偏差",
        "",
    ]
    lines.extend(b.render() for b in biases)
    lines += [
        "",
        (
            "请把上述偏差纳入考虑：偏差不使菜单不可用，但它意味着菜单里的机制不是"
            "从无偏的宇宙里抽出来的。如果你的提案依赖某个高偏差的族，请在 rationale 里说明。"
        ),
        "",
        "## 结构化事实",
        "",
        "```json",
        json.dumps(
            {k: v for k, v in facts.items() if k not in ("menu",)},
            ensure_ascii=False, indent=2, sort_keys=True, default=str,
        ),
        "```",
        "",
        "## 候选机制族（菜单）",
        "",
        "```json",
        json.dumps(
            facts["menu"]["candidate_families"], ensure_ascii=False, indent=2, default=str
        ),
        "```",
        "",
        "## 输出",
        "",
        (
            "只输出一个 JSON 对象，字段见 output_contract。特征必须用 primitives 里列出的"
            "原语表达；若现有原语无法表达你想要的机制，改为输出 "
            '`{"unsupported_mechanism": {...}}`，说明缺哪个原语以及为什么现有的不够用。'
            "声明缺口是有价值的产出，不是失败。"
        ),
    ]
    return "\n".join(lines)


def record_context(ledger: EvidenceLedger, bundle: ContextBundle, study_id: str) -> str:
    """把上下文写进账本。模型看到了什么本身就是证据。"""
    return ledger.append("context_assembled", bundle.ledger_payload(), study_id=study_id)
