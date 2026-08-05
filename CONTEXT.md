# ARAD Research Context

本文件固定 ARAD 的领域语言。研究、代码、产物和提示词都使用这些词，避免把“特征”“因子”“策略”和“实验”混为一谈。

## 数据与时间

**Observation**：
来自原始数据源的一条不可再分记录，例如一笔 Polymarket 成交、一条期货 tick 或一则财联社电报。
_Avoid_: Sample, Row

**Availability Time**：
研究者在真实历史时点最早能够获得某条 Observation 的时间；所有特征对齐都以它为准。
_Avoid_: Event time, Publication time, Resolved time

**Point-in-Time View**：
在给定决策时点，仅由当时已经可用的数据重建出的世界状态。
_Avoid_: Latest snapshot, Backfilled truth

**Market Belief**：
由某一 Polymarket 市场在 Point-in-Time View 中表达的、带市场身份与方向定义的概率状态。
_Avoid_: Price alone, Ground truth probability

**Independent Episode**：
统计上近似独立的一次信息冲击；同一事件、同一新闻链或高度重叠窗口的观测属于同一 Episode。
_Avoid_: Market row, Signal timestamp

## 研究对象

**Feature**：
具有经济含义、可重现计算和明确来源的可测事实；它尚未承诺对任何目标有预测力。
_Avoid_: Arbitrary transform, Indicator

**Signal**：
绑定了目标、预测时域、方向和可用时间的 Feature；同一 Feature 在不同时域上是不同 Signal。
_Avoid_: Feature, Trade

**Factor**：
一个版本化的 Signal 家族及其经济机制、证据、适用域和生命周期记录，而不是某次回归中显著的一列。
_Avoid_: Feature column, Strategy

**Candidate Factor**：
通过历史样本、对抗诊断和正交性闸门，但尚未通过未触碰前向样本确认的 Factor。
_Avoid_: Confirmed alpha, Production signal

**Production Factor**：
通过前向留出、成本与容量、组合边际价值和运行监控准入的 Factor。
_Avoid_: Candidate, Backtest winner

**Factor Inventory**：
按机制、品种、时域和风险暴露组织的 Candidate Factor 与 Production Factor 组合，并带有覆盖目标和替换需求。
_Avoid_: Factor count, Leaderboard

## 研究过程

**Hypothesis Lock**：
在读取目标变量结果前冻结的机制、方向、目标、时域、样本、控制、变换、分母和失败条件声明。
_Avoid_: Experiment config, Post-hoc rationale

**Study**：
回答一个冻结研究问题的最小可审计工作单元；`null` 和 `underpowered` 都是合法完整产出。
_Avoid_: Strategy, Trial

**Experiment Family**：
共享同一研究意图、且必须共同承担多重检验分母的一组 Study 或变体。
_Avoid_: Only the surviving tests

**Search Episode**：
在固定预算内探索一个局部假设邻域的过程；Episode 可以因枯竭或模型建议而结束，但不会结束 Research Service。
_Avoid_: Campaign, Global run

**Research Program**：
持续调度 Study、维护研究覆盖和 Factor Inventory 的长期任务。
_Avoid_: One process invocation, Strategy search

**Evidence Ledger**：
追加式保存全部提案、冻结、运行、诊断、判决和数据血缘的事实记录。
_Avoid_: Results table, Best runs

**Failure Archive**：
Evidence Ledger 中用于记录 `null / underpowered / blocked / error / retired` 及复跑条件的知识集合。
_Avoid_: Trash, Failed experiments

## 判决与运行

**Study Verdict**：
Study 的终态：`candidate / null / underpowered / blocked / error`；它描述证据状态，不代表服务是否停止。
_Avoid_: Pass/fail, Stop reason

**Research Service**：
持久运行、可恢复的顶层调度器；它只接受人工 `pause / resume / shutdown`，不接受模型全局停止。
_Avoid_: Loop script, Campaign

**Factor Decay**：
Factor 的预测力、机制有效性、数据质量、成本后收益或组合正交性相对准入基线的持续恶化。
_Avoid_: One losing period, P-value increase

**Retirement**：
Production Factor 因预先定义的退役规则退出库存，同时保留完整历史并触发替代研究需求。
_Avoid_: Delete, Forget
