# 决定 0001：两组设计文档的合并与权威划分

日期：2026-08-05。状态：**已被 [决定 0002](0002-canonical-plan.md) 取代**（canonical plan 为 `Merge-Plan-2.md`），本文保留为历史记录。

## 背景

2026-08-05 上午，两个并行工作的会话各自在 ARAD 写入了一组设计文档：

- A 组（11:20 至 11:24）：`CONTEXT.md`、`docs/FOUNDATION_ANALYSIS.md`、
  `docs/DECISION_MAP.md`、`docs/IMPLEMENTATION_PLAN.md`、`docs/ENGINEERING_PROMPT.md`，
  并改写了 `README.md`。强项：领域语言、三层停止语义状态机
  （Search Episode / Study / Research Service）、按依赖排序的决策票、
  逐票实施的工程提示词。
- B 组（11:29 至 11:34）：`docs/00-material-analysis.md`、`docs/01-goal.md`、
  `docs/02-plan.md`、`program.md`。强项：五个专项深度审查得出的数据事实
  （tick 909 交易日、六陷阱、negRisk 缺口与可回爬性、财联社完整性证伪、
  Alpha-Data 2,742 项检验的正负结论、ADAR 循环死结的代码级定位）、
  量化判据细节、噪声底与基线因子库设计。

两组内容高度互补，无根本矛盾。

## 权威划分（本决定的核心）

| 主题 | 权威文档 |
|---|---|
| 领域语言与术语 | `CONTEXT.md` |
| 数据事实（覆盖、陷阱、缺口） | `docs/00-material-analysis.md`（其结论覆盖其他文档中的同类陈述） |
| 最终形态与停止语义 | `docs/01-goal.md` + `FOUNDATION_ANALYSIS.md` §4/§5（三层状态机采纳 A 组表述） |
| 实施顺序 | `DECISION_MAP.md`（决策票机制）；`IMPLEMENTATION_PLAN.md` 与 `02-plan.md` 待合并，冲突处以 DECISION_MAP 的票序为准 |
| 建设期提示词（逐票实现系统） | `docs/ENGINEERING_PROMPT.md` |
| 运行期提示词（研究循环协议） | `program.md` |

建设期与运行期是两个不同阶段：ENGINEERING_PROMPT 指导"把机器造出来"，
program.md 指导"机器造好后如何做研究"。两者不合并。

## 已执行的事实更正

依据 B 组审查证据，对 A 组文档做了三处定点更正：

1. 财联社"历史回填仅 70%"结论已被独立逐日比对证伪（实际 99% 至 100%），
   `FOUNDATION_ANALYSIS.md` §3.3 与 `ENGINEERING_PROMPT.md` 数据事实节已更正；
2. 期货 `主力连续` 文件不是"编码损坏的禁用副本"，而是当日主力的逐字节别名，
   `InstrumentID` 保留真实代码，换月时点可恢复（连续序列仍自行构造，这一点两组一致）；
3. Polymarket 数据事实补全：negRisk 缺口机制、自爬扩展段、4 处类型冲突、续爬需求。

## 遗留合并项（需人类确认后执行）

- `IMPLEMENTATION_PLAN.md`（M0 至 M8）与 `02-plan.md`（Phase 0 至 5）的目录结构与
  阶段划分存在差异（例如调度存储 SQLite 对纯文件注册表、tracer bullet 先行对
  基线因子库先行）。建议以 A 组的"tracer bullet + 决策票"作为推进方式，
  以 B 组的数据层 ETL 规格与基线因子库设计作为 M1/M2 票的实质内容。
- 里程碑表述差异：B 组承诺"5 个 production 因子"为里程碑一；A 组明确拒绝
  承诺因子数量、只承诺库存覆盖目标。二者可统一为：因子数量是**调度优先级与
  库存覆盖目标**（研究资源向未达标机制桶倾斜），不是降低证据门槛的理由；
  `01-goal.md` 第 3 节的六条判据描述的是"何时允许宣告里程碑"，不是"必须何时达到"。
