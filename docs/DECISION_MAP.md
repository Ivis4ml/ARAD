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

## M9.1 演化视图（React 应用，已交付）

人类要求把 Atlas 做成 React 应用，主视图是关键指标在迭代中的走势曲线。
**这个需求自带一个会骗人的形状**：旧系统 `ADAR/artifacts/hillclimb` 的实测里，
81 次爬山选出的最好 Sharpe 是 2.40，而同一套搜索在零假设下的期望是 2.63（该文件
自己记录的 `sr_null_ann`）—— 曲线在涨，实际比噪声还差。因此本票的核心是**第三条线**：
同样次数的搜索在纯噪声上能达到的水平（`evaluation/selection.py`）。实现以旧系统
独立算出的 `sr_null = 0.16595662` 做跨实现核对，误差 1e-4 以内；单侧用于 Sharpe，
双侧用于 |t|，用错一侧会把零假设抬高约 10%。带随**已读 outcome 的次数**上升，
被挡下的轮次留在图上但不抬高它。

指标口径：新增 IC（Spearman/Pearson），**明确标注为时序 IC 而非截面 IC** ——
本样本单品种，`product_clusters` 为 1，叫它 IC 而不注明会被按截面 IC 的直觉误读。
Sharpe 的机制照实现（含偏度、峰度、`deflated_sharpe`），但**当前两个 target 的 label
都不是收益**（已实现波动、吸收比例），因此 `label_is_return` 默认为假，Sharpe 返回
未定义加理由。真 Sharpe 需要一个收益型 target，另立一票。

谱系：`StudySpec` 新增 `parent_study_id` 与 `change_summary`，`run_episode` 新增
`schedule_next` 回调 —— 此前 `NextAction.CREATE_NEW_VERSION` 写进账本却没有任何东西
会执行它。默认按谱系展开，可切时间轴；时间轴下不画零假设带并说明原因。

技术：Vite + React + TS 构建成单文件 HTML 随包分发，Python 注入投影 JSON。
渲染不需要 node，页面零网络请求。详见 `docs/tickets/M9.1-evolution-app.md`。

**实测**：`--provider lineage` 一条五版链，|t| 3.06 → 5.03，IC 0.059 → 0.161，
零假设带 0.80 → 1.58。曲线始终在带之上，但这是 Baseline Control 且判决全为 blocked，
不构成任何可交易主张。

## M2.1 收益型 target（已交付）

Atlas 能画 Sharpe，但两个已有 target 的 label 都不是有符号收益，Sharpe 一直是未定义。
新增 `sc_ret_next_session`：决策在开盘前 60 秒，**入场在开盘后 1 分钟**取该分钟最后
一笔（决策到成交需要时间，取最后一笔是保守的一侧），出场在收盘，label = 对数收益。
集合竞价成交价不参与，**开盘跳空不在本目标的主张之内** —— 这是遵守 M2 已记录的
「开盘价对决策时点不可执行」。全史 1,816 行 → 有取值 1,782，无定义 34
（no_ticks 24 + 入场触板 6 + 出场触板 4）。

**顺带修掉 M2 的一个 P1**：`is_limit_locked()` 用精确浮点相等比对交易所限价。实测
sc2604 在 20260303 日盘整段 225 根 bar 收于 572.3，而限价字段是 572.3000000000002，
差 2.7e-13，判据返回 False，于是一个一手都买不到的 session 被物化成
`value=0.0, no_trade=False`，直接违反 `targets.py` 自己的假设 5。改为按半个 tick
容差逐价判断；RV 表有取值行数 1,789 → 1,788，`limit_locked` 3 → 4。

三条连带修正：`sc_rv_next_session.tradable_claim` 由 True 改为 **False**（本数据集
没有 SC 的波动率工具，已实现波动不是可捕获的收益，原值属记录错误）；`label_rule`
改为映射派发（原 if/else 的 else 落在 RV 上，漏加分支会静默以新名字发出旧口径）；
评价机新增 `LabelIsNotAReturn`，对非收益 label 声明 `label_is_return=True` 直接拒绝 ——
没有这道检查，`tradable_claim` 只是装饰。

年化系数：SC 实测每年约 485 个 session，沿用 252 会把年化 Sharpe 低估约三成。
评价机从实际决策时点导出并与声明值并列输出，不一致不阻断。

Sharpe 的零假设带用 `expected_max_sharpe`（**单侧**）加本链自身的 Sharpe 离散度，
并给出紧缩 Sharpe。详见 `docs/tickets/M2.1-return-target.md`。

**实测中最要紧的一条**：换成收益型 label 之后，演化曲线**是往下走的** ——
|t| 由 5.03 降到 0.83，IC 由 +0.161 变成 −0.014，五版 Sharpe 全为负且全在零假设带
之下（DSR 最高 0.28）。波动特征能预测波动的**幅度**，不能预测收益的**方向**。
之前那条漂亮的上升曲线量的是另一件事。

## M6 连续研究服务 + M9.2 逐拍回放（已交付）

此前循环停在一张写死的变体表上，`Role.SEMANTIC_AUDITOR` / `INTERPRETER` / `RED_TEAM`
三个角色声明过但从没被调用。核心矛盾是：让 LLM 读到结果再提下一版，系统就变成在检验
统计量上爬山，而那正是零假设带度量的过程；完全不给反馈又永远迭代不了。

解法是**按驱动来源拆开迭代**。语义通道盲化，比对「特征机制 ↔ 目标语义 ↔ 可证伪条件
↔ 已接入数据源」，能发现「幅度对方向」这类错配而**不需要任何效应量**（已在真实账本上
实测）；结果通道可见效应，但其产出**不进提案器上下文**。

审计位置是关键：`study_created` 之后、`record_outcome_read` **之前**，**无条件**执行。
无条件意味着调用本身不携带结果信息，盲化由哈希链 seq 顺序证明而非事后检查提示词；
发现错配即 blocked 且不读 outcome —— 问错了的问题不消耗多重检验预算。审计员输入按
白名单从类型化对象构造，绝不走 `read_events`（那条路曾泄漏带符号 t 值）。回传给下一版
的是**封闭词表的码**，不是自由文本。

停止语义各归其位：服务的停止条件全是外部边界或**停滞**，停滞判据只用与结果无关的量
（连续 k 轮没有新的特征内容身份）。停下来时写 `human_review_required` ——
「该不该继续找」是人的判断。

实跑暴露并修掉三个退化：诊断只看上一轮导致 A/B/A/B 震荡（改为累积）；动量特征两窗
相等使回归元恒为零（基线强制严格长于观测窗）；停滞按 `proposal_id` 计数而
`ProposalSpec` 不含 feature_spec，参数扫描的变体共用一个提案身份，5 轮就误判停滞
（改按 `FeatureSpec.content_id`）。

**实测（`arad episode service`）**：16 轮、16 版一条链、11 个互异特征。第 0 版被语义
审计拦下且没读 outcome（统计分母 15 而非 16）。**结论是负的**：15 次检验里最好的
|t| 是 1.776，而 `expected_max_abs_z(15)` = 2.073 —— 最好的一次仍在噪声带之下。

Atlas 同步改为**按账本 seq 逐拍回放**（M9.2）：落点分两步（提案冻结先出空心待定点，
评价出结果才落到纵轴），中间隔着「读 outcome」那一拍，带在那里抬高。关键时刻由 Python
算好供跳转，其中最要紧的是「零假设带追上 running best」—— 这张图真正的结论不在曲线
最高点，而在那一拍。详见 `docs/tickets/M6-continuous-research.md`。

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

M6.1（真实模型实跑暴露的四件事）：`--provider claude` 首轮 8 分钟 3 次调用全部解析
失败，唯一错误是 `direction` 写成 `"positive"` 而契约只列了字段名没列类型。修正为
逐字段声明类型（有结构测试钉住与 `ProposalOutput.model_fields` 一致）、封闭同义词表
规范化为 ±1（**表外词整条报错**：`direction=None` 会被 `to_proposal()` 写成 0，
使预注册的方向主张变成空的）、`ParseFailure` 逐次记错并记原始长度（摘录截在 500 字，
截断与格式错误在摘录里无法区分）。

更要紧的第四件是**停止语义被污染**：解析失败的一轮没有内容身份，原实现按停滞计数，
因此一个 schema 缺陷再多两轮就会写下「模型问不出新东西」。判据改为「这一轮有没有
形成过提案」——`parse_failure` / `provider_error` / `context_blocked` /
`invalid_proposal` 都在 `record_proposal` 之前返回，单独计入 `infrastructure_failures`，
连续多轮以 `provider_unusable` 停止，复核理由明说不构成任何研究结论。

同一次运行的后续轮次证明通道是通的：模型自主从 30 个族的菜单（不含任何指向原油的
提示）里选中 `cand:iran`，构造「1 日名义成交额相对 30 日基线的 innovation → 90 日
日度采样 z 分数」，并写下四条证否路径。两轮判决均为 `blocked` 且理由成立：置换检验
0.980 / 0.880，最大 DFBETA 占斜率 9.72 / 4.84（上限 0.5）。诚实的说法是「一个离群日
撑起了整条斜率」，不是「机制不成立」。

新增阻塞事项 7：**重尾回归元没有反馈通路**。`blocked_reasons` 按盲化白名单不进提案器
上下文，模型无从知道问题出在特征的分布形状上，只会继续产出同样重尾的名义成交额特征。
可行解法是只用 X、不碰 y 的特征健康诊断（偏度、峰度、最大单点占比），与语义审计同属
读 outcome 之前的通道，因此不构成在检验统计量上爬山。另立一票。

M6.2（影响度量除错了分母）：真实模型自主提出的前三条 Polymarket 特征全部被
「单点影响过大：最大 DFBETA 占斜率 9.72」拦下。只用 X 重算杠杆后排序与闸门相反 ——
study-1 的最大杠杆只有 0.022（最有影响的点占回归元总变异 2%），而 study-2 是 0.607。
缺陷不需要数据即可论证：`|DFBETA| / |β̂|` 在 β̂ → 0 时发散，因此该闸门在**完全没有
效应**时最响，而那正是不存在「被单点主导的结论」的情形，它报出的理由在那里是假的。

改为按斜率的标准误标准化（Belsley-Kuh-Welsch 的 DFBETAS），分母取本次推断实际使用的
双向 cluster 标准误，阈值取先验的 `|DFBETAS| > 1`（BKW 同时给出的 `2/sqrt(n)` 是用于
筛出待检视点的大样本阈值，不用于阻断）。**写下该阈值时已看过三个 DFBETAS 值，因此不以
「恰好把三条分开」为理由**；扫全部四个账本共 3 次评价，每条除影响度量外各有 3 条其他
阻塞理由（含对每条都成立的「未声明成本模型」），因此阈值取 1 还是 2/sqrt(n)，
**没有任何已记录判决的结论会改变**。`EVALUATOR_VERSION` 升至 0.2.0。

新增两个诊断量且都不阻断：`max_leverage`（只依赖回归元，读标签之前即可算，有测试钉住
它对同一组 X、两组不同残差取值相同）与原样保留的旧口径 `dfbeta_over_slope`。
不为 `max_leverage` 设阈值：它只捕到三条里的一条，而「一个点占多少变异算太多」同样是
我无法在不看这些结果的前提下定下来的数。

据此修订 M6.1 记下的阻塞事项 7：只用 X 的通道能捕到 study-2 那一类（杠杆 0.607），
捕不到 study-1 那一类（DFBETA 膨胀来自残差），因此它是部分手段而不是解法。

新增阻塞事项 8：**`Verdict.NULL` 从未被任何代码路径产出过**。判决导出是
`verdict = BLOCKED if blocked else CANDIDATE`，而 `cost_model_declared=False` 对每一条
Study 都成立，于是 auto-study-1 这样 t = −0.030、置换检验 0.980、506 行有效样本的
干净否定结论被记成 `blocked`（词表里意思是「判不出来」），与真正无法判定的 Study
在账本里无从区分。这与 M6.1 修掉的停滞误判是同一类归因错误。另行裁定。

M7 / 决定 0005（让否定结论能被记下来）：`Verdict.NULL` 从未被任何代码路径产出过 ——
判决原本是 `BLOCKED if blocked else CANDIDATE`，而 `cost_model_declared=False` 对每一条
Study 都成立。第一次真实模型自主运行的四条判决全部记为 `blocked`，其中 auto-study-1 的
t = −0.030、置换检验 0.980、506 行有效样本，是干净的有功效否定结论，而 `blocked` 在词表里
的意思是「判不出来」。

判决改由**每条理由使哪些结论失效**推出（`REASON_INVALIDATES`）：未声明成本模型与 cluster
退化只使 candidate 失效（断言「没有统计关系」不需要成本模型；标准误被低估只会高估显著性，
真实标准误更大反而让 null 更强，且置换检验不使用标准误）；单点影响方向感知（守 candidate
问「这一点是否撑起了效应」，守 null 问「删掉它 |t| 能否够到 2.8」）；置换检验未通过本身就是
null 的证据，不使任何结论失效。四条已记录判决按新规则全部为 `null`。null 必须携带
`null_exclusion_bound`（本次达到的 MDE），否则它只是「没找到」而不是「排除了什么」。

两条不变量有合同测试钉住：判决只能是理由**种类**的函数（条件化到未经预注册闸门表达的效应
数值就是泄漏，因此强弱两个 null 必须共用一个词）；提案器提示词只拿到按判决词的**聚合计数**，
拿不到逐 Study 的判决（否则可把机制与结果一一对上）。`EVALUATOR_VERSION` 升至 0.3.0，
账本只增不改，口径以该版本号区分。

一次撤回：第一版把提案器视图里的 null 折叠成 blocked，但既有合同测试
`test_proposer_sees_verdict_categories_but_not_effects` 早于本次会话，明确断言提案器应看到
null 分类，且 verdict 本就在白名单上。那是项目记录的设计意图，已撤回折叠，改为钉住披露边界。

新增阻塞事项 9：**语义诊断对真实模型是断开的**。`service.py` 用
`if hasattr(provider, "mismatch_codes")` 回传错配码，而该属性只有确定性变异器
`AutoProposer` 有，`ClaudeCliProvider` 没有，因此诊断被静默丢弃。实跑 8 轮里最后三轮
连续撞在同一个 `magnitude_vs_signed_label` 上（都被审计拦下且没读 outcome，统计分母
因此是 4 而不是 7），正是因为模型无从得知上一轮错在哪。M6 票称之为「环真正闭上的地方」，
而它只对变异器闭上了。

M7.1（环只对确定性变异器闭上了，已修）：实跑 8 轮里最后三轮的结局都是
`semantic_mismatch` 且错配码都是同一个 `magnitude_vs_signed_label` —— 三个不同构造，
同一个语义错误。原因是 `service.py` 用 `if hasattr(provider, "mismatch_codes")` 回传诊断，
而该属性只有 `AutoProposer` 有，`ClaudeCliProvider` 没有，诊断被静默丢弃。审计本身有效
（三轮都被拦下且没读 outcome，统计分母 4 而不是 7），损失的是时间与调用预算。

改为走**任务载荷**：`run_service` 把累积的错配码写进入队载荷，
`assemble_proposer_context` 按封闭词表渲染进提示词并附上解释，**未登记的码不渲染**
（自由文本是效应走私的通道，有测试用带数字的假码验证它不出现）。载荷这条路对任何
provider 都成立，因为提示词是所有 provider 共同的入口。不构成泄漏：错配码在读取任何
outcome 之前产生，被拦下的版本根本没读 outcome，且整张词表不含数字（有既有测试钉住）。

据此结清阻塞事项 9。

M4.2（分位排名原语）：M6.2 只用 X 重算杠杆时发现一条真实特征的最大杠杆是 0.607，
而当时语言里没有任何稳健变换可用。zscore 在重尾输入下有两种方向相反的失效：离群日落在
被评估的点里时最大杠杆 0.9714（一个观测占掉回归元 97% 的变异），落在参考窗口里时极差塌到
0.0046（特征几乎恒定，评价机报「回归元没有变异」）。rank_pct 两种都不发生，取值有界 [0,1]。

定义用中位秩的经验分布函数 `(#{s<x} + ½·#{s=x}) / n`，与 zscore 共用采样网格与全部约束
（`SAMPLED_KINDS`）。**它不是 zscore 的替代，是另一个假设** —— 代价是丢掉幅度信息，
提示词里明写。`_no_nested_zscore` 推广到整个 `SAMPLED_KINDS`，交叉嵌套一并拒绝。
生成代码与解释器逐位一致。`FEATURE_SPEC_VERSION` 升至 0.3.0。

M7.2（标识必须带上运行 id）：修完 M7.1 重启服务，`--max-rounds 12` 却只跑了一轮就以
`no_runnable_work` 停止。队列与账本跨运行持久，而 `auto-task-N` / `auto-study-N` 不带运行
标识，第二次运行的 `auto-task-1` 在上一次里已是 `done`，入队成空操作。更糟的一面是
`auto-study-N` 同样会撞，两次运行的证据会被写进同一个 Study 标识下，`collect_snapshot`
按 study_id 收集，快照因此混成一份。`run_service` 新增 `run_id` 并由 CLI 的 `--run-id`
透传（该参数此前只用于 Atlas 运行目录命名，没有进入证据标识）。测试在同一队列上连跑两次。

M7.2 补充两处同类问题：（一）`--run-id` 缺省时时间戳兜底原本写在函数末尾（只为 Atlas
运行目录命名），因此缺省调用时 `run_service` 拿到 None，任务标识恒为 "None-task-0"，
冲突原样回来；兜底移到服务启动之前。（二）`no_runnable_work` 是唯一一个能由缺陷触发却
读起来像干净完成的停止理由 —— 入队静默成空操作、不写 human_review_required、退出 0。
改为入队前检查标识存在即抛 `TaskIdentifierCollision`。同时把解释器的
`ZScoreCoverage` / `zscore_reference_samples` 改名为 `ReferenceSampleCoverage` /
`reference_samples`：rank_pct 的证据此前被记在 zscore 名下。

M7.3（幅度判据改成结构的）：M7.1 把错配码送进提示词之后，模型收到了也照做了 —— 它立刻
用上刚加的 rank_pct，把特征改成 `sum(log_return) ÷ mean(realised_volatility)` 再取分位排名，
即波动率归一的**有符号**收益。七轮全部仍被 `magnitude_vs_signed_label` 拦下，因为判据对
**机制散文**做子串匹配，而要表达「按波动率归一」就必须提到波动率，模型无法逃出该判定。

判据改为沿 DAG 从输出步骤反推，只看字段名与算子：叶子按算子（std）与字段名判定，派生步骤
**当且仅当全部输入都是量级时**才是量级。因此 `有符号 ÷ 量级` 仍有方向，`量级 ÷ 量级` 是量级。
用全部 16 条历史规格回测：四条真阳性（rv 均值、`std(p)`、rv÷rv、`std(rv)÷mean(rv)`）
**全部保留**，放行的都是分子带 log_return 的构造。`AUDIT_VERSION` 升至 0.2.0。

顺带：`IMPLEMENTED_STEP_KINDS` 在 M4.2 新增 rank_pct 时没同步却一声不响，因为它与
`unsupported_step_kinds` 全仓没有调用方 —— 正是 M6 票开头点名过的「声明了却没人读」形态。
已补上并加合同测试钉住它等于「除 residualise 之外的全部步骤类型」，注释里明记它当前无调用方。

M8 草案（多品种与横截面 IC）：一次四路只读勘察的产物，尚未实施。核心裁决是**一条特征在 N 个
品种上评一次算 1 次检验**，当且仅当 universe 在 Hypothesis Lock 中冻结为一个面板对象且判决
只由该面板的单一汇总估计量导出；逐品种各评一次算 N 次，两者不得混用（先跑面板再看逐品种、
报最好的那个，是 Merge-Plan-2 §5.5 已禁止的事后检验）。三个参考实现（Alpha-Data、ADAR、
LBG-Agent）都走逐品种且分母随品种数相乘，因此该裁决需另立决定 0006。

已独立复核的三条事实：`temporal/build.py` 的 `_CONTRACT_RE` 用 `[a-z]` 而 M1 扫描器用
`[A-Za-z]`，35 个大写前缀品种会静默得到空 spine；`demo.py:381` 与 `baseline.py:62` 用
`contract[:2]` 切品种，对单字母品种错误（`'a2601'[:2] == 'a2'`），而目标表本来就有 `product`
列，`'sc'[:2] == 'sc'` 恰好正确所以至今没暴露；`sessions.PRODUCTS` 只有 sc。

**两份项目文档在扩品种的立项理由上直接矛盾**（逐字核对属实）：`docs/01-goal.md:115` 写
「n 从几十升到数万量级」，而 `Merge-Plan-2.md:224` 写「不能把『50 个品种 × 900 日』直接当
数万独立样本」。开工前必须更正目标文档。

第 1 层起全部被取数授权阻塞：三个只读源仓库中都不存在合约乘数与最小变动价位的元数据，
必须从交易所公告引入，属新的取数，需单独人工授权。文末另列十条待人裁决事项与七条新增阻塞。

M8.1（时段表参数化，品种 1 → 72）：从原始 tick 实测归纳，品种之间**只差夜盘收盘时刻**，
日盘分段（09:00-10:15、10:30-11:30、13:30-15:00）全部商品品种共用，而那一套正是 SC 表里
已按交易所规则声明过的。因此不是新写 5 张表，是复用已有权威几何 + 按实测判定类成员资格。
四类：夜盘至 02:30（sc au ag）、01:00（有色 10 个）、23:00（42 个）、无夜盘（17 个）。
出处标注明写「夜盘收盘与类成员资格由原始 tick 实测归纳，不是交易所公告；开盘时刻不取实测值，
因为集合竞价窗口内没有 tick」。合约乘数与最小变动价位记 None（已核实不进入任何计算）。
同时修掉两处会让新品种**静默失败**的缺陷：`build.py` 的合约正则用 `[a-z]` 而 M1 扫描器用
`[A-Za-z]`（35 个大写前缀品种匹配不上且不报错，建出空 spine）；`product_cluster` 切
`contract[:2]` 对单字母品种是错的，改用目标表本来就有的 `product` 列。
未入表：中金所 8 个（日盘 09:30-11:30/13:00-15:00，且金融期货是否属研究范围待人裁决）、
空壳 6 个（全样本期只有 15:00 一个结算打印）。

M8.2（模型的选择必须真的算数）：全部 12 条 Study 都声明 `target=sc_rv_next_session`
（已实现波动，菜单只列了这一个），而评价机用的标签是 `sc_ret_next_session`（有符号收益）——
**预注册的是波动幅度的假设，检验的是收益方向**，两者秩相关只有 −0.05。没有任何检查比对
这两个名字，证据里各自都对，只是从不相互比对。这也是 M7.3 底下更深的一层：模型被告知
目标是波动、据此提出幅度型特征（完全正确），却被审计判「幅度对方向」连续七轮 —— 模型是对的，
是框架在目标上对它说了假话。

三处改：读 outcome **之前**硬比对，不一致抛 `TargetMismatch`（不是判 blocked：那是关于
Study 的结论，而这里根本没形成可下结论的 Study，有测试钉住此时统计分母仍为 0）；菜单由
`TARGET_SPECS` 如实列出全部已物化 target 及其真实 label 语义；标签、`label_is_return`、
`label_rule` 全部按声明的 target 取，语义审计的 `target_record` 同样。`EPISODE_VERSION`
升至 0.2.0。**已记录的 12 条判决回答的不是提案所问的问题**，账本只增不改，引用时必须注明。

M9（记忆架构）：先把前提摆正 —— 组合无限不等于可以一直找下去。零假设带按 Bailey & López de Prado 的期望最大值近似抬升（此前文档写作 √(2 ln n)，那是渐近形式，非 selection.py 实际所算），同一条 t = 2.049 的证据在 9 次检验下自罚奖励 +0.195，到第 25 次变成 −0.227。
**因此记忆的任务不是让模型想出更多主意，而是让它少花检验。**

事故：`feature_spec_locked` 不在提案器白名单里，模型看不到自己写过的任何一条规格，
每一轮从空白重新推导 —— 它不是在第 12 轮，是把第 1 轮做了 12 遍。实测 run3 七轮给出
七个几乎相同的构造，run1 四轮全在 cand:iran 族内打转（此前我把后者误读成「发散」）。

三层：第 0 层提案侧（免费，读 outcome 之前就已知，泄漏为零按构造成立）；第 1 层消耗账
（已披露，但改为**报价**渲染：已花 n 次、地板多少、再提一个变成多少 —— 同样的数说成价格，
决策才会变）；第 2 层结果侧归纳对提案器**永久关闭**（那正是零假设带度量的过程，且
`E[max|z|]` 假设独立抽取，被引导的搜索破坏该假设而带不为此定价）。

边界由账本强制：`proposer_memory(event_type)` 只放两种事件、逐字段过白名单、
**丢弃 study_id**（它是事件的列而非 payload 字段，白名单管不到；留着提案器就能把规格
与判决一一对上）。第一版写成全量 `read_events(role=PROPOSER)` 被 `CapabilityDenied`
拦下，那条拦截是对的，没有绕过。规格按 content_id 而非时间排序。
如实记下一条无法消除的小样本泄漏：族内只有一条规格与一条判决时对应关系是平凡的。

M8.1 构建实测：**51 个品种建成**（36 个有完整 1816 行），21 个失败且**全部是郑商所**。
修掉一处机械缺陷（无夜盘品种上无条件调 `table.session("night")` 硬失败）之后，
失败集完全等于交易所约定差异，见下条阻塞。

新增阻塞事项 10：**郑商所的 TradingDay 约定与上期所相反**。实测 20260519 同一天：
sc/rb 的夜盘 tick 标 TradingDay=20260519（交易日约定，夜盘归次日），MA 标 20260518
（自然日约定）。守卫 `tick 表的 TradingDay 与声明的交易日不一致；拒绝继续` **做得正确** ——
按上期所约定处理郑商所会把每个夜盘归到错的交易日，决策时点与标签窗口整体错位一天，
即一天的前视。需在 `ProductReference` 上声明 per-exchange 的 TradingDay 约定并逐一校验，
这是 PIT 相关的语义裁决，不猜。21 个品种在此之前不建。

决定 0006（判决分类退出提案器上下文）：M9 的对抗性审查（五个独立视角）证否了我在 M9 里
写的「泄漏为零，按构造成立」。**逐条记录成立，逐视图不成立** —— 由「每一条都不含结果」
推出「视图不含结果」是组合谬误。

决定 0005 把判决计数定价为安全，有一个未写出的前提：计数指向一个**匿名总体**（提案器每轮
由独立子进程承载，跨轮不带上下文，因此「9 个 null」指哪 9 条它无从知道）。M9 的具名清单
取消了匿名，而定价没有被重新审视。推断链：规格与判决一一对应；`null` 充要条件是置换检验
未通过（一条关于**量级**的陈述）；`null` 只可能在读过 outcome 之后产生，故
`#null <= tests_spent`。**实测 run4：规格 11、outcome_read 9、判决 {null:9,...}，
`#null = tests_spent = 9`**，等式成立即确定地推出「全部被度量过的具名规格都是 null」。
新族、新账本、冷启动都落在这个区间，而它们正是常态运行的开端。

裁决：`verdict_taxonomy` 与 `studies_seen` 不再进提案器上下文（`blinded_history` 保留供
Atlas 与人工复核）。留下的是具名清单、tests_spent、地板、两本分母 —— 「哪些被度量过」由
语义审计与解释器可求值性决定，两者都是读 outcome 之前的纯函数。模型会读到的两处 note
字符串一并改掉：只改 docstring 而把错误的保证留在提示词里，等于让模型继续读到假话。

顺带关掉两处结构问题：记忆的投影表与 `read_events` 的投影表分开（合用会让
`read_events(role=PROPOSER, study_id=X)` 一次返回规格与判决，由同一 study_id 串起，
绕过 `proposer_memory` 刻意丢弃 study_id 的保护）；记忆补上第二道递归遮蔽
（`steps` 是嵌套结构且逐字保留）。

新增阻塞事项 11：记忆不按族过滤（`events` 表无 `family` 列，而 `search_price` 按族取分母），
多族共存时族 A 的提案器会读到族 B 的具名规格；当前单族未触发。
新增阻塞事项 12：M5 接入成本模型后本条严重度上升 —— 届时 `candidate` 可达，
而 `tried_features` 保留机制全文、机制陈述通常已蕴含方向，一条 `candidate: 1`
配合结构筛收缩即成为**方向**陈述，不再只是量级上界。

M8.4（universe 真的解析成品种清单）：`build_evaluation` 此前只装 sc 一个品种的序列，
因此矩阵与横截面在多品种建成之后仍然是空的。改法三处：

一、`universe_members()` 把 universe 名解析成品种清单，**不认识的名字直接报错**。两种形态：
`<品种>_dominant_t1`（sc 那个取值不变）与 `full_coverage_panel`（目标表满 1816 行的品种，
实测 36 个）。面板的成员资格是**数据可得性**规则，与任何结果无关，因此不构成结果依赖的选择；
但它排除了样本期内退市或中途上市的品种，这一条是幸存者性质的，已写进 docstring。

二、特征**逐品种**求值再汇集。每个品种有自己的 session 表、决策时点与 bar 序列，
混在一条序列上求值会算出一个不属于任何品种的数。

三、目标按**族名后缀**逐品种解析。目标名带品种（`sc_ret_next_session`），第一版用 sc 的键
去查其余品种的标签，把它们全部过滤掉，于是面板与单品种给出**同样的 926 行、同样的 1 个
品种簇** —— 看起来在工作。这一条有测试钉住行键跨品种互不相交。

顺带修掉：`_load_sc` 用字符串替换推兄弟目标表路径，只在 sc 上碰巧成立 —— au 的表名里不含
`sc_rv_next_session`，三个 spec 会全部指向同一个文件而不报错。改为按品种推路径。

实测：`sc_dominant_t1` 926 行 / 1 个品种簇；`full_coverage_panel` **33,129 行 / 36 个
品种簇 / 513 个日期簇**（首次装载 32.6 秒，同一次服务运行内缓存）。
`two_way_cluster_se` 的退化条件是任一维少于 2 组，36 ≥ 2，因此
`cluster_structure_insufficient` 这条出现在此前**每一条**判决里的理由会消失，
`candidate` 只剩 `cost_model_missing` 一道闸门。

M8.5（universe 进菜单）：`universe_menu()` 列出 52 项（1 个面板 + 51 个单品种），
每项带成员数、成员清单、成员资格规则与一句说明。面板的说明写明它是唯一能做截面推断的
形态、且其成员资格是幸存者性质的；`PROPOSAL_OUTPUT_TYPES` 里写明**一次评价只能取一个
universe** —— 先跑面板再看逐品种、报告其中最好的那个，是事后检验。
`run_service_demo` 的 `build_evaluation` 带上 `loader=_load_product`，多品种才装得进来。

写这段菜单文字时被 `assert_blinded` 拦下：我在说明里写了「截面 IC」，而 `ic` 是效果字段名。
**那道检查做得对**，措辞改为「截面推断 / 截面统计量」。这条记在这里，是因为它说明盲化边界
连提示词的散文都管 —— 而散文正是最容易把效应量带进去的地方。

M9.3（实时进度）：运行目录只在 `run_service` 返回后写一次，因此运行期间应用里什么都看不到 ——
实测 run6 跑到第 4 轮时 `runs/` 里仍没有 run6，只能查账本才知道进度。参考
`minute_factor_agent` 的 gui，但按 ARAD 的实际情况调整了三处：

一、**不重写运行目录，只读账本**。账本本来就是实时写的；把 `write_run` 挪进循环每轮调一次
最省事，但它每轮重算整个投影，随账本变大越来越慢 —— 观测不该改变被观测的过程。
`live.py` 只用 SQL 聚合，代价与账本大小无关。

二、**「在跑」按最后一个事件的年龄判断，不按进程状态**。账本是唯一事实来源；进程可能在别的
机器上，也可能被杀掉却没写停止事件。阈值 15 分钟（真实一轮 3 到 8 分钟）：宁可把已停的报成
在跑，也不要把在跑的报成已停 —— 后者会让人以为出事而去干预一个正常运行。

三、**实时栏不显示任何效应量**。这与参考实现不同，理由是：运行期间盯着效应看，会让
「要不要继续找」这个判断变成事后选择，而那正是零假设带在度量的东西。结果在运行结束后的
判决视图里看。

从参考实现直接照搬的四条轮询性质（`livePoll.ts`），每条对应一种实测过的失败：在途不重排
（否则长出孤儿定时器链，页面开久了频率自己变快）、序号防竞态（慢请求会用旧数据覆盖新数据）、
回前台立即刷一次、隐藏时退避。失败**只标记不清空**：把「暂时读不到」显示成「什么都没有」，
与本仓库一直在修的那类错误是同一种。

一个 Study 固定走 11 步，因此「第 k / 11 步」有确切含义。**缺步本身是信息**：语义审计拦下的
Study 在 `semantic_audit` 之后直接跳到 `verdict_recorded`，`outcome_read` 与
`evaluation_result` 两步缺席 —— 那正是它没消耗多重检验预算的证据。

M9.4 / M9.5（实时曲线与 residualise）：实时曲线接上时撞见 |t| = 9.300 与 8.867 两条。
查规格：两条都是 `something(log_return) ÷ mean(realised_volatility) → rank_pct`，
而 target 是 `sc_rv_next_session` —— **分母是已实现波动，目标也是已实现波动**。
PIT 没问题（窗口严格在决策时点之前），置换检验也过了，因为那个关系是真的：
它重新发现了**波动率聚集**，教科书级的 Baseline Control，不是另类数据的 alpha。
证据本身让这件事一眼可查，不需要重跑任何东西 —— 账本里冻结的规格直接说明了它。

因此把 `residualise` 实现掉（此前抛 `StepNotImplemented`）。关键约束：**在全样本上拟合
再取残差，等于用未来数据定义每个时点的残差** —— 那是最隐蔽的一种前视，残差看起来永远
「干净」，而干净正是因为它见过未来。因此 `residualise` 加入 `SAMPLED_KINDS`，
由规格自己声明拟合网格，样本取自 `t - k*sample_every`，逐点重拟合。
第一版只支持**一个**控制项：多元要解正规方程，多写一个直接拒绝而不是静默只用第一个。
门槛计**控制变量的互异取值**：控制恒定时斜率不可识别，此时残差只是去均值，那不是残差化。
控制按登记表解析（brent、own_realised_volatility），未登记直接拒绝；缺控制序列时报错，
**不得退化为原样返回** —— 那等于把未残差化的值当成已残差化的证据。
生成代码与解释器逐位一致（有等价测试）。`FEATURE_SPEC_VERSION` 0.4.0，
`INTERPRETER_VERSION` 0.4.0。

实时曲线（M9.4）改变了 M9.3 的一个决定：实时栏此前不显示任何效应量，理由是盯着结果看会让
停止判断变成事后选择。那条顾虑是真的但用错了地方 —— 这个决定按设计本来就归人（M6）。
形态上定死一条：**曲线绝不单独出现**，每点同时带 running best 与地板，
因为一条随迭代上升的曲线本身就是选择在纯噪声上必然产出的形状。
残余风险如实写进界面：早停不会把已花的检验退回来，因此不制造额外的多重检验偏差；
真正的风险是「看着不错就停」，缓解手段正是把地板画在旁边。

M9.6（中间结论进 app）：`/api/live` 新增 `recent` —— 最近几版的机制全文、证否条件、
语义审计的错配码、判决与理由。此前这些只有服务跑完写进运行目录才看得到，而运行期间
恰恰最想看它们；账本本来就是实时写的，直接读即可。这一段给**人**看，因此可以带机制全文；
它不进提案器上下文（提案器那侧的记忆走 `memory/induction.py`，判决分类已按决定 0006 退出）。

同时把「已落下但没有取值的版本」画成坐标轴上的**空心刻度**（此前什么都不画）。
不画它，用户会以为图坏了；画成实心点，又等于伪造一个不存在的取值。
实测 `run3-study-0` 那条 14 点的链前 6 点全部如此 —— 它们被语义审计拦下、根本没读
outcome，因此地板不因它们抬高。**那是审计在替我们省检验预算的证据，此前在图上完全看不见。**
已目视确认渲染正确。

M9.7（回放变实时播放）：新增 `/api/live/beats?since=N`，回放的数据源由「静态快照」
可切换为「增量追加的实时流」。三处设计：

一、**只拉 since 之后的新拍**。节拍带两个累计量（提案分母、统计分母），因此不能只看新事件
就算出来；服务端先用两条聚合查询取 `since` 处的计数，再在新拍上往后累加。每次从头重算会让
轮询随运行时间变慢，而那正是最需要它的时候。提案分母按**内容去重**计数
（`record_proposal` 是 INSERT OR IGNORE），数事件次数会与账本对不上。

二、**一次轮询把落后的拍全部追上**（最多 20 批）。服务端每批最多 400 拍，落后很多时只前进
一批就永远追不上正在跑的运行。

三、**拖动进度条自动关掉跟随**。「看历史」与「跟着跑」是两种意图，混在一起会互相打架。

实测：`since=600` 返回 7 拍，`tests_so_far` 跨批次接得上（26 延续自前一批）。

M9.4 补正（横轴标注）：实时曲线复用 `Chart` 组件，把演化视图的横轴文案「第几版（沿谱系）」
一并带了过来，而它其实是**本族第几次检验、跨全部运行累计**：实测那 27 个点跨了 5 次运行
（auto 5 / run3 2 / run4 10 / run5 3 / run6 7），相邻两点之间没有父子关系，根本不是一条谱系。
同一行的「点开一个点看它的判决快照」在实时视图里也是假的（传的是空回调）。
`Chart` 新增 `xCaption`，由调用方给出；写死一个会骗人。

顺带记下那条陡升的来历：第 20 点是 `run5-study-2`（|t| = 9.300），第 24 点是
`run6-study-4`（8.867），正是分母为 `mean(realised_volatility)` 而目标也是已实现波动的
那两条 —— 它们重新发现的是波动率聚集，是 Baseline Control，不是发现。图上它看起来像突破。

M9.5 验证（residualise 是否减掉了它该减的那一层）：用 `run5-study-2` 的构造做**离线诊断**
（不走 harness、不记进族账本、不消耗统计分母 —— 它是看过结果之后的变体，不是预注册研究）：

| | 行数 | t | IC（秩） |
|---|---|---|---|
| 原样 | 29,108 | −12.072 | **−0.5695** |
| 减掉自身波动 | 24,574 | −5.446 | **−0.0077** |

**秩相关塌了 74 倍**，那条 |t| = 9 的「发现」几乎全部是波动率持续性，与诊断一致。

剩余部分要单独记：t 只从 12.07 降到 5.45 而 IC 已近零。**线性 t 还在、单调秩相关没了**，
这个组合通常意味着剩余关系由少数极端观测撑着，不是单调信号；24,574 行下秩相关的标准误
约 1/√n = 0.0064，因此 IC = −0.0077 大致就是噪声。行数由 29,108 降到 24,574 是 120 日
拟合窗的预热期代价 —— 这是 PIT 安全取法的必然开销，拟合样本必须严格取自过去。

M7.2 补正（认领也要按运行范围隔离）：启动 run8 之后账本里写出的第一条事件是
**`run6-study-9`**。队列是持久的，里面积着 6 个 ready 与 2 个 leased 的旧任务
（run6、run7 被停时留下的），而 `queue.claim` 按 created_at 升序取最早的一个 ——
于是新运行先去替上一次运行干活，24 轮的统计预算会花在陈旧任务上，
而它们的载荷带着旧的错配码与旧的谱系。

M7.2 让**标识**唯一了，但没让**认领**按运行范围隔离，这是同一个缺陷的另一半。
`queue.claim` 新增 `prefix`，`run_service` 传 `f"{run_id}-task-"`。
有测试钉住：留一个别的运行的 ready 任务，新运行必须只认领自己的，且旧任务原封不动。

M9.8（residualise 没被用上，原因不是可见性）：run9 十一个版本里 residualise 用了 **0 次**，
而它在原语表、控制项名、schema 说明里都可见。查下来两件事：

**一处提示词在说假话（已修）。**`blockers` 写着「pm_market 与 cls_telegraph 尚未接入」，
而 pm_market 在 M5.2 就接入了，菜单同时列着 30 个族 —— 提示词自相矛盾。
我据此推断模型被这句话挡住了，**数据否定了该推断**：run9 实际用了 pm_market 20 次、
commodity_bar 6 次。那句话仍然要改（它就是假的），但它不是本条的原因。

**真正的原因：没有任何地方告诉模型为什么要残差化。**schema 说明只讲了怎么用。
项目自己早就定下的口径（Merge-Plan-2 §3.1）——只用 commodity_bar 的量价特征属
Baseline Control、不计入另类因子清单，另类数据的主张必须是它之上的增量——
从未出现在提示词里。新增 `what_counts_as_a_finding` 一条陈述该口径。
**这不是对结果的引导**：它陈述的是既有的记账规则，与「哪类机制效应更大」无关。

M9.9（缺 feature_spec 的提案会打断整个服务，已修）：run9 在第 11 轮崩溃退出，
`AttributeError: 'NoneType' object has no attribute 'steps'` —— 模型返回了一个文字字段
齐全但 `feature_spec` 为 null 的提案，既不是原语缺口声明也不是解析失败。
`to_proposal()` 只校验文本字段，因此它通过了；随后 `contamination(parsed.feature_spec)`
拿到 None 就崩，**整个服务挂掉**，24 轮预算废掉 13 轮。

非正常产出一律降级为证据、不打断 Episode，这是本仓库反复立过的规矩（坏 JSON、原语缺口、
上下文泄漏、特征恒定四种都已如此）。补上第五种：缺 feature_spec 记 `invalid_proposal`，
任务退避重排不丢。它已在 `INFRASTRUCTURE_OUTCOMES` 里，因此不计入停滞。

run9 实测（11 轮，10 次读 outcome）：判决 null 7 / blocked 3 / underpowered 1；
数据源 pm_market 20 次、commodity_bar 6 次；最好 |t| = 2.261，而全族 40 次检验的地板是
2.451，自罚奖励 **−0.190**。residualise 用了 0 次（原因见 M9.8，提示词此前没说为什么要用）。

M9.10（登记而不装载，已修）：run10 的模型行为完全正确 —— **residualise 五个版本全用上**
（M9.8 的口径立刻生效），并在 own_realised_volatility 与 brent 两个控制项之间交替。
但用 brent 的三条全死在 interpretation_gap：CONTROL_SERIES 登记了 brent，
装载器却从没把 controls/brent.parquet 装进序列字典。拒绝本身是对的（缺控制序列不退化为
原样返回），缺的是接线。已接上（可用时刻取 available_time，PIT 由它保证），
合同测试钉住「登记表里的每一个控制项，序列字典里必须有对应的键」。

用 own_realised_volatility 的两条正常评出 null（置换 0.480 / 0.225）。

顺带修一处「看起来卡死」的界面缺陷：每一轮最长的阶段是模型调用（3 至 8 分钟），
而它在流水线视图里不可见 —— 停在「第 1/11 步」看起来像挂了。实时视图在等待模型时
显式说明这一点。

M9.11（驾驶舱换上参照实现的实测 token）：形态批评成立 —— 此前的 Atlas 是事后审计文档，
而需求是随时点开任何细节的研究驾驶舱。重构为三栏实时工作台（左：全部 Study 按运行分组；
中：曲线与过程流；右：选中 Study 的完整产物台），默认页签。设计 token 不是"参考风格"而是
从 minute_factor_agent 的 gui 源码逐项提取的同一套数值：表面层级 #1c1c1e/#2c2c2e/#3a3a3c、
分隔线 0.5px、强调 #7fa0ce、卡片圆角 16、入场 0.42-0.45s cubic-bezier(0.22,1,0.36,1)、
脉冲 1.6s、直播轮询 1.2s、基准字号 13px、SF 字体栈。

两条驾驶舱特有的选择：跟随模式选**最近一条有内容的** Study 而不是正在等模型的空壳
（右栏否则会空白整整一次调用）；等待模型时顶栏实时计秒并说明这是每轮最长的阶段。

M10（study-3 封存段裁决）：按用户指令为 run11-study-3
（pm_iran_hazard_level_30d_resid_own_rv_90d）开启封存段，一次性、写死在账本。
开启前修掉封存路径上残留的 M8.2 缺陷形状：`sealed_pass` 调 build 不带 proposal，
标签会回落到默认收益 target，而该 Study 声明的是波动 target —— 等于用一次性的封存机会
回答模型没问的问题。现在按 Study 声明的 target 评。

**结果：discovery t=+2.416 → 封存段 t=+0.426（405 行），线性效应没有保住**
（保留率 17.6%，低于预注册的 35% 保持线，按因子卡自己的规则属 sealed_failed）。
值得如实并记的一面：秩相关反而从 +0.087 升到 +0.128（约 2.6 个标准误），
单调关联在样本外仍在，线性斜率没了。且 taxonomy_clean=false（决定 0004：
族归纳语料覆盖全部三段），任何主张本就被封顶。裁决一次性有效，不重开、不重试 ——
这正是封存段存在的意义。

M10.1（app 视觉与动画）：图表颜色全部从硬编码改走 CSS 类，深色下白描边退役、
零假设带发光虚线、running best 描线动画（1.2s draw-in）；过程流卡片入场错峰
（45ms/张）、悬停抬升、特征名升为主标题；数字变化轻闪。

M10.2（把推理过程流出来 + 图表纵轴截顶）：单次模型调用 3 至 8 分钟，等待期间一个字都
看不到是实测里最难受的一段。`claude -p` 改走 `--output-format stream-json
--include-partial-messages`，文本增量实时落到 `data/ledger/inflight_proposer.txt`
（调用结束即删）；**解析仍以 result 事件为准，增量拼接只作兜底** —— 观察窗坏了不能影响
研究本身。`/api/live` 新增 `thinking`（active/chars/tail），驾驶舱在等待时显示模型正在写
的文字（尾部 3000 字，自动滚动）。

逐次检验图的纵轴截顶：两个 |t|=9.3 的量价假象点把其余全部点压成底部一条线，整张图废掉。
上限取「地板最大值的 1.6 倍」与 3.5 的大者，超出的点画在顶边并标真实值（如 9.3↑）——
它们存在这件事要看得见，但不配决定整张图的比例。

M10.3（一个 NaN 打不开整个 app）：`/api/live/projection` 里一条 `abs_t: NaN` 使浏览器端
JSON.parse 报错，app 整个打不开。Python 的 `json.dumps` 默认允许 NaN（非标准扩展），
浏览器按 RFC 8259 拒绝；**单文件模式一直没事** —— 它把同一份数据注入成 JS 字面量，
NaN 在 JS 里合法。同一份数据、两条通路、一条炸，只能在边界统一杀：新增
`atlas/jsonsafe.finite()` 递归把非有限浮点换成 None（前端显示「—」，与解释器
「无定义返回 None 绝不返回 0」同一条纪律），服务端 `_json` 改 `allow_nan=False`，
归档与单文件注入同样净化。

M10.4（195 秒零字节：管道块缓冲）：同一进程里一次调用流畅（2162 字）、下一次 195 秒
零字节 —— `claude` CLI 检测到 stdout 是管道时按块缓冲（约 8KB），事件攒在它的缓冲区里
不吐。stdout 改走**伪终端**，CLI 以为在跟终端说话，恢复行刷新。端到端冒烟：真实调用下
在途文件逐秒增长（51→171→336→450 字节）。顺带：思考先于落笔，0 字阶段界面明示
「已连接，等待首批增量」而不是让 0 字看起来像坏了。

M10.5（完整研究报告，可打印）：`scripts/build_report.py` 从证据账本生成完整报告
（封面、摘要、计划与八条设计原则、数据、方法、十六次运行编年含逐 Study 表、结果综合、
封存段全记录、工程史、未决事项、全部 Study 附录），无头 Chrome 打印为 A4 PDF（13 页）。

一条硬约束写进脚本：**报告里的每一个数字都从同一次账本快照派生，包括标题措辞。**
起因是手写「六十次检验」而账本已跑到 65 —— 服务在跑时统计分母每几分钟就变一次，
手抄的数字必然与表格自相矛盾。脚本一次读完账本、记下冻结点（末条事件 seq 与时间）
并印在封面，其后所有文字引用同一份快照；叙述部分（为什么停、修了什么）由人撰写，
但不含任何数字。

M10.6（报告补齐数学、动机与结论三章）：为写准公式，对全部参与判决的统计量做了一次
逐行提取（五个并行读取器，87 项，每项带 file:line 与 caveat）。报告因此新增三章：
第一章按「失败形态 → 约束 → 实测证据」写动机；第三章写确切数学定义，凡实现与教科书
形式或与本仓文档不一致处一律写明；第七章写编号结论，每条附证否条件。

提取顺带发现并写入 docs/BLOCKERS.md 的票外问题：驾驶舱曲线与顶栏用两个口径不同的 n；
search_price 给提案器的说明文字写 √(2 ln n) 而实现是 Bailey & López de Prado 两项式；
「线性效应保留率」比的是两个 t 值而非效应量（样本量不同则 t 自带 √(n₂/n₁) 缩放，
修正后约 21.7%，裁决不变）；_HOLD_RATIO=0.35 与 min_rows=120 无推导；
taxonomy_clean 只用区间起点。另在报告第六章列出 12 处实现与文档不符，
并指出没有一处能把 null 翻成 candidate —— candidate 被失效表结构性挡住。

同时更正本仓多处「零假设带按 √(2 ln n) 抬升」的说法：那是渐近主项，非 selection.py
所算（n=10 时渐近式 2.146，实际 1.901）。报告脚本亦补上 study-3 全部数字的快照派生，
消除「封面声明数字来自快照、散文却硬编码」的自我违约。

M10.7（发表格式报告 + 逐 Study 信号图）：按用户指定的参照
（Alpha-Data cn_futures_polymarket_ext_round.pdf：ctexart/xelatex、蓝链接、
摘要加粗关键数、目录、booktabs、结尾复现节）生成 LaTeX 报告
（scripts/build_report_tex.py，55 页），复用 collect() 快照纪律。

图文并茂的实现（scripts/build_figures.py）：为每一条有冻结规格的 Study 画
「信号（蓝，左轴）× SC 收盘价（红，右轴）」双轴图，97 张。信号不是回放存档，
而是**用冻结规格在 discovery 决策网格上重新求值** —— 这本身构成一次可复现性检验。
价格来自 ret 目标表的 exit_price（_read_target 做了列投影不含价格列，
图脚本用 pyarrow 直读并按 (contract, trading_day, session) 对齐，对齐率断言 >80%）。
正文放候选与假象的图，附录 B 收全部 97 张。matplotlib 为绘图新增开发依赖（未入
pyproject，报告脚本文档内声明）。

M11（最小成本模型，决定 0007）：用户选定方案 A。tick_size 从 spine 分钟 bar 实测归纳
（62 品种，sc 自检与权威规格一致），半点差与佣金为人批准的声明常量。评价机：提供
cost_model 即视为已声明；新增 uneconomic_target（往返成本 ≥ 平均绝对收益时只废
candidate）；digest 纳入成本版本。同轮修正呈现：成本状态以系统级表述进提案器上下文
（system_state）、判决文案与发现卡，不再像每条提案的缺陷。EVALUATOR_VERSION 0.4.0。
candidate 自此可达 —— 下一个越过地板、过置换、影响有界、经济可行的构造，将是第一个
真正的候选。

M11.1（报告第三版：回溯投影与 ARAD 搜索全貌图）：成本模型建成后按失效表对全部历史
判决作回溯投影（不改写账本）：16 条 blocked 翻为 candidate 形态，分三组（基线假象 4 条、
未越地板 PM 11 条、真形态 1 条）。新增图 2「ARAD 搜索全貌」与旧系统爬山基线成对：
逐次检验 |t| 对同步抬升的地板，按来源与残差化着色，圈出 run16-study-3
（t=+4.39 对地板 2.60，置换 0/200，自罚奖励 +1.79，残差化另类构造首次为正；
模型预注册的证否线就是当时的地板 2.5998）。其封条未开（B6：束被基线假象占位，
收尾自动封存未轮到它），是否开启属人的一次性决定。结论一改为「已解除」，
新增结论八；摘要更新为四条主结果。

M11.2（run16-study-3 开封，人的一次性决定）：开封前修掉封存路径的面板缺口 ——
sealed_pass 不传 loader，面板 universe 在封存段构造不出来（一次不可比的评估同样烧掉
封条）；修为按封存段绑定的逐品种装载器，并先做只看构造元数据的干跑（14,297 行、
36 品种簇、target 正确、成本模型随附）再开封。

**裁决：未保住。**发现段 t=+4.393 → 封存段 t=+0.823（t 保持率 18.7% < 0.35），
秩相关同塌（0.085 → 0.029）—— 比 run11-study-3 更干净的否决。预注册证否条件触发。
两次开封两次否决共同指向：发现段上越过地板、通过置换的构造，其强度主要来自该段
特有的样本构成。封存段正是为识别这一点而存在。报告第三版已更新（67 页）。

M11.3（经验跨轮回放）：用户要求确保每一轮吸取此前全部经验。核查三条受准许通道：
已试构造清单与检验价格直接读账本、天然跨运行；语义错配码却在 run_service 开头
清零 —— run3 用七轮撞出的 magnitude_vs_signed_label，run18 并不知道。修为初值从
账本回放全部 semantic_audit 的码（只取码，不取数值与效应，与盲化无涉），合同测试
钉住跨运行存续。第四条通道（结果侧归纳）按决定 0006 对提案器永久关闭 —— 这不是
缺口而是边界：具名清单 + 判决信息可做减法。run18 停止（旧代码），run19 在修复后
代码上启动并沿用方向指令。

M12（Polymarket 因子起点的选择设计）：把「起点选择」从两级默认（物化取成交量前 30、
菜单只列已物化）改为预注册的三层结构。一、资格筛（qualify-v1，纯 PM 侧统计）：
覆盖跨度、桶数、未决性（时均 p(1-p) —— 钉死在 0/1 的死族没有信息流）、活动度，
1,998 族筛得 1,404 合格。二、事前经济映射：只读引入 Alpha-Data 扩展轮 P1 的
tier registry（166 对、8 主题，验证只用外部 ETF 证据从未接触期货收益），以
声明先验形式标注菜单，不过滤。三、分层轮换菜单（menu-v2）：每轮 30 项 =
4 先验 + 3 安慰剂 + 8 头部 + 15 轮换；有意设计的层先认领（安慰剂族常在成交量
前列，让 top 先挑会吃掉配额——实测形态）；轮换确定性（同轮重放同菜单），
轮次间零重叠，长期覆盖全部合格族。评价侧配惰性装载（LazyPMSeries：
首次引用某合格族时按 family 过滤读全量表，不合格族即使被引用也不装载）。
刻意不做：按历史成绩调菜单（决定 0006 封的门）；先验过滤（证伪机会留给模型）。

M12.1（run20 事故三连修）：run20 第 2-4 轮 provider 三次 900s 超时触发
provider_unusable 保护性停机（行为正确），但暴露三处：束段与 finally 归档的
project 均为 strict=True，被停机留下的半途 Study 炸掉 —— 归档为崩溃而生却在
崩溃现场先崩，且掩盖原始异常；两处改 strict=False（半途 Study 是常态不是账本缺口，
与 /api/live/projection 的 503 修复同一论断）。超时 900s 卡在实测思考时长分布
中间（run14 实测 11 分钟思考），提为 1800s。run21 重启。

M12.2（B7：underpowered 不进束）：run22 收尾的自动封存把封条烧在 run13-study-1 上 ——
该 Study 发现段仅 10 行观测（判 underpowered），|t|=3.17 与 IC=0.72 无统计含义，
但束只挡「无取值」不挡「样本不足」，假奖励 +0.63 进榜；封存段 405 行还原形
（t=1.617、IC 0.036、置换 13% 未通过）。修：demo 侧 offer 前过滤 underpowered ——
null/blocked/candidate 都过了样本闸门，t 值可比，照旧进束。

M13（信号侧事前筛，prescreen-v1）：run22 十六条 null 的主要形态是 exceed 0.9+ 的
持续性构造 —— 在决策节奏上几乎不动的信号（长窗水平类），块置换对它没有分辨力，
读 outcome 只能得到一条注定的 null 并抬高地板。该性质只依赖特征值本身，
可在读 outcome 之前判定：signal_power()（不读任何标签）按 AR(1) 折算有效独立观测
n_eff = n(1−ρ)/(1+ρ)，n_eff < 30 或互异值 < 3（防退化；主责在 n_eff，定 10 会误伤
十分位 rank，实测夹具即中招）→ blocked，不读、不占分母、地板不抬。
同时把置换检验的机理与事前筛写进提案器上下文（evaluation_mechanics）——
这是预注册规则的方法说明，不是任何结果的泄漏。事件 signal_prescreen 记录每次
筛查的统计量（含通过者），合同测试钉住「拦下者不动分母」。

M14（事件条件研究计划，决定 0008）：146 个构造证明「永远在线的线性检验」问题族
无信号后，把问题换成对着 PM 长处提问 —— 事件窗口。Proposal 契约新增 event_trigger
（field/lookback/min_abs_move，进 content id），触发只用严格早于边界的分桶
（PIT 合同测试钉住右端点排他），不活跃时点按预注册排除不读 outcome。
run_service_demo 与 CLI 增 --family：事件程序用独立问题族，分母从零、地板从 0.798
起，旧族账目原样保留（分账纪律同 Alpha-Data 主族/扩展族）。

M14.1（B8：束按族过滤）：run23（事件族）收尾的束全是旧族老面孔 —— 投影含账本
全部 Study，束不筛族，把封条烧在旧族的 pm_iran_belief_jump_studentised_range 上
（旧族 |t|=3.25、奖励 +0.62 的候选形态；封存段 t=0.413，保持率 12.7%，sealed_failed
—— 裁决按规格记账有效，第四个被封存段否决的候选）。修：束构建以 evaluation_result
载荷的 family 为准过滤。run23 本身：20 轮、19 null、触发器采用 19/19（iran 17 版，
集中度过高）、最好 |t|=1.73 对收盘地板 2.169 —— 事件条件下 iran 窗口对 SC 仍无
线性可预测性。

M14.2（B9：评价证据的族标签写死）：_build_evaluation 把 family 写死为旧族，
事件族全部评价证据被贴错标签，按族过滤的束（B8 修复）一个成员都认不出 ——
run24 实测束为空、无封存。修：family 由调用方传入（run_service_demo 传 fam，
sealed_pass 同步增参）。run24 本身：20 轮、11 null + 3 underpowered + 4 blocked，
触发源铺开到 11 个互异族（多样化指令生效）；事前筛在生产首次开张，拦下两版
（n_eff 13.9 / 23.1），省两次预算。事件族 n=33、地板 2.381，最好 |t|=1.87。

M14.3（报告第四版，107 页）：编年补齐 run17-24（成本模型时代、菜单时代、事件族两轮）；
方法节新增 M12 三层菜单、M13 事前筛（n_eff 公式）、M14 触发器数学与分账纪律；
结果节新增事件族搜索曲线（独立地板）与四次封存否决共同判词；工程史补束四连修
（B6-B9，含 B9 族标签不可靠期的口径声明）与 provider 四课；结论二扩展为两种问题
形态、新增结论九（事件条件下结论不变）。修三处生成缺陷：封存载荷统计量嵌在
result.effects 下（表列全空）、插值百分比未转义（% 吃掉行尾 \\，级联 100 错 ——
v3 即潜伏，当时表现为静默丢字）、hero 表列宽。全部 Study 200 条、图 180 张。

M14.4（报告第五版，112 页：为零背景审计者重写入口与算术）：用户两次指出叙述过于抽象
（「指标是怎么定义的」「假设对面完全不了解背景」）。两处补齐：

一、新增 §1「给零背景读者」：Polymarket 与中国商品期货是什么、项目问什么、
为什么需要制度而非试几次（引旧系统 81 次爬山 2.40 对噪声期望 2.63）、一轮六步流程、
**十二个术语表**、四种判决释义、全文导读。审计者读完该节即可读懂全文。

二、新增 §5「一条特征的完整算术」：取 run16-study-3 在 2024-01-26 08:59 决策时点，
三层逐位展开 ——（信号侧）三个 PM 小时桶 0.04/0.05/0.21948 → p̄=0.10316009 →
七步 DAG 逐步取值（含模型用 p̄ ÷ 1/(1−p̄) 绕行表达乘法）→ 残差化 85/90 对样本、
β̂=0.089024、α̂=0.513978 → 信号 −0.00091809，与解释器记忆表逐位一致；
（标签侧）日盘三段 74+59+89=222 个对数收益、Σr²=3.7173e−5、RV=0.006096934357，
与账本逐位一致 —— 并演示把三段并作一段会得 0.006538（偏高 7.2%），
说明「跨段不产生收益」不是形式主义；（回归侧）37,245 候选行 → 22,322 预注册排除 →
14,923 入回归，β̂=0.0041296、V=8.8388e−7、SE=0.00094015、t=4.392535，
附 Kish n_eff 与全部诊断。末段做量纲换算：一个标准差信号（sd=0.0704）对应 RV 变化
0.000291，占典型 RV 0.008516 的 3.4% —— t 大不等于经济上大。
另补字段字典（pm p/notional/trades、commodity_bar、intl 各自的含义与单位）。

M14.5（报告第六版，116 页：结构重排）：用户指出方法类内容散落、要有大白话结论、
结果被编年压到 99 页后。重排为「主文 21 页 + 附录 95 页」：

一、新增 §2「核心要点：八句话与它们背后的数据」——每条一句白话 + 支撑数据 + 交叉
引用（不设防搜索必然发现噪声 / 减掉已知后新东西消失 / 四候选全死终审 / 换问法答案
不变 / t 大不等于效应大 / 搜索有价格 / 否定是产出 / 方法被事故打磨）。数字全部占位
注入（N_OLD/FLOOR_OLD/TOP_T/N_NULL/EVENT_N/EVENT_FLOOR），与快照同源。

二、方法归拢为单节 §4（十二小节）：设计原则（原「动机」整节并入）、流水线、全部
统计量、事前筛、事件条件形态、菜单三层、封存段，并新增 §4.12「方法的迭代：哪次
事故催生了哪条规则」十一行对应表 —— 方法演化本身成为报告内容。

三、编年（23 小节、180 图、约 80 页）整体迁往附录 B，一字不删；结果从第 99 页
提前到第 16 页，结论第 20 页。零编译错误、零未定义引用。

M14.6（报告第七版，117 页：对抗性评审入册）：按用户指示生成持全部上下文的 Fable
评审代理做对抗性检查（每条断言须读码/读数核实）。评审返回 12 条核实主张，核心判定：
**方法的边界先于市场的真相被触到** —— 实际检验的切面（session 级、线性、单控制、
无先验地图）恰好避开了先验证据最强的三块地：休市吸收目标仅用 2/200 次（先验相关
0.86）、前身 2,742 项检验的四个阳性种子从未进提案器（含 tension→波动的负号，而本系
统 rv 提案几乎全为 +1）、t=5.0 的截面暴露度框架被两个原语缺口恰好卡死。另有反向
发现：地板不偏严（同族信号平均 |ρ|=0.097，独立性近似成立——不要往放松标准找出路）；
实质数据缺陷两处（族序列稀疏：主力族 21-34% 天数无桶、hero 面板 60% 行被排；
negRisk 2024 大选期 2,873 市场无成交，回爬需授权）；单控制残差可能残留共同因子，
与四次封存否决的形态一致。报告新增 §9 全文收录，摘要与要点（第九条）同步，
下一步重排为两梯队（第一梯队三件合计约两张票：吸收目标提升、先验种子喂入、
多控制残差化——是检验「市场真相还是方法边界」的最短路径）；
评审明确不建议做的（tick 分钟管道）也如实入册。

M15（决定 0009：评审第一梯队开工）：吸收目标升 primary（前身唯一强阳性形态不再被
kind 字段劝退）；residualise 支持 1-3 个互异控制（单控制路径逐位不变保可复现，
多控制正规方程+高斯消元，解释器与生成码逐位一致有合同测试）；先验四种子经方向
通道喂入 run25。FEATURE_SPEC_VERSION/INTERPRETER_VERSION 0.5.0。

M15.1（run26 结算：评审最短路径检验完毕，归因偏向市场真相）：run25 因方向文本
含效果词被盲化三拦作废（人写指令不豁免，系统按设计工作）；改词后 run26 二十回合
出十五版：吸收目标被采纳 10 次（±1 两方向）、brent+own_rv 双控制残差化 14 次
（正规方程路径首次生产使用），14 null + 1 blocked（cluster 结构退化），最好
|t|=2.31（sc_ret_next_session，低于其预注册证否线 2.85），吸收目标侧最好 1.83。
前身 0.86 的休市吸收相关在七倍样本上未再现。旧族分母升至 135（地板 2.8622）。
报告第八版 127 页：摘要、要点第十条、结论第十条、§9 后记、下一步第一梯队标注
完成状态、run25/run26 编年入册。第一梯队唯一未做项：稀疏族延用末值语义
（需先出决定文档）。

M17（决定 0010：研究员进程封闭化、方法说明显式装载、搜索覆盖表）：核查「claude -p
用得好不好」时实测到一个结构性漏洞 —— 默认调用给盲化研究员 Bash/Read/Write/Edit/
Task/WebSearch 与全部 MCP 服务器，工作目录即仓库根，原理上可自行读取账本的全部判决；
用户级 CLAUDE.md 也在进上下文。两条通道都在 assert_blinded 的射程之外。过去是否
被用过无法追认（provider 不记 num_turns 与 tool_use）。处置：四个封闭参数
（--disallowed-tools 37 项、--strict-mcp-config、--disable-slash-commands、
--setting-sources ""），并以 CLI 自己的 init 回报做断言（清单会过期，断言不会），
num_turns 与 tool_use 入证据。方法说明改为显式装载：configs/skills/arad-proposer.md
经 assert_blinded、内容寻址、作为 ProviderRequest.system_prompt（该字段进 request_id）
发出，指纹入账本；frontmatter 的 update_rule 必须是 mechanical_failures_only，
否则拒绝装载 —— 它只承载机械失败的教训，承载判决即成为结果回流通道。
搜索覆盖表（只数 proposal_locked，不含任何判决）进上下文，回答「为什么只看伊朗轴」：
196 条提案里 119 条 sc_dominant_t1、只用过 3 个 target、1998 族只引用过 23 个，
单个组合 cand:iran×sc×rv 就有 34 条提案。菜单升 menu-v3 加机制族层（配额 6，
先认领名额），重合度裁断为「重放」的 ISR_IRAN 与 US_SHUTDOWN 被排除；
机制族资格筛只在 discovery 段统计（qualify-mech-v1，八族全过）。
另修：提示词 93% 是旧提案的机制叙述（633,755 字符 → 246,890），
只保留最近 12 条全文；27 条非 sc 的 Study 此前在账本里记着 sc 的目标名，
现改为声明名与逐品种实解名并列。

M18（决定 0011：机制先验族的统计账与广度形状）：用户委托裁定两问。其一，机制族
提案**新开族 sc_mechanism_prior_v1**（否决并入事件族：把常在线性检验并进由
event_trigger 定义的族，族的定义会退化成一个日期；否决留旧族：五族的词汇前身
历史引用 0/0/0/76/32 次且重合度判「不可区分于无关序列」，135 次极大值从未在
这些候选上取过）。正当性以五条约束买下：重合度闸门已证、花名册以内容指纹闭合
（五族 + 三目标族 + 七原语，运行期不得增补）、预算预注册（20 回合，证否线取
预算末地板 E2(20)=2.1895 而非轮内早期低地板）、每条评价与每张卡双地板并印
（family_floors：族地板 + 合并地板）、同机制×目标跨族双计。HOUTHI（部分重合
0.703）属旧族账户，新族运行菜单不含它（admit 按运行族收窄）。其二，广度**面板
与逐品种并存**，选择权在提案器的机制文本：面板=一次检验（时间变异识别，反号
机制会自我抵消须拆品种）；逐品种每条一次检验、品种须由传导通道论证；分母爆炸
不再威胁旧账（新族自付）；「先面板后择优」被 0006 盲化结构性挡住。连带修复：
封条加地板门 —— 束按 reward 收人而新族早期 E2(1)=0.80，不加门会把一次性封条
烧在 |t|=1.5 的弱构造上（B7 同形，经低分母而非低行数）；sealed_pass 只对越过
本族当前地板的成员开封，挡下者如实入账。第四本账的请求默认拒绝。

M18.5（run28 结算与报告第九版收尾）：机制先验族首轮跑满。19 版判决、统计分母 15：
13 null、5 blocked、1 candidate。19/19 条规格引用机制族（此前 196 条提案里机制族
出现 0 次），18 个互异品种（此前 119/196 挤在原油），五族全部用上。最好 |t|=2.028，
低于本族地板 E2(15)=2.0734，更低于预注册证否线 E2(20)=2.1895 —— 无一越线。
唯一 candidate（run28-study-12，加息路径构成受控分量 × 36 品种面板）闸门全过、
置换 exceed 0.000，但 |t|=1.353、自罚奖励 −0.589，封条地板门判定不予开封。
报告新增「candidate 不等于越过地板」一节，并明确写下**不因此改判据**：
看到不喜欢的结果之后再收紧判据，与看到不喜欢的 null 之后放松判据是同一种病；
若要改须在下一轮之前以决定文档预注册。机械失败对照：run26 三次 provider 修复
加一次解析失败（约四分之一回合），run28 为 0 与 0 —— 方法说明层的直接效果。
两处生产缺陷已修：(1) mech: 族不在惰性装载准入名单，run27 前三版因此全 blocked
（菜单与准入必须同源）；(2) 修复提示词回显模型原文，ic_dominant_t1 撞效果字段
前缀 ic_ 使一轮作废（改为剥掉 input_value 回显，模型自己的上一版输出不是结果）。
报告第九版 147 页、217 图，新增三节（机制族、进程边界、三本账）与机制族搜索曲线
（同时画本族地板与合并地板，兑现约束 4）。

M20（决定 0012：预注册方向进入评价机）：run29-study-4 是历史上第一条越过预注册证否线
的构造（|t|=2.5649 对 E2(45)=2.4933），核实发现斜率符号与其声明方向相反，机器仍判
candidate。根因：EvaluationRequest 里根本没有方向字段，direction 在提案锁定后就再没被
读过 —— 每份提案在 falsifiable_condition 里写下的符号判据从未被执行。全史 190 条有方向
且斜率非零的 Study 中符号相反 105 条（55.3%），与掷硬币无异，正说明该字段此前不起作用。
**本次改动的性质是让机器执行一条早已预注册的判据，不是收紧或放松标准**——这一区分决定了
它可以在一轮进行中实施。实现：declared_direction 进请求与 digest；符号相反追加阻断理由
direction_mismatch；失效表令其只使 candidate 失效（幅度小的反号读数本就是合法否定）；
反号且幅度大者归 blocked，不得改写为事后的相反假设（HARKing）。回溯投影（读取侧，
账本不回写，与决定 0007 同形）：candidate 由 4 降为 1，null 与 underpowered 不变，
blocked 由 38 升至 41；变化的三条是 run28-study-12、run29-study-4、run29-study-5，
全部为「声明 −1 实得正号」。唯一在方向核对下仍成立的 candidate 是 run29-study-2
（|t|=0.954），远在地板之下，属「闸门全过而效应微弱」。run29 在第 8 回合被停
（族分母 22），剩余约 22 个回合在修复后继续，预算与证否线均不变。

M23（决定 0013：第二批、机制子面板、两条经验零分布、封存段分母）：路由判据更正为
「区域搜过没有」而非「序列新不新」——实测 mech:BIRD_FLU 与 cand:flu 序数一致 1.000
（该词汇族 344 个成员里只有 10 个在 discovery 段有成交，恰好都是禽流感市场），
但 cand:flu 引用 0 次，旧族的极大值从没在这片区域取过。永久排除仍需「重放且前身测过」。
新增 mech_panel:<品种>+… 子面板 universe：一次评价覆盖多品种且品种维有变异因而候选可达，
是覆盖全部 51 个品种的唯一可负担形态（11 票对逐品种 51 票，且逐品种取不到 candidate）。
第二批花名册九族闭合，指纹 0660fdebe064ac97；US_ELECTION_2024（76 成员、覆盖 52.1%、
前身是介词族 cand:from 说明现有聚类里根本没有「大选」这个概念）与 BIRD_FLU 进新账，
HEZBOLLAH_LEBANON（前身 cand:israel 引用 17 次）归旧账，ISR_IRAN 两处都排除。
预算 40 票，证否线 E2(82)=2.7000（并如实记下：分账的门槛优势随预算增大而消失）。
两条经验零分布回答「确认模式的基准线怎么定」：置换切标签侧、decoy 循环平移因子侧
（保留标签的肥尾体制与因子的自相关，打乱会毁掉后者而后者正是伪迹主要来源）；
原印的四条构造对照（0.872/0.923/0.359/1.000 对 0.730/0.635/0.265/0.935）**无产出脚本、
已作废**，见决定 0013 §九；替换为账本逐条可复算的配对读数
（scripts/measure_empirical_nulls.py）：decoy 更严的占多数，符号检验显著，
但 39 次平移使单条比例的蒙特卡洛标准误上界达 0.080，可读的是方向一致性而非单对差值。
这与「我们数据的噪声比理论假设更容易碰出大读数」相容（实际 |t| 90 分位 2.03 对正态 1.51）。
decoy 只披露不作判据，不进统计分母，禁止用它给构造排序。封存段补记自己的分母：
已开 18 次、地板 E2(18)=2.1475，而封存段历史最大 |t| 仅 1.836 ——
连封存段自己的地板都没越过，这比「四次封存否决」更硬。停止规则预注册。

## M23 · run31 收官与报告第十版（2026-08-15）

决定 0013 的四十票跑完：三十七版判决（29 null、5 blocked、3 candidate），
三个回合未走到读取因而未消耗分母（盲化拦截一次、装配后无提案一次、
提案缺 feature_spec 一次），分母停在 79/82。十五次 provider 修复，
高于 run30 的两次：机械损耗并非单调下降，报告据此把「装置在变好」这句话
降格为「整体改善但非单调」。

覆盖：提案全部使用机制子面板，覆盖四十个品种；未读到的十一个全部是目标表
行数不足者，满行品种一个不剩。「覆盖全品种」在有足够历史可供检验这个意义上
已经完成。

三条 candidate 全部出自同一条机制轴（US_ELECTION_2024），符号与声明一致
（方向判据生效后的第一批），但 |t| 全部低于各自读取时刻的本族地板，
属「闸门全过而效应微弱」；且三条不是三个独立发现，当作三份证据会重复计数。
预注册停止规则三条中成立两条，因候选计数不为零而暂不触发；是否续投预算
属统计预算决定，由人裁断。

报告第十版新增四节（scripts/report_sections_v10.py），177 页。
该模块**不写死任何数字**，全部从 artifacts/manifests/ 读取，缺产物即报错 ——
这条纪律来自本轮发现的一次实际失败：先前流通的两组数字复算不出来，
因为它们出自临时计算而产物已不存在。重建报告即重算。

本轮改正的实质错误（详见决定 0012 §七至十、0013 §九至十）：
「既不收紧也不放松」是自利修辞（执行的判据确实收紧了）；run30 判决与方向
判据无关；「第一条越线」须区分当次族地板与批级预注册证否线；实测构造相关是
真的（先前那句「多半是抽样噪声」出自中位对均值的错误比较）；decoy 更严的
结论须按实测比例陈述并同印蒙特卡洛误差；作图脚本的族归属缺 run31 分支会把
旧族点数由 134 抬到 152；两处写死的「全史实测」已随时间变成假话，改为重算。
