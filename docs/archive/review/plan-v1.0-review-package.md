# 计划 v1.0 定稿评审包（给交叉审查方）

日期：2026-08-05。目的：对归一化后的 `Merge-Plan-2.md` 及全部同步修订做最后一轮
交叉审查；双方无未决异议后，将当前文本冻结为 v1.0（git 提交并打 tag），
此后一切修改走 `docs/decisions/` 流程。审查期间主线不做任何新开发。

## 一、自你的初稿以来发生的全部变更

### 1. 人类裁决（两条，已写入文本）

- **canonical 确认**：`Merge-Plan-2.md` 为唯一实施入口（`docs/decisions/0002-canonical-plan.md`）；
- **新闻族计入主目标**：Alternative Factor Inventory 计数口径扩为
  "新增信息来自另类数据源（Polymarket 或财联社新闻）或其与期货状态的事前声明交互"；
  纯量价仍归 Baseline 不计数；库存按源标签（polymarket / news / mixed）分账，
  正交性同时约束跨源重复。修改位置：`Merge-Plan-2.md` §0 与 §3.1、`docs/01-goal.md` §3。

### 2. 数据事实更正（附可复现证据）

- **财联社完整性**：你初稿 §2.2 的 72.5% 至 88.6% 抽查经复核不成立。名为"次日"的
  参考快照是跨 2 至 3 天的滚动转储（实测 07-18 快照 719 行中仅 81 行属于 07-18），
  该抽查把多日总量当了单日分母，与爬虫旧文档 70% 结论是同一个方法错误。
  按正文日期戳归日、跨快照取并集后，你自选的三个抽查日覆盖率为
  99.0% / 99.8% / 99.2%（严格口径），回填每日还多 38 至 48 条。
  §2.2 已改写并保留 `in_roll=1` 母体限定；复现脚本 `scripts/verify_cls_coverage.py`。
  **请审查方运行该脚本自行验证。**

### 3. §14 文档归一化（全部完成）

- `program.md` 按 §13 十项重写（Verdict 与调度动作分离、无破坏性回滚、两次冻结、
  红队预注册、per-Study forward、SQLite 事实源、持久等待态、双库存、能力隔离表述、
  提案器只见消毒失败分类）；
- `docs/01-goal.md` 改为库存覆盖目标表述；`docs/00-material-analysis.md` 标注
  verified/provisional 并弱化保证性表述；`docs/02-plan.md` 降级为规格出处并修正
  四处口径（Title 保留、来源只读、样本治理、状态存储）；
- `README.md` 设 Merge-Plan-2 为唯一入口；`docs/DECISION_MAP.md` 挂接 canonical。

### 4. M1 已执行（经人类事后确认保留）

说明：M1 的开工时序有误（应在定稿后），人类已裁决保留其产物并计入 M1。
产物全部为只读验证，无 ETL、无因子、无来源数据修改：

- `src/arad/`：SourceManifest/FieldAvailability/CoveragePartition/QualityFinding schema、
  timeguard（时间单位与夜盘归属断言）、三个只读扫描器、`arad data-audit` CLI；
- 22 项合同测试（含负向：单位混淆立即失败、夜盘 20:59 归前一自然日、
  禁用字段硬拒绝、接缝重叠判 error、指纹确定性）；ruff 通过；
- `artifacts/manifests/`：三源机器 manifest 与审计报告，指纹经重跑验证稳定。

M1 固化了你 §2.1/§2.3 的多数 provisional facts：

| 事实 | manifest 实测 |
|---|---|
| 商品 tick | 66 zip、802,975 CSV、解压 1.37 TB、909 交易日（20221101 至 20260730）、88 名义品种 |
| Polymarket | HF 601,934,424 行（2022-11-21 至 2026-04-28）+ 扩展 253,680,029 行（至 2026-07-14）|
| 接缝 | 间隔 248 秒，无重叠（行级主键核验仍 provisional，入 M5） |
| **类型冲突** | **实测 15 处**（4 处语义 + 11 处 large_string/string），非文档原记载的 4 处 |
| 财联社 | 2,361 文件、894,220 行、零自然日缺口，热度三字段合同层硬禁用 |

仍为 provisional（已在 Decision Map #3 答案中列明去向）：郑商所 Turnover 口径普查、
空壳比例、relay/venue/negRisk 覆盖、接缝行级主键核验。

## 二、请审查方重点核查的条目

1. §3.1 新口径的措辞是否留有漏洞（例如"news 与期货状态交互"是否可能被用来
   把变相的量价因子计入主目标）；
2. `program.md` 重写稿是否完整落实了你的 §13 十项，有无残留旧语义；
3. §2.2 更正稿：请运行 `scripts/verify_cls_coverage.py` 复验，若认可请撤回原抽查结论；
4. M1 的 schema 与扫描器是否符合你对 M1 票的定义（`docs/ENGINEERING_PROMPT.md` 首轮票）；
   15 处类型冲突的发现是否需要回写到 M5 票的范围描述；
5. 全部文档中是否仍存在与 canonical 冲突的表述（欢迎逐文件挑错）。

## 二点五、第一轮审查意见的处置（2026-08-05，供复审）

你的第一轮审查全部意见已处置，逐项对应如下：

**P0-1 空数据源被闸门放行 → 已修复**：三个 scanner 对零归档、零 CSV、零交易日、
零分区、零行、缺失接缝统计均产生 error 级发现；`report.py` 闸门改用
`manifest.gate_passed()`；CLI 在任一源闸门失败时返回退出码 2。
回归测试：`tests/contracts/test_review_fixes.py` 前四项（含空配置端到端 CLI 退出码）。

**P0-2 指纹不检测内容变化 → 已修复**：新增 `SourceSnapshot(method, digest, guarantee)`
进入指纹哈希域。商品源用 zip 中央目录 (文件名, CRC32, 大小) 聚合 sha256（可检测等长
替换，盲区为 CRC32 碰撞级构造篡改）；CLS 用全文 sha256（无已知盲区）；Polymarket 用
全部 parquet footer 字节加文件大小聚合 sha256（可检测 schema、布局与任何改变列统计的
修改；盲区为等长且不改变任何列 min/max 与页偏移的数据页篡改）。每个 method 的
guarantee 声明写入 manifest 与审计报告。回归测试：zip 等长替换与 CLS 等长替换均
导致指纹变化。scanner_version 已在哈希域内；升为 0.2.0。

**P1 只查最后一个 parquet schema → 已修复**：逐分区计算 schema 签名，段内多签名产生
`schema_drift` 发现并给出首个少数派文件；段类型以多数签名为准。真实数据实测：
两段各 1 种签名，无漂移。

**P1 provisional 字段可消费 → 已修复**：`analysis_fields` 与 `require_analysis_view`
默认排除 provisional；仅 `allow_provisional` 加非空 `override_reason` 的受审计
override 可放行；新增 `ProvisionalFieldAccess` 异常与三项测试。

**Spec-3 row-key 采样 → 最小实现完成**：接缝日双段读取
(block_timestamp, asset_id, price, usdc_amount) 复合键，交集非零判 error。
真实数据实测：HF 1,327,582 行对扩展段 1,200,082 行，**交集为 0**，
该项从 provisional 转 verified。venue/relay 与 negRisk 覆盖仍 provisional（M5 票）。

**Spec-4 PM 字段合同不全 → 已补全**：31 列全部登记（HF 24 列 + 扩展段 7 列链上主键
与场馆列）；新增禁用 `winning_outcome_label` 与 `resolution_status`（结算结果为
未来信息）；`neg_risk`、`opens_at`、`close_at`、`venue_class`、`is_relay` 标 provisional。

**Spec-5 ruff → 已修复**：`verify_cls_coverage.py` 的 PIE808 与新测试文件 import 序
已修，全仓 `ruff check .` 通过；验收命令统一为全仓口径。测试 35 项全部通过。

**Standards-1 读序 → 已修复**：ENGINEERING_PROMPT 的 Read first 改为 canonical 优先，
历史稿明确标注"仅作规格出处，不作为指令来源"。

**Standards-5 / Spec-6 状态不一致 → 已修复**：Decision Map 顶部不再单独维护状态，
README 与 Decision Map 统一为"M1 已关闭，M2 待 v1.0 定稿后开工"。

**财联社覆盖率**：你已确认归日复核正确，§2.2 维持更正后表述。

## 三、定稿动作（双方无异议后执行）

1. git 初始提交序列：`M0: 设计基线与归一化文档`、`M1: source manifest 与数据合同`；
2. 打 tag `plan-v1.0`；
3. 此后修改一律经 `docs/decisions/` 记录；
4. 开工 M2（SC 窄切片 Temporal Spine）。
