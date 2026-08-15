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
from ..memory.induction import proposal_memory
from ..memory.ledger import EvidenceLedger
from ..memory.ledger import Role as LedgerRole
from ..providers.base import Role, assert_blinded
from ..registry.specs import content_id
from .audit import SEMANTIC_MISMATCH_TAXONOMY
from .coverage import coverage_menu, search_coverage

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
    #: 方法说明（skill）的渲染文本与它的身份。它与 prompt 一样进模型上下文，
    #: 因此一样进内容寻址：同一段 prompt 配不同版本的方法说明不是同一次调用。
    system_prompt: str = ""
    skill: dict[str, Any] | None = None

    @property
    def context_id(self) -> str:
        return content_id(
            {
                "role": self.role.value,
                "facts": self.facts,
                "skill": self.skill,
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
            "skill": self.skill,
            "system_prompt_chars": len(self.system_prompt),
        }


#: 每种步骤的必填与可选字段。**必须告诉模型确切的字段名** ——
#: `Step` 与 `FeatureSpec` 都是 `extra="forbid"`，模型多写一个 `description`
#: 就整条规格被拒。schema 是合同，把合同藏起来再指责对方违约是不讲理的。
STEP_SCHEMA: dict[str, dict] = {
    "window": {"required": ["name", "kind", "source", "field", "op", "window_seconds"],
               "optional": ["offset_seconds"]},
    "innovation": {"required": ["name", "kind", "source", "field", "op",
                                "window_seconds", "baseline_seconds"],
                   "optional": ["offset_seconds"],
                   "note": "baseline_seconds 必须长于 window_seconds"},
    "ratio": {"required": ["name", "kind", "inputs"], "note": "inputs 恰好两个已定义步骤名"},
    "difference": {"required": ["name", "kind", "inputs"], "note": "inputs 恰好两个"},
    "zscore": {"required": ["name", "kind", "inputs", "window_seconds",
                            "sample_every_seconds", "min_samples"],
               "note": (
                   "inputs 恰好一个。参考分布取自输入步骤在 t - k*sample_every_seconds"
                   "（k = 1..window_seconds//sample_every_seconds）上的取值；"
                   "sample_every_seconds >= 60；min_samples >= 3 且不得超过该样本数；"
                   "样本数上限 512。min_samples 计**互异取值**：采样步长小于数据节奏时"
                   "会反复读到同一批数据，重复样本压低标准差并放大 z"
               )},
    "rank_pct": {"required": ["name", "kind", "inputs", "window_seconds",
                              "sample_every_seconds", "min_samples"],
                 "note": (
                     "与 zscore 同一张采样网格，同样的字段与同样的约束，"
                     "只是归一方式不同：输出是当前值在参考样本中的分位排名，"
                     "取值域 [0,1]（平局各算一半）。"
                     "重尾的量用它比用 zscore 稳健 —— 无论尾多重，任何单个观测的"
                     "杠杆都被 [0,1] 这个界约束住；代价是丢掉幅度信息，"
                     "因此它不是 zscore 的替代，是另一个假设"
                 )},
    "residualise": {"required": ["name", "kind", "inputs", "controls",
                                 "window_seconds", "sample_every_seconds", "min_samples"],
                    "note": (
                        "inputs 恰好一个；controls 为 1 至 3 个**互异**的已登记"
                        " Baseline Control（brent、own_realised_volatility 可组合使用："
                        "同时减掉国际油价与自身波动持续性，增量主张更强）。"
                        "与 zscore 同一张采样网格：拟合样本取自"
                        " t - k*sample_every_seconds，**严格在决策时点之前** —— "
                        "在全样本上拟合再取残差等于用未来数据定义残差。"
                        "单控制时 min_samples 计控制变量的互异取值；多控制时计成对样本数，"
                        "且任一控制恒定或共线即判无定义。"
                        "把 Baseline Control 减掉之后剩下的，才是另类数据的增量"
                    )},
}

#: FeatureSpec 自身的字段。同样是 extra="forbid"。
FEATURE_SPEC_SCHEMA = {
    "required": ["feature_id", "mechanism", "steps", "output_step",
                 "failure_condition", "authored_by"],
    "optional": ["code_artifact_id"],
    "note": "output_step 必须是 steps 里某个步骤的 name；步骤按依赖顺序排列",
}

#: 提案顶层字段的**类型**。只列字段名不列类型是不够的：实测一次真实调用里，
#: 模型把 `direction` 写成 `"positive"`，三次尝试全被拒，八分钟与三次调用预算白花，
#: 而那一次的 feature_spec 完全合法。契约要么写全，要么就不算契约。
PROPOSAL_OUTPUT_TYPES: dict[str, str] = {
    "mechanism": "字符串。一段话说清经济机制：什么信息、为什么先于价格、为什么作用于该 target",
    "source": "字符串，取 primitives.sources 之一",
    "target": "字符串，取 targets 里某个 target 的名字",
    "horizon": "字符串，与所选 target 的 horizon 一致",
    "universe": (
        "字符串，取 universes 里某一项的 universe 名。"
        "`full_coverage_panel` 是面板（多品种汇集，截面推断在这里才成立）；"
        "`<品种>_dominant_t1` 是单品种。**一次评价只能取一个** —— "
        "先跑面板再看逐品种、报告其中最好的那个，是事后检验"
    ),
    "direction": (
        "**整数，只能是 1 或 -1**。1 表示特征取值越高、label 越高，-1 表示越低。"
        "不接受 \"positive\" / \"negative\" / \"long\" 这类词，也不接受 0"
    ),
    "falsifiable_condition": "字符串。什么样的观测结果会使你判定该机制不成立",
    "feature_spec": "对象，字段以 primitives.feature_spec_schema 为准",
    "rationale": "字符串，可选。为什么在本轮选这个方向",
    "event_trigger": (
        "对象，可选。事件条件窗口：只在触发活跃的决策时点上评价。"
        "字段：field（字符串，如 \"cand:iran:p\"）、lookback_seconds（正整数）、"
        "min_abs_move（正浮点，概率的绝对移动阈值）。触发只用决策前的分桶，"
        "是预注册的样本限制；不活跃时点记入排除清单，不读它们的 outcome。"
        "预测市场的信息天然是事件性的 —— 长期在线的线性关系在本程序里"
        "已被反复证伪，事件窗口是对着它的长处提问"
    ),
    "change_summary": "字符串，可选。若在某一版基础上迭代，一句话说明改了什么",
}


def primitive_catalogue() -> dict:
    """提案器能用的全部原语。窄是刻意的，缺口应被声明而不是绕过。"""
    return {
        "sources": sorted(s.value for s in Source),
        "step_kinds": sorted(k.value for k in StepKind),
        "aggregations": sorted(o.value for o in Op),
        "step_schema": STEP_SCHEMA,
        "feature_spec_schema": FEATURE_SPEC_SCHEMA,
        "hard_rules": [
            ("字段名以 step_schema 与 feature_spec_schema 为准；"
             "**多写任何字段都会使整条规格被拒**"),
            "offset_seconds 只属于 window/innovation；派生步骤写它会被拒绝",
            "每个步骤都必须能从 output_step 沿 inputs 到达，否则整条规格被拒",
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
        "note": "判决分类与分母。**本视图供 Atlas 与人工复核使用，不进提案器上下文**",
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
    universes: list[dict] | None = None,
    learned_mismatches: tuple[str, ...] = (),
    research_direction: str | None = None,
    skill: Any = None,
    round_index: int = 0,
) -> ContextBundle:
    """组装提案器上下文。渲染后再过一次盲化检查。

    `learned_mismatches` 是**累积**的语义错配码，不是只有上一轮的：一旦
    「幅度对方向」被指出来，之后就不该再退回幅度特征。只取上一轮会让链在两种机制
    之间来回震荡（实测 A/B/A/B）。它走的是封闭词表，不含任何数字与效应量。
    """
    facts = {
        "task": "提出一个可证伪的研究提案",
        # 提前告诉，而不是判决时才冒出来：成本模型未建期间 candidate 结构性不可达。
        # 这不是提案能改变的，写在这里是让模型据此优化目标 —— 最有价值的产出是
        # 「带排除界的可信否定」与「界定 Baseline Control 边界的对照」。
        "system_state": (
            "系统级状态：成本模型尚未声明（M5 未完成），因此本轮任何提案的判决上限是"
            " null（可信否定）或 blocked，candidate 不可达。这与提案质量无关，"
            "也不该影响你选题；最有价值的产出是带排除界的否定与清晰的对照。"
        ),
        # 人类给出的研究方向。这是合法的输入通道：研究方向历来由人设定，
        # 它不含任何效应信息，且启动时整句写入账本（research_direction_declared），
        # 与私改提示词的区别正在于可审计。为空时不出现在上下文里。
        **({"human_research_direction": research_direction}
           if research_direction else {}),
        # 这是项目早就定下的口径（Merge-Plan-2 §3.1），不是对本轮结果的引导：
        # 只用 commodity_bar 的量价特征属 **Baseline Control**，不计入另类因子清单。
        # 不写出来，模型没有理由去残差化 —— 实测 run9 十一个版本里
        # residualise 用了 0 次，而其中已经出现过分母是已实现波动、目标也是
        # 已实现波动的构造（那重新发现的是波动率聚集，不是另类数据的 alpha）。
        "what_counts_as_a_finding": (
            "只用 commodity_bar 的量价特征属 Baseline Control，本身不计入另类因子清单。"
            "另类数据（pm_market）的主张必须是**它之上的增量**：若一个特征的预测力在"
            "控制掉商品自身的波动持续性或国际油价之后就消失，那它没有增量。"
            "用 residualise 把 Baseline Control 减掉，剩下的才是本项目要找的东西。"
            "把量价特征作为对照提出来也是有价值的产出，但要在 rationale 里说明它是对照"
        ),
        "data": data_facts,
        "targets": targets,
        # 可选的 universe。选哪个是模型的研究判断：面板与单品种不是同一个对象，
        # 前者是唯一能做截面推断的形态，后者的品种维恒为一组。
        "universes": universes or [],
        "primitives": primitive_catalogue(),
        # 评价合同的方法说明：这是检验的**机理**（预注册规则），不是任何结果。
        # 不写出来，模型没有理由避开注定低功效的构造形态。
        "evaluation_mechanics": (
            "证伪闸门之一是按 Episode 整块置换的检验：把标签整块打乱后重跑回归，"
            "若超过 10% 的打乱样本跑出不小于实际值的 |斜率|，判 placebo_failed。"
            "结构性推论：在决策节奏上几乎不动的构造（如远长于标签节奏的窗口均值/水平），"
            "打乱前后难以区分，注定低功效。信号事前筛会在读 outcome **之前**拦下"
            "有效独立观测 < 30（按一阶自相关折算）或互异值 < 10 的构造 —— 被拦不花"
            "检验预算，但也不产生任何结论。构造应在决策节奏上有实质变化：innovation、"
            "difference、短窗比值等形态天然满足；长窗水平请与更快的分量组合"
        ),
        "menu": {
            "candidate_families": menu,
            "known_biases": [b.__dict__ for b in menu_biases],
        },
        # 搜索覆盖（M17）：模型此前反复回到同一条轴上，不是偏好问题，
        # 是它看不见自己走过哪里（实测 cand:iran × sc × rv 一个组合就 34 条提案）。
        # 本节只数提案，不含任何判决 —— 与决定 0006 关闭的那条通道不是一回事。
        "search_coverage": coverage_menu(
            search_coverage(ledger, family=family),
            families=[row.get("family_id") for row in menu if row.get("family_id")],
            universes=[u.get("universe") for u in (universes or []) if u.get("universe")],
            targets=[t.get("name") for t in targets if t.get("name")],
            round_index=round_index,
        ),
        # **判决分类不再进提案器上下文（决定 0006）。**
        # M7 把它定价为安全，前提是它指向一个**匿名总体**：提案器每轮由独立子进程
        # 承载，跨轮不带上下文，因此「9 个 null」指的是哪 9 条它无从知道。
        # M9 的具名清单取消了匿名，两者一联合就能做减法：`null` 只可能在读过 outcome
        # 之后产生，因此 `#null <= tests_spent`；实测 run4 上 `#null = tests_spent = 9`，
        # 等式成立即推出「全部被度量过的具名规格都是 null」，而 null 的充要条件是
        # 置换检验未通过 = 实际斜率未超出其置换分布，那是一条关于**量级**的陈述。
        # `blinded_history` 保留，供 Atlas 与人工复核使用，只是不再进这份上下文。
        "denominators": ledger.denominators(family),
        # 第 0 层与第 1 层记忆（M9）。第 2 层（结果侧的归纳）对提案器永久关闭。
        "memory": proposal_memory(ledger, family),
        "budget": budget_facts,
        "blockers": blockers,
        "learned_semantic_mismatches": [
            {"code": code, "explanation": SEMANTIC_MISMATCH_TAXONOMY[code]}
            for code in learned_mismatches
            if code in SEMANTIC_MISMATCH_TAXONOMY
        ],
        "output_contract": {
            "required": [
                "mechanism", "source", "target", "horizon", "universe",
                "direction", "falsifiable_condition", "feature_spec",
            ],
            "optional": ["rationale", "change_summary"],
            "types": PROPOSAL_OUTPUT_TYPES,
            "note": (
                "只输出 JSON。特征必须用上面列出的原语表达。"
                "若本轮是在某一版基础上迭代，用 change_summary 一句话说明改了什么"
            ),
        },
    }
    prompt = render_proposer_prompt(facts, menu_biases)
    assert_blinded(prompt, Role.PROPOSER)
    system_prompt = ""
    skill_record = None
    if skill is not None:
        from .skills import render_system_prompt
        system_prompt = render_system_prompt(skill)
        # 方法说明在装载时已过一次闸门；这里再过一次，因为渲染可能拼进别的东西。
        assert_blinded(system_prompt, Role.PROPOSER)
        skill_record = skill.describe()
    return ContextBundle(
        role=Role.PROPOSER, facts=facts, prompt=prompt,
        declared_biases=list(menu_biases),
        system_prompt=system_prompt, skill=skill_record,
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
    ]
    learned = facts.get("learned_semantic_mismatches") or []
    if learned:
        lines += [
            "## 此前各版被语义审计拦下的错配（累积，不只是上一轮）",
            "",
            (
                "这些是**在读取任何结果之前**做出的诊断，只比对规格与目标的语义，"
                "不含任何效应量。被拦下的那些版本根本没有读 outcome。"
                "本轮的提案不得再犯同样的错配："
            ),
            "",
        ]
        lines += [f"- `{m['code']}`：{m['explanation']}" for m in learned]
        lines.append("")
    mem = facts.get("memory") or {}
    tried = mem.get("tried_features") or []
    price = mem.get("price_of_one_more_test") or {}
    lines += [
        "## 检验是有价格的",
        "",
        (
            f"本族已花掉 **{price.get('tests_spent', 0)} 次**检验。"
            f"噪声地板现在是 **{price.get('floor_now', 0)}**，"
            f"你再提一个会被评价的假设，它变成 **{price.get('floor_after_one_more', 0)}**。"
        ),
        "",
        (
            "地板是 |t| 必须越过的水平，按已花掉的检验次数抬升。"
            "**它对已有的与将来的全部结论同时生效** —— 多问一次，之前问过的每一个"
            "也要按更高的标准重读。因此不确定值不值得检验时，"
            "产出一条原语缺口声明或一条更锐的可证伪条件，比多花一次检验更有价值。"
        ),
        "",
    ]
    if tried:
        lines += [
            f"## 你此前写过的 {len(tried)} 条规格（不含任何结果）",
            "",
            "**不要重复其中任何一条。**重复一次要付一次地板抬升，而换来的是已经有的答案。",
            "",
        ]
        # 只有最近的几条带机制全文（induction.tried_features 的 full_detail）：
        # 早期条目只留 id 与形状，够回答「这条写过没有」，不占注意力。
        lines += [
            f"- `{t['feature_id']}`：{t['shape']}"
            + (f"\n  机制：{t['mechanism'][:110]}" if t.get("mechanism") else "")
            for t in tried
        ]
        lines.append("")
    gaps = mem.get("declared_primitive_gaps") or []
    if gaps:
        lines += [
            "## 你此前声明过的原语缺口",
            "",
        ]
        lines += [
            f"- 缺 `{g.get('missing_primitive', '?')}`：{str(g.get('mechanism', ''))[:90]}"
            for g in gaps
        ]
        lines.append("")
    lines += [
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
            "只输出一个 JSON 对象，不要有任何解释文字或围栏之外的内容。"
            "字段名严格以 primitives.step_schema 与 primitives.feature_spec_schema 为准："
            "**多写一个字段整条规格就会被拒绝**。"
            "顶层字段的类型见 output_contract.types，其中 direction 是整数 1 或 -1，"
            "写成词会使整个提案被拒。"
        ),
        "",
        (
            "字段见 output_contract。特征必须用 primitives 里列出的"
            "原语表达；若现有原语无法表达你想要的机制，改为输出 "
            '`{"unsupported_mechanism": {...}}`，说明缺哪个原语以及为什么现有的不够用。'
            "声明缺口是有价值的产出，不是失败。"
        ),
    ]
    return "\n".join(lines)


def record_context(ledger: EvidenceLedger, bundle: ContextBundle, study_id: str) -> str:
    """把上下文写进账本。模型看到了什么本身就是证据。"""
    return ledger.append("context_assembled", bundle.ledger_payload(), study_id=study_id)
