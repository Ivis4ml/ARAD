# SC Temporal Spine 人工回放清单（lg_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`154ba5c3dc783d0b7d1b49ccb453ce46386f45c9fa130e8ac17fb645eb169350`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. lg2507 20241211 day （discovery）

- Episode：`lg:20241211`
- 决策时点：`2024-12-11T08:59:00+08:00`
- 执行时点：`2024-12-11T09:01:00+08:00`
- label 窗口：`2024-12-11T09:01:00+08:00` → `2024-12-11T15:00:00+08:00`
- 目标值：0.00062247123 = ln(803.5 / 803)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-10T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-10T14:59:00+08:00', 'close': 804.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-10T15:00:00.025000+08:00` | 64739 | {'trading_day': 20241210, 'close': 804.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-11T08:57:18+08:00` | 102 | {'title': '', 'labels': '期货市场情报 原油市场动态'} |
| brent_last_close | intl_brent | `2024-12-11T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-10', 'value': 73.64} |

## 01. lg2507 20241220 day （discovery）

- Episode：`lg:20241220`
- 决策时点：`2024-12-20T08:59:00+08:00`
- 执行时点：`2024-12-20T09:01:00+08:00`
- label 窗口：`2024-12-20T09:01:00+08:00` → `2024-12-20T15:00:00+08:00`
- 目标值：0.020719815 = ln(829 / 812)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-19T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-19T14:59:00+08:00', 'close': 810.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-19T15:00:00.024000+08:00` | 64739 | {'trading_day': 20241219, 'close': 810.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-20T08:49:12+08:00` | 588 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-20T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-19', 'value': 73.75} |

## 02. lg2507 20250127 day （historical_validation）

- Episode：`lg:20250127`
- 决策时点：`2025-01-27T08:59:00+08:00`
- 执行时点：`2025-01-27T09:01:00+08:00`
- label 窗口：`2025-01-27T09:01:00+08:00` → `2025-01-27T15:00:00+08:00`
- 目标值：0.0022883305 = ln(875 / 873)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-24T15:00:00+08:00` | 237540 | {'bar_start': '2025-01-24T14:59:00+08:00', 'close': 870.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-24T15:00:00.047000+08:00` | 237539 | {'trading_day': 20250124, 'close': 870.5} |
| cls_last_telegraph | cls_telegraph | `2025-01-27T08:49:42+08:00` | 558 | {'title': '【两市融资余额减少111.69亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-01-25T06:00:00+08:00` | 183540 | {'quote_date': '2025-01-24', 'value': 78.71} |

## 03. lg2507 20250226 day （historical_validation）

- Episode：`lg:20250226`
- 决策时点：`2025-02-26T08:59:00+08:00`
- 执行时点：`2025-02-26T09:01:00+08:00`
- label 窗口：`2025-02-26T09:01:00+08:00` → `2025-02-26T15:00:00+08:00`
- 目标值：-0.00057954218 = ln(862.5 / 863)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-02-25T14:59:00+08:00', 'close': 867.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-25T15:00:00.030000+08:00` | 64739 | {'trading_day': 20250225, 'close': 867.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-26T08:56:29+08:00` | 151 | {'title': '【丰田将下调零部件制造商的钢材价格】', 'labels': '汽车大新闻 钢铁'} |
| brent_last_close | intl_brent | `2025-02-26T06:00:00+08:00` | 10740 | {'quote_date': '2025-02-25', 'value': 73.11} |

## 04. lg2507 20250311 day （historical_validation）

- Episode：`lg:20250311`
- 决策时点：`2025-03-11T08:59:00+08:00`
- 执行时点：`2025-03-11T09:01:00+08:00`
- label 窗口：`2025-03-11T09:01:00+08:00` → `2025-03-11T15:00:00+08:00`
- 目标值：-0.0034965071 = ln(856.5 / 859.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-10T15:00:00+08:00` | 64740 | {'bar_start': '2025-03-10T14:59:00+08:00', 'close': 862.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-10T15:00:00.035000+08:00` | 64739 | {'trading_day': 20250310, 'close': 862.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-11T08:57:10+08:00` | 110 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-03-11T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-10', 'value': 71.08} |

## 05. lg2507 20250313 day （historical_validation）

- Episode：`lg:20250313`
- 决策时点：`2025-03-13T08:59:00+08:00`
- 执行时点：`2025-03-13T09:01:00+08:00`
- label 窗口：`2025-03-13T09:01:00+08:00` → `2025-03-13T15:00:00+08:00`
- 目标值：0.011387597 = ln(839 / 829.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-12T15:00:00+08:00` | 64740 | {'bar_start': '2025-03-12T14:59:00+08:00', 'close': 834.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-12T15:00:00.042000+08:00` | 64739 | {'trading_day': 20250312, 'close': 834.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-13T08:53:32+08:00` | 328 | {'title': '【日本投资者上周净买入海外股票规模创纪录次高】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-03-13T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-12', 'value': 72.36} |

## 06. lg2507 20250425 day （historical_validation）

- Episode：`lg:20250425`
- 决策时点：`2025-04-25T08:59:00+08:00`
- 执行时点：`2025-04-25T09:01:00+08:00`
- label 窗口：`2025-04-25T09:01:00+08:00` → `2025-04-25T15:00:00+08:00`
- 目标值：0.0025157246 = ln(796 / 794)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-24T15:00:00+08:00` | 64740 | {'bar_start': '2025-04-24T14:59:00+08:00', 'close': 793.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-24T15:00:00.048000+08:00` | 64739 | {'trading_day': 20250424, 'close': 793.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-25T08:57:57+08:00` | 63 | {'title': '【苹果调整管理层 将机器人业务从AI业务中剥离】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2025-04-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-24', 'value': 67.5} |

## 07. lg2507 20250626 day （historical_validation）

- Episode：`lg:20250626`
- 决策时点：`2025-06-26T08:59:00+08:00`
- 执行时点：`2025-06-26T09:01:00+08:00`
- label 窗口：`2025-06-26T09:01:00+08:00` → `2025-06-26T15:00:00+08:00`
- 目标值：0.0042879086 = ln(818 / 814.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-06-25T14:59:00+08:00', 'close': 811.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-06-25T15:00:00.006000+08:00` | 64739 | {'trading_day': 20250625, 'close': 811.0} |
| cls_last_telegraph | cls_telegraph | `2025-06-26T08:51:03+08:00` | 477 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-06-26T06:00:00+08:00` | 10740 | {'quote_date': '2025-06-25', 'value': 68.4} |

## 08. lg2507 20250627 day （historical_validation）

- Episode：`lg:20250627`
- 决策时点：`2025-06-27T08:59:00+08:00`
- 执行时点：`2025-06-27T09:01:00+08:00`
- label 窗口：`2025-06-27T09:01:00+08:00` → `2025-06-27T15:00:00+08:00`
- 目标值：0.002444989 = ln(819 / 817)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-26T15:00:00+08:00` | 64740 | {'bar_start': '2025-06-26T14:59:00+08:00', 'close': 818.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-06-26T15:00:00.046000+08:00` | 64739 | {'trading_day': 20250626, 'close': 818.0} |
| cls_last_telegraph | cls_telegraph | `2025-06-27T08:49:19+08:00` | 581 | {'title': '【两市融资余额增加91.48亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-06-27T06:00:00+08:00` | 10740 | {'quote_date': '2025-06-26', 'value': 68.57} |

## 09. lg2509 20250731 day （historical_validation）

- Episode：`lg:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.0036452045 = ln(821.5 / 824.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 64740 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 825.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250730, 'close': 825.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 10. lg2509 20250812 day （historical_validation）

- Episode：`lg:20250812`
- 决策时点：`2025-08-12T08:59:00+08:00`
- 执行时点：`2025-08-12T09:01:00+08:00`
- label 窗口：`2025-08-12T09:01:00+08:00` → `2025-08-12T15:00:00+08:00`
- 目标值：-0.01085656 = ln(824.5 / 833.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-11T14:59:00+08:00', 'close': 832.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.004000+08:00` | 64739 | {'trading_day': 20250811, 'close': 832.5} |
| cls_last_telegraph | cls_telegraph | `2025-08-12T08:52:43+08:00` | 377 | {'title': '【德国7月破产企业数量同比大幅增加】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-11', 'value': 67.36} |

## 11. lg2511 20250925 day （historical_validation）

- Episode：`lg:20250925`
- 决策时点：`2025-09-25T08:59:00+08:00`
- 执行时点：`2025-09-25T09:01:00+08:00`
- label 窗口：`2025-09-25T09:01:00+08:00` → `2025-09-25T15:00:00+08:00`
- 目标值：0.0055883412 = ln(807.5 / 803)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-24T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-24T14:59:00+08:00', 'close': 803.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-24T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250924, 'close': 803.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-25T08:57:00+08:00` | 120 | {'title': '【花旗上调阿里巴巴美港股目标价 因人工智能云需求不断增长】', 'labels': '人工智能 阿里巴巴'} |
| brent_last_close | intl_brent | `2025-09-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-24', 'value': 69.64} |

## 12. lg2511 20250930 day （historical_validation）

- Episode：`lg:20250930`
- 决策时点：`2025-09-30T08:59:00+08:00`
- 执行时点：`2025-09-30T09:01:00+08:00`
- label 窗口：`2025-09-30T09:01:00+08:00` → `2025-09-30T15:00:00+08:00`
- 目标值：0.0098401778 = ln(817 / 809)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-29T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-29T14:59:00+08:00', 'close': 810.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-29T15:00:00.043000+08:00` | 64739 | {'trading_day': 20250929, 'close': 810.5} |
| cls_last_telegraph | cls_telegraph | `2025-09-30T08:58:52+08:00` | 8 | {'title': '【上海发布雷电黄色、大风蓝色预警信号】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-09-30T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-29', 'value': 69.0} |

## 13. lg2601 20251020 day （historical_validation）

- Episode：`lg:20251020`
- 决策时点：`2025-10-20T08:59:00+08:00`
- 执行时点：`2025-10-20T09:01:00+08:00`
- label 窗口：`2025-10-20T09:01:00+08:00` → `2025-10-20T15:00:00+08:00`
- 目标值：0.0011990409 = ln(834.5 / 833.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-17T15:00:00+08:00` | 237540 | {'bar_start': '2025-10-17T14:59:00+08:00', 'close': 835.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-17T15:00:00.040000+08:00` | 237539 | {'trading_day': 20251017, 'close': 835.5} |
| cls_last_telegraph | cls_telegraph | `2025-10-20T08:56:55+08:00` | 125 | {'title': '【中东部多地冷如常年11月 华西地区阴雨仍频繁】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-10-18T06:00:00+08:00` | 183540 | {'quote_date': '2025-10-17', 'value': 61.23} |

## 14. lg2601 20251024 day （historical_validation）

- Episode：`lg:20251024`
- 决策时点：`2025-10-24T08:59:00+08:00`
- 执行时点：`2025-10-24T09:01:00+08:00`
- label 窗口：`2025-10-24T09:01:00+08:00` → `2025-10-24T15:00:00+08:00`
- 目标值：0.0018110479 = ln(829 / 827.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-23T15:00:00+08:00` | 64740 | {'bar_start': '2025-10-23T14:59:00+08:00', 'close': 828.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-23T15:00:00.029000+08:00` | 64739 | {'trading_day': 20251023, 'close': 828.5} |
| cls_last_telegraph | cls_telegraph | `2025-10-24T08:57:54+08:00` | 66 | {'title': '【中国代表：加沙是巴勒斯坦人民的家园 不是国际政治的筹码】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-10-24T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-23', 'value': 66.32} |

## 15. lg2601 20251029 day （historical_validation）

- Episode：`lg:20251029`
- 决策时点：`2025-10-29T08:59:00+08:00`
- 执行时点：`2025-10-29T09:01:00+08:00`
- label 窗口：`2025-10-29T09:01:00+08:00` → `2025-10-29T15:00:00+08:00`
- 目标值：-0.001904158 = ln(787 / 788.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-28T15:00:00+08:00` | 64740 | {'bar_start': '2025-10-28T14:59:00+08:00', 'close': 786.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-28T15:00:00.021000+08:00` | 64739 | {'trading_day': 20251028, 'close': 786.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-29T08:54:25+08:00` | 275 | {'title': '【2025年APEC工商领导人峰会开幕】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-10-29T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-28', 'value': 64.03} |

## 16. lg2601 20251114 day （historical_validation）

- Episode：`lg:20251114`
- 决策时点：`2025-11-14T08:59:00+08:00`
- 执行时点：`2025-11-14T09:01:00+08:00`
- label 窗口：`2025-11-14T09:01:00+08:00` → `2025-11-14T15:00:00+08:00`
- 目标值：0.0063613446 = ln(788.5 / 783.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-13T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-13T14:59:00+08:00', 'close': 783.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-13T15:00:00.011000+08:00` | 64739 | {'trading_day': 20251113, 'close': 783.5} |
| cls_last_telegraph | cls_telegraph | `2025-11-14T08:58:36+08:00` | 24 | {'title': '', 'labels': '互动平台精选 储能'} |
| brent_last_close | intl_brent | `2025-11-14T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-13', 'value': 62.14} |

## 17. lg2601 20251127 day （historical_validation）

- Episode：`lg:20251127`
- 决策时点：`2025-11-27T08:59:00+08:00`
- 执行时点：`2025-11-27T09:01:00+08:00`
- label 窗口：`2025-11-27T09:01:00+08:00` → `2025-11-27T15:00:00+08:00`
- 目标值：-0.0026109675 = ln(765 / 767)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-26T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-26T14:59:00+08:00', 'close': 765.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-26T15:00:00.002000+08:00` | 64739 | {'trading_day': 20251126, 'close': 765.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T08:58:38+08:00` | 22 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 18. lg2601 20251216 day （historical_validation）

- Episode：`lg:20251216`
- 决策时点：`2025-12-16T08:59:00+08:00`
- 执行时点：`2025-12-16T09:01:00+08:00`
- label 窗口：`2025-12-16T09:01:00+08:00` → `2025-12-16T15:00:00+08:00`
- 目标值：0.011224945 = ln(761.5 / 753)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-15T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-15T14:59:00+08:00', 'close': 753.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-15T15:00:00.017000+08:00` | 64739 | {'trading_day': 20251215, 'close': 753.5} |
| cls_last_telegraph | cls_telegraph | `2025-12-16T08:50:48+08:00` | 492 | {'title': '【两市融资余额增加48.39亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-12-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-15', 'value': 61.55} |

## 19. lg2603 20251226 day （historical_validation）

- Episode：`lg:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：0 = ln(776.5 / 776.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-25T14:59:00+08:00', 'close': 778.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.010000+08:00` | 64739 | {'trading_day': 20251225, 'close': 778.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 20. lg2603 20260113 day （contaminated_audit）

- Episode：`lg:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：0.0012919898 = ln(774.5 / 773.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-12T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-12T14:59:00+08:00', 'close': 773.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.029000+08:00` | 64739 | {'trading_day': 20260112, 'close': 773.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 21. lg2603 20260122 day （contaminated_audit）

- Episode：`lg:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.0058727738 = ln(768.5 / 764)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-21T14:59:00+08:00', 'close': 764.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.033000+08:00` | 64739 | {'trading_day': 20260121, 'close': 764.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 22. lg2603 20260204 day （contaminated_audit）

- Episode：`lg:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：0.0018593126 = ln(807.5 / 806)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T15:00:00+08:00` | 64740 | {'bar_start': '2026-02-03T14:59:00+08:00', 'close': 801.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.019000+08:00` | 64739 | {'trading_day': 20260203, 'close': 801.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 23. lg2605 20260305 day （contaminated_audit）

- Episode：`lg:20260305`
- 决策时点：`2026-03-05T08:59:00+08:00`
- 执行时点：`2026-03-05T09:01:00+08:00`
- label 窗口：`2026-03-05T09:01:00+08:00` → `2026-03-05T15:00:00+08:00`
- 目标值：-0.0024953226 = ln(800.5 / 802.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-04T15:00:00+08:00` | 64740 | {'bar_start': '2026-03-04T14:59:00+08:00', 'close': 802.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-04T15:00:00.043000+08:00` | 64739 | {'trading_day': 20260304, 'close': 802.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-05T08:53:55+08:00` | 305 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-03-05T06:00:00+08:00` | 10740 | {'quote_date': '2026-03-04', 'value': 81.56} |

## 24. lg2605 20260417 day （contaminated_audit）

- Episode：`lg:20260417`
- 决策时点：`2026-04-17T08:59:00+08:00`
- 执行时点：`2026-04-17T09:01:00+08:00`
- label 窗口：`2026-04-17T09:01:00+08:00` → `2026-04-17T15:00:00+08:00`
- 目标值：0.0024420037 = ln(820 / 818)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-16T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-16T14:59:00+08:00', 'close': 818.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-16T15:00:00.037000+08:00` | 64739 | {'trading_day': 20260416, 'close': 818.5} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T08:48:12+08:00` | 648 | {'title': '【两市融资余额增加107.35亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 25. lg2607 20260511 day （contaminated_audit）

- Episode：`lg:20260511`
- 决策时点：`2026-05-11T08:59:00+08:00`
- 执行时点：`2026-05-11T09:01:00+08:00`
- label 窗口：`2026-05-11T09:01:00+08:00` → `2026-05-11T15:00:00+08:00`
- 目标值：-0.00061481711 = ln(813 / 813.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-08T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-08T14:59:00+08:00', 'close': 815.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-08T15:00:00.023000+08:00` | 237539 | {'trading_day': 20260508, 'close': 815.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T08:57:06+08:00` | 114 | {'title': '【伊朗媒体公布伊朗回应美方要点】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 26. lg2607 20260518 day （contaminated_audit）

- Episode：`lg:20260518`
- 决策时点：`2026-05-18T08:59:00+08:00`
- 执行时点：`2026-05-18T09:01:00+08:00`
- label 窗口：`2026-05-18T09:01:00+08:00` → `2026-05-18T15:00:00+08:00`
- 目标值：0.012330612 = ln(816 / 806)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-15T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-15T14:59:00+08:00', 'close': 807.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-15T15:00:00.022000+08:00` | 237539 | {'trading_day': 20260515, 'close': 807.5} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T08:57:46+08:00` | 74 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 27. lg2607 20260529 day （contaminated_audit）

- Episode：`lg:20260529`
- 决策时点：`2026-05-29T08:59:00+08:00`
- 执行时点：`2026-05-29T09:01:00+08:00`
- label 窗口：`2026-05-29T09:01:00+08:00` → `2026-05-29T15:00:00+08:00`
- 目标值：-0.0093897403 = ln(795 / 802.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-28T14:59:00+08:00', 'close': 802.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-28T15:00:00.030000+08:00` | 64739 | {'trading_day': 20260528, 'close': 802.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-29T08:57:30+08:00` | 90 | {'title': '【江苏省政府召开智能机器人具身智能产业高质量发展专题推进会议】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2026-05-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-28', 'value': 95.47} |

## 28. lg2607 20260610 day （contaminated_audit）

- Episode：`lg:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：-0.0056550575 = ln(793.5 / 798)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-09T14:59:00+08:00', 'close': 797.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260609, 'close': 797.5} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 29. lg2609 20260716 day （contaminated_audit）

- Episode：`lg:20260716`
- 决策时点：`2026-07-16T08:59:00+08:00`
- 执行时点：`2026-07-16T09:01:00+08:00`
- label 窗口：`2026-07-16T09:01:00+08:00` → `2026-07-16T15:00:00+08:00`
- 目标值：-0.0018320616 = ln(818 / 819.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-15T14:59:00+08:00', 'close': 819.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.012000+08:00` | 64739 | {'trading_day': 20260715, 'close': 819.5} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2434540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-13', 'value': 81.62} |
