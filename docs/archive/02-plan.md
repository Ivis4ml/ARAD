# ARAD 工程实施计划（历史稿，规格出处）

> **状态（决定 0002）**：实施顺序与冲突裁决以 `Merge-Plan-2.md` 为准（窄切片
> tracer bullet 先行，本文的 Phase 顺序不再执行）。本文保留为 ETL 细节、
> 评价机规格与研究族设计的出处，供各工程票引用。
> 与 Merge-Plan-2 的已知口径差异：状态存储以 SQLite 为事务事实源（本文 registry
> 文件降为确定性导出）；样本治分中 2026-01 至 07 为 contaminated audit 段，
> 不能升级 Production；forward 资格按 per-Study 计算；来源仓库一律只读，
> 数据更新属于需单独授权的 acquisition 流程。
> 前置阅读：`docs/00-material-analysis.md`（事实快照）、`docs/01-goal.md`（最终形态）。

---

## 0. 目录结构

```
ARAD/
├── program.md                  # 研究循环的工程提示词（人类维护，智能体执行）
├── README.md                   # 项目入口与运行手册
├── docs/
│   ├── 00-material-analysis.md
│   ├── 01-goal.md
│   ├── 02-plan.md
│   └── decisions/              # 后续重要设计决定，一事一文
├── pyproject.toml              # uv 管理，依赖锁定
├── src/arad/
│   ├── data/                   # 数据层：加载、日历、合约参照、点时接口
│   │   ├── etl/                # 一次性 ETL 脚本（tick→bar、tape 拼接、新闻转 parquet）
│   │   ├── catalog.py          # 统一数据目录（路径模板，无硬编码绝对路径）
│   │   ├── calendar.py         # 交易日历与品种时段表
│   │   ├── contracts.py        # 合约参照（乘数、交易所、上市日）、连续合约
│   │   └── pit.py              # available_time 语义与点时读取接口
│   ├── eval/                   # 评价机（冻结区，研究循环只读）
│   │   ├── gates.py            # 五关判据
│   │   ├── power.py            # MDE、Kish n_eff、可行性预检
│   │   ├── stats.py            # HAC、块自助、影响点、家族记账与门槛
│   │   ├── xsec.py             # 横截面评价：RankIC、分位组合、换手与成本
│   │   ├── ortho.py            # 正交性引擎：相关、残差 IC、边际贡献
│   │   ├── noise.py            # 噪声底校准（随机因子、种子扰动分布）
│   │   └── bounds.py           # 经济上限登记表读取（未登记即 blocked）
│   ├── registry/               # 注册表读写（循环状态的唯一载体）
│   │   ├── features.py         # Feature Object 与生命周期状态机
│   │   ├── experiments.py      # 实验账本（全量，含失败）
│   │   ├── backlog.py          # 假设积压（提案写入，循环读取）
│   │   └── memory.py           # 判决记忆、覆盖判定（含数据增长重开条件）
│   ├── signals/                # 因子计算实现（研究循环在此写代码）
│   │   ├── baseline/           # 基线因子（动量、期限结构、持仓、成交量）
│   │   ├── polymarket/         # Polymarket 系因子
│   │   ├── news/               # 财联社系因子
│   │   └── lib.py              # 统一因子接口：f(date) -> 品种截面得分
│   └── proposer/               # 盲提案：功效账本构造与屏蔽断言
├── configs/
│   ├── economic_bounds.yaml    # 经济上限（事前登记，附推导）
│   ├── universe.yaml           # 品种池规则（流动性阈值、上市时点）
│   ├── splits.yaml             # 样本划分（冻结）
│   ├── costs.yaml              # 成本假设（分品种双边 bp）
│   └── contracts.yaml          # 合约乘数等静态参照
├── registry/                   # 循环状态（git 跟踪，人类可读）
│   ├── features/               # 因子对象，一因子一目录（spec.yaml + evidence/）
│   ├── backlog.jsonl           # 假设积压
│   ├── experiments.tsv         # 全量实验账本（对应 autoresearch 的 results.tsv）
│   ├── families.jsonl          # 实验家族与累计检验数
│   ├── memory.jsonl            # 判决记录（null/underpowered 含重开条件）
│   └── monitoring/             # 在役因子监控记录
├── data/                       # 本地数据（不入 git）
│   ├── bars/                   # tick 聚合产物（parquet，按品种×频率分区）
│   ├── polymarket/             # 统一 tape 与登记表（软链或复制自 Alpha-Data）
│   ├── news/                   # 财联社 parquet（按年分区，已剔前视字段）
│   └── reference/              # 日历、参照表产物
├── tests/                      # 评价机与数据层的回归测试（语义级）
└── scripts/
    ├── run_loop.sh             # 外部驱动（会话重启保护）
    ├── refresh_data.py         # 三源数据更新（期货 pull、PM 续爬、新闻回爬）
    └── holdout_judge.py        # 留出集裁决（独立于研究循环运行）
```

冻结区规则：`src/arad/eval/`、`src/arad/data/`、`configs/`、`tests/` 对研究循环只读；
研究循环可写的只有 `src/arad/signals/`、`registry/`、`docs/decisions/`。
该边界写入 `program.md` 并由 pre-commit 钩子核验改动路径。

---

## Phase 0：数据基座（预计工作量最大的阶段）

**目标**：三个数据源全部转为点时正确、可快速查询的 Parquet 层，配套参照表与回归测试。

### 0.1 期货 tick → bar ETL

输入 `/Users/xinyu/Code/AR-Polymarket/chinese-commodity` 的 66 个 zip（三种归档形态）。

- 统一处理：CP437/GBK 与 UTF-8 文件名解码；郑商所三位合约代码补世纪位；
  品种代码大小写规范化；空壳文件跳过并记录。
- 逐合约聚合为 1min / 5min / 15min / 日频 bar：OHLC、成交量增量（累计差分）、
  成交额增量（郑商所补乘数并做单调性修复）、持仓量水平与变化、买卖价差均值。
  集合竞价首行单独标记。会话切分依据品种级时段表（从数据实测，参考 Alpha-Data
  `sessions.py` 的三档夜盘边界）。
- 连续合约构造：从 `主力连续` 文件的 `InstrumentID` 列提取换月时点，
  比例复权生成连续序列；换月日收益标记 `roll`，原值保留。
- 日频衍生表：分时段收益（夜盘、隔夜跳空、日盘、收收），对应 ADAR 日线 schema 的
  六个收益列设计；期限结构表（同品种各挂牌合约的收盘价与持仓，计算斜率与展期收益）。
- 产物分区：`data/bars/{freq}/{product}.parquet`；一次构建后 zip 归档只读。
- 工程模式沿用 Alpha-Data 构建脚本的断点标记与输入指纹校验。

### 0.2 Polymarket tape 统一

- 统一 4 处类型冲突后拼接 `daily_aligned`（HF，至 2026-04-28）与
  `features/extension_tape/`（自爬，至 2026-07-14），验证接缝无重叠无缺口；
- 复制或软链 `cn_registry_v3.parquet`、`tier_registry.parquet`、钱包技能表；
- 续爬：用已验证的链上爬虫把 tape 推进到当前日期，并建立每周续爬任务；
- 可选高价值项（独立排期）：回爬 NegRisk Exchange 合约历史区块，
  补齐 2024 美国大选样本。

### 0.3 财联社新闻

- 2361 个 CSV 合并为按年分区 Parquet：拼接完整时间戳，展开 `Labels` 为规范化标签列，
  `Title`、`Content`、`Labels` 全部保留，**`Reads/Comments/Shares` 物理隔离**
  （前视污染，移出分析视图，原值存档）；
- 建标签 → 品种映射表（人工审定的静态 YAML：原油市场动态→SC/fu/lu，
  有色金属→cu/al/zn/ni 等，中东冲突→能源与贵金属，作为初版）；
- 回爬 2026-06-19 至今的缺口，并将 `cls_realtime.py` 纳入数据更新任务
  （今后的热度字段才可用）。注意：一切数据获取属于 acquisition 流程，
  需人类单独授权后执行，ARAD 研究侧不自动触发；
- `crawler_cls/data/output/` 重复副本（约 475MB）建议人工清理；
  ARAD 对来源仓库只读，不执行删除。

### 0.4 参照表与日历

- 交易日历：从 909 个交易日的实际集合生成，含节假日表；
- 合约参照：乘数（tick 数据反推并人工核对，郑商所必须手工登记）、交易所、
  最小变动价位、上市日期；四个待确认代码（bz/op/pd/pt）核实后登记；
- 品种池规则：以日均成交量与有效 tick 数动态筛选，排除 7 个空品种与极低流动性品种，
  新上市品种按首个数据日之后 60 个交易日才进入截面。

### 0.5 样本划分（冻结进 `configs/splits.yaml`）

```
discovery             2022-11-01 .. 2024-12-31   假设构建、参数拟合
historical validation 2025-01-01 .. 2025-12-31   历史时间外验证（最多产生 Candidate）
contaminated audit    2026-01-01 .. 2026-07-31   回归、防错、敏感性；不能升级 Production
forward confirmation  按 per-Study 资格计算        observation_time > max(协议冻结,
                                                 Study 冻结, 源快照) + embargo
```

**完成判据**：三源数据全部可用 DuckDB 在秒级查询；数据层回归测试通过
（含六陷阱各一条断言、点时语义断言、接缝完整性断言）；`refresh_data.py` 三条更新路径可运行。

## Phase 1：评价机（冻结的 ground truth）

**目标**：实现并冻结全部判决基础设施，对应 autoresearch 的 `prepare.py` 角色。

- 移植并适配：MDE 与 n_eff（ADAR `spec.py`）、HAC 回归与块自助与影响点
  （ADAR `overnight.py`）、五关判据（ADAR `endpoints.py` 语义）、
  分位分档与成本净边界（Alpha-Data `v3_quantile.py`）；
- 新建横截面评价 `xsec.py`：逐日 RankIC 与 HAC t、ICIR、分位多空组合、换手率、
  成本后净收益、视界衰减曲线（1/5/10/20 日）、子区间稳定性；
- 新建正交性引擎 `ortho.py`：与基线因子库及在库因子的相关矩阵（Pearson 与 Spearman）、
  残差化后的 RankIC、对既有因子组合的边际 ICIR；
- 新建噪声底 `noise.py`：随机截面因子与真实因子置换的指标分布，
  输出各指标的噪声分位数供判决引用；
- 实验家族记账 `stats.py`：家族注册、累计检验计数（按提案总数而非通过数）、
  Bonferroni 与 BH 双轨报告、门槛只升不降；
- 经济上限 `bounds.py`：读取 `configs/economic_bounds.yaml`，未登记标的即 blocked。

**完成判据**：语义级测试覆盖每个判决函数（含"伪重复必须被拦截"、
"全段统计量变换必须报错"、"建仓日夏普口径禁止"这类针对已知缺陷的反例测试）；
评价机 API 文档写入 `program.md` 附录；冻结后打 tag。

## Phase 2：注册表与记忆

**目标**：循环状态的唯一载体，产出即输入。

- Feature Object schema（YAML）：六要素 + 判决证据引用 + 生命周期状态；
- 实验账本 `experiments.tsv`：commit、假设 ID、家族 ID、终点、指标、判决、一句话描述
  （制表符分隔，含失败，不入 git 的部分只有大体积证据文件）；
- 假设积压 `backlog.jsonl`：提案的唯一入口与循环选题的唯一出口，
  字段含机制路径、终点、视界、预期方向、功效预估；
- 记忆 `memory.jsonl`：判决记录；`underpowered` 记录必须写明
  "重开条件"（所需样本量或数据范围），循环每轮开头核查是否有记录满足重开条件；
- 基线因子先行入库：动量（多窗口）、期限结构斜率与展期收益、持仓量变化、
  成交量异常、短期反转，各自完整走一遍五关流程（它们同时是流程的首次全面演练）。

**完成判据**：基线因子库建成且判决证据完整；注册表读写有测试；
一次人工模拟的完整 Study 生命周期走通。

## Phase 3：研究循环

**目标**：`program.md` 驱动的自主循环，外加会话与失败保护。

- `program.md`（见同名文件）：任务协议、可变边界、Study 生命周期、判决规则引用、
  NEVER STOP 段、继续路径清单、上下文节流规则；
- 盲提案子代理：主循环在积压少于阈值时，以"只含功效账本 + 失败档案摘要 +
  机制词表 + 数据目录"的提示词生成新假设批次，效应类数字物理不出现在提示词中
  （`assert_blinded` 在构造时断言）；
- 外部驱动 `run_loop.sh`：while 循环重启 Claude 会话，每次会话从注册表恢复状态；
  会话内目标为完成 1 至 3 个 Study；git 提交纪律沿用 autoresearch
  （先提交后运行，接受则保留，拒绝则回退，账本全量记录）；
- 上下文节流：回测输出重定向文件，只提取判决所需标量；
- LLM 与工具失败显式计数，写入账本备注列。

**完成判据**：无人值守连续运行 24 小时以上；期间完成至少 5 个 Study 且判决与证据齐全；
故意注入的三类故障（评价脚本报错、数据缺失、会话中断）均能恢复而非停止。

## Phase 4：挖掘战役（里程碑一）

**目标**：活性因子库达到 5 个 production 因子（判据见 `docs/01-goal.md` 第 3 节）。

建议的战役顺序（写入初始积压，此后由盲提案接管）：

1. **基线族确认**（Phase 2 已完成，作为正交性标尺）；
2. **闭市吸收条件化族**：把已证实的截面暴露度识别（RankIC 0.185/0.261）转化为
   可交易变体：开盘后延续、次日延续、按吸收不完全程度条件化；
3. **新闻标签族**：板块新闻强度、异常关注度、隔夜与盘前信息量，
   先做纯计数因子（无需语言模型），残差化对基线与 Polymarket 族；
4. **Polymarket 波动与风险族**（T5 类终点）：tension 对已实现波动的预测已有 t=−4.40 种子，
   扩展到品种截面；R3 尾部旗标按预约在 holdout 裁决；
5. **期限结构与持仓的交互族**：量价基线与替代数据的条件化交互
   （例如新闻强度高时的动量衰减）；
6. **知情流族**（探索档）：钱包技能条件化的概率创新，episode 口径。

每族独立记账。语言模型派生特征（新闻情绪打分等）按"派生数据集"纪律执行：
文档约束抽取、保存 prompt 与模型版本、时间截断防训练知识泄漏，且排在纯计数因子证明
残差价值之后。

**完成判据**：里程碑一达成；每个 production 因子的证据目录可独立审计；
战役报告（全部家族的检验总数、通过率、失败档案）生成。

## Phase 5：维护模式

- 监控任务：滚动窗口 IC、与库内因子相关性漂移、覆盖率、数据健康，写入
  `registry/monitoring/`；触发退化阈值后自动生成"衰减分解 + 替换评估" Study 进入积压；
- 前向裁决：`holdout_judge.py` 独立运行（不共享研究循环上下文），按预约日期裁决候选；
- 数据更新节律：期货每周 `git pull` 加增量 ETL；Polymarket 每周续爬；
  财联社每日实时采集加每周补爬校验；
- 每季度人工审查：判据是否需要收紧、经济上限是否需要修订（修订走 `docs/decisions/`）。

---

## 里程碑总览

| 阶段 | 交付 | 完成判据摘要 |
|---|---|---|
| Phase 0 | 点时数据基座 | 三源 Parquet 可秒级查询，回归测试通过，更新脚本可用 |
| Phase 1 | 冻结评价机 | 判决函数全测试，反例测试拦截已知缺陷模式 |
| Phase 2 | 注册表 + 基线因子库 | 基线因子完整走通五关，注册表读写可靠 |
| Phase 3 | 自主循环 | 无人值守 24h，故障恢复验证 |
| Phase 4 | 里程碑一 | 5 个 production 因子，证据可审计 |
| Phase 5 | 维护模式 | 监控、前向裁决、数据更新常态化 |

## 主要风险与对策

| 风险 | 对策 |
|---|---|
| ETL 工程量超预期（1.37 TB、六陷阱） | 先做 5 个品种的纵向切片打通全流程，再横向扩展 |
| 横截面框架下品种数偏少（约 50） | 截面与时序混合评价；分位数减为五档；家族记账吸收多终点 |
| 2026 上半年 holdout 的弱污染 | 污染标记随假设族传递；源自旧研究的族主要依赖 forward 段裁决 |
| 判据过严导致里程碑一遥遥无期 | 判据不放松；扩大提案的机制多样性与数据源覆盖；基线族保底 |
| 判据过松导致假因子入库 | 反例测试 + 噪声底 + 红队审查（判决前独立子代理证伪）|
| 智能体绕过冻结区 | pre-commit 路径核验 + 评价机结果哈希记录 |
| 单次 Study 耗时过长拖垮循环 | bar 层预聚合保证单次评价分钟级；超时即记 blocked 进账本 |
