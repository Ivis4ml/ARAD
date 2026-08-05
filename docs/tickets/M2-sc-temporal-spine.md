# 工程票 M2：SC 窄切片 Temporal Spine

对应 Decision Map #4 与 #5 的第一部分；canonical 依据 `Merge-Plan-2.md` §10 的 M2。
使用方式：将本票全文替换 `docs/ENGINEERING_PROMPT.md` 中的 `<CURRENT_TICKET>` 后
交给实现会话执行。

## 范围（窄切片，不做全量）

- 品种：仅 SC（上海原油）及其构造主力视图所需的最少挂牌合约；
- Polymarket：少量地缘政治/能源类市场（从冻结的 `cn_registry_v3.parquet` 中选取，
  仅用其 admit_ts 与市场元数据，不读期货 outcome）；
- 控制数据：匹配时间段的财联社电报（走 M1 manifest 的分析视图，热度字段已禁用）
  与国际油价基准（`Alpha-Data/data/intl/`）；
- 时间范围：以 M1 manifest 的实测覆盖为准。

## 工作项

1. SC 合约解析与品种时段表：TradingDay 与自然日的还原（夜盘至次日 02:30 归属规则，
   复用并扩展 `timeguard.natural_date_of_tick`）、集合竞价首行标记、
   Volume/Turnover 累计量差分与重置检测；
2. 逐合约 panel 与 **t-1 信息主力选择**（只用前一交易日已知的成交量/持仓；
   来源 `主力连续` 文件仅作 QA 对照，不作依赖）、换月事件标记；
3. 最小物化：SC 的 1min 与日频 bar（Parquet，写 `data/` 下，不入 git），
   以及带 `available_time` 的 as-of join 接口；
4. 目标定义并登记：primary target 为决策 cutoff 后的下一 SC session 已实现波动；
   diagnostic-only target 为同期开盘跳空吸收（明确标注不作可交易 alpha 主张）；
   每个 target 声明 decision time、execution lag 与 no-trade 状态；
5. Episode ID、purge/embargo 与样本段污染标签
   （discovery / historical validation / contaminated audit，见 Merge-Plan-2 §4）。

## 不做

全品种 ETL、任何因子计算、任何 IC/回归、评价机、调度器、外部数据获取。

## 出口条件

- 同一 target 在给定 PIT 快照上可重复生成（指纹或哈希证明）；
- 随机抽取 30 个时间点的人工回放清单生成，逐条核验无未来信息，
  所有 feature 的 `availability_time` 严格早于 label 窗口起点；
- 合同测试覆盖：夜盘归属、午休不判中断、集合竞价行处理、累计量差分与重置、
  t-1 主力规则不读当日数据（负向测试：喂入当日数据必须报错）；
- 全仓 ruff 与 pytest 通过；Decision Map #4 更新 Answer。
