# ARAD Decision Map

本地图是实现顺序的唯一入口，隶属于 canonical plan `Merge-Plan-2.md`（决定 0002）。
已回答项冻结产品边界；未回答项是下一轮逐一推进的调查票，而不是在同一轮凭直觉全部填满。
当前前沿见文末"当前前沿"一节（此行不再单独维护状态，避免与票内 Answer 不一致）。

## #1 — 产品真相与停止语义

- **Blocked by**: nothing
- **Type**: Discuss
- **Question**: ARAD 能承诺什么，哪一层允许停止？
- **Answer**: 已决定。承诺持续、可审计的研究生产线与因子库存维护，不承诺必然发现统计有效因子。Search Episode 可结束并重启；Study 以明确 Verdict 结束；Research Service 只能人工暂停或关闭。

## #2 — 领域语言与研究工作单元

- **Blocked by**: #1
- **Type**: Discuss
- **Question**: Feature、Signal、Factor、Study、Episode、Program 的边界是什么？
- **Answer**: 已决定，见 `CONTEXT.md`。Study 取代 Strategy 成为最小研究单元；Signal 必须绑定 target 与 horizon；Factor 是带证据和生命周期的版本化 Signal 家族。

## #3 — 数据源真值与 Point-in-Time 合同

- **Blocked by**: #2
- **Type**: Research
- **Question**: 每个原始字段的 event/publication/availability time、覆盖、重复、修订和不可用条件是什么？
- **Answer**: **已回答（2026-08-05，M1 完成）**。机器 manifest 位于 `artifacts/manifests/`（三源 JSON + `audit_report.md`），由 `arad data-audit` 只读生成，指纹经重跑验证确定性。已固化：商品 tick 66 zip / 802,975 CSV / 909 交易日（20221101 至 20260730）/ 88 名义品种，时间合同含夜盘归属规则；Polymarket HF 段 6.019 亿行（2022-11-21 至 2026-04-28）+ 扩展段 2.537 亿行（至 2026-07-14），接缝间隔 248 秒无重叠，**列类型冲突实测 15 处**（4 处语义冲突 + 11 处 large_string/string 差异），`resolved_at` 禁用；CLS 2,361 文件 / 894,220 行 / 零自然日缺口，`Reads/Comments/Shares` 禁用（合同层硬拒绝）。负向测试覆盖时间单位混淆、夜盘归属、禁用字段访问、接缝重叠、指纹确定性（22 项通过）。仍列 provisional：郑商所 Turnover 口径普查、空壳比例、relay/venue/negRisk 覆盖（进入 M2/M5 票）。
  **验收修复（2026-08-05 第二轮，Codex 交叉审查）**：修复 P0 两项（空数据源与缺失接缝统计改为 error 级并阻断质量闸门，CLI 非零退出；指纹加入来源内容身份，含保证等级声明：商品 zip 中央目录 CRC 聚合、CLS 全文 sha256、Polymarket footer 字节聚合）与 P1 三项（全分区 schema 签名审计，实测两段各仅 1 种签名无漂移；provisional 字段默认禁止消费，仅受审计 override 可用；PM 字段合同补全至 31 列，`winning_outcome_label`/`resolution_status` 新增禁用）。**接缝行级主键核验完成**：接缝日 HF 1,327,582 行对扩展段 1,200,082 行，复合键交集为 0，该项从 provisional 转 verified。回归测试增至 35 项，全仓 ruff 通过，指纹重跑确定性复验通过。

## #4 — 商品合约与连续序列

- **Blocked by**: #3
- **Type**: Prototype
- **Question**: 如何从逐合约 tick 确定性地产生可交易主力、次主力与连续收益，同时避免换月前视？
- **Answer**: 未回答。需要比较仅用 t-1 成交量/持仓的主力规则、固定换月规则和全合约 panel；来源自带乱码连续文件在审计前禁用。

## #5 — 事件语义、映射与 Episode

- **Blocked by**: #3
- **Type**: Research
- **Question**: 如何把 Polymarket 市场和 CLS 新闻映射为可泛化机制，并定义独立 Episode？
- **Answer**: 未回答。必须同时做语义、机制和经验三层去重；旧手工 taxonomy 只能当种子，不能当真值。需要金标样本和跨模型一致性审计。

## #6 — Study 合同与不可变评估器

- **Blocked by**: #3, #5
- **Type**: Prototype
- **Question**: Hypothesis Lock、功效预检、运行、诊断、Verdict 和 artifact 的最小机器合同是什么？
- **Answer**: 未回答。以旧 ADAR v3 的 StudySpec 为输入，但需补齐 Feature Object、数据哈希、Experiment Family、holdout 权限、成本和正交性接口。

## #7 — 统计准入与经济边界

- **Blocked by**: #4, #6
- **Type**: Discuss
- **Question**: 各 target×horizon 的经济效应下限、MDE、n_eff、FDR/FWER、影响点、成本和组合准入阈值是什么？
- **Answer**: 未回答。门槛必须在查看结果前由领域专家或公开成本模型冻结；不同目标不能共享一个随意的 bp 上限。

## #8 — 假设搜索空间与研究多样性

- **Blocked by**: #5, #6
- **Type**: Discuss
- **Question**: 模型可以变异哪些维度，如何防止同质化和无限 p-hacking？
- **Answer**: 未回答。候选维度应是 mechanism×source×target×horizon×regime×transform；完整提案批次计入分母，LLM 只看盲化功效账本，且需配额约束机制覆盖。

## #9 — 持久调度与故障恢复

- **Blocked by**: #6, #8
- **Type**: Prototype
- **Question**: 如何确保 stop、空计划、坏 JSON、provider 故障、进程重启和空间枯竭都不会丢失研究进度？
- **Answer**: 部分回答。需要 durable queue、租约、幂等 artifact、checkpoint 和显式状态机；模型无权写顶层终态。具体存储和恢复协议待 tracer bullet 验证。

## #10 — 因子库存、衰减与替代

- **Blocked by**: #7, #9
- **Type**: Prototype
- **Question**: Candidate 如何升级、Production 如何监控，何时降级/退役并触发替代？
- **Answer**: 未回答。至少分别监控预测、机制、数据、成本和正交性衰减；替代需求按库存缺口进入 Research Program，历史不得删除。

## #11 — 第一条端到端 tracer bullet

- **Blocked by**: #3, #4, #5, #6, #7
- **Type**: Prototype
- **Question**: 哪个最小 Study 能证明整条协议而非只证明一段回测代码？
- **Answer**: 候选已选：地缘政治概率创新 → SC 下一交易窗口开盘跳空/波动，加入国际油价与 CLS 公共信息控制。待 #3-#7 关闭后冻结，不预设为正结果。

## 当前前沿

票 #3 已关闭（M1 完成，含 2026-08-05 第二轮交叉审查验收修复）。
下一项为 **#4 商品合约与连续序列** 的 SC 窄切片部分（Merge-Plan-2 的 M2），
**开工前提**：计划 v1.0 定稿（交叉审查通过并冻结）。
