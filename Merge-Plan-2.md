# ARAD 统一实施计划（Merge-Plan-2）

> 日期：2026-08-05  
> 状态：建议作为后续实施的唯一入口，待人类确认  
> 来源：Codex 方案、Fable 方案、`Merge-Plan-1.md`，以及两次独立交叉审阅与本地证据复核。  
> 原始方案保留为设计审计记录；本文件不靠拼接，而是逐项裁决冲突后重建执行顺序。

## 0. 最终裁决摘要

两份方案的最佳合并方式是：

- 采用 Codex 方案的科学承诺、领域语言、三层停止语义、Decision Map、持久调度和 tracer-bullet 推进方式；
- 吸收 Fable 方案的数据审计颗粒度、经典商品基线库、噪声底、可移植资产清单、运行期行为协议和初始研究族；
- 拒绝任何把污染历史段称为最终留出、把 5 个因子变成科学保证、用提示词代替权限隔离、以全量 ETL 阻塞首条纵向验证、或用破坏性 Git 回滚维持循环的设计。

统一后的真实目标是：

> 建成一个持续运行、可恢复、模型无关的另类数据研究服务。它以 Polymarket 与财联社新闻为另类数据研究源、以中国商品期货为目标、以传统量价为正交性对照（财联社同时承担公共信息控制角色），持续产生可审计 Study 判决，维护另类数据 Candidate/Production Factor Inventory，并在因子衰减时复验或替换。

“5 个 Production Factor”保留为库存覆盖目标，不是期限承诺，不是服务停止条件，也不能由经典量价基线凑数。

## 1. 双方互审结论

### 1.1 Fable 方案应吸收的内容

1. 商品 tick 的具体风险清单：郑商所口径与代码、品种级夜盘、集合竞价首行、空壳合约、低流动性与新上市品种。
2. Polymarket 两段 tape、schema 冲突、negRisk 历史缺口、协议迁移、既有 registry 与钱包特征资产。
3. 财联社 Labels 的结构化价值，以及历史 Reads/Comments/Shares 的前视禁用规则。
4. 旧 ADAR/Alpha-Data 可移植资产：MDE、Kish n_eff、HAC/块自助、影响点、blind ledger、机制词表、logit innovation 和质量门。
5. 经典商品因子作为正交性对照集，以及随机/置换负对照构成的实测噪声底。
6. 建设期提示词与运行期 `program.md` 分离；运行期包含启动检查、盲提案、失败计数、上下文节流和继续路径。
7. 初始研究族：闭市信息、新闻标签计数、Polymarket 波动/风险、期限结构交互、知情流探索。

### 1.2 Codex 方案必须保留的内容

1. `Feature → Signal → Factor` 与 `Episode → Study → Research Program → Research Service` 的统一语言。
2. Search Episode 可结束、Study 必须判决、Research Service 只能人工暂停的三层停止语义。
3. 可信 null、underpowered、blocked 和数据缺口也是研究产出；优化目标不是正结果数。
4. 历史数据最多产生 Candidate；Production 必须依赖 Study 冻结之后真正未触碰的新数据。
5. 数据/PIT 合同先行、窄切片 tracer bullet、Decision Map 逐票推进。
6. SQLite 事务、租约、幂等、heartbeat、checkpoint 和 WAITING 状态，不用一句 `NEVER STOP` 代替工程活性。
7. evaluator/holdout 的能力隔离、provider-neutral 领域模型和不可降低的证据门槛。

### 1.3 对 Merge-Plan-1 的评价

`Merge-Plan-1.md` 正确解决了目录整合、基线因子位置、SC tracer bullet、SQLite 与人类可读账本的职责划分，并明确 2026 历史段受污染。它仍需以下修正：

- 运行期事实不能同时以 SQLite、JSONL 和 Git 三套形式成为权威；
- `program.md` 的 SHIP/KILL 等动作与 Study Verdict 混在一起；
- `git reset --hard` 会伤害共享工作树和账本，必须删除；
- 先用 shell while-loop 跑自治 campaign 仍会复制旧系统的停止/恢复缺陷；
- Phase M2 仍过早承担大规模 ETL，第一条端到端证据出现得太晚；
- 经典基线没有与“Polymarket/另类数据因子库存”分账；
- 未处理横截面 product-day 伪样本量和事后红队产生自适应检验的问题。

## 2. 经本地复核的数据事实

所有长期事实最终都必须由 M1 的机器 manifest 固化。当前分成“已复核”和“待复核”，不再用某一份文档覆盖另一份文档。

### 2.1 已复核

| 数据源 | 当前可确认事实 |
|---|---|
| 商品 tick | 66 个 zip；archive 内可识别 909 个交易日期目录，2022-11-01 至 2026-07-30；约 802,975 个 CSV；统一 15 列 tick schema |
| 商品主力别名 | 2026-07-01 抽样的 `ad主力连续` 与其 `InstrumentID=ad2608` 对应合约文件逐字节相同；这是抽样证据，不外推为所有品种全史真值 |
| Polymarket HF | `daily_aligned` 为 1,248 个日分区，2022-11-21 至 2026-04-28，样本日文件约 163 万行；字段包含 `p_event`、`D` 和链上时间 |
| Polymarket 扩展 | `features/extension_tape` 有 78 个日分区，2026-04-28 至 2026-07-14；与 HF 在日期上共享 2026-04-28，必须用稳定主键核验接缝，不能只凭日期声称“无重叠” |
| 市场目录 | `asset_map` 约 351 万行，`markets_clob` 约 177 万行；链上分析层与 HF 层存在类型差异 |
| 财联社 | 2,361 个日 CSV，文件日期连续覆盖 2020-01-01 至 2026-06-18；字段包含 Title、Content、Labels 和互动量；互动量历史不可用 |

**2026-08-05 追加的 verified facts（M2.5 全史普查，见 `artifacts/manifests/pm_market_index.json`）**：

| 事实 | 证据 |
|---|---|
| 两段 tape 列名集合相同、均为 24 列（类型仍有 15 处冲突） | 1,248 + 78 个分区各 1 种 schema 签名；`venue_class`/`is_relay`/`protocol`/`exchange`/`tx_hash`/`log_index` 在两段都不存在，relay 剔除与 unknown venue 隔离在现有数据上不可执行 |
| 两段都不含 negRisk 成交 | 全史 `neg_risk` 为真的 (市场, 日) 数为 0；扩展段未补上 HF 段的 negRisk 缺口 |
| 逐笔在样本段间极度不均衡 | 855,614,453 笔中 discovery 段 0.84%、historical validation 段 11.29%、contaminated audit 段 87.87% |
| 抽样重复腿检出率 3.47% | 24 个分区 1,333 万行中 46.3 万行与另一行完全相同；缺 `tx_hash`/`log_index` 无法区分中继腿与真实重复，名义额类指标一律 provisional |
| asset→(市场, 结果序号) 映射一致 | 抽样 70,747 组与 `polymarket_chain/asset_map.parquet` 零不一致 |

上述事实不改变 §4 的样本段划分；2026 仍是 contaminated audit。

### 2.2 财联社内容完整性：72.5%–88.6% 的抽查结论经复核不成立，99%–100% 维持

本节初稿曾依据"目标日回填条数 ÷ 次日参考快照条数"得到 72.5%–88.6% 的覆盖率，
并据此撤回 Fable 文档的 99%–100% 结论。2026-08-05 的第二次复核证实该抽查
重复了爬虫旧文档"70% 完整性"结论的同一个方法错误：`examples/cls` 的参考快照是
**跨 2 至 3 天的滚动转储**，不能整文件当单日基准。实测名为 07-18 的快照 719 行中
仅 81 行属于 07-18（517 行属于 07-17，79 行属于 07-16）。

把快照行按正文"财联社X月Y日"日期戳重新归日、跨快照取并集后，在同样三个抽查日上：

| 目标日 | 快照并集（归日后） | 历史回填 | 精确交集 | 仅快照有 | 覆盖率（严格/宽松） |
|---|---:|---:|---:|---:|---:|
| 2024-07-17 | 519 | 553 | 514 | 5 | 99.0% / 99.4% |
| 2024-07-18 | 486 | 523 | 485 | 1 | 99.8% / 100.0% |
| 2024-07-23 | 600 | 643 | 595 | 5 | 99.2% / 99.8% |

回填每日还比快照并集多 38 至 48 条。这与全局检验一致：把 `examples/cls`
全部 43.9 万行（去重后 22.7 万条）合并进回填仅新增 2,554 条（1.1%）。
复现脚本：`scripts/verify_cls_coverage.py`。

**保留的限定**：两个来源都只能看到进入过滚动列表（`in_roll=1`）的电报，
上述覆盖率是相对"实时快照可见母体"而非"全部新闻母体"；发布后在下一次轮询前
即被移出的条目两者都会漏掉，但一致性证据表明该比例很低。M1 的系统化内容覆盖
审计照常执行，工作假设采用 99%–100%；财联社用于公共信息控制时仍报告
coverage sensitivity。

### 2.3 待 M1 固化的 provisional facts

- 商品解压规模约 1.37 TB、88 个名义品种、约 78–80 个可用品种；
- 郑商所 Turnover 单位和日内倒退的普遍性；
- 空壳文件比例、各品种真实可用区间、15 个新上市品种清单；
- 所有 `主力连续` 文件与逐合约文件的对应关系；
- Polymarket 两段 tape 的逐笔接缝、relay 清理、unknown venue、negRisk 覆盖率和 4 个 schema 冲突的完整范围；
- CLS Labels 覆盖率、规范化标签数以及相对可靠参考源的内容召回率。

这些内容可以作为 scanner 测试假设，不能作为已冻结业务真值。

## 3. 产品目标、库存与非目标

### 3.1 双库存，而不是一个混合排行榜

ARAD 维护两个不同对象：

1. **Baseline Control Library**：动量、短期反转、期限结构、持仓、成交量、流动性等传统商品因子。用途是数据/评价 sanity check、残差化、正交性和增量价值对照。
2. **Alternative Factor Inventory**：其新增信息必须来自另类数据源（Polymarket 或财联社新闻），或来自另类数据与期货状态的事前声明交互；这是用户目标与“5 个因子”库存目标的计数口径（2026-08-05 经人类确认：新闻族计入主目标，见 `docs/decisions/0002-canonical-plan.md`）。

纯量价因子不能被统计为另类因子。库存内每个因子标注其信息来源标签（`polymarket` / `news` / `mixed`），按源分别记账并报告库存的源构成；正交性要求同时约束跨源重复（新闻因子若只是 Polymarket 因子或量价因子的代理，不得入库，反之亦然）。

### 3.2 库存目标

建议的首个覆盖目标是最多推动 5 个低相关 Alternative Candidate/Production Factor，且至少覆盖两个机制族和两个时域。这个数字：

- 驱动调度优先级；
- 不设承诺日期；
- 不允许降低 PIT、功效、多重检验、稳健性、成本或前向门槛；
- 达到后切换为“维护优先”模式，但 Research Service 继续寻找增量和替代项；
- 数据无法支持时允许长期保持 0–4 个 Production，同时继续产生可信研究信息。

### 3.3 明确非目标

- 不做实盘下单、组合资金分配或交易系统；只提供因子、证据和组合边际统计。
- 不保证某一来源必然产生 alpha，不用经典因子给另类数据目标“保底”。
- 不把既有样本上的分钟级负结果推广成永久不存在；它只降低该方向当前优先级。
- 不用“文献保证存在因子”作为工程或科学承诺。
- 不让无限循环退化为重复检验和烧算力；没有可运行工作时持久等待数据、人工裁决或到期复验。

## 4. 时间、污染与真正前向留出

建议历史段只作开发口径：

| 区间 | 角色 | 可支持的最强结论 |
|---|---|---|
| 2022-11 至 2024-12 | discovery | 原型、参数、机制探索 |
| 2025 | historical validation | 历史时间外验证 |
| 2026-01 至 2026-07 | contaminated audit | 回归、防错、敏感性检查；不能升级 Production |
| Study 冻结后新到数据 | forward confirmation | 唯一 Production 升级依据 |

真正前向起点不是一个全局写死的 `2026-08-01`。每个 Study 的可裁决数据必须满足：

```text
observation_time > max(
    system_protocol_freeze_at,
    study_confirmatory_freeze_at,
    source_snapshot_at
) + embargo
```

若模型、人工或旧报告已经读取某一段结果，该段自动降级为 contaminated。污染沿 Hypothesis Family 继承，不能靠改名字恢复“未触碰”。

## 5. 统一 Study 生命周期与统计协议

### 5.1 两次冻结，解决现有文档自相矛盾

```text
ProposalSpec
  → outcome-blind Feasibility
  → Hypothesis Lock
  → discovery prototype / registered variants
  → Confirmatory Lock
  → historical validation
  → pre-registered adversarial diagnostics
  → Study Verdict
  → forward queue（仅 Candidate）
```

**Hypothesis Lock** 在第一次读取相关目标结果前冻结机制、方向、target、horizon、universe、可证伪条件和数据来源。

**Confirmatory Lock** 在 discovery 完成、validation 开始前冻结最终公式、控制、变换、成本、统计量、诊断、经济边界和检验 family。

看过 outcome 后的任何变体都属于 outcome-exposed discovery family；不能回写为事前设计。

### 5.2 两本分母账

- **Proposal denominator**：全部模型/人工提案，包括被语义、数据和功效预检挡下的想法；用于研究效率、选择偏差和覆盖审计。
- **Statistical denominator**：所有实际读取 outcome 的检验与变体；用于 FWER/FDR。只要看过 outcome 就必须计入，筛掉或没报告也不能回缩。

Outcome-blind、事前固定的 feasibility 可以不进入统计分母，但必须进入 proposal denominator 和 Evidence Ledger。

### 5.3 Study Verdict 与调度动作分离

Evidence Verdict 只能是：

- `candidate`
- `null`
- `underpowered`
- `blocked`
- `error`

调度动作另存为：

- `queue_forward`
- `create_new_version`
- `archive_evidence`
- `wait_for_data`
- `retry_infrastructure`
- `request_human_review`

`SHIP / ITERATE / KILL / ARCHIVE` 不再作为 Verdict。尤其禁止 KILL 删除代码或证据；负结果必须保留。

### 5.4 独立性与横截面推断

不能把“50 个品种 × 900 日”直接当数万独立样本。评价器必须同时报告：

- calendar-date cluster；
- product cluster；
- Independent Episode；
- serial dependence 与 block length；
- cross-sectional effective breadth；
- nominal n、Kish n_eff 和对斜率的 top-k influence。

主要推断单位由 mechanism 与 target 事前确定；Kish n_eff 不能替代双向 cluster、HAC 或 block bootstrap。

### 5.5 红队规则

泄漏、伪重复、极端点、传统因子代理、单一情景、成本等核心诊断必须在 Confirmatory Lock 中预注册。看到 validation 后提出的新检验只能：

- 解释已有证据；或
- 创建新的 Study/version，在新数据上裁决。

不能事后增加三个检验，再继续把同一 validation 结果称为 confirmatory。

## 6. 三层活性与持久状态

| 层级 | 可以结束吗 | 结束/等待后的动作 |
|---|---|---|
| Search Episode | 可以：局部枯竭、预算、模型建议换线 | 保存局部证据，换 seed/mechanism/provider |
| Study | 可以：形成 Verdict | 写事务 ledger，更新队列与重开条件 |
| Research Service | 只能人工 pause/shutdown | checkpoint 后等待或恢复 |

顶层不存在模型可写的 `stop/completed`。当没有可运行 Study 时：

- 等待数据 manifest 变化；
- 等待 forward 预约到期；
- 处理监控/衰减；
- 请求人工补经济边界或语义裁决；
- 以退避策略重新尝试 provider；
- 进入不受当前 blocker 影响的研究桶。

`WAITING_FOR_DATA` 和 `HUMAN_REVIEW_REQUIRED` 是持久、可唤醒状态，不是失败，也不应该 busy loop。

## 7. 权威状态、权限与 Git

### 7.1 单一事实源

采用：

- SQLite WAL：运行期唯一事务事实源，包含 Study、队列、租约、heartbeat、Evidence Event、family denominator 和状态转换；Evidence Event 采用 append-only/hash-chain。
- YAML/JSON：冻结的 Proposal/Hypothesis/Confirmatory/Factor spec，内容寻址，不原地覆盖。
- JSONL/TSV/Markdown：从 SQLite 与 immutable specs 确定性导出的审阅快照，可提交 Git，但不是第二事实源。
- Parquet：大体积派生数据、预测与诊断明细，不入 Git，manifest 记录 URI/hash/schema。

任何跨对象更新在一个 SQLite transaction 中完成；不得先写 JSONL 再更新队列。

### 7.2 真实权限边界

Prompt 与 pre-commit 只作提醒，不是安全边界：

- research worker：读取 PIT features，写候选实现和预测；不能读 final labels/forward data，不能写 evaluator/config/gates。
- evaluator：读取冻结 spec、预测和授权 label；唯一可签发 evidence result。
- proposer：只读 sanitised coverage/power/failure taxonomy；不得读取 β/t/p/IC/Sharpe 或原始结果。
- orchestrator：调度与状态转换；无权篡改 evidence payload。
- human operator：pause/resume、批准经济边界、数据源变更和 Production 升级策略。

### 7.3 禁止破坏性 Git 回滚

删除 `program.md` 中 `git reset --hard` 的运行规则。每个 Study 使用独立 revision、临时 worktree 或内容寻址代码快照；拒绝版本只是不提升为当前实现，绝不回滚共享工作树。Ledger 与失败实现全部可追溯。

## 8. 数据建设原则

1. 来源仓库只读；ARAD 通过 URI + content hash 引用，不删除 sibling 数据、不自动 `git pull`、不改爬虫状态。
2. acquisition 与 research ingestion 分离。ARAD 可以检测新数据和生成更新请求，但修改外部来源需要单独授权/流程。
3. 先 metadata、后窄切片、再按研究需求物化；不先复制或解压全部约 1.37 TB。
4. 原始值永远保留。对累计量 reset、单位差异和异常只产生带 provenance 的派生列，不“修复后覆盖”。
5. `Title`、`Content`、`Labels` 都保留；只把互动量从历史分析视图物理隔离。
6. 合约乘数、时段、上市日和交易日历优先使用版本化权威参照；仅靠数据反推时标为 inferred 并进入 quarantine/review。
7. 来源 `主力连续` 仅作 QA。可交易主力选择只用决策时点已知信息。
8. 连续合约不是一个万能序列：收益/PnL、carry、价格水平分别声明 roll 与 adjustment view。
9. `cn_registry_v3`、tier registry 和 wallet tables 是映射/特征种子，必须重新通过 PIT、语义和 provenance 审计。

## 9. 目标模块

保持模块化单体：

```text
src/arad/
├── data_catalog/      # read-only adapters, manifests, quality gates
├── temporal/          # sessions, as-of, roll views, purge/embargo, Episode
├── registry/          # immutable specs and domain state
├── evaluation/        # protected deterministic kernel
├── orchestrator/      # durable queue, leases, wakeups, checkpoints
├── memory/            # evidence queries, failure archive, dedup
├── inventory/         # baseline controls + alternative candidate/production
├── features/          # feature implementations and materialization
├── proposer/          # blinded proposal construction and diversity policy
├── providers/         # model-neutral adapters
└── cli.py
```

不在真实 profiling 前拆微服务、消息队列或多 Agent 基础设施。角色隔离优先由 capability 和数据视图实现，不由“多开几个模型”假装实现。

## 10. 合并后的 M0–M9 实施路线

### M0 — 合并设计基线（当前阶段）

**交付**：本文件、原方案差异裁决、待修订文档清单。

**出口**：人类确认本文件为 canonical plan；随后一次性修正文档冲突，不让 Agent 在不同权威计划间选择。

### M1 — Source Manifest 与 Availability Contract

对应 Decision Map #3。

**只做**：

- 初始化最小 Python 包、配置与测试；
- 定义 `SourceManifest`、`FieldAvailability`、`CoveragePartition`、`QualityFinding`；
- 三类只读 scanner：commodity zip central directory、Polymarket parquet metadata/row-key sampling、CLS CSV coverage/content sampling；
- 固化 event/publication/availability time、单位、时区、禁用字段和不确定性；
- 生成机器 JSON manifest 与人类审计报告；
- 为时间单位、夜盘归属、CLS 互动量、PM seam/venue、输入哈希写负向测试。

**不做**：全量解压、bar ETL、因子、回测、外部数据刷新。

**出口**：任一字段没有可用时间合同，Study 无法消费；provisional facts 被 manifest 确认或推翻。

### M2 — SC 窄切片 Temporal Spine

对应 Decision Map #4/#5 的第一部分。

**范围**：SC + 最少必要相关合约，少量地缘/能源 Polymarket 市场，匹配时间段 CLS 与国际油价控制。

**工作**：

- 合约解析、品种 session、TradingDay/自然日、集合竞价、累计量 reset；
- 原始合约 panel、t-1 主力视图、roll 标记；
- 最小 1min/日频物化和 as-of join；
- primary target：在决策 cutoff 后的下一 SC session realized volatility；
- diagnostic-only target：同期 open gap absorption，明确不称可交易 alpha；
- Episode ID、purge/embargo 与 contamination tag。

**出口**：随机 30 个时点可人工回放，所有 Feature availability 严格早于 label start。

### M3 — 最小 Research Kernel

对应 Decision Map #6/#7。

**工作**：

- ProposalSpec、Hypothesis Lock、Confirmatory Lock、Study、Evidence Verdict、Factor schemas；
- schema 设计约束（决定 0003）：任意 Study 的账本事件与证据引用必须足以渲染为
  自包含的判决时刻快照（供 M9 Research Atlas 只读投影使用）；
- SQLite append-only/hash-chain ledger 与 durable queue 最小实现；
- proposal/statistical 双分母；
- 最小 evaluator：coverage、Episode、MDE、n_eff、cluster/HAC、影响点、placebo、成本占位和 artifact hashing；
- provider 与 evaluator capability boundary；
- 最小 Baseline Control：SC 自身收益/波动、Brent/USO、CLS 公开新闻强度。

**出口**：一个合成 Study 可完整回放，且可从账本机械地渲染为自包含快照
（渲染器可以是最简单的 Markdown 导出，验证的是 schema 完整性而非界面）；
故意泄漏、单位错误、结果依赖过滤和记录删除全部失败。

### M4 — 第一条端到端 tracer bullet

对应 Decision Map #11。

建立一个 Study Family，但每个 Study 只绑定一个 endpoint/horizon：

- 主 Study：闭市期间残差化地缘概率创新 → 下一 SC session realized volatility；
- 同 family 诊断 Study：概率创新 → 同期 open gap absorption，只验证信息到达，不用于 Production；
- 控制：SC 自身信息、国际油价/风险状态、CLS 已公开新闻；
- 完整执行 feasibility、两次冻结、discovery、validation、预注册红队、Verdict 和 ledger 回放。

**出口**：`candidate / null / underpowered / blocked` 任一都算平台成功；不预设强结果。所有新发现的平台缺陷变成回归测试。

### M5 — 数据扩展与 Evaluation Hardening

在 M4 证明协议后再扩展：

- 从 SC 扩到能源、贵金属，再到约 5 个代表品种，最后按研究需求扩全域；
- 需求驱动的 bar/materialization，支持断点、hash 和 reference equivalence；
- Polymarket tape seam、venue、relay、negRisk 与 asset mapping 完整审计；
- CLS coverage sensitivity、标签规范化与标签—品种映射金标；
- Baseline Control Library：动量、反转、期限结构、持仓、成交量、流动性；
- 完整 evaluator：block bootstrap、双向 cluster、视界衰减、噪声底、四层正交性、腿分解、容量与更精确成本。

**出口**：代表品种端到端重复通过；大规模 ETL 只物化已登记需求，性能和 reference 结果一致。

### M6 — Persistent Orchestrator 与受限模型角色

`program.md` 作为行为规范，但不把 shell while-loop 当生产调度器。

**工作**：

- Research Director、Hypothesis Generator、Semantic Auditor、Red Team、Interpreter 的受限视图；
- SQLite queue、lease、heartbeat、attempt、idempotency、checkpoint、wake condition；
- Episode restart、provider retry/backoff、WAITING_FOR_DATA、HUMAN_REVIEW_REQUIRED；
- 搜索空间扩展写入同一事务队列并立即可调度；
- blind ledger 对 effect fields 做结构化 deny-list/allow-list 测试；
- 独立 code revision，不使用 destructive reset。

**出口**：

1. 第一次模型响应 stop，服务仍继续或进入持久等待；
2. 空计划、坏 JSON、provider 超时不丢任务；
3. 扩展出的提案在本次 Program 生效；
4. kill -9 后幂等恢复；
5. 无工作时不 busy loop；
6. 故意越权读 forward/写 evaluator 被能力边界拒绝。

随后进行 24 小时 soak test；它是最终验收，不是替代前述确定性测试。

### M7 — 多机制研究 Program 与 Candidate Queue

初始 Program：

1. 数值阶梯/隐含分布变化 → 直接报价品种；
2. 闭市概率创新的延续、反转与状态依赖；
3. 临近期限 hazard → 次期波动/尾部；
4. Polymarket 分歧/概率不确定性 → 商品风险状态；
5. Polymarket × CLS 公共信息残差；
6. Polymarket × 期限结构/库存状态交互；
7. 钱包/知情流，仅作探索，先验证稳定性与 PIT。

每个 Program 设机制覆盖预算、proposal denominator、统计 family、功效预算和重复检测。Baseline Control 不计入 Alternative Inventory。

**出口**：每个主攻族得到 candidate/null/underpowered/blocked 的可信覆盖；Candidate queue、Failure Archive 和自动战役报告可生成。没有 Candidate 仍可完成 M7，因为科学判决不能被产品目标篡改。

### M8 — Forward Judge、Production 与维护替换

**工作**：

- 每个 Candidate 根据自身 freeze time、source snapshot 和 embargo 预约真正 forward 数据；
- 独立 evaluator 一次性裁决，研究 worker 看不到 forward labels；
- 通过后进入 Alternative Production Inventory，并评估组合边际、成本、容量与风险暴露；
- 监控数据、机制、预测、交易、正交性五类衰减；
- `PRODUCTION → MONITORING → DEGRADED → RECALIBRATED | RETIRED`；
- 退役保留全史并创建 Replacement Need；
- 库存达到 5 个符合覆盖约束的 Production 时切换为维护优先，但服务不停止。

**出口**：Production 的每个成员都有真正前向证据；退化、退役、替代和数据到期唤醒均可演练。

### M9 — Research Atlas（可视化交付层，决定 0003）

M6 之后可开始，与 M7/M8 并行推进（依赖 M3 定稿的账本 schema 与 M6 的运行状态机）。

**产品形态**（三层，详见 `docs/decisions/0003-research-atlas.md`）：

- 总览层：Service 状态、库存覆盖热力图（机制族 × 源 × 时域）、吞吐与 verdict 分布、
  三源数据新鲜度；
- 过程层：Study 时间线/DAG（verdict 着色）、假设族谱系（承继、重开、家族分母）、
  Episode 展开收束；
- 快照层：任一 Study 点开为判决时刻的自包含证据快照（锁定假设、功效预检、
  Confirmatory 规格、五关逐项、正交性与腿分解、红队诊断、图表、verdict、
  artifact 哈希、当时可见数据范围）。快照展示当时的结论，不用后见数据回填。

**边界（不可妥协）**：只读投影，不构成第二事实源；forward 数据与标签不可见
（仅显示预约状态）；一切数字来自评价机结构化输出，前端不重算统计量。

**工作**：

- `atlas/` 投影层：读 SQLite 账本与 parquet 证据的查询接口（复用 M3 的渲染合同）；
- 轻量实现（票内定稿）：本地小型后端加静态前端，或按里程碑生成静态站点；
  不引入重框架，遵守模块化单体约束；
- 图表遵循评价机口径（衰减曲线、分位单调性、覆盖热力图），标注样本段与污染标签。

**出口**：全部历史 Study 可在 Atlas 中打开且快照证据完整（拼不出完整快照即账本
缺口，按 bug 处理并回补回归测试）；Atlas 对 forward 数据的不可见性有负向测试；
一次完整战役可以只通过 Atlas 讲清楚"机器做了什么、为什么这样判决"。

## 11. 依赖关系

```text
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8
             │           │     │
             │           │     ├─ M5 后可继续按需扩数据
             │           │     └─ M9 Research Atlas（M6 后开始，与 M7/M8 并行）
             │           └─ 第一条真实 Study 早于全量 ETL
             └─ schema 只在真实 PIT/target 事实后定稿（含 M9 的快照渲染合同）
```

不允许跳过 M4 直接跑大规模自动战役。M1–M4 是第一个发布目标；此前不做 Web UI、分布式系统、多 Agent 基础设施或实盘执行。

## 12. 每个里程碑的统一 Definition of Done

- 有一个先失败、后通过的 contract/regression test；
- 至少一个测试对应旧 ADAR/Alpha-Data 的真实失败模式；
- 数据、代码、配置、模型和产物有 hash/provenance；
- 运行结果来自 evaluator 结构化输出，不手抄关键数字；
- 相关 unit、leakage、statistics、integration tests 和静态检查通过；
- 性能优化有 reference implementation 等价测试；
- 来源仓库保持只读；不提交大数据、密钥、缓存或临时日志；
- Decision Map 的当前 ticket 被更新，不顺手实现被阻塞的后续票；
- 未确认数据事实明确标为 provisional/quarantined，不静默猜测。

## 13. program.md 必须修订后才能启用

当前 `program.md` 是优秀的运行协议草案，但不是可直接运行的最终程序。M6 前至少修订：

1. 用 Evidence Verdict + Next Action 替换 SHIP/ITERATE/KILL/ARCHIVE 混合状态；
2. 删除所有 `git reset --hard`，改为独立 revision/worktree；
3. 把“Hypothesis Lock 后又做冻结前预检”改为两次冻结生命周期；
4. 把 validation 后新增红队检验改为预注册诊断或新 Study；
5. 把固定全局 holdout/forward 日期改为 per-Study forward eligibility；
6. 把 Git JSONL 文件改为 SQLite 事务事实源的确定性导出；
7. 把 `NEVER STOP` 解释为“不自行终止服务”，允许持久 WAITING/HUMAN_REVIEW，而非 busy loop；
8. 明确 Baseline Control 不计入 Polymarket/Alternative Inventory；
9. 用能力隔离替代“不得修改”提示词和 pre-commit 安全假设；
10. 禁止提案器通过失败摘要间接读取效果方向，只给 sanitised failure taxonomy 与功效信息。

## 14. 需要同步修正的源文档

确认本计划后执行一次文档归一化：

- `docs/00-material-analysis.md`：CLS 99%–100% 完整性经二次复核维持（见 §2.2），补充 `in_roll=1` 母体限定；把 909 日、80 万文件等分为 verified/provisional；弱化“保证存在因子”类表述。
- `docs/01-goal.md`：把 5 个 Production 改为库存目标；明确 Baseline 与 Alternative 分账；Production 只凭 per-Study forward。
- `docs/02-plan.md`：改为窄切片优先；保留 Title；不删除/修改 sibling 数据；修正 holdout、状态存储和完整性口径。
- `docs/FOUNDATION_ANALYSIS.md` 与 `docs/ENGINEERING_PROMPT.md`：恢复财联社内容缺失风险；引用 M1 manifest，而不是让某份手工分析永久覆盖其他文档。
- `program.md`：按第 13 节修订。
- `README.md`：把本文件设为唯一实施入口；其他计划标为来源/历史。
- `docs/decisions/0001-two-docsets-merge.md`：状态改为被本裁决取代，保留历史。

在归一化完成前，发生冲突时以本文件为准；数据事实仍以 M1 生成的 manifest 为最终权威。

## 15. 下一步

人类确认本计划后：

1. 先执行第 14 节文档归一化；
2. 更新 Decision Map，将 #3 标记为唯一当前前沿；
3. 用 `docs/ENGINEERING_PROMPT.md` 启动 M1；
4. M1 只做只读 scanner、Availability Contract 和数据质量测试，不开始因子回测。

这使两份方案真正合并为一条路线：Fable 的深数据/统计规格进入每张工程票，Codex 的科学边界、依赖顺序和持久活性负责防止系统再次在错误方向上“聪明地停止”。
