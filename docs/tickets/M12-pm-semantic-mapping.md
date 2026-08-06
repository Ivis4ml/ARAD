# 工程票 #12：Polymarket 市场语义映射

对应 Decision Map #12。前置：M2.5（PIT Market Index）已关闭 —— 市场与资产的
点时化身份已具备，缺的是**机制分族**。

## 已完成的取证阶段（2026-08-05）

产物：`artifacts/manifests/pm_metadata_audit.json`，命令
`python -m arad.cli pm-index metadata-audit`。该命令以非零码退出，因为两条
error 级 finding 尚未被解决 —— 这是设计如此：文本不可证时 Study 只能 blocked。

三条实测结论约束后续全部设计：

1. **扩展段完全没有 `category` 与 `category_refined`**（HF 段填充率 100%，
   扩展段 0%）。扩展段覆盖 2026-04-28 至 2026-07-14，占全史成交的 87.9%。
   任何以交易所类别为输入的映射在成交最密集的区段不可用。
2. **`market_slug` 在两次抓取之间会变化**：3,258 个跨段可比市场中 78 个不同，
   形态是末尾追加消歧数字段（`...-by-end-of-june` → `...-by-end-of-june-796-981-212`）。
   去掉末尾 `(-<数字>)+` 后跨段差异**归零**。因此映射必须以 `condition_id` 为键、
   以归一化基名为文本特征；以完整 slug 为键会在市场改名后静默失配。
3. **`outcome_label` 跨抓取稳定**（3,094 个可比 asset 零差异），但它是
   **asset 级**字段：按 `condition_id` 归并会把同一市场的 YES/NO 当成同一实体的
   两个取值，产生假漂移。首版审计犯过这个错，已修并有回归测试。

据此，历史时点可证明可见的文本只有：`condition_id`（不可变）、归一化 slug 基名、
`outcome_label`（按 asset）。`category` 只在 HF 段可用且属回填元数据，
`markets_clob.parquet` 的 `question`/`tags`/`end_date_iso` 等均无可证明的历史可见性。

## 范围

1. **版本化语义映射**：从归一化 slug 基名（HF 段可另加 `category` 作为
   provisional 辅助信号）产生 `mechanism_family` 标注；每个版本内容寻址、不可原地覆盖；
2. 映射以 `condition_id` 为键；同一市场在不同版本下的标注变化必须可追溯；
3. **金标样本**：人工标注一个分层抽样集合，作为准确率与一致性的基准；
4. **跨模型一致性审计**：至少两个独立 provider 对同一批市场标注，报告一致率与分歧样本；
5. 标注过程 label-blind：不读取 `resolution_status`、`winning_outcome_label`、
   `resolved_at`，也不读取任何商品收益或研究 target；
6. 输出接入 PIT Market Index：`(condition_id, mechanism_family, mapping_version)`，
   查询仍受 `eligible_from < decision_cutoff` 约束。

## 不做

- 不使用 `cn_registry_v3.parquet` 的 theme/product/sigma（已弃用并隔离）；
- 不消费无法证明历史可见性的可变元数据；确需使用时保持 provisional 并显式标注；
- 不做因子、不做评价机、不改 canonical sample split。

## 出口条件

- 映射版本化且内容寻址，同一版本可确定性重放；
- 金标样本上的准确率与跨模型一致率有结构化报告，不手抄数字；
- 负向测试：完整 slug 改名后映射仍命中（因为键是 `condition_id`，特征是基名）；
  资产级字段不得按市场级归并；结果字段读取被拒绝；
- 全仓 ruff 与 pytest 通过；Decision Map 更新。

## 需要人类裁决的事项

- **机制族的粒度与清单**：是沿用旧系统的 8 个主题（mideast_conflict、oil_price、
  russia_ukraine、metal_price、fed_policy、us_china_trade、us_shutdown、taiwan_risk）
  作为**待验证的假设集合**，还是从数据自下而上重新归纳？前者快但继承了旧系统的
  选择偏差，后者慢但独立。
- **金标样本的规模与标注人**：谁标、标多少、分歧如何裁决。
- **商品映射是否属于本票**：市场 → 机制族是语义问题；机制族 → 商品品种是经济假设，
  可能应留给 Study 的 Hypothesis Lock 而不是固化在映射表里。
