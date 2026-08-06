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
- **Answer**: 部分回答（2026-08-05，M3 第一块）。**不可变规格与 Evidence Ledger 已交付**，
  工程票 `docs/tickets/M3-research-kernel.md`。
  规格：`ProposalSpec` / `HypothesisLock` / `ConfirmatoryLock` / `StudySpec` /
  `StudyVerdict`，全部内容寻址（改内容即新 id，原地改冻结规格在数据结构层不可能）；
  `Verdict` 只有五个值，调度动作以 `NextAction` 另存，`SHIP/KILL` 不在词表内；
  Confirmatory Lock 强制要求预注册对抗诊断，事后补检验无法通过构造。
  账本：SQLite WAL 追加式哈希链。**三条边界由数据库或查询层强制**：events 表的
  UPDATE/DELETE 触发器直接 ABORT；每个事件链接前一事件哈希，篡改可定位到具体 seq；
  proposer 角色读不到 β/t/p/IC/Sharpe（含嵌套结构），且不能全量拉取账本。
  两本分母：proposal denominator 计入被预检挡下的提案（且必须给理由），
  statistical denominator 只增不减（DELETE 与 UPDATE 均被触发器拒绝）。
  快照渲染合同（决定 0003）：一个合成 Study 可从账本回放为自包含快照；
  缺任一必需段落即报 `SnapshotIncomplete`，按账本缺口处理。26 项合同测试。
  **第二块（最小 evaluator）已交付**：受保护的确定性评价机，唯一读取标签、唯一签发
  evidence result。M3 出口要求的四类操作全部失败：故意泄漏（feature 可用时点不早于
  决策时点，或决策不早于 label 起点）、单位错误（控制变量全样本恒定 —— 旧系统真实
  故障形态）、结果依赖过滤（提交行集合是权威集合真子集且无预注册排除规则）、
  记录删除（第一块）。结构化输出同时给出 nominal n、Episode/日期/品种三维 cluster、
  Kish n_eff、双向 cluster 与 Newey-West HAC、残差自相关与建议块长、DFBETA 影响点、
  按 Episode 整块置换的 placebo、成本占位；请求与结果均内容寻址。
  **实测发现并修复的两个自身缺陷**：(1) 某个 cluster 维只有一组时双向 cluster 方差
  恒为零（OLS 一阶条件），原实现吐 NaN，现降级为单向并显式声明；(2) 相邻 session
  配对把夜盘/日盘水平差误读成波动反转，改为同类型配对。
  **最小 Baseline Control 已跑通**：`arad study baseline` 在 SC discovery 段
  976 个观测、499 个 Episode（2022-11-02 至 2024-12-31）上给出对数已实现波动的
  一阶持续性 slope 0.846、双向 cluster SE 0.0167、置换检验通过、最小提前量 64,740 秒；
  Verdict 为 blocked，理由是单品种样本识别不出横截面相关结构。该结果标注
  `inventory: baseline_control`，**不计入 Alternative Factor Inventory**。
  **第三块（durable queue）已交付**：SQLite 持久任务队列，四条边界由代码或数据库强制 ——
  租约带过期时刻（进程被 kill 后到期即可重新认领，任务不丢也不会被两个 worker 同时持有）；
  副作用带幂等键且 append-only（重复完成只留第一次结果）；空计划、坏 JSON、
  provider 超时统一走 `fail()`，attempt 加一并按退避重排，达到上限转
  `HUMAN_REVIEW_REQUIRED` 而不是失败终态；`next_wakeup()` 给出下次唤醒时刻，
  无可运行任务时休眠而非 busy loop，且 `claim()` 返回 None 而**不返回"研究完成"**。
  顶层 `ServiceState` 只有 running/paused/shutdown，**没有 completed**，
  且只接受 human 角色改写 —— 模型的 stop 只能结束 Search Episode。
  检查点跨重新认领与跨进程重启存活。26 项合同测试预先固定了 M6 的活性出口条件。
  **仍未交付**：多元回归（本版一元，controls 只做完整性检查，残差化由 worker 负责）、
  block bootstrap、真实成本与容量模型、把 queue 接进实际研究循环。

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
- **Answer**: 部分回答（2026-08-05，M3 第三块）。durable queue 已交付：
  `arad.orchestrator.queue.DurableQueue`，含租约与过期重认领、心跳、检查点、
  幂等副作用（append-only）、退避重排、`WAITING_FOR_DATA` 与
  `HUMAN_REVIEW_REQUIRED` 两个可唤醒等待状态、`next_wakeup()` 避免 busy loop。
  顶层状态没有 completed，且只接受 human 改写。26 项合同测试覆盖
  kill -9 恢复、空计划/坏 JSON/provider 超时不丢任务、跨进程重启存活。
  **仍未回答**：把 queue 接进实际研究循环（Episode restart、provider retry/backoff
  的真实调用、搜索空间扩展写入同一事务队列并立即可调度）属 M6；
  24 小时 soak test 是 M6 的最终验收。

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
- **Answer**: 取证阶段已完成（2026-08-05），语义部分未回答。工程票见
  `docs/tickets/M12-pm-semantic-mapping.md`，产物见 `artifacts/manifests/pm_metadata_audit.json`
  （`arad pm-index metadata-audit`，因文本不可证而以非零码退出）。
  **三条实测结论约束后续设计**：(1) `category`/`category_refined` 在扩展段填充率为 0
  （HF 段 100%），而扩展段占全史成交 87.9%，交易所类别在最密集区段不可用；
  (2) `market_slug` 跨抓取会变化（3,258 个可比市场中 78 个不同，形态是末尾追加
  消歧数字段），去掉末尾 `(-<数字>)+` 后差异归零，因此映射必须以 `condition_id` 为键、
  以归一化基名为文本特征；(3) `outcome_label` 跨抓取稳定但是 **asset 级**字段，
  按市场级归并会产生假漂移。
  历史时点可证明可见的文本仅：`condition_id`、归一化 slug 基名、按 asset 的
  `outcome_label`。`markets_clob.parquet` 的 `question`/`tags`/`end_date_iso`
  均无可证明的历史可见性。不使用 `cn_registry_v3`；需要金标样本与跨模型一致性审计。
  **机制族口径已裁决（2026-08-05）**：从数据自下而上重新归纳，不沿用旧系统的 8 个主题。
  **第一层（模板）**：slug 归一化后把数字/年份/月份替换为占位符。实测 542,058 个模板中
  90.6% 是单例，头部完全由机器生成的加密涨跌梯队占据（btc/eth/sol/xrp/doge/bnb/hype
  合计 412,683 个市场，34%）；期外覆盖率曲线为 2024 切点 0.0%、2025 切点 0.9%、
  2026 切点 26.7%。结论：模板层不能直接当机制族。
  **第二层（实体共现）**：归纳单元下沉到 token，用 PMI 建边（PMI 天然压低与什么都
  共现的功能词，因此不写停用词表）。实测单靠 PMI 阈值会**渗流**：阈值提到 5.0 仍有
  95% 的 token 挤在一个巨型分量。改为**互为 top-k 近邻**建边后切断枢纽链，
  在 2026-01-01 切点、1,500 个 token 上得到 81 个候选族，可辨识的族自下而上浮现
  （NHL 队名族、MLB 族、UFC 族、earnings 族、`before russia ukraine capture trade deal`、
  `israel strike gaza lebanon invade`），全程未写任何分类法。
  **81 个候选族已全部登记为提案**并计入 proposal denominator（`arad pm-index families`，
  账本 162 个事件、链完整）；族只有 id、成员 token 与规模，**没有名字、不绑定 target**。
  **两项可逆假设（人类未逐条裁决，已明确记录）**：市场→商品映射**不属本票** ——
  族→品种是经济假设，应在各 Study 的 Hypothesis Lock 冻结，不固化进映射表；
  金标样本的规模与标注人待人工安排，本票先建机制。
  **仍未交付**：机制族命名、金标样本、跨模型一致性审计；最大的族仍有 648 个 token
  且 `oil`/`gold` 陷在其中，需要更细的切分。

## M3 Research Kernel（已交付，三块）

- **账本**：SQLite WAL 上的追加式哈希链。UPDATE/DELETE 触发器直接 ABORT，
  proposer 角色的查询路径递归遮蔽效果字段，两本分母分表存放且统计分母只增不减。
  任意 Study 可折叠为自包含判决快照，拼不出即按 bug 处理；
- **评价机**：唯一读取标签的组件。三类操作必须失败而非告警 —— 前视、控制变量恒定
  （旧系统真实故障形态：微秒时间戳按纳秒解析致新闻控制恒为零）、结果依赖过滤。
  推断用双向 cluster SE 与 Newey-West，另出 Kish n_eff、DFBETA 影响与置换安慰剂。
  **本版回归是一元的，controls 只做完整性检查不进回归**，残差化是 worker 的职责；
- **durable queue**：租约、过期回收、心跳、检查点、幂等完成、退避重试到
  HUMAN_REVIEW_REQUIRED。ServiceState 只有 running / paused / shutdown，
  **没有 completed**，且只有 `role="human"` 能改。

## M4 Research Harness（已交付，五块）—— 环已转起来

定位纠正：此前建的是确定性的一半，执行者 LLM 面向的一半一行都没有。M4 补上后者。

- **特征规格语言**：PIT 安全是结构性的。所有窗口结束于决策时点之前，`offset_seconds`
  只能非负，因此"写出一个前视特征"在这门语言里**无法表达**，而不是写出来被拦下。
  原语不足以表达某机制时产出 `UnsupportedMechanism` —— 缺口是证据，不是失败；
- **provider 适配层**：`ProviderRequest` 刻意没有会话 id、没有历史消息，
  角色隔离因此是结构性的；盲化在**每次**发送前扫描 prompt（含修复重试）；
  坏 JSON 重试用尽后降级为 `ParseFailure`，任务退避重排不丢。`claude -p` 适配器
  与 MockProvider 并存，后者使闭环可在零调用成本下端到端测试；
- **上下文组装器**：先组装结构化 facts 再渲染 prompt，facts 内容寻址且入账，
  "模型当时看到了什么"是可回放的证据。菜单偏差（#12 实测的 83.7% 后见暴露与
  10.4 个百分点的结果邻接）**必须写进 prompt**，藏起来会原样传导成提案偏差；
- **反馈格式化器**：评价结果不能原样回灌 —— `blocked_reasons` 带着数字。
  只回传白名单分类与白名单覆盖字段，建议文本不得含数字，有断言强制；
- **Episode 循环**：认领任务 → 组装盲化上下文 → 调用 → 解析 → 计入分母 →
  冻结两把锁 → 求特征 → 评价 → 判决入账 → 反馈。预算耗尽结束 Episode 并交回
  剩余预算，**Research Service 不停**。

**分母边界已精确化**：被预检挡下的提案与原语缺口声明都计入 proposal denominator；
解析失败没有任何提案内容可供内容寻址，作为中止轮次单独入账，不计入分母 ——
把它算进去等于虚构一个从未被提出的假设。

**实跑结果（`arad episode demo`，真实 SC discovery 段 1,040 个决策点）**：
四轮四种结局，evaluated / primitive_gap / interpretation_gap / parse_failure 各一。
唯一走完评价的是量价对照集（Baseline Control，**不计入 Alternative Factor Inventory**），
斜率 0.4116、t 5.64（**序列未按 roll 切分**，演示用，不作为实证结论），仍判 **blocked**，
因为未声明成本模型且单品种样本使双向 cluster 退化。另类数据侧的提案判 blocked：解释器尚未接入 `pm_market`。这与 M4 票的预期一致
（第一版应当全是 underpowered 与 blocked），暴露的正是真实边界。

## M9 Research Atlas（已交付，最小版本）

技术选型定稿：**静态生成，不做服务端**。不引入新依赖，且只读边界从承诺变成物理事实
（HTML 文件写不了账本），也不必解释"Atlas 停了是不是研究停了"。
入口 `arad atlas render`，产物 `artifacts/atlas/index.html` 与 `atlas.json`。

三个映射陷阱已处理：没有 study_id 的事件（原语缺口、Episode 起讫）进 Episode 层
不被丢弃；有 study_id 但无 `study_created` 的轮次是中止轮次而非账本缺口；
以 human 角色读账本，否则快照层会被 proposer 遮蔽规则清空。
真实 Study 拼不出完整快照时抛 `SnapshotIncomplete`，按决定 0003 视为账本缺口。

Atlas 每次渲染都重算整条哈希链，因此同时是账本完整性的持续检验。

**真实 `claude -p` 已跑通（2026-08-05，两轮，Opus 5）**：这是本系统区别于
harness 模拟器的唯一证据 —— 盲化检查、`extra="forbid"` 的 schema、PIT 原语约束，
都只有真实产出能检验。三项实测结论：

1. **两轮都需要一次修复重试**（首轮输出不合规，按修复提示重试后通过）。已新增
   `provider_repair` 事件入账：模型第一次没产出合规 JSON 是关于**这份提示词**的
   研究信息，不记下来就无法知道 schema 说明是否够清楚。修复前提示词根本没有告诉
   模型 `Step` 与 `FeatureSpec` 的确切字段名，而两者都是 `extra="forbid"`，
   把合同藏起来再指责对方违约是不讲理的，已补入 `primitive_catalogue()`；
2. **两轮提案都用了 `zscore`**。真实模型想要的是相对自身历史的标准化，
   而解释器没有实现它 —— 这是数据给出的下一个原语优先级，不是猜的；
3. 第一轮的提案是 vol-of-vol 离散度，第二轮是波动创新的 z 标准化，
   都自己声明了不依赖候选族菜单以规避 83.7% 后见暴露。菜单偏差写进提示词
   确实改变了提案行为。

**由真实运行暴露并修复的 P1 缺陷：解释器把 `zscore` 与 `residualise` 实现成恒等映射。**
后果是评价机为一个**并非规格声明的数**出具结果，而结果照样记成该规格的证据 ——
这正是评价机被建出来要拦的单位错误形态，只不过发生在解释器内部，没有任何检查能看见
（第一轮真实运行就已经被这样评过一次，斜率 -2.10、t -2.66，那个数不属于它的规格）。
已改为抛 `StepNotImplemented` 并判 blocked：宁可拒绝求值，不可伪造证据。
同时 `FeatureSpec.describe()` 改为无损 —— 账本里存的就是它，规格若不能从证据里重建，
快照就不是自包含的；原实现省略了 `source`/`field`/`inputs`，快照里的 ratio 步骤
看不出它引用了哪两步。

**M9 工作中发现并修复的能力边界缺陷（P1）**：`EFFECT_FIELDS` 原名单只有教科书叫法，
漏了评价机实际输出的 `slope` 与 `intercept` —— 一元回归斜率就是效应量，换个名字
不改变这一点。已补入名单，并另加前缀规则（`se_`、`mde_` 等标准误与最小可检测效应
同样泄漏量级）与容器规则（整个 `effects` 子对象一律遮蔽），因为逐字段挡只能挡住
已经想到的名字。

## M4.1 zscore 原语（已交付）

优先级由数据给出：接通真实 `claude -p` 后两轮提案都用 `zscore`。核心设计问题是
参考分布从哪里来，**采样网格由规格自己定义**（`sample_every_seconds` 与
`min_samples` 进 Step，因而进 content id），而不是由调用方请求了哪些决策时点决定 ——
后者会让同一个 content id 在不同调用方处得到不同的数。

三个连带修正：门槛计**互异取值**（实测可出现 37 个有定义样本只对应 2 个互异取值，
标准差被压低而放大 |z|）；**覆盖准入**使"可求值蕴含值唯一"（代价是演示最早 153 个
决策点变为无定义，那正是被修正的缺陷）；`required_lookback_seconds` 沿 DAG 累加，
原实现逐步取 max 会在账本里写下一个偏小的假数。

语言层新增三条拒绝：派生步骤不接受 `offset_seconds`（此前静默忽略，让它生效会使同一
content id 换一个数）、从 `output_step` 不可达的步骤一律拒绝（惰性求值够不到它们，
而 `describe()` 仍会声称本特征用了它们的数据源）、禁止 zscore 嵌套。

`FEATURE_SPEC_VERSION` 升 0.2.0，新增 `INTERPRETER_VERSION` 进入证据摘要。详见
`docs/tickets/M4.1-zscore-primitive.md`。

**实测**：真实 Opus 5 首次输出即合规（schema 说明修复有效，无 `provider_repair`），
产出 10 日/30 日均值之比再作 126 天 z 标准化，830/1040 点有定义，走完评价判 blocked，
只剩两条已知结构性阻塞。另一侧，未标准化的波动创新此前 t 值 5.64 且通过置换检验，
**标准化之后置换检验不再通过**（36.5% 的置换斜率不小于实际值）—— 原先的强度有一部分
来自水平与趋势结构。两者都是 Baseline Control，不计入 Alternative Factor Inventory。

## 当前前沿

**#6（M3）、M4、M9 已交付。下一步是 M5：成本与容量模型 + 多元回归。**
在成本模型建成之前，任何 Study 都不可能取 candidate，这是评价机的硬闸门。

票 #12 的取证与自下而上归纳已完成并阻塞在账本上：机制族命名需要把整批实体提案
计入 proposal denominator，而记账能力已由 M3 提供。#12 的剩余部分
（机制族命名、金标、跨模型一致性）可以恢复。

已关闭：#3（M1）、#4（M2 SC 窄切片 Temporal Spine）、**M2.5（PIT Market Index，
2026-08-05 三轮评审后关闭）**。#5 的时间侧随 M2 关闭，市场身份侧随 M2.5 关闭。

M2.5 验收轮次：第二轮评审提出 Standards 5 项、Spec 3 项，已全部修复
（整文件内容哈希、整包代码哈希、产物完整性与独立重建确定性分开报告、
asset_day 孤儿与缺失检查、周期心跳、市场级最大无成交间隔按 condition 序列计算、
markets_clob 移出 inputs 改记 deferred、真正 n_eff 移交 #6）。

M2.5 交付：855,614,453 笔的 label-blind 普查（1,208,594 个市场 / 2,126,849 个 asset，
市场与资产两级点时化身份），成交按样本段分布 discovery 0.84% / historical validation
11.29% / contaminated audit 87.87%（**样本段划分未修改，2026 仍是 contaminated audit**）；
1,816 个 SC 决策 cutoff 上 7 日窗内有成交的市场数中位 601、最大 66,523、42 个为零。
成交集中度的 Kish 等价数（市场维 113,631、日维 225.3）**不是**统计有效样本量，
产物中以 `is_effective_sample_size: false` 显式标注，不得用于功效计算；
真正的 n_eff 必须绑定 Feature、target、Episode 与相关结构（双向 cluster、HAC、
block bootstrap），已按裁决移交 **#6 评价机**，工程票同步修订。

尚未解决的阻塞事项记录在两份 manifest 的 `blockers` 字段：
`sc_temporal_spine.json`（Brent 发布时点核实、adjusted 连续序列、curve 参照仅覆盖
2026 段）与 `pm_market_index.json`（两段 tape 都缺 venue/relay 列致中继腿无法剔除、
两段都不含 negRisk 成交、语义映射另立票）。M1 的 Polymarket 字段合同已改为由实测
schema 生成，`ENGINEERING_PROMPT.md` 与 `Merge-Plan-2.md` §2.1 已完成对应的文档归一化。

M2.5 关闭 → #12 语义映射 → #6（M3 Research Kernel）→ M4 Research Harness →
M9 Research Atlas 最小版本，环已转起来且可视。

M4/M9 遗留的阻塞事项（记录不修，属后续票）：

1. **解释器只接入 `commodity_bar`**，`pm_market` 与 `cls_telegraph` 未接入，
   因此另类因子的实证路径尚未打通，当前一切另类提案只能判 blocked（M5/M6）；
2. **无成本与容量模型**，评价机的硬闸门使任何 Study 都不可能取 candidate（M5）；
3. **回归仍是一元的**，多元回归与 block bootstrap 待建（M5）；
   `residualise` 亦因此仍抛 `StepNotImplemented`：解释器不持有控制序列；
4. **LLM 产出的代码没有沙箱**，当前只执行结构化规格，代码路径未开（M4 后续块）；
5. 决定 0004 的两项验证测试（2024→2025 双重差分、forward 拆分试验）未补；
6. 机制族命名、金标样本规模与标注人、跨模型一致性审计仍待人工安排（#12）。
