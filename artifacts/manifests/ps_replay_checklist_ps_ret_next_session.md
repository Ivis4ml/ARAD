# SC Temporal Spine 人工回放清单（ps_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`7120d38d785a05f8daa5ebae51a7dc91a36f273c0825ebfbec208df1a4cc1fe7`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. ps2506 20241231 day （discovery）

- Episode：`ps:20241231`
- 决策时点：`2024-12-31T08:59:00+08:00`
- 执行时点：`2024-12-31T09:01:00+08:00`
- label 窗口：`2024-12-31T09:01:00+08:00` → `2024-12-31T15:00:00+08:00`
- 目标值：-0.0023521121 = ln(42465 / 42565)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-30T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-30T14:59:00+08:00', 'close': 42535.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-30T15:00:00.005000+08:00` | 64739 | {'trading_day': 20241230, 'close': 42535.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-31T08:55:19+08:00` | 221 | {'title': '【上海二手房单日成交量创年内新高】', 'labels': '房地产头条'} |
| brent_last_close | intl_brent | `2024-12-31T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-30', 'value': 74.24} |

## 01. ps2506 20250127 day （historical_validation）

- Episode：`ps:20250127`
- 决策时点：`2025-01-27T08:59:00+08:00`
- 执行时点：`2025-01-27T09:01:00+08:00`
- label 窗口：`2025-01-27T09:01:00+08:00` → `2025-01-27T15:00:00+08:00`
- 目标值：0.007114201 = ln(43730 / 43420)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-24T15:00:00+08:00` | 237540 | {'bar_start': '2025-01-24T14:59:00+08:00', 'close': 43195.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-24T15:00:00.007000+08:00` | 237539 | {'trading_day': 20250124, 'close': 43195.0} |
| cls_last_telegraph | cls_telegraph | `2025-01-27T08:49:42+08:00` | 558 | {'title': '【两市融资余额减少111.69亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-01-25T06:00:00+08:00` | 183540 | {'quote_date': '2025-01-24', 'value': 78.71} |

## 02. ps2506 20250226 day （historical_validation）

- Episode：`ps:20250226`
- 决策时点：`2025-02-26T08:59:00+08:00`
- 执行时点：`2025-02-26T09:01:00+08:00`
- label 窗口：`2025-02-26T09:01:00+08:00` → `2025-02-26T15:00:00+08:00`
- 目标值：0.017791846 = ln(44515 / 43730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-02-25T14:59:00+08:00', 'close': 43835.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-25T15:00:00.004000+08:00` | 64739 | {'trading_day': 20250225, 'close': 43835.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-26T08:56:29+08:00` | 151 | {'title': '【丰田将下调零部件制造商的钢材价格】', 'labels': '汽车大新闻 钢铁'} |
| brent_last_close | intl_brent | `2025-02-26T06:00:00+08:00` | 10740 | {'quote_date': '2025-02-25', 'value': 73.11} |

## 03. ps2506 20250311 day （historical_validation）

- Episode：`ps:20250311`
- 决策时点：`2025-03-11T08:59:00+08:00`
- 执行时点：`2025-03-11T09:01:00+08:00`
- label 窗口：`2025-03-11T09:01:00+08:00` → `2025-03-11T15:00:00+08:00`
- 目标值：0.0055647182 = ln(44150 / 43905)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-10T15:00:00+08:00` | 64740 | {'bar_start': '2025-03-10T14:59:00+08:00', 'close': 43850.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-10T15:00:00.015000+08:00` | 64739 | {'trading_day': 20250310, 'close': 43850.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-11T08:57:10+08:00` | 110 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-03-11T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-10', 'value': 71.08} |

## 04. ps2506 20250313 day （historical_validation）

- Episode：`ps:20250313`
- 决策时点：`2025-03-13T08:59:00+08:00`
- 执行时点：`2025-03-13T09:01:00+08:00`
- label 窗口：`2025-03-13T09:01:00+08:00` → `2025-03-13T15:00:00+08:00`
- 目标值：0.0011339155 = ln(44120 / 44070)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-12T15:00:00+08:00` | 64740 | {'bar_start': '2025-03-12T14:59:00+08:00', 'close': 44050.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-12T15:00:00.118000+08:00` | 64739 | {'trading_day': 20250312, 'close': 44050.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-13T08:53:32+08:00` | 328 | {'title': '【日本投资者上周净买入海外股票规模创纪录次高】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-03-13T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-12', 'value': 72.36} |

## 05. ps2506 20250425 day （historical_validation）

- Episode：`ps:20250425`
- 决策时点：`2025-04-25T08:59:00+08:00`
- 执行时点：`2025-04-25T09:01:00+08:00`
- label 窗口：`2025-04-25T09:01:00+08:00` → `2025-04-25T15:00:00+08:00`
- 目标值：-0.024317699 = ln(38390 / 39335)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-24T15:00:00+08:00` | 64740 | {'bar_start': '2025-04-24T14:59:00+08:00', 'close': 39375.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-24T15:00:00.011000+08:00` | 64739 | {'trading_day': 20250424, 'close': 39375.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-25T08:57:57+08:00` | 63 | {'title': '【苹果调整管理层 将机器人业务从AI业务中剥离】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2025-04-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-24', 'value': 67.5} |

## 06. ps2508 20250627 day （historical_validation）

- Episode：`ps:20250627`
- 决策时点：`2025-06-27T08:59:00+08:00`
- 执行时点：`2025-06-27T09:01:00+08:00`
- label 窗口：`2025-06-27T09:01:00+08:00` → `2025-06-27T15:00:00+08:00`
- 目标值：0.035750828 = ln(33315 / 32145)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-26T15:00:00+08:00` | 64740 | {'bar_start': '2025-06-26T14:59:00+08:00', 'close': 31715.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-06-26T15:00:00.067000+08:00` | 64739 | {'trading_day': 20250626, 'close': 31715.0} |
| cls_last_telegraph | cls_telegraph | `2025-06-27T08:49:19+08:00` | 581 | {'title': '【两市融资余额增加91.48亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-06-27T06:00:00+08:00` | 10740 | {'quote_date': '2025-06-26', 'value': 68.57} |

## 07. ps2509 20250731 day （historical_validation）

- Episode：`ps:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.062430918 = ln(49130 / 52295)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 64740 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 54705.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.031000+08:00` | 64739 | {'trading_day': 20250730, 'close': 54705.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 08. ps2511 20250812 day （historical_validation）

- Episode：`ps:20250812`
- 决策时点：`2025-08-12T08:59:00+08:00`
- 执行时点：`2025-08-12T09:01:00+08:00`
- label 窗口：`2025-08-12T09:01:00+08:00` → `2025-08-12T15:00:00+08:00`
- 目标值：-0.019783701 = ln(51800 / 52835)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-11T14:59:00+08:00', 'close': 52985.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.019000+08:00` | 64739 | {'trading_day': 20250811, 'close': 52985.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-12T08:52:43+08:00` | 377 | {'title': '【德国7月破产企业数量同比大幅增加】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-11', 'value': 67.36} |

## 09. ps2511 20250925 day （historical_validation）

- Episode：`ps:20250925`
- 决策时点：`2025-09-25T08:59:00+08:00`
- 执行时点：`2025-09-25T09:01:00+08:00`
- label 窗口：`2025-09-25T09:01:00+08:00` → `2025-09-25T15:00:00+08:00`
- 目标值：0.0011687934 = ln(51365 / 51305)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-24T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-24T14:59:00+08:00', 'close': 51380.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-24T15:00:00.013000+08:00` | 64739 | {'trading_day': 20250924, 'close': 51380.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-25T08:57:00+08:00` | 120 | {'title': '【花旗上调阿里巴巴美港股目标价 因人工智能云需求不断增长】', 'labels': '人工智能 阿里巴巴'} |
| brent_last_close | intl_brent | `2025-09-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-24', 'value': 69.64} |

## 10. ps2511 20250930 day （historical_validation）

- Episode：`ps:20250930`
- 决策时点：`2025-09-30T08:59:00+08:00`
- 执行时点：`2025-09-30T09:01:00+08:00`
- label 窗口：`2025-09-30T09:01:00+08:00` → `2025-09-30T15:00:00+08:00`
- 目标值：0.011948041 = ln(51360 / 50750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-29T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-29T14:59:00+08:00', 'close': 51280.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-29T15:00:00.047000+08:00` | 64739 | {'trading_day': 20250929, 'close': 51280.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-30T08:58:52+08:00` | 8 | {'title': '【上海发布雷电黄色、大风蓝色预警信号】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-09-30T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-29', 'value': 69.0} |

## 11. ps2511 20251015 day （historical_validation）

- Episode：`ps:20251015`
- 决策时点：`2025-10-15T08:59:00+08:00`
- 执行时点：`2025-10-15T09:01:00+08:00`
- label 窗口：`2025-10-15T09:01:00+08:00` → `2025-10-15T15:00:00+08:00`
- 目标值：0.016452304 = ln(50865 / 50035)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-14T15:00:00+08:00` | 64740 | {'bar_start': '2025-10-14T14:59:00+08:00', 'close': 49990.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-14T15:00:00.009000+08:00` | 64739 | {'trading_day': 20251014, 'close': 49990.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-15T08:52:56+08:00` | 364 | {'title': '【百利天恒董事长：未来公司仅针对部分项目考虑开展BD合作】', 'labels': '医药'} |
| brent_last_close | intl_brent | `2025-10-15T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-14', 'value': 63.0} |

## 12. ps2511 20251020 day （historical_validation）

- Episode：`ps:20251020`
- 决策时点：`2025-10-20T08:59:00+08:00`
- 执行时点：`2025-10-20T09:01:00+08:00`
- label 窗口：`2025-10-20T09:01:00+08:00` → `2025-10-20T15:00:00+08:00`
- 目标值：-0.027431187 = ln(50340 / 51740)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-17T15:00:00+08:00` | 237540 | {'bar_start': '2025-10-17T14:59:00+08:00', 'close': 52340.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-17T15:00:00.007000+08:00` | 237539 | {'trading_day': 20251017, 'close': 52340.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-20T08:56:55+08:00` | 125 | {'title': '【中东部多地冷如常年11月 华西地区阴雨仍频繁】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-10-18T06:00:00+08:00` | 183540 | {'quote_date': '2025-10-17', 'value': 61.23} |

## 13. ps2601 20251024 day （historical_validation）

- Episode：`ps:20251024`
- 决策时点：`2025-10-24T08:59:00+08:00`
- 执行时点：`2025-10-24T09:01:00+08:00`
- label 窗口：`2025-10-24T09:01:00+08:00` → `2025-10-24T15:00:00+08:00`
- 目标值：-0.010365744 = ln(52305 / 52850)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-23T15:00:00+08:00` | 64740 | {'bar_start': '2025-10-23T14:59:00+08:00', 'close': 53080.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-23T15:00:00.043000+08:00` | 64739 | {'trading_day': 20251023, 'close': 53080.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-24T08:57:54+08:00` | 66 | {'title': '【中国代表：加沙是巴勒斯坦人民的家园 不是国际政治的筹码】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-10-24T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-23', 'value': 66.32} |

## 14. ps2601 20251029 day （historical_validation）

- Episode：`ps:20251029`
- 决策时点：`2025-10-29T08:59:00+08:00`
- 执行时点：`2025-10-29T09:01:00+08:00`
- label 窗口：`2025-10-29T09:01:00+08:00` → `2025-10-29T15:00:00+08:00`
- 目标值：0.0093176887 = ln(54990 / 54480)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-28T15:00:00+08:00` | 64740 | {'bar_start': '2025-10-28T14:59:00+08:00', 'close': 54355.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-28T15:00:00.030000+08:00` | 64739 | {'trading_day': 20251028, 'close': 54355.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-29T08:54:25+08:00` | 275 | {'title': '【2025年APEC工商领导人峰会开幕】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-10-29T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-28', 'value': 64.03} |

## 15. ps2601 20251114 day （historical_validation）

- Episode：`ps:20251114`
- 决策时点：`2025-11-14T08:59:00+08:00`
- 执行时点：`2025-11-14T09:01:00+08:00`
- label 窗口：`2025-11-14T09:01:00+08:00` → `2025-11-14T15:00:00+08:00`
- 目标值：0.0031504844 = ln(54045 / 53875)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-13T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-13T14:59:00+08:00', 'close': 54195.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-13T15:00:00.030000+08:00` | 64739 | {'trading_day': 20251113, 'close': 54195.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-14T08:58:36+08:00` | 24 | {'title': '', 'labels': '互动平台精选 储能'} |
| brent_last_close | intl_brent | `2025-11-14T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-13', 'value': 62.14} |

## 16. ps2601 20251127 day （historical_validation）

- Episode：`ps:20251127`
- 决策时点：`2025-11-27T08:59:00+08:00`
- 执行时点：`2025-11-27T09:01:00+08:00`
- label 窗口：`2025-11-27T09:01:00+08:00` → `2025-11-27T15:00:00+08:00`
- 目标值：-0.013040339 = ln(55235 / 55960)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-26T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-26T14:59:00+08:00', 'close': 55895.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-26T15:00:00.013000+08:00` | 64739 | {'trading_day': 20251126, 'close': 55895.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T08:58:38+08:00` | 22 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 17. ps2605 20251216 day （historical_validation）

- Episode：`ps:20251216`
- 决策时点：`2025-12-16T08:59:00+08:00`
- 执行时点：`2025-12-16T09:01:00+08:00`
- label 窗口：`2025-12-16T09:01:00+08:00` → `2025-12-16T15:00:00+08:00`
- 目标值：-0.0085808266 = ln(58600 / 59105)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-15T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-15T14:59:00+08:00', 'close': 58030.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-15T15:00:00.019000+08:00` | 64739 | {'trading_day': 20251215, 'close': 58030.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-16T08:50:48+08:00` | 492 | {'title': '【两市融资余额增加48.39亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-12-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-15', 'value': 61.55} |

## 18. ps2605 20251226 day （historical_validation）

- Episode：`ps:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：-0.024628486 = ln(58955 / 60425)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-25T14:59:00+08:00', 'close': 60760.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.013000+08:00` | 64739 | {'trading_day': 20251225, 'close': 60760.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 19. ps2605 20260113 day （contaminated_audit）

- Episode：`ps:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：-0.023295563 = ln(49005 / 50160)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-12T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-12T14:59:00+08:00', 'close': 49995.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.005000+08:00` | 64739 | {'trading_day': 20260112, 'close': 49995.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 20. ps2605 20260122 day （contaminated_audit）

- Episode：`ps:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.015259858 = ln(50515 / 49750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-21T14:59:00+08:00', 'close': 49700.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.023000+08:00` | 64739 | {'trading_day': 20260121, 'close': 49700.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 21. ps2605 20260204 day （contaminated_audit）

- Episode：`ps:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：0.019029413 = ln(51195 / 50230)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T15:00:00+08:00` | 64740 | {'bar_start': '2026-02-03T14:59:00+08:00', 'close': 50000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.028000+08:00` | 64739 | {'trading_day': 20260203, 'close': 50000.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 22. ps2605 20260305 day （contaminated_audit）

- Episode：`ps:20260305`
- 决策时点：`2026-03-05T08:59:00+08:00`
- 执行时点：`2026-03-05T09:01:00+08:00`
- label 窗口：`2026-03-05T09:01:00+08:00` → `2026-03-05T15:00:00+08:00`
- 目标值：-0.0049545931 = ln(42280 / 42490)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-04T15:00:00+08:00` | 64740 | {'bar_start': '2026-03-04T14:59:00+08:00', 'close': 42200.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-04T15:00:00.065000+08:00` | 64739 | {'trading_day': 20260304, 'close': 42200.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-05T08:53:55+08:00` | 305 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-03-05T06:00:00+08:00` | 10740 | {'quote_date': '2026-03-04', 'value': 81.56} |

## 23. ps2606 20260417 day （contaminated_audit）

- Episode：`ps:20260417`
- 决策时点：`2026-04-17T08:59:00+08:00`
- 执行时点：`2026-04-17T09:01:00+08:00`
- label 窗口：`2026-04-17T09:01:00+08:00` → `2026-04-17T15:00:00+08:00`
- 目标值：0.0042826618 = ln(39780 / 39610)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-16T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-16T14:59:00+08:00', 'close': 39380.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-16T15:00:00.018000+08:00` | 64739 | {'trading_day': 20260416, 'close': 39380.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T08:48:12+08:00` | 648 | {'title': '【两市融资余额增加107.35亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 24. ps2606 20260511 day （contaminated_audit）

- Episode：`ps:20260511`
- 决策时点：`2026-05-11T08:59:00+08:00`
- 执行时点：`2026-05-11T09:01:00+08:00`
- label 窗口：`2026-05-11T09:01:00+08:00` → `2026-05-11T15:00:00+08:00`
- 目标值：-0.013773607 = ln(38215 / 38745)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-08T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-08T14:59:00+08:00', 'close': 38540.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-08T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260508, 'close': 38540.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T08:57:06+08:00` | 114 | {'title': '【伊朗媒体公布伊朗回应美方要点】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 25. ps2606 20260518 day （contaminated_audit）

- Episode：`ps:20260518`
- 决策时点：`2026-05-18T08:59:00+08:00`
- 执行时点：`2026-05-18T09:01:00+08:00`
- label 窗口：`2026-05-18T09:01:00+08:00` → `2026-05-18T15:00:00+08:00`
- 目标值：-0.00094729014 = ln(36930 / 36965)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-15T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-15T14:59:00+08:00', 'close': 37025.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-15T15:00:00.154000+08:00` | 237539 | {'trading_day': 20260515, 'close': 37025.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T08:57:46+08:00` | 74 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 26. ps2609 20260529 day （contaminated_audit）

- Episode：`ps:20260529`
- 决策时点：`2026-05-29T08:59:00+08:00`
- 执行时点：`2026-05-29T09:01:00+08:00`
- label 窗口：`2026-05-29T09:01:00+08:00` → `2026-05-29T15:00:00+08:00`
- 目标值：-0.008515291 = ln(36835 / 37150)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-28T14:59:00+08:00', 'close': 36960.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-28T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260528, 'close': 36960.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-29T08:57:30+08:00` | 90 | {'title': '【江苏省政府召开智能机器人具身智能产业高质量发展专题推进会议】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2026-05-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-28', 'value': 95.47} |

## 27. ps2609 20260610 day （contaminated_audit）

- Episode：`ps:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：0.042005751 = ln(36100 / 34615)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-09T14:59:00+08:00', 'close': 34280.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260609, 'close': 34280.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 28. ps2609 20260629 day （contaminated_audit）

- Episode：`ps:20260629`
- 决策时点：`2026-06-29T08:59:00+08:00`
- 执行时点：`2026-06-29T09:01:00+08:00`
- label 窗口：`2026-06-29T09:01:00+08:00` → `2026-06-29T15:00:00+08:00`
- 目标值：0.013436451 = ln(35215 / 34745)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T15:00:00+08:00` | 237540 | {'bar_start': '2026-06-26T14:59:00+08:00', 'close': 34745.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00.022000+08:00` | 237539 | {'trading_day': 20260626, 'close': 34745.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 965740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-27T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-26', 'value': 70.16} |

## 29. ps2609 20260716 day （contaminated_audit）

- Episode：`ps:20260716`
- 决策时点：`2026-07-16T08:59:00+08:00`
- 执行时点：`2026-07-16T09:01:00+08:00`
- label 窗口：`2026-07-16T09:01:00+08:00` → `2026-07-16T15:00:00+08:00`
- 目标值：0.0037063478 = ln(35140 / 35010)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-15T14:59:00+08:00', 'close': 35160.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260715, 'close': 35160.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2434540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-13', 'value': 81.62} |
