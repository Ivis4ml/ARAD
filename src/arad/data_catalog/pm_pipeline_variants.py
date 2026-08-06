"""管线变体的提案登记（决定 0004 连带约束 2）。

归纳管线的超参数是在观察"商品族是否浮现"的过程中调出来的。这些探索没有读取
SC outcome，但**目标函数是一个期望的定性结果**，属于以先验为目标的调参。
因此全部被弃变体必须各计一条被预检挡下的提案，进入 proposal denominator，
而不是只登记最终采纳的那套族。

本清单是**已发生探索的审计记录**，不是分类法：它记的是"我实际试过什么、
为什么放弃"，每条都附实测数字。清单只应追加，不应因为结论变化而改写历史条目。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..memory.ledger import EvidenceLedger
from ..registry.specs import ProposalSpec

VARIANT_NAMESPACE = "pm_taxonomy_pipeline_variant"


@dataclass(frozen=True)
class PipelineVariant:
    """一个被探索过的管线配置及其结局。"""

    variant_id: str
    stage: str
    params: dict
    outcome: str
    adopted: bool
    abandoned_reason: str = ""

    def proposal(self) -> ProposalSpec:
        return ProposalSpec(
            mechanism=f"分类法管线变体 {self.variant_id}（{self.stage}）",
            source="polymarket",
            target="unbound",
            horizon="unbound",
            universe=f"taxonomy_pipeline:{self.stage}",
            direction=0,
            falsifiable_condition=(
                "该变体若无法产生稳定、可复现且非退化的机制分组，则被证伪"
            ),
            proposed_by="pm_taxonomy_pipeline",
            rationale=f"参数 {self.params}；实测结局：{self.outcome}",
        )


#: 2026-08-05 之前实际探索过的全部变体。数字来自当次实测，不得事后修改。
EXPLORED_VARIANTS: tuple[PipelineVariant, ...] = (
    PipelineVariant(
        "template-level", "归纳单元",
        {"unit": "slug_template"},
        "542,058 个模板中 90.6% 为单例；头部由机器生成的加密涨跌梯队占据"
        "（btc/eth/sol/xrp/doge/bnb/hype 合计 412,683 个市场，34%）",
        adopted=False,
        abandoned_reason="模板层被机器生成的市场系列淹没，不能直接当机制族",
    ),
    PipelineVariant(
        "pmi-threshold-only-cc", "建边规则",
        {"edges": "pmi_threshold_only", "clustering": "connected_components",
         "min_pmi_tried": [1.0, 2.0, 3.0, 4.0, 5.0]},
        "渗流：PMI 阈值 1.0/2.0 时 100% 的 token 在一个分量，3.0 时 99.9%，"
        "4.0 时 99.1%，5.0 时仍有 95.0%",
        adopted=False,
        abandoned_reason="纯阈值建边会被弱枢纽串成巨型分量，阈值无法解决",
    ),
    PipelineVariant(
        "mutual-knn-k5-cc", "建边规则",
        {"mutual_knn": 5, "clustering": "connected_components"},
        "9 个族，最大族 1,254 token",
        adopted=False,
        abandoned_reason="k 过大仍保留桥接边，巨型分量未被切开",
    ),
    PipelineVariant(
        "mutual-knn-k8-cc", "建边规则",
        {"mutual_knn": 8, "clustering": "connected_components"},
        "4 个族，最大族 1,324 token",
        adopted=False,
        abandoned_reason="同上，且更差",
    ),
    PipelineVariant(
        "mutual-knn-k3-cc", "聚类算法",
        {"mutual_knn": 3, "clustering": "connected_components"},
        "81 个族，最大族 648 token；该子图平均度仅 2.28，接近一棵树，"
        "连通分量必然把整条链并成一族",
        adopted=False,
        abandoned_reason="连通分量在近似树上不可用；oil 与 gold 陷在巨型族内",
    ),
    PipelineVariant(
        "max-tokens-1500", "词表宽度",
        {"max_tokens": 1500},
        "hormuz(188 市场)、crude(222)、strait(163) 被挡在词表外",
        adopted=False,
        abandoned_reason="为控制计算量设的任意上限，把有实质规模的实体排除了",
    ),
    PipelineVariant(
        "modularity-res-0p5", "聚类分辨率",
        {"clustering": "modularity", "resolution": 0.5},
        "316 族，最大 11 token，中位 3",
        adopted=False,
        abandoned_reason="与 res=1.0 差异不大，未采纳以免多一个自由度",
    ),
    PipelineVariant(
        "modularity-res-2p0", "聚类分辨率",
        {"clustering": "modularity", "resolution": 2.0},
        "326 族，最大 8 token，中位 3",
        adopted=False,
        abandoned_reason="同上",
    ),
    PipelineVariant(
        "cutoff-2024-01-01", "归纳期切点",
        {"induction_cutoff": "2024-01-01"},
        "期外模板覆盖率 0.0%",
        adopted=False,
        abandoned_reason="归纳期内市场过少（2,457），无法形成任何稳定分组",
    ),
    PipelineVariant(
        "cutoff-2025-01-01", "归纳期切点",
        {"induction_cutoff": "2025-01-01"},
        "期外模板覆盖率 0.9%",
        adopted=False,
        abandoned_reason="同上（10,204 个市场）",
    ),
    PipelineVariant(
        "cutoff-2026-01-01", "归纳期切点",
        {"induction_cutoff": "2026-01-01"},
        "期外模板覆盖率 26.7%；wti/brent/opec 不在词表，hormuz 仅 4 个市场，"
        "iran 只能形成 2 token 的族",
        adopted=False,
        abandoned_reason=(
            "PIT 上更诚实，但商品相关机制族根本不存在。**保留为对照工件**："
            "决定 0004 的检验 (b) 用它与全史版本对比，测出后见暴露的量级"
        ),
    ),
    PipelineVariant(
        "cutoff-2026-08-01-knn3-modularity-8000", "最终采纳",
        {"induction_cutoff": "2026-08-01", "max_tokens": 8000, "min_pmi": 3.0,
         "mutual_knn": 3, "clustering": "modularity", "resolution": 1.0},
        "2,108 个族；商品相关族浮现（hormuz strait / oil crude production / "
        "iran shipping / closes wti spy）；hindsight exposure 83.7%",
        adopted=True,
        abandoned_reason="",
    ),
)


def register_variants(ledger: EvidenceLedger) -> dict:
    """把全部探索过的变体登记为提案。被弃的标为预检挡下并附理由。"""
    rows = []
    for variant in EXPLORED_VARIANTS:
        proposal = variant.proposal()
        ledger.record_proposal(
            proposal.content_id,
            VARIANT_NAMESPACE,
            screened_out=not variant.adopted,
            reason=variant.abandoned_reason,
        )
        ledger.append(
            "pipeline_variant_recorded",
            {
                "variant_id": variant.variant_id,
                "stage": variant.stage,
                "params": variant.params,
                "outcome": variant.outcome,
                "adopted": variant.adopted,
                "abandoned_reason": variant.abandoned_reason,
                "proposal_id": proposal.content_id,
            },
        )
        rows.append(
            {
                "variant_id": variant.variant_id,
                "stage": variant.stage,
                "adopted": variant.adopted,
                "proposal_id": proposal.content_id,
            }
        )
    return {
        "variants_recorded": len(rows),
        "variants_abandoned": sum(1 for r in rows if not r["adopted"]),
        "denominators": ledger.denominators(VARIANT_NAMESPACE),
        "variants": rows,
        "note": (
            "超参数是在观察『商品族是否浮现』的过程中调出的，虽未读 SC outcome，"
            "但目标函数是期望的定性结果，属以先验为目标的调参，故全部计入分母"
        ),
    }
