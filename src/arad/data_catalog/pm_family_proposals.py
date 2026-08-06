"""把候选机制族登记为提案（#12 与 M3 的接点）。

每个候选族都是**提案**，不是真值：全部计入 proposal denominator，包括被规模预检
挡下的。这正是 #12 之前被阻塞的环节 —— 在账本存在之前，"挑一批候选"无处留痕。

登记只写族 id、成员 token 与规模，不写名字、不写商品映射。族→商品是经济假设，
应在各 Study 的 Hypothesis Lock 冻结，不固化进映射表（2026-08-05 记录的可逆假设）。
"""

from __future__ import annotations

import pyarrow as pa

from ..memory.ledger import EvidenceLedger
from ..registry.specs import ProposalSpec
from .pm_entity_clusters import ClusterSpec, induce_families
from .pm_text_corpus import size_entity_proposal

FAMILY_NAMESPACE = "pm_candidate_family"


def register_families(
    ledger: EvidenceLedger,
    market_text: pa.Table,
    presence: pa.Table,
    market_totals: pa.Table,
    spec: ClusterSpec,
    *,
    min_markets: int = 50,
) -> dict:
    """归纳候选族并逐个登记为提案。规模不足的照样登记，只是标为被挡下。"""
    families, stats = induce_families(market_text, presence, spec)
    cutoff = spec.induction.induction_cutoff
    registered = []
    for family in families:
        sizing = size_entity_proposal(
            market_text, presence, market_totals, family["tokens"], cutoff=cutoff
        )
        proposal = ProposalSpec(
            mechanism=f"候选机制族 {family['family_id']}：{' '.join(family['head_tokens'])}",
            source="polymarket",
            target="unbound",
            horizon="unbound",
            universe=f"markets_matching_tokens@{cutoff}",
            direction=0,
            falsifiable_condition=(
                "该族的成员市场若在任何已声明 target 上都无可检出信息，则该族被证伪"
            ),
            proposed_by="pm_entity_clusters",
            rationale=(
                f"自下而上归纳：PMI 互为 top-{spec.mutual_knn} 近邻的连通分量；"
                f"成员 {family['size']} 个 token，归纳期内覆盖 {sizing['markets']} 个市场"
            ),
        )
        screened = sizing["markets"] < min_markets
        ledger.record_proposal(
            proposal.content_id,
            FAMILY_NAMESPACE,
            screened_out=screened,
            reason=(
                f"规模预检不足：归纳期内仅 {sizing['markets']} 个市场，低于下限 {min_markets}"
                if screened else ""
            ),
        )
        ledger.append(
            "candidate_family_registered",
            {
                "family_id": family["family_id"],
                "proposal_id": proposal.content_id,
                "tokens": family["tokens"],
                "head_tokens": family["head_tokens"],
                "sizing": {k: v for k, v in sizing.items() if k != "proposal_tokens"},
                "screened_out": screened,
            },
        )
        registered.append(
            {
                "family_id": family["family_id"],
                "proposal_id": proposal.content_id,
                "tokens": family["size"],
                "head_tokens": family["head_tokens"],
                "markets": sizing["markets"],
                "trades": sizing["trades"],
                "screened_out": screened,
            }
        )
    registered.sort(key=lambda r: (-r["markets"], r["family_id"]))
    return {
        "spec": spec.describe(),
        "induction_stats": {k: v for k, v in stats.items() if k != "spec"},
        "families_registered": len(registered),
        "families_screened_out": sum(1 for r in registered if r["screened_out"]),
        "denominators": ledger.denominators(FAMILY_NAMESPACE),
        "families": registered,
    }
