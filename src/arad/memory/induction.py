"""对过往经验的归纳（M9）。**按「知道这件事要付多少代价」分层。**

组合空间无限不等于可以一直找下去：零假设带按 √(2 ln n) 抬升，因此搜索是有价格的。
实测同一条 t = 2.049 的证据，在 9 次检验下自罚奖励 +0.195，到第 25 次就变成 −0.227。
不是它变弱了，是我们自己把地板抬上去了。穷举无限组合等于把地板抬到没有任何真实效应
够得着。

**因此记忆的任务不是让模型想出更多主意，而是让它少花检验。**主意是免费的，
检验是唯一稀缺且被定价的资源。

分层：

- **第 0 层（本模块，免费）**：提案侧。写过哪些机制与构造、哪些规格因回看深度
  超出覆盖而无定义、声明过哪些原语缺口、撞过哪些语义错配码。这些在**读任何
  outcome 之前**就已知，因此泄漏为零是按构造成立的，不靠事后检查。
- **第 1 层（本模块，已披露）**：消耗账。分母与地板此前以「统计量」的形式给出，
  改为以**报价**的形式：这个族已花掉几次检验、地板是多少、再提一个变成多少。
  同样一个数，说成价格，决策才会变。它只是 n 的函数，不含任何结果。
- **第 2 层（不在本模块，对提案器永久关闭）**：结果侧的归纳。「哪类机制效应更大」
  恰恰是零假设带在度量的那个过程，而且更糟 —— `E[max|z|]` 假设独立抽取，
  被引导的搜索破坏该假设，而带**不会**为此定价。这一层给人与确定性调度器看。

一条无法消除的小样本泄漏，如实记在这里：族内只有一条规格且只有一条判决时，
两者的对应关系是平凡的。这在提案器视图里本来就存在（判决计数一直可见），
本模块不加重它，也无法消除它。规格按 content_id 排序而不是按时间，
因此至少不额外泄漏「越近的越可能是哪一个判决」。
"""

from __future__ import annotations

from ..evaluation.selection import expected_max_abs_z
from .ledger import EvidenceLedger

INDUCTION_VERSION = "0.1.0"

#: 一条规格在记忆里保留哪些字段。**全部来自模型自己的产出**，不含任何评价机产物。
REMEMBERED_SPEC_FIELDS = (
    "feature_id", "mechanism", "steps", "output_step",
    "failure_condition", "required_lookback_seconds", "sources", "content_id",
)


def _step_shape(step: dict) -> str:
    """把一个步骤压成一行。给模型看构造形状，不是让它逐字复制。"""
    kind = step.get("kind", "?")
    if step.get("inputs"):
        inner = ", ".join(step["inputs"])
        return f"{kind}({inner})"
    field = step.get("field") or "?"
    op = step.get("op") or "?"
    return f"{kind}({field}, {op}, {step.get('window_seconds')}s)"


def tried_features(ledger: EvidenceLedger, *, limit: int = 200) -> list[dict]:
    """已经写过的规格。**按 content_id 排序，不带 study_id，不带任何判决。**

    走 `ledger.proposer_memory()`：那是账本自己强制的窄口子，只放两种事件、
    逐字段过白名单、且不返回 study_id。不走 `read_events` —— 全量读取对提案器
    是禁止的，而「在调用方小心一点」不是边界。
    """
    seen: dict[str, dict] = {}
    for payload in ledger.proposer_memory("feature_spec_locked"):
        content_id = payload.get("content_id")
        if not content_id or content_id in seen:
            continue
        seen[content_id] = {
            "content_id": content_id,
            "feature_id": payload.get("feature_id", ""),
            "mechanism": payload.get("mechanism", ""),
            "shape": " -> ".join(_step_shape(s) for s in payload.get("steps", [])),
            "sources": payload.get("sources", []),
        }
    return [seen[k] for k in sorted(seen)][:limit]


def search_price(ledger: EvidenceLedger, family: str) -> dict:
    """第 1 层：把分母与地板说成价格。只是 n 的函数，不含任何结果。"""
    spent = ledger.denominators(family)["statistical_denominator"]
    now = expected_max_abs_z(spent) if spent else 0.0
    nxt = expected_max_abs_z(spent + 1)
    return {
        "tests_spent": spent,
        "floor_now": round(now, 4),
        "floor_after_one_more": round(nxt, 4),
        "note": (
            "地板是 |t| 必须越过的噪声水平，按已花掉的检验次数抬升（√(2 ln n)）。"
            "每多提一个会被评价的假设，**已有的与将来的全部结论**都要按更高的地板重读。"
            "因此不确定值不值得检验时，产出一条原语缺口声明或一条更锐的可证伪条件，"
            "比多花一次检验更有价值"
        ),
    }


def proposal_memory(ledger: EvidenceLedger, family: str, *, limit: int = 200) -> dict:
    """第 0 层加第 1 层。这是允许进提案器上下文的全部归纳。"""
    gaps = ledger.proposer_memory("primitive_gap_declared")
    return {
        "induction_version": INDUCTION_VERSION,
        "tried_features": tried_features(ledger, limit=limit),
        "declared_primitive_gaps": gaps,
        "price_of_one_more_test": search_price(ledger, family),
        "note": (
            "这些是**你自己**此前的产出与本族已消耗的检验预算，不含任何效应的方向与量级。"
            "给你看它们，是为了让你不必重复已经问过的问题 —— 重复一次问题要付一次地板抬升"
        ),
    }
