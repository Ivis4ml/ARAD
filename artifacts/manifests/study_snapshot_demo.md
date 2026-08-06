# Study demo-sc-rv-geopolitical-innovation 判决快照

- Verdict：`blocked`　下一步动作：`wait_for_data`
- 理由：评价机尚未建成，且 Polymarket 侧缺机制分族（Decision Map #12）。本 Study 未读取任何 outcome，statistical denominator 为 0；在这两项就绪之前，任何非 blocked 的判决都不可能有证据支撑。
- 当时可见数据范围：{'forward_data': 'not read (per-Study forward eligibility 未到期)', 'from': '2022-11-02T02:30:00+08:00', 'rows': 1054, 'segment': 'discovery', 'to': '2024-12-31T15:00:00+08:00'}

## 分母

- proposal denominator：2（其中预检挡下 1）
- statistical denominator：0

## 冻结的假设

- 提案：{'direction': 1, 'falsifiable_condition': '概率创新与下一 session 已实现波动无关则证伪', 'horizon': 'next_session', 'mechanism': '闭市期间地缘政治概率创新', 'proposed_by': 'demo', 'rationale': 'M2.5 词表显示 iran/israel/russia 是数据中最密集的地缘实体', 'source': 'polymarket', 'target': 'sc_rv_next_session', 'universe': 'sc_dominant_t1'}
- Hypothesis Lock：{'controls': ['sc_own_information', 'cls_public_news'], 'experiment_family': 'sc_rv_geopolitical_innovation', 'locked_at': '2026-08-06T00:51:26.539057+00:00', 'proposal_id': 'e195877b665a1629e12c4dcf8d8ea54cc36a3600d09db68ba6e25ba0f65c05f1', 'sample_segments': ['discovery'], 'stage': 'hypothesis'}
- Confirmatory Lock：{'controls': ['sc_own_information', 'cls_public_news'], 'cost_model': 'placeholder', 'economic_bound': '待人工冻结', 'formula': 'rv_next_session ~ residualised_probability_innovation + controls', 'hypothesis_id': 'dc1a686dd1ef692b393a8ad6e039e77d2a80b6f0eea3adefc183c9a33da3a0a6', 'locked_at': '2026-08-06T00:51:26.539072+00:00', 'preregistered_diagnostics': ['leakage', 'pseudo_replication', 'influence_points', 'classical_factor_proxy', 'single_regime', 'cost'], 'stage': 'confirmatory', 'statistics': ['two_way_cluster', 'block_bootstrap'], 'test_family': 'sc_rv_geopolitical_innovation', 'transforms': ['log', 'winsorise_none']}

## 读过 outcome 的检验（0 次）


> 快照只呈现判决当时可见的内容；forward 数据与标签不可见。