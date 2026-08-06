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
from .pm_text_corpus import _cutoff_epoch, slug_tokens

FAMILY_NAMESPACE = "pm_candidate_family"


def _size_all_families(
    market_text: pa.Table,
    presence: pa.Table,
    market_totals: pa.Table,
    families: list[dict],
    cutoff: str,
) -> dict[str, dict]:
    """一遍扫过全部市场，同时给所有族算规模。

    逐族各扫一遍全库是 O(族数 × 市场数)：2,108 个族对 120 万市场就是 25 亿次操作。
    这里反过来，按市场查它命中哪些族，复杂度降到 O(市场数 × 每市场 token 数)。
    """
    token_to_families: dict[str, list[str]] = {}
    for family in families:
        for token in family["tokens"]:
            token_to_families.setdefault(token, []).append(family["family_id"])
    first = dict(
        zip(
            presence.column("condition_id").to_pylist(),
            presence.column("first_trade_ts").to_pylist(),
        )
    )
    totals = {
        c: (t, n)
        for c, t, n in zip(
            market_totals.column("condition_id").to_pylist(),
            market_totals.column("trades").to_pylist(),
            market_totals.column("notional").to_pylist(),
        )
    }
    limit = _cutoff_epoch(cutoff)
    acc: dict[str, dict] = {
        f["family_id"]: {"markets": 0, "trades": 0, "notional": 0.0} for f in families
    }
    all_markets = all_trades = 0
    for cid, base in zip(
        market_text.column("condition_id").to_pylist(),
        market_text.column("slug_base").to_pylist(),
    ):
        ts = first.get(cid)
        if ts is None or ts >= limit:
            continue
        trades, notional = totals.get(cid, (0, 0.0))
        all_markets += 1
        all_trades += trades
        hits = {
            fid for token in slug_tokens(base) for fid in token_to_families.get(token, ())
        }
        for fid in hits:
            bucket = acc[fid]
            bucket["markets"] += 1
            bucket["trades"] += trades
            bucket["notional"] += notional
    return {
        fid: {
            "cutoff": cutoff,
            "markets": v["markets"],
            "markets_share": v["markets"] / all_markets if all_markets else 0.0,
            "trades": v["trades"],
            "trades_share": v["trades"] / all_trades if all_trades else 0.0,
            "notional_provisional": v["notional"],
            "universe": {"markets": all_markets, "trades": all_trades},
        }
        for fid, v in acc.items()
    }


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
    sizes = _size_all_families(market_text, presence, market_totals, families, cutoff)
    registered = []
    for family in families:
        sizing = sizes[family["family_id"]]
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
