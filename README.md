# ARAD

ARAD（Autoresearch on Alternative Data）是一个面向中国商品期货的持续因子研究系统：
以 Polymarket 与财联社新闻为另类数据研究源，以期货自身量价为正交性对照，
自主地提出、检验、注册、监控和替换预测因子，维护一个每个成员都带完整证据链的
Alternative Factor Inventory。

`LLM proposes; deterministic code disposes; every result becomes durable evidence.`

三层停止语义：Search Episode 可以结束；Study 必须形成
`candidate / null / underpowered / blocked / error` 之一的可审计判决；
Research Service 只能由人类暂停或关闭。

## 状态（plan-v1.0 已定稿）

- **[`Merge-Plan-2.md`](./Merge-Plan-2.md) 是 canonical plan**（决定 0002，经两轮
  交叉审查定稿）。与其他文档冲突时以它为准。
- 数据事实以 `artifacts/manifests/`（M1 机器 manifest）为最终权威。
- **M1 已完成并关闭**（Decision Map #3，含第二轮验收修复：空源阻断闸门、
  内容身份指纹、全分区 schema 审计、provisional 默认禁止、接缝 row-key 核验为零重叠）。
- **M2 已完成并关闭**（Decision Map #4，#5 的时间侧）：SC 窄切片 Temporal Spine，
  909 交易日、3.44 亿 tick、848 万根 1min bar、t-1 主力视图、两个已登记目标与
  30 点人工回放清单。
- **M2.5 已完成并关闭**：Polymarket label-blind 全史普查（8.56 亿笔）与 PIT Market
  Index（市场与资产两级点时化身份，存在性与流动性资格分离）。`cn_registry_v3.parquet`
  已弃用并隔离。
- **M3 已交付**：证据账本（SQLite 追加式哈希链）、受保护评价机、durable queue。
- **M4 已交付**：Research Harness —— 特征规格语言、provider 适配（含真实 `claude -p`）、
  盲化上下文组装、反馈格式化、Search Episode 闭环。**M4.1** 补齐 `zscore` 原语。
- **M9 / M9.1 已交付**：Research Atlas 只读投影，以及 React 演化视图
  （指标沿谱系的走势 + running best + 选择零假设带）。
- 其后：**M5**（成本与容量模型、多元回归）。在成本模型建成之前，
  任何 Study 都不可能取 candidate —— 这是评价机的硬闸门。

## 怎么运行

环境（一次）：

```bash
uv venv && uv pip install -e ".[dev]"
```

以下命令都用 `.venv/bin/python -m arad.cli <子命令>`（本项目没有安装 `arad` 可执行文件）。

### 零、连续研究（一轮接一轮，直到边界或停滞）

```bash
.venv/bin/python -m arad.cli episode service --max-rounds 24
open artifacts/atlas_service/index.html
```

下一版由**变异**产生，方向由**盲化的语义诊断**给出，不靠任何写死的变体表。
停滞时写 `human_review_required` 并停下 ——「该不该继续找」是人的判断。

### 零点五、独立 app（看历史、并排比较、读因子卡）

```bash
.venv/bin/python -m arad.cli episode service --max-rounds 30 --run-id run_a
.venv/bin/python -m arad.cli atlas serve --runs runs --port 8770
open http://127.0.0.1:8770/
```

只读 API，只绑本机，没有任何写入路径（POST 一律 405，路径穿越在读取层挡掉）。
单文件那条路保留：`--out <目录>` 生成的 index.html 自带数据，不需要服务器。

### 一、跑一遍研究循环并出 Atlas

```bash
# 一条五版演化链：同一机制的连续变体，每一版由上一版的判决触发
.venv/bin/python -m arad.cli episode demo --provider lineage \
  --ledger data/ledger/lineage.db --queue data/ledger/lineage_q.db \
  --atlas artifacts/atlas_lineage

open artifacts/atlas_lineage/index.html      # 单文件，零网络请求，直接打开即可
```

`--provider` 三选一：

| 值 | 用途 |
|---|---|
| `mock`（默认） | 四种结局各一次：走完评价、原语缺口、解释器缺口、解析失败。用于看环路的完整形态 |
| `lineage` | 一条五版演化链。**演化曲线要看这个** |
| `claude` | 真实调用 `claude -p`（**花钱**），只跑一轮。默认 `--model claude-opus-5` |

前置：`data/spine/sc/target_sc_rv_next_session.parquet`（M2 产物）。没有它先跑
`.venv/bin/python -m arad.cli spine build`。

### 二、只从已有账本重渲 Atlas

```bash
.venv/bin/python -m arad.cli atlas render \
  --ledger data/ledger/lineage.db --queue data/ledger/lineage_q.db \
  --family demo_sc_price_volume --out artifacts/atlas_lineage
```

`--renderer static` 可退回服务端渲染的静态页（无演化曲线）。Atlas 只读账本，
每次渲染都重算整条哈希链，因此它同时是账本完整性的持续检验。

### 三、单独跑一个 Baseline Control

```bash
.venv/bin/python -m arad.cli study baseline      # SC 自身波动持续性，不计入另类因子库存
```

### 四、改前端后重新构建

`atlas-app/` 是 React 源码，构建产物随包分发在 `src/arad/atlas/app_shell.html`，
因此**渲染 Atlas 不需要 node**，只有改前端时才需要：

```bash
cd atlas-app && npm install && npm run build
cp dist/index.html ../src/arad/atlas/app_shell.html
```

### 五、验收

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest tests/ -q     # 当前基线：613 项通过
```

### 数据准备（只在首次或数据更新后）

```bash
.venv/bin/python -m arad.cli data-audit          # 三源只读扫描，出 manifest
.venv/bin/python -m arad.cli spine build         # SC Temporal Spine（重，约数十分钟）
.venv/bin/python -m arad.cli pm-index build      # Polymarket 普查与 PIT 索引（重）
```

源数据仓库**只读**；续爬、回爬与更新属于 acquisition 流程，需人类单独授权。

## 新会话开工指引（#12）

1. 完整阅读 `Merge-Plan-2.md`、`CONTEXT.md`、`docs/DECISION_MAP.md`；
2. 取 `docs/ENGINEERING_PROMPT.md`，把其中 `<CURRENT_TICKET>` 替换为
   `docs/tickets/M12-pm-semantic-mapping.md` 的全文，作为实现会话的任务提示词；
3. 环境：`uv venv && uv pip install -e ".[dev]"`；验收命令统一为
   `ruff check .` 与 `python -m pytest tests/ -q`（当前基线：613 项测试通过）；
   数据审计入口 `python -m arad.cli data-audit`，
   Temporal Spine 入口 `python -m arad.cli spine build|replay|verify`，
   Polymarket 普查与索引入口 `python -m arad.cli pm-index build|metadata-audit`
   （质量闸门失败时退出码非零）；
4. 约束提醒：来源数据仓库只读；数据获取（续爬/回爬/更新）属于 acquisition 流程，
   需人类单独授权；forward 段数据永不可读。

## 文档地图

| 文件 | 角色 |
|---|---|
| `Merge-Plan-2.md` | **canonical**：目标、裁决、M0 至 M9 路线（M9 为 Research Atlas 可视化交付层，决定 0003） |
| `CONTEXT.md` | 领域语言（权威） |
| `docs/DECISION_MAP.md` | 决策票与当前前沿 |
| `docs/ENGINEERING_PROMPT.md` | 建设期提示词模板（逐票替换 `<CURRENT_TICKET>`） |
| `docs/tickets/` | 工程票（M2、M2.5 已完成；当前 #12） |
| `program.md` | 运行期研究循环协议（M6 起生效） |
| `docs/00-material-analysis.md` | 材料审查快照（数据事实以 manifest 为准） |
| `docs/01-goal.md` | 最终形态与库存覆盖目标 |
| `docs/decisions/` | 决定记录（0002 为最新） |
| `artifacts/manifests/` | 三源机器 manifest 与审计报告（M1）、`sc_temporal_spine.json` 与 30 点人工回放清单（M2）、`pm_market_index.json` 与 `pm_metadata_audit.json`（M2.5、#12） |
| `docs/archive/` | 历史文稿与定稿评审记录（只读参考，见其 README） |

## 代码与依赖

- `src/arad/data_catalog/`：SourceManifest/Availability Contract schema、
  timeguard（时间单位与夜盘归属断言）、三个只读扫描器；
- `src/arad/temporal/`：交易日历、品种时段表、tick 归一化与 bar 物化、
  t-1 主力视图、as-of join、目标定义、Episode 与 purge/embargo、spine manifest；
- `src/arad/data_catalog/pm_census.py` 与 `temporal/pm_market_index.py`：
  Polymarket label-blind 普查与 PIT Market Index；
- `src/arad/registry/`、`src/arad/memory/`、`src/arad/evaluation/`、
  `src/arad/orchestrator/`：不可变规格与判决词表、证据账本与判决快照、
  受保护评价机与选择校正、durable queue；
- `src/arad/features/`、`src/arad/providers/`、`src/arad/harness/`：
  特征规格语言与解释器、模型无关的 provider（含 `claude -p`）、
  盲化上下文组装、反馈格式化与 Search Episode 驱动；
- `src/arad/atlas/` 与 `atlas-app/`：只读投影与 React 演化视图；
- `src/arad/cli.py`：`data-audit`、`spine`、`pm-index`、`study`、`episode`、`atlas`；
  `tests/contracts/`：613 项合同与回归测试；
- 依赖（`pyproject.toml`，`uv.lock` 锁定）：pydantic、pyyaml、pyarrow；
  开发依赖 pytest、ruff。Python 3.11 以上。

## 数据源（只读；覆盖以 manifest 为准）

| 源 | 位置 | manifest 实测覆盖 |
|---|---|---|
| 期货 tick（500ms 一档） | `/Users/xinyu/Code/AR-Polymarket/chinese-commodity` | 20221101 至 20260730，909 交易日，88 名义品种 |
| Polymarket 逐笔成交 | `/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/` | 2022-11-21 至 2026-07-14（两段，接缝已核验） |
| 财联社电报 | `/Users/xinyu/Code/AR-Polymarket/Crawler/cls-data/data/output/` | 2020-01-01 至 2026-06-18，894,220 行，零缺失日 |
