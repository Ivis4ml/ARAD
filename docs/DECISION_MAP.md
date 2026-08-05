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
- **Answer**: **已回答（2026-08-05，M2 SC 窄切片完成）**。规则冻结为
  `t1-volume-open_interest-monotone-v1`：主力取**前一交易日**成交量最大的合约，
  依次以持仓量、合约代码为次级排序键，且交割月不允许回退。选择器对含当日或以后
  数据的面板抛 `LookaheadError`（负向测试覆盖）；按 t-1 信息选出的合约当日无数据时
  记为 no-trade，不用当日信息替换。909 个交易日中 45 个换月日。
  **来源 `主力连续` 只作 QA 对照**：一致率 898/908 = 98.9%，分歧集中于
  2024-10-09 至 10-18 与 2026-01-16 至 01-19 两个换月过渡窗口（别名是当日口径的
  事后结果，与只用 t-1 信息的规则在换月前后本应不同；未据此调参）。
  **时段表**按 Merge-Plan-2 §8.6 声明为版本化权威参照（INE 交易时间规则），
  并用 909 日全史实测校验：日盘收盘恒为 15:00:00、夜盘收盘恒为 02:30:00、
  夜盘首笔恒为 20:59:00（885 日有夜盘）、日盘首笔为 08:59:00 或 09:00:00，
  全部落在声明窗口内；时段表之外的 tick 集中于 15:13 至 15:21（收盘后结算快照，
  903 日共 18,113 行），已标记且不进入 bar。
  **累计量**逐 tick 差分且不跨交易日；INE 同样存在 Turnover 日内倒退
  （98 个交易日、213 行），原值与负差分一并保留，另出置零派生列，不做修复覆盖。
  **物化**：909 日、64 个合约、3.4417 亿 tick → 8,481,512 根 1min bar 与
  18,180 根日频 bar（`data/`，不入 git）。日频结果与独立参照
  `Alpha-Data/data/intl/curve_daily.parquet` 在 2,500 个可比 (日, 合约) 上
  仅 1 处成交量差 1 手、1 处持仓差 15 手（2026-03-03 sc2604）。
  **目标**：primary `sc_rv_next_session` 与 diagnostic-only `sc_open_gap_absorption`
  各 1,816 行；按样本段为 discovery 1,054 / historical validation 486 /
  contaminated audit 276（`sc_rv_next_session`；`sc_open_gap_absorption` 为
  1,055 / 486 / 275）。其中有取值的行 1,789 与 1,599，其余是 NULL 加原因的
  no-trade 行（RV：no_ticks 24、limit_locked 3；跳空吸收：gap_below_threshold 169、
  no_ticks 24、no_prev_close 24）。`arad spine verify` 从已物化 bar 重建目标后
  指纹 MATCH，8 个数据集（含 909 分区的 1min 与日频 bar）指纹全部 MATCH；
  另从 zip 重建 6 个代表性交易日，逐日 bar 指纹与已物化产物一致。
  **仍未定稿**：经 roll 调整的连续价格序列。Merge-Plan-2 §8.8 要求收益/PnL、carry、
  价格水平分别声明 roll 与 adjustment view；本票只产出换月标记与主力视图，
  adjusted 连续序列留待 M5。

## #5 — 事件语义、映射与 Episode

- **Blocked by**: #3
- **Type**: Research
- **Question**: 如何把 Polymarket 市场和 CLS 新闻映射为可泛化机制，并定义独立 Episode？
- **Answer**: 部分回答。M2 关闭了**时间侧**：Episode 缺省按交易日成组（同一交易日的
  夜盘与日盘共享信息环境），并提供 purge/embargo 与样本段污染标签
  （discovery / historical validation / contaminated audit；forward 只在给出
  freeze_at 与 embargo 时才成立，不写死日期）。**语义侧仍未回答**：必须同时做语义、
  机制和经验三层去重；旧手工 taxonomy（`cn_registry_v3` 的 theme/product 映射）
  只能当种子，不能当真值，需要金标样本和跨模型一致性审计。
  **2026-08-05 人类裁决：`cn_registry_v3.parquet` 已弃用并隔离**，不再作为市场来源、
  市场映射或任何研究输入。替代是从原始 tape 推导的 **PIT Market Index**（M2.5）：
  存在性只由首笔公开成交决定（`eligible_from = block_timestamp + 冻结延迟`），
  流动性资格只由决策时点之前已完整结束的分区日计算且**不参与成员资格判定**，
  门槛由每个 Study 自行冻结，不建立全局优质市场表。实测：1,208,594 个市场、
  2,784,797 个 (市场, 日)、覆盖 2022-11-21 至 2026-07-14。prefix-invariance
  负向测试保证追加未来成交不改变任何历史 cutoff。
  **弃用前的复核记录**（保留作为裁决依据；来源 `Alpha-Data/scripts/select_polymarket_markets.py`）：
  登记表一行是一个 (市场, 品种) 对，836 行对应 492 个市场；主题与方向
  `sigma` 来自事前注册的规则表（slug 子串匹配），**不是**由历史结果拟合；
  `usdc_win`/`n_win` 是窗口内累计名义额与笔数（win 指 window），对窗口内任一决策
  时点均为前视。`admit_ts` 是窗口内累计名义额首次达到 10 万美元的链上时刻，构造上
  点时化，但**成员资格本身是全窗口筛选**（要求全窗口累计额达到同一门槛），在决策
  时点不可知，因此市场选择存在幸存者偏差，`admit_ts` 修不掉。覆盖仅 2026-01-04 至
  2026-07-13，起点是脚本里写死的分析窗口而非 Polymarket 数据限制
  （`daily_aligned` 回溯至 2022-11-21），与 `curve_daily` 的 2026-01-05 同源，
  约束来自前一代系统期货侧的日频数据可得性。M2.5 已用 `daily_aligned` 全史重建了
  点时化的市场身份与资格，该项不再阻塞。

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

## #12 — Polymarket 市场语义映射

- **Blocked by**: #5（时间侧已闭）
- **Type**: Research
- **Question**: 如何从原始市场标题、描述与创建时间构造版本化的地缘/能源/商品语义映射？
- **Answer**: 未回答。约束已定：只用经 PIT 审计的原始元数据与 `markets_clob.parquet`，
  不使用 `cn_registry_v3`；任何可变或无法证明历史时点可见的元数据保持 provisional；
  需要金标样本与跨模型一致性审计。M2.5 已交付市场身份与点时资格，语义分组尚缺，
  因此 PM 侧目前没有可用的机制分族。

## 当前前沿

**当前唯一在办票：#12 Polymarket 市场语义映射。**

已关闭：#3（M1）、#4（M2 SC 窄切片 Temporal Spine）、#5 的时间侧与市场身份侧
（M2.5 PIT Market Index）。

M2.5 交付：855,614,453 笔的 label-blind 普查（1,208,594 个市场 / 2,126,849 个 asset，
市场与资产两级点时化身份），成交按样本段分布 discovery 0.84% / historical validation
11.29% / contaminated audit 87.87%（**样本段划分未修改，2026 仍是 contaminated audit**）；
1,816 个 SC 决策 cutoff 上 7 日窗内有成交的市场数中位 601、最大 66,523、42 个为零。
成交集中度的 Kish 等价数（市场维 113,631、日维 225.3）**不是**统计有效样本量，
真正的 n_eff 需要双向 cluster、HAC 与 block bootstrap，属 #6 评价机范围。

尚未解决的阻塞事项记录在两份 manifest 的 `blockers` 字段：
`sc_temporal_spine.json`（Brent 发布时点核实、adjusted 连续序列、curve 参照仅覆盖
2026 段）与 `pm_market_index.json`（两段 tape 都缺 venue/relay 列致中继腿无法剔除、
两段都不含 negRisk 成交、语义映射另立票）。M1 的 Polymarket 字段合同已改为由实测
schema 生成，`ENGINEERING_PROMPT.md` 与 `Merge-Plan-2.md` §2.1 已完成对应的文档归一化。

#12 关闭后进入 **#6 Study 合同与不可变评估器**（Merge-Plan-2 的 M3）。
