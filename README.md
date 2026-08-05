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
- **下一步：M3**（最小 Research Kernel），工程票待撰写。

## 新会话开工指引（M3）

1. 完整阅读 `Merge-Plan-2.md`、`CONTEXT.md`、`docs/DECISION_MAP.md`；
2. 取 `docs/ENGINEERING_PROMPT.md`，把其中 `<CURRENT_TICKET>` 替换为 M3 工程票全文，
   作为实现会话的任务提示词；
3. 环境：`uv venv && uv pip install -e ".[dev]"`；验收命令统一为
   `ruff check .` 与 `python -m pytest tests/ -q`（当前基线：158 项测试通过）；
   数据审计入口 `python -m arad.cli data-audit`，
   Temporal Spine 入口 `python -m arad.cli spine build|replay|verify`
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
| `docs/tickets/` | 工程票（M2 已完成，M3 待撰写） |
| `program.md` | 运行期研究循环协议（M6 起生效） |
| `docs/00-material-analysis.md` | 材料审查快照（数据事实以 manifest 为准） |
| `docs/01-goal.md` | 最终形态与库存覆盖目标 |
| `docs/decisions/` | 决定记录（0002 为最新） |
| `artifacts/manifests/` | 三源机器 manifest 与审计报告（M1）、`sc_temporal_spine.json` 与 30 点人工回放清单（M2） |
| `docs/archive/` | 历史文稿与定稿评审记录（只读参考，见其 README） |

## 代码与依赖

- `src/arad/data_catalog/`：SourceManifest/Availability Contract schema、
  timeguard（时间单位与夜盘归属断言）、三个只读扫描器；
- `src/arad/temporal/`：交易日历、品种时段表、tick 归一化与 bar 物化、
  t-1 主力视图、as-of join、目标定义、Episode 与 purge/embargo、spine manifest；
- `src/arad/cli.py`：`data-audit` 与 `spine` 命令；
  `tests/contracts/`：158 项合同与回归测试；
- 依赖（`pyproject.toml`，`uv.lock` 锁定）：pydantic、pyyaml、pyarrow；
  开发依赖 pytest、ruff。Python 3.11 以上。

## 数据源（只读；覆盖以 manifest 为准）

| 源 | 位置 | manifest 实测覆盖 |
|---|---|---|
| 期货 tick（500ms 一档） | `/Users/xinyu/Code/AR-Polymarket/chinese-commodity` | 20221101 至 20260730，909 交易日，88 名义品种 |
| Polymarket 逐笔成交 | `/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/` | 2022-11-21 至 2026-07-14（两段，接缝已核验） |
| 财联社电报 | `/Users/xinyu/Code/AR-Polymarket/Crawler/cls-data/data/output/` | 2020-01-01 至 2026-06-18，894,220 行，零缺失日 |
