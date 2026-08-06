# 决定 0004：分类法冻结时点进入前向门

- 日期：2026-08-05
- 状态：已采纳
- 触发：Decision Map #12 的机制族归纳期裁决，经独立评审
- 影响：扩展 `Merge-Plan-2.md` §4 的前向门公式

## 裁决

§4 的前向门由

```text
observation_time > max(system_protocol_freeze_at, study_confirmatory_freeze_at,
                       source_snapshot_at) + embargo
```

扩展为

```text
observation_time > max(system_protocol_freeze_at, study_confirmatory_freeze_at,
                       source_snapshot_at, taxonomy_freeze_at) + embargo
```

实现见 `arad.temporal.episode.forward_gate()` 与 `classify_segment(taxonomy_freeze_at=...)`。

## 理由

机制族分类法从 Polymarket 市场文本自下而上归纳。归纳期若覆盖裁决区间，
机制分组就被未来塑造过。

关键论证是**市场宇宙不是外生文本**：Polymarket 上创建哪些市场，对真实事件内生，
而这些事件恰恰是推动商品价格的事件。实测证据：`hormuz` 相关市场从 4 个涨到 188 个，
`iran` 从 277 个涨到 1,399 个 —— 增长正是因为发生了同时推动原油波动的地缘事件。

因此"市场宇宙的后见"与"结果的后见"**不是两类不相交的污染**。在全史宇宙上选机制，
等于在一个与目标已实现波动相关的变量上做选择：条件化之后，
`E[效应估计 | 该族被选中] ≠ E[效应估计]`，选择偏差变成估计偏差。
它只在冻结之后到达的前向数据上失效，因为那时裁决数据与选择事件独立。

这与 `cn_registry_v3.parquet` 因全窗口成员资格筛选被弃用是**同一条逻辑**。
不能为自建分类法豁免同类操作，只能封顶并前移前向门。

## 连带约束

1. **verdict 封顶**：归纳语料与 Study 读取 outcome 的任何区间重叠时，
   verdict 上限为 `candidate`（机器可检，见 `TaxonomyContamination.verdict_cap()`）。
   这不新增限制 —— §4 本就规定历史数据最多产生 Candidate。
2. **管线变体全部计入 proposal denominator**：归纳期切点、token 集宽度、
   PMI 阈值、互为 top-k 的 k、纯阈值版本等被弃变体，各计一条被预检挡下的提案。
   这些超参数是在观察"商品族是否浮现"的过程中调出来的，虽未读 SC outcome，
   但目标函数是一个期望的定性结果，属于以先验为目标的调参。
3. **诚实陈述**：实测覆盖率曲线（2025-07 切点期外覆盖仅 3.3%）与样本段分布
   （discovery 段仅占成交 0.84%）说明商品机制在 Polymarket 上是 **2026 现象**，
   历史段对商品族本无统计功效。M4 tracer bullet 的定位相应改为**管线验证**
   而非证据生产，其预期 verdict 是 `underpowered`（§5.3 的合法结果），
   随后 `queue_forward`。不得用归纳期的选择让历史段显得有证据。

## 可推翻条件（预注册）

前向数据到达 N 个月后，用**仅前向语料**重新归纳分类法。若冻结族的再现稳定性
（token 集 Jaccard 或调整 Rand 指数）低于事先声明的阈值，
则宣布全史分类法为后见工件，相关 Study 强制开新版本。

## 采纳的检验

- **(a) 族涌现日期曲线**：每个族在哪个归纳期切点首次出现；Study 层指标为
  hindsight exposure（涌现日期晚于该 Study discovery 窗口末端的族占比）。
- **(b) 结果相邻性检验**：族活动落在 |SC 日收益| 顶部十分位日上的份额，
  比较晚涌现族与早涌现族，置换检验给出效应量与 p 值。这是直接测量偏差通道的主指标。
- **(c) 2024 至 2025 边界预演**：双重差分形式的后见溢价。
- **(d) 前向分裂试验**（预注册，最终裁决）：两套分类法同管线，只在
  `taxonomy_freeze_at` 之后的前向数据上裁决，比较前向收缩率。
