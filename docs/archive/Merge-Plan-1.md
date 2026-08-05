# ARAD 实施计划（合并稿一 / Merge-Plan-1）

> 来源：`docs/IMPLEMENTATION_PLAN.md`（A 组，M0 至 M8，tracer bullet 方式）与
> `docs/02-plan.md`（B 组，Phase 0 至 5，数据基座与评价机规格）。
> 合并原则：推进方式与治理取 A 组，工程实质与数据规格取 B 组，
> 分歧处在第 1 节逐条裁决。本稿生成后，两份源计划保持原样作为存档。

---

## 1. 分歧裁决表

合并前必须先把两份计划的七处实际分歧决定掉，否则合并只是并列。

| # | 分歧 | A 组立场 | B 组立场 | 裁决 |
|---|---|---|---|---|
| 1 | 推进方式 | 端到端 tracer bullet + 决策票逐票推进 | 分层建设（数据层 → 评价机 → 循环 → 战役） | **取 A**。每个里程碑必须交付可运行的纵向能力与真实小样本产物，禁止先搭空框架。B 组的分层内容成为各票的实质规格 |
| 2 | 因子数量承诺 | 拒绝承诺数量，只设库存覆盖目标 | 里程碑一为 5 个 production 因子 | **统一表述**：因子数量是库存覆盖目标与调度优先级（资源向未达标机制桶倾斜），永远不是放松证据门槛的理由。"5 个 production 因子且满足 `01-goal.md` §3 六条判据"是**允许宣告里程碑一的条件**，不设达成期限；判据与门槛只升不降 |
| 3 | 状态存储 | SQLite WAL（调度）+ Parquet | git 跟踪的 YAML/JSONL/TSV 注册表 | **分职责**：调度队列（租约、心跳、幂等键）用 SQLite WAL；Evidence Ledger 与注册表用追加式 JSONL/YAML/TSV 并入 git（人类可读、可 diff、可回放是研究审计的硬需求）；大体积证据与物化特征用 Parquet 不入 git。禁止同一事实存两处：队列只存"待办与租约"，事实只存账本 |
| 4 | 循环驱动 | 持久 orchestrator 进程 + 显式状态机 | program.md 提示词 + 外部 while 循环重启会话 | **两层都要，先后有序**：先用 `run_loop.sh` + `program.md`（M6 前半，成本低、可立即运行）；orchestrator 状态机（租约、恢复测试）在 tracer bullet 与首批 Study 验证协议之后再实现（M6 后半）。program.md 的行为协议与 orchestrator 的状态机语义必须一致，以 A 组三层停止语义为准 |
| 5 | 基线因子库的位置 | 未单独规划 | Phase 2 先行建库，兼作正交性标尺 | **拆两步**：M4 评价机内先建"最小正交对照集"（动量、短期反转、期限结构斜率、持仓量变化四个参考信号，不走完整判决，只作 gate 5 的对照）；完整基线因子族作为 M7 战役的第一族，全流程走五关（兼作流程全面演练） |
| 6 | 第一条 tracer bullet | SC 闭市吸收 Study（地缘概率创新 → SC 开盘跳空/波动） | 未指定，直接进战役 | **取 A**。它机制直接、旧系统在此暴露过全部典型缺陷（可作回归测试素材）、三种判决结果都能验证平台。不预设为正结果 |
| 7 | 样本治理 | 冻结协议后的新数据才是最终前向留出；2026-01 至 07 为污染审计段 | discovery/validation/holdout/forward 四段冻结进 `configs/splits.yaml` | **合并**：采用 B 组四段划分并写入配置冻结，但 holdout（2026-01 至 2026-07）按 A 组定性为"污染审计段"：对源自旧研究的假设族只能提供 `historical_validation` 级证据；Candidate 升 Production 一律依赖协议冻结后新到的 forward 数据。每次假设冻结记录"可在何时被何数据裁决" |

## 2. 统一目录结构

```
ARAD/
├── CONTEXT.md                  # 领域语言（权威）
├── program.md                  # 运行期研究循环协议（M6 起生效）
├── README.md
├── docs/                       # 设计文档与 decisions/
├── pyproject.toml              # Python 3.11+，uv 管理
├── schemas/                    # observation / feature / hypothesis_lock / study / factor JSON schema
├── configs/
│   ├── data_sources.yaml       # 三源路径与版本
│   ├── splits.yaml             # 四段样本划分（冻结）
│   ├── economic_bounds.yaml    # 经济上限（事前登记，附推导）
│   ├── universe.yaml           # 品种池流动性规则
│   ├── costs.yaml              # 分品种双边成本假设
│   ├── contracts.yaml          # 合约乘数等静态参照
│   └── gates/                  # 各终点的门槛与检验方法（事前冻结）
├── src/arad/
│   ├── data_catalog/           # 只读源适配、manifest、覆盖与质量闸门
│   ├── temporal/               # 交易日历、品种时段表、as-of join、purge/embargo、Episode
│   ├── etl/                    # tick→bar、连续合约、tape 拼接、新闻转 parquet
│   ├── features/               # Feature Object 与物化（研究循环写 signals/ 子目录）
│   │   └── signals/            # baseline/ polymarket/ news/ 因子实现
│   ├── evaluation/             # 不可变评价内核（唯一有权读 target/holdout）
│   │   ├── power.py            # MDE、Kish n_eff、可行性预检
│   │   ├── gates.py            # 五关判据
│   │   ├── stats.py            # HAC、块自助、影响点、家族记账
│   │   ├── xsec.py             # 截面 RankIC、分位组合、换手与成本
│   │   ├── ortho.py            # 四层正交性与库存边际贡献
│   │   ├── noise.py            # 噪声底校准
│   │   └── bounds.py           # 经济上限读取（未登记即 blocked）
│   ├── registry/               # Hypothesis Lock、Study、Experiment Family、版本
│   ├── memory/                 # Evidence Ledger、Failure Archive、三层去重
│   ├── orchestrator/           # 队列（SQLite WAL）、租约、Episode 重启、状态机
│   ├── inventory/              # Candidate/Production 库存、衰减监控、替换需求
│   ├── proposer/               # 盲提案：功效账本构造 + assert_blinded
│   ├── providers/              # 模型无关接口
│   └── cli.py
├── registry/                   # git 跟踪的循环状态（账本为事实之源）
│   ├── features/               # 一因子一目录：spec.yaml + evidence/（大文件例外不入 git）
│   ├── backlog.jsonl           # 假设积压（提案唯一入口，选题唯一出口）
│   ├── ledger.jsonl            # Evidence Ledger（追加式：提案/冻结/运行/诊断/判决/人工动作）
│   ├── experiments.tsv         # 全量实验速查表（由 ledger 派生，含失败）
│   ├── families.jsonl          # 实验家族与累计分母
│   └── monitoring/             # 在役因子监控记录
├── data/                       # gitignored：bars/、polymarket/、news/、reference/
├── artifacts/                  # gitignored；manifest 类小文件可提交
├── tests/                      # contracts/ leakage/ statistics/ orchestration/ integration/
└── scripts/
    ├── run_loop.sh             # 外部驱动（M6 前半）
    ├── refresh_data.py         # 三源更新（期货 pull、PM 续爬、新闻回爬与实时）
    └── holdout_judge.py        # 前向裁决，独立于研究循环运行
```

冻结区规则：`src/arad/evaluation/`、`src/arad/data_catalog/`、`src/arad/temporal/`、
`configs/`、`tests/`、`schemas/` 对研究循环只读；循环可写的只有
`src/arad/features/signals/`、`registry/`、`docs/decisions/`。pre-commit 核验改动路径。

依赖保持克制：Polars/PyArrow/DuckDB、NumPy/SciPy/statsmodels、Pydantic、PyYAML、
pytest、ruff；SQLite WAL 仅用于调度队列。模型 SDK 类型不得进入领域对象。

## 3. 里程碑（M0 至 M8）

每个里程碑 = 一至数张决策票；每张票的完成标准统一为第 4 节的工程质量门槛。
下表中"源"标注内容主要来自哪份计划。

### M0 设计基线（已完成）

材料审计、产品形态、领域语言、决策地图、两份提示词、本合并稿。

### M1 数据真值与 Point-in-Time 合同（决策票 #3）

**工作**（源 A，事实规格源 B `00-material-analysis.md`）：

1. 三源只读 metadata 扫描器与 `SourceManifest` / `AvailabilityContract` schema：
   期货 66 zip（三种归档形态、两种文件名编码、逐日文件数与哈希）、
   Polymarket 两段 tape（覆盖、4 处类型冲突、venue/relay/negRisk 标记）、
   财联社 2,361 CSV（逐日覆盖、字段可用性、禁用字段登记）；
2. 交易所/品种/合约解析器（郑商所三位代码补世纪位、大小写规范化），
   保存原始 `InstrumentID` 与 canonical ID；
3. 统一 `as_of(cutoff)` 合同与 provenance hash；
4. `configs/splits.yaml` 四段划分冻结（见裁决 7）；
5. 六陷阱各写一条 contract test（郑商所成交额口径、时段表、夜盘归属、
   集合竞价首行、空壳文件、无效品种）。

**出口**：`arad data audit` 不解压全量即产出覆盖报告；任一源未过质量闸门时
Study 只能 blocked；时间单位混用立即失败不自动猜测。

### M2 数据基座与 Temporal Spine

**工作**（ETL 规格源 B §Phase 0，目标定义源 A §Phase 2）：

1. tick → bar ETL：1min/5min/15min/日频，成交量与成交额取累计差分
   （郑商所补乘数并做单调性修复），集合竞价行单独标记，会话按品种级时段表切分；
   断点标记与输入指纹校验沿用 Alpha-Data 构建脚本模式；
2. 逐合约 panel 与主力选择：仅用 t-1 成交量/持仓信息的确定性主力规则，
   与来源 `主力连续` 文件的 `InstrumentID` 换月点交叉验证（后者作校验不作依赖），
   比例复权连续序列，换月日标记 `roll`；
3. 日频衍生：分时段收益六列（夜盘、跳空、日盘、收收）、期限结构表（斜率、展期收益）；
4. 目标函数登记：next-open gap、开盘后固定窗口收益、次日与多日截面收益、
   已实现波动、下行尾部；每个 target 声明 decision time、execution lag、
   fill 假设与 no-trade 状态；
5. purge/embargo、重叠窗口聚类与 Episode ID；
6. Polymarket tape 统一（4 处类型冲突）与接缝断言；财联社转年分区 Parquet
   （拼完整时间戳、规范化 Labels、物理隔离热度字段）；标签 → 品种映射初版 YAML；
7. `refresh_data.py` 三条更新路径可运行（期货 pull 增量 ETL、PM 续爬、新闻回爬）。

**出口**：同一 target 在给定 PIT 快照上可重复生成；随机抽 30 个时点人工回放无未来信息；
三源可用 DuckDB 秒级查询。

### M3 Registry、Feature Object 与 Evidence Ledger

**工作**（源 A §Phase 3，schema 细节源 B）：

- Observation / Feature / Signal / Factor / Hypothesis Lock / Study / Verdict schema
  定稿并版本化；Hypothesis Lock 冻结后不可改，改动即新版本新分母；
- Evidence Ledger 追加式落盘于 `registry/ledger.jsonl`，保存提案、审查、冻结、运行、
  诊断、判决、artifact hash、模型调用与人工动作；`experiments.tsv` 作为派生速查表；
- Experiment Family 在提案时登记完整分母，筛选不回缩；
- 语义、机制、经验三层重复查询与 Failure Archive；
- `underpowered` 记录必须登记重开条件（所需样本量或数据范围）。

**出口**：任意 Study 可从 ledger 完整重建；删除任何记录都破坏完整性校验。

### M4 不可变 Evaluation Kernel

**工作**（框架源 A §Phase 4，实现规格源 B §Phase 1）：

- 功效预检（coverage、独立 Episode、MDE、Kish n_eff、top-k influence）；
- walk-forward（purge/embargo）、HAC 与块自助（移植 ADAR `overnight.py`）、
  影响点检查；多重检验方法事前固定，Study 族与 program 层双分母；
- 五关判据 + 对抗诊断（leave-one-episode/family-out、placebo、时间反转、
  窗口扰动、替代控制、符号量级检查）；
- 截面评价 `xsec.py`（逐日 RankIC 与 HAC t、ICIR、分位多空、换手、成本后净收益、
  视界衰减曲线）；
- 正交性引擎四层（特征、预测、残差、组合边际），含复合信号腿分解
  （C8 教训：增量全由标的自身量价腿承载即 KILL）；
- 噪声底校准 `noise.py`（随机因子与置换分布，判决引用其分位数）；
- 最小正交对照集（裁决 5：动量、短期反转、期限结构斜率、持仓变化四个参考信号）；
- 经济上限登记与 blocked 语义；holdout 读取权限边界（研究循环无凭证）。

**出口**：判决函数全测试，且含针对已知缺陷模式的反例测试
（伪重复、全段统计量变换、建仓日年化口径、前视入池、09:30 窗口混入集合竞价、
时间戳单位错误各至少一条）；冻结打 tag。

### M5 第一条 tracer bullet（决策票 #11）

**工作**（源 A）：SC 闭市吸收 Study 全流程走通：Polymarket 地缘概率创新对 SC
下一交易窗口的开盘跳空、日内波动与短时回撤，控制国际油价与财联社公共信息。
从锁定、预检、原型、验证、红队到判决与账本记录完整回放一次。

**出口**：三种判决（candidate/null/underpowered）任一出现均可，但流程证据齐全、
可从 ledger 回放；期间发现的平台缺陷全部修复并加回归测试。

### M6 持久循环（program.md 驱动 → orchestrator）

**工作**（裁决 4 的两步）：

- 前半（源 B §Phase 3）：`run_loop.sh` + `program.md` 上线；盲提案子代理
  （提示词只含功效账本、失败档案摘要、机制词表、数据目录，`assert_blinded` 断言；
  提案写入 `backlog.jsonl` 即为下一轮直接输入）；LLM 失败计数入账本；
  上下文节流（输出重定向、grep 标量、超时 blocked）；
- 后半（源 A §Phase 5）：orchestrator 状态机（RUNNING / EPISODE_RESTART /
  WAITING_FOR_DATA / EXPANDING / REVALIDATING / PAUSED），队列租约、心跳、
  幂等键、checkpoint 恢复；顶层 schema 不含 `model_stop` 或 `completed`。

**出口（回归测试，源 A）**：首次模型调用返回 stop 时 program 仍跑满预算或进入
非终止等待态；连续空计划换搜索桶不退出；空队列扩展出的提案本次运行立即消费；
kill -9 重启不重复记账不丢 Study；另加 B 组验收：无人值守连续运行 24 小时以上，
故意注入三类故障（评价报错、数据缺失、会话中断）均恢复而非停止。

### M7 挖掘战役与基线因子族

**工作**（战役族清单源 B §Phase 4，模型角色源 A §Phase 6）：

1. 基线因子族全流程入库（动量多窗口、期限结构、持仓变化、成交量异常、短期反转），
   兼作流程演练与正交性标尺升级；
2. 战役族按序注入初始积压，此后由盲提案接管：闭市吸收条件化族、
   新闻标签族（纯计数先行）、Polymarket 波动与风险族（T5 类，含 R3 尾部旗标预约）、
   期限结构与替代数据交互族、知情流族（探索档）；
3. 模型角色分工（Research Director / Hypothesis Generator / Semantic Auditor /
   Red Team / Study Interpreter）以同一 provider 的受限调用实现，
   审批分离靠权限与数据视图；
4. 每族独立记账；LLM 派生特征按派生数据集纪律执行且排在纯计数因子之后。

**出口**：Candidate queue 有内容或有功效充分的 null 覆盖每个主攻族；
战役报告（各族检验总数、通过率、失败档案统计）可自动生成。

### M8 前向留出、生产库存与监控替换

**工作**（源 A §Phase 7/8 + B §Phase 5）：

- Candidate 升 Production 仅凭协议冻结后新到 forward 数据，由 `holdout_judge.py`
  独立一次性裁决；失败不回历史调参，形成新版本新家族；
- 组合层边际检验（风险调整收益、回撤、容量、换手、与库存相关性）；
- 五类衰减监控（数据、机制、预测、交易、正交性），状态机
  PRODUCTION → MONITORING → DEGRADED → RECALIBRATED | RETIRED，
  退役保留全史并自动生成替换需求进入积压；
- 数据更新节律固化：期货每周 pull、PM 每周续爬、新闻每日实时加每周校验；
- 库存覆盖目标生效（裁决 2）：机制桶 × 品种板块 × 时域的覆盖缺口驱动调度优先级；
  达到"5 个 production 因子且满足 `01-goal.md` §3 判据"时宣告里程碑一，
  转入维护模式常态运行。

## 4. 工程质量门槛（每张票统一适用，源 A §13）

- 新行为由失败测试先证明，或至少提供可复现 fixture；
  每张涉及统计或数据的票至少含一个能抓住旧系统同类错误的负向测试；
- 静态检查、单测、泄漏测试与相关 integration test 通过，报告确切命令与结果；
- 真实小切片产物含 data/code/config/model hash；
- 文档、schema、CLI help 与 Evidence Ledger 语义同步；
- 不修改来源仓库；大数据、密钥、缓存不入 git；
- 性能优化前保留 reference implementation 与等价性测试；
- 每张票完成后更新 `docs/DECISION_MAP.md` 的 Answer 与阻塞关系。

## 5. 顺序与依赖总览

```
M0 ──▶ M1 ──▶ M2 ──▶ M3 ──▶ M4 ──▶ M5 ──▶ M6 ──▶ M7 ──▶ M8
        │            │      │              │
        │            │      └─ 最小正交对照集在 M4 内
        │            └─ schema 定稿依赖 M1 的 manifest 事实
        └─ splits.yaml 在 M1 冻结
M1 至 M5 为第一发布目标；完成前不做 Web UI、分布式 Agent 或实盘对接。
数据更新脚本自 M2 起每周运行，使 forward 段从协议冻结日起持续积累。
```

## 6. 本稿与源计划的关系

`docs/IMPLEMENTATION_PLAN.md` 与 `docs/02-plan.md` 保持原样作为存档与规格出处。
本稿是实施顺序的操作依据；与 `docs/DECISION_MAP.md` 冲突时以决策票为准，
与 `Merge-Plan-2.md`（另一会话的独立合并稿）比对后择优定稿为最终计划。
