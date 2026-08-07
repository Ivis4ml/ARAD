# SC Temporal Spine 人工回放清单（br_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`21b87fccef71330f55e89cf41c9e6d80de761d79b03a2b25cc27640bfba83996`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. br2401 20230905 day （discovery）

- Episode：`br:20230905`
- 决策时点：`2023-09-05T08:59:00+08:00`
- 执行时点：`2023-09-05T09:01:00+08:00`
- label 窗口：`2023-09-05T09:01:00+08:00` → `2023-09-05T15:00:00+08:00`
- 目标值：-0.0024301349 = ln(14385 / 14420)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-09-04T23:00:00+08:00` | 35940 | {'bar_start': '2023-09-04T22:59:00+08:00', 'close': 14350.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-09-04T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230904, 'close': 13680.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-09-05T08:54:11+08:00` | 289 | {'title': '', 'labels': '港股动态 港股通'} |
| brent_last_close | intl_brent | `2023-09-05T06:00:00+08:00` | 10740 | {'quote_date': '2023-09-04', 'value': 90.42} |

## 01. br2401 20230918 night （discovery）

- Episode：`br:20230918`
- 决策时点：`2023-09-15T20:59:00+08:00`
- 执行时点：`2023-09-15T21:01:00+08:00`
- label 窗口：`2023-09-15T21:01:00+08:00` → `2023-09-15T23:00:00+08:00`
- 目标值：-0.0050559877 = ln(13810 / 13880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-09-15T15:00:00+08:00` | 21540 | {'bar_start': '2023-09-15T14:59:00+08:00', 'close': 13860.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-09-15T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230915, 'close': 13860.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-09-15T20:56:11+08:00` | 169 | {'title': '【苹果iPhone 15 Pro系列在中国延迟交付最高达4-5周】', 'labels': '苹果产业链'} |
| brent_last_close | intl_brent | `2023-09-15T06:00:00+08:00` | 53940 | {'quote_date': '2023-09-14', 'value': 95.2} |

## 02. br2401 20231109 night （discovery）

- Episode：`br:20231109`
- 决策时点：`2023-11-08T20:59:00+08:00`
- 执行时点：`2023-11-08T21:01:00+08:00`
- label 窗口：`2023-11-08T21:01:00+08:00` → `2023-11-08T23:00:00+08:00`
- 目标值：-0.003562244 = ln(12610 / 12655)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-11-08T15:00:00+08:00` | 21540 | {'bar_start': '2023-11-08T14:59:00+08:00', 'close': 12695.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-11-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20231108, 'close': 12695.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-11-08T20:58:27+08:00` | 33 | {'title': '【盈方微：拟筹划购买华信科及World Style 49%股权 股票停牌】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-11-08T06:00:00+08:00` | 53940 | {'quote_date': '2023-11-07', 'value': 83.43} |

## 03. br2402 20231205 night （discovery）

- Episode：`br:20231205`
- 决策时点：`2023-12-04T20:59:00+08:00`
- 执行时点：`2023-12-04T21:01:00+08:00`
- label 窗口：`2023-12-04T21:01:00+08:00` → `2023-12-04T23:00:00+08:00`
- 目标值：-0.0050526423 = ln(11845 / 11905)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-12-04T15:00:00+08:00` | 21540 | {'bar_start': '2023-12-04T14:59:00+08:00', 'close': 11915.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-12-04T15:00:00.500000+08:00` | 21539 | {'trading_day': 20231204, 'close': 11915.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-12-04T20:55:10+08:00` | 230 | {'title': '【“有人买近5万倍单注彩票中2亿多”？江西福彩：还无法核实】', 'labels': '彩票'} |
| brent_last_close | intl_brent | `2023-12-02T06:00:00+08:00` | 226740 | {'quote_date': '2023-12-01', 'value': 78.72} |

## 04. br2402 20231208 night （discovery）

- Episode：`br:20231208`
- 决策时点：`2023-12-07T20:59:00+08:00`
- 执行时点：`2023-12-07T21:01:00+08:00`
- label 窗口：`2023-12-07T21:01:00+08:00` → `2023-12-07T23:00:00+08:00`
- 目标值：0.0017006807 = ln(11770 / 11750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-12-07T15:00:00+08:00` | 21540 | {'bar_start': '2023-12-07T14:59:00+08:00', 'close': 11740.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-12-07T15:00:00.500000+08:00` | 21539 | {'trading_day': 20231207, 'close': 11740.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-12-07T20:57:43+08:00` | 77 | {'title': '【本轮巴以冲突已致双方超1.86万人死亡】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2023-12-07T06:00:00+08:00` | 53940 | {'quote_date': '2023-12-06', 'value': 74.33} |

## 05. br2404 20240312 night （discovery）

- Episode：`br:20240312`
- 决策时点：`2024-03-11T20:59:00+08:00`
- 执行时点：`2024-03-11T21:01:00+08:00`
- label 窗口：`2024-03-11T21:01:00+08:00` → `2024-03-11T23:00:00+08:00`
- 目标值：-0.0079621274 = ln(13135 / 13240)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-11T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-11T14:59:00+08:00', 'close': 13240.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240311, 'close': 13240.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-03-11T20:54:43+08:00` | 257 | {'title': '【通用电气能源与Montana Technologies成立合资企业】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-09T06:00:00+08:00` | 226740 | {'quote_date': '2024-03-08', 'value': 84.29} |

## 06. br2407 20240515 night （discovery）

- Episode：`br:20240515`
- 决策时点：`2024-05-14T20:59:00+08:00`
- 执行时点：`2024-05-14T21:01:00+08:00`
- label 窗口：`2024-05-14T21:01:00+08:00` → `2024-05-14T23:00:00+08:00`
- 目标值：0.0037850159 = ln(13235 / 13185)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-14T15:00:00+08:00` | 21540 | {'bar_start': '2024-05-14T14:59:00+08:00', 'close': 13205.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240514, 'close': 13205.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-05-14T20:57:11+08:00` | 109 | {'title': '【美国PPI超预期后美债收益率攀升 市场下调降息预期】', 'labels': '经济数据及解读 美国宏观速递 美联储动态 环球市场情报'} |
| brent_last_close | intl_brent | `2024-05-14T06:00:00+08:00` | 53940 | {'quote_date': '2024-05-13', 'value': 83.18} |

## 07. br2407 20240605 night （discovery）

- Episode：`br:20240605`
- 决策时点：`2024-06-04T20:59:00+08:00`
- 执行时点：`2024-06-04T21:01:00+08:00`
- label 窗口：`2024-06-04T21:01:00+08:00` → `2024-06-04T23:00:00+08:00`
- 目标值：0.006665522 = ln(14300 / 14205)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-06-04T15:00:00+08:00` | 21540 | {'bar_start': '2024-06-04T14:59:00+08:00', 'close': 14255.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-06-04T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240604, 'close': 14255.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-06-04T20:57:56+08:00` | 64 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-06-04T06:00:00+08:00` | 53940 | {'quote_date': '2024-06-03', 'value': 76.45} |

## 08. br2408 20240710 day （discovery）

- Episode：`br:20240710`
- 决策时点：`2024-07-10T08:59:00+08:00`
- 执行时点：`2024-07-10T09:01:00+08:00`
- label 窗口：`2024-07-10T09:01:00+08:00` → `2024-07-10T15:00:00+08:00`
- 目标值：-0.0061287219 = ln(14640 / 14730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T23:00:00+08:00` | 35940 | {'bar_start': '2024-07-09T22:59:00+08:00', 'close': 14740.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-09T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240709, 'close': 15055.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-10T08:51:26+08:00` | 454 | {'title': '【两市融资余额减少4.14亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-07-10T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-09', 'value': 86.48} |

## 09. br2408 20240712 day （discovery）

- Episode：`br:20240712`
- 决策时点：`2024-07-12T08:59:00+08:00`
- 执行时点：`2024-07-12T09:01:00+08:00`
- label 窗口：`2024-07-12T09:01:00+08:00` → `2024-07-12T15:00:00+08:00`
- 目标值：-0.0094883802 = ln(14685 / 14825)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-11T23:00:00+08:00` | 35940 | {'bar_start': '2024-07-11T22:59:00+08:00', 'close': 14840.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-11T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240711, 'close': 14770.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-12T08:58:47+08:00` | 13 | {'title': '【两市融资余额较上一日增加28.77亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-07-12T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-11', 'value': 86.49} |

## 10. br2410 20240827 day （discovery）

- Episode：`br:20240827`
- 决策时点：`2024-08-27T08:59:00+08:00`
- 执行时点：`2024-08-27T09:01:00+08:00`
- label 窗口：`2024-08-27T09:01:00+08:00` → `2024-08-27T15:00:00+08:00`
- 目标值：0.012401701 = ln(15010 / 14825)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-08-26T23:00:00+08:00` | 35940 | {'bar_start': '2024-08-26T22:59:00+08:00', 'close': 14825.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-08-26T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240826, 'close': 14810.0} |
| cls_last_telegraph | cls_telegraph | `2024-08-27T08:55:48+08:00` | 192 | {'title': '', 'labels': '太空探索'} |
| brent_last_close | intl_brent | `2024-08-24T06:00:00+08:00` | 269940 | {'quote_date': '2024-08-23', 'value': 80.34} |

## 11. br2411 20240920 day （discovery）

- Episode：`br:20240920`
- 决策时点：`2024-09-20T08:59:00+08:00`
- 执行时点：`2024-09-20T09:01:00+08:00`
- label 窗口：`2024-09-20T09:01:00+08:00` → `2024-09-20T15:00:00+08:00`
- 目标值：-0.011278315 = ln(15870 / 16050)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-19T23:00:00+08:00` | 35940 | {'bar_start': '2024-09-19T22:59:00+08:00', 'close': 16050.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-19T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240919, 'close': 16125.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-20T08:57:04+08:00` | 116 | {'title': '【T-Mobile CEO：苹果iPhone16销量优于iPhone15】', 'labels': '消费电子'} |
| brent_last_close | intl_brent | `2024-09-20T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-19', 'value': 75.93} |

## 12. br2411 20241022 day （discovery）

- Episode：`br:20241022`
- 决策时点：`2024-10-22T08:59:00+08:00`
- 执行时点：`2024-10-22T09:01:00+08:00`
- label 窗口：`2024-10-22T09:01:00+08:00` → `2024-10-22T15:00:00+08:00`
- 目标值：0.016702533 = ln(15395 / 15140)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-10-21T23:00:00+08:00` | 35940 | {'bar_start': '2024-10-21T22:59:00+08:00', 'close': 15135.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-10-21T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241021, 'close': 15205.0} |
| cls_last_telegraph | cls_telegraph | `2024-10-22T08:58:06+08:00` | 54 | {'title': '【PC、智能手机需求不振致DRAM价格1年5个月来首降】', 'labels': '半导体芯片 存储芯片'} |
| brent_last_close | intl_brent | `2024-10-22T06:00:00+08:00` | 10740 | {'quote_date': '2024-10-21', 'value': 73.29} |

## 13. br2501 20241114 night （discovery）

- Episode：`br:20241114`
- 决策时点：`2024-11-13T20:59:00+08:00`
- 执行时点：`2024-11-13T21:01:00+08:00`
- label 窗口：`2024-11-13T21:01:00+08:00` → `2024-11-13T23:00:00+08:00`
- 目标值：0.0011011196 = ln(13630 / 13615)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-11-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-11-13T14:59:00+08:00', 'close': 13570.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-11-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20241113, 'close': 13570.0} |
| cls_last_telegraph | cls_telegraph | `2024-11-13T20:53:51+08:00` | 309 | {'title': '【港交所：台风影响下交易市场平台将正常全面运作】', 'labels': '港交所动态'} |
| brent_last_close | intl_brent | `2024-11-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-11-12', 'value': 72.56} |

## 14. br2502 20250113 night （historical_validation）

- Episode：`br:20250113`
- 决策时点：`2025-01-10T20:59:00+08:00`
- 执行时点：`2025-01-10T21:01:00+08:00`
- label 窗口：`2025-01-10T21:01:00+08:00` → `2025-01-10T23:00:00+08:00`
- 目标值：0.036774151 = ln(14125 / 13615)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-01-10T14:59:00+08:00', 'close': 13600.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250110, 'close': 13600.0} |
| cls_last_telegraph | cls_telegraph | `2025-01-10T20:53:57+08:00` | 303 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-01-10T06:00:00+08:00` | 53940 | {'quote_date': '2025-01-09', 'value': 78.44} |

## 15. br2504 20250305 night （historical_validation）

- Episode：`br:20250305`
- 决策时点：`2025-03-04T20:59:00+08:00`
- 执行时点：`2025-03-04T21:01:00+08:00`
- label 窗口：`2025-03-04T21:01:00+08:00` → `2025-03-04T23:00:00+08:00`
- 目标值：-0.004379569 = ln(13670 / 13730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-04T15:00:00+08:00` | 21540 | {'bar_start': '2025-03-04T14:59:00+08:00', 'close': 13765.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-04T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250304, 'close': 13765.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-04T20:53:47+08:00` | 313 | {'title': '', 'labels': '环球市场情报 期货市场情报 原油市场动态 海外大宗商品 沙特'} |
| brent_last_close | intl_brent | `2025-03-04T06:00:00+08:00` | 53940 | {'quote_date': '2025-03-03', 'value': 72.85} |

## 16. br2506 20250509 night （historical_validation）

- Episode：`br:20250509`
- 决策时点：`2025-05-08T20:59:00+08:00`
- 执行时点：`2025-05-08T21:01:00+08:00`
- label 窗口：`2025-05-08T21:01:00+08:00` → `2025-05-08T23:00:00+08:00`
- 目标值：0.0061376782 = ln(11440 / 11370)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-05-08T15:00:00+08:00` | 21540 | {'bar_start': '2025-05-08T14:59:00+08:00', 'close': 11370.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-05-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250508, 'close': 11370.0} |
| cls_last_telegraph | cls_telegraph | `2025-05-08T20:53:36+08:00` | 324 | {'title': '【水利部珠江委：云南、广西等地旱情得到缓解】', 'labels': '水利'} |
| brent_last_close | intl_brent | `2025-05-08T06:00:00+08:00` | 53940 | {'quote_date': '2025-05-07', 'value': 60.31} |

## 17. br2506 20250516 night （historical_validation）

- Episode：`br:20250516`
- 决策时点：`2025-05-15T20:59:00+08:00`
- 执行时点：`2025-05-15T21:01:00+08:00`
- label 窗口：`2025-05-15T21:01:00+08:00` → `2025-05-15T23:00:00+08:00`
- 目标值：0.0065199905 = ln(12310 / 12230)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-05-15T15:00:00+08:00` | 21540 | {'bar_start': '2025-05-15T14:59:00+08:00', 'close': 12260.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-05-15T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250515, 'close': 12260.0} |
| cls_last_telegraph | cls_telegraph | `2025-05-15T20:56:23+08:00` | 157 | {'title': '【航新科技：原控股股东柳少娟拟减持不超3%公司股份】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-05-15T06:00:00+08:00` | 53940 | {'quote_date': '2025-05-14', 'value': 65.91} |

## 18. br2509 20250812 day （historical_validation）

- Episode：`br:20250812`
- 决策时点：`2025-08-12T08:59:00+08:00`
- 执行时点：`2025-08-12T09:01:00+08:00`
- label 窗口：`2025-08-12T09:01:00+08:00` → `2025-08-12T15:00:00+08:00`
- 目标值：0.0076401051 = ln(11825 / 11735)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T23:00:00+08:00` | 35940 | {'bar_start': '2025-08-11T22:59:00+08:00', 'close': 11720.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250811, 'close': 11785.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-12T08:52:43+08:00` | 377 | {'title': '【德国7月破产企业数量同比大幅增加】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-11', 'value': 67.36} |

## 19. br2510 20250915 night （historical_validation）

- Episode：`br:20250915`
- 决策时点：`2025-09-12T20:59:00+08:00`
- 执行时点：`2025-09-12T21:01:00+08:00`
- label 窗口：`2025-09-12T21:01:00+08:00` → `2025-09-12T23:00:00+08:00`
- 目标值：-0.0038768086 = ln(11585 / 11630)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-12T15:00:00+08:00` | 21540 | {'bar_start': '2025-09-12T14:59:00+08:00', 'close': 11615.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250912, 'close': 11615.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-12T20:50:21+08:00` | 519 | {'title': '【国产离子回旋加热系统研制成功】', 'labels': 'TMT行业观察 RFID'} |
| brent_last_close | intl_brent | `2025-09-12T06:00:00+08:00` | 53940 | {'quote_date': '2025-09-11', 'value': 67.25} |

## 20. br2511 20250919 day （historical_validation）

- Episode：`br:20250919`
- 决策时点：`2025-09-19T08:59:00+08:00`
- 执行时点：`2025-09-19T09:01:00+08:00`
- label 窗口：`2025-09-19T09:01:00+08:00` → `2025-09-19T15:00:00+08:00`
- 目标值：0 = ln(11445 / 11445)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-18T23:00:00+08:00` | 35940 | {'bar_start': '2025-09-18T22:59:00+08:00', 'close': 11425.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-18T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250918, 'close': 11415.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-19T08:49:35+08:00` | 565 | {'title': '【两市融资余额减少26.28亿元】', 'labels': '盘面直播 融资融券'} |
| brent_last_close | intl_brent | `2025-09-19T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-18', 'value': 67.83} |

## 21. br2511 20250922 night （historical_validation）

- Episode：`br:20250922`
- 决策时点：`2025-09-19T20:59:00+08:00`
- 执行时点：`2025-09-19T21:01:00+08:00`
- label 窗口：`2025-09-19T21:01:00+08:00` → `2025-09-19T23:00:00+08:00`
- 目标值：0 = ln(11495 / 11495)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-19T15:00:00+08:00` | 21540 | {'bar_start': '2025-09-19T14:59:00+08:00', 'close': 11445.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-19T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250919, 'close': 11445.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-19T20:57:51+08:00` | 69 | {'title': '【创意信息：2022年年报、2023年半年报多计营业收入 9月23日起股票简称变', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-09-19T06:00:00+08:00` | 53940 | {'quote_date': '2025-09-18', 'value': 67.83} |

## 22. br2602 20251209 day （historical_validation）

- Episode：`br:20251209`
- 决策时点：`2025-12-09T08:59:00+08:00`
- 执行时点：`2025-12-09T09:01:00+08:00`
- label 窗口：`2025-12-09T09:01:00+08:00` → `2025-12-09T15:00:00+08:00`
- 目标值：-0.0062008307 = ln(10450 / 10515)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-08T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-08T22:59:00+08:00', 'close': 10520.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251208, 'close': 10530.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-09T08:58:19+08:00` | 41 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-08', 'value': 63.3} |

## 23. br2602 20251218 night （historical_validation）

- Episode：`br:20251218`
- 决策时点：`2025-12-17T20:59:00+08:00`
- 执行时点：`2025-12-17T21:01:00+08:00`
- label 窗口：`2025-12-17T21:01:00+08:00` → `2025-12-17T23:00:00+08:00`
- 目标值：-0.0013492244 = ln(11110 / 11125)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-17T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-17T14:59:00+08:00', 'close': 11160.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251217, 'close': 11160.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-17T20:58:46+08:00` | 14 | {'title': '【光启技术：乐山无人机基地预计明年一季度投产】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-12-17T06:00:00+08:00` | 53940 | {'quote_date': '2025-12-16', 'value': 59.93} |

## 24. br2603 20260114 night （contaminated_audit）

- Episode：`br:20260114`
- 决策时点：`2026-01-13T20:59:00+08:00`
- 执行时点：`2026-01-13T21:01:00+08:00`
- label 窗口：`2026-01-13T21:01:00+08:00` → `2026-01-13T23:00:00+08:00`
- 目标值：0.00081933638 = ln(12210 / 12200)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-13T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-13T14:59:00+08:00', 'close': 12000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260113, 'close': 12000.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T20:53:46+08:00` | 314 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 25. br2603 20260119 night （contaminated_audit）

- Episode：`br:20260119`
- 决策时点：`2026-01-16T20:59:00+08:00`
- 执行时点：`2026-01-16T21:01:00+08:00`
- label 窗口：`2026-01-16T21:01:00+08:00` → `2026-01-16T23:00:00+08:00`
- 目标值：-0.0042247634 = ln(11810 / 11860)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-16T14:59:00+08:00', 'close': 11815.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260116, 'close': 11815.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T20:57:39+08:00` | 81 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 26. br2603 20260204 day （contaminated_audit）

- Episode：`br:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：-0.0052434577 = ln(13315 / 13385)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T23:00:00+08:00` | 35940 | {'bar_start': '2026-02-03T22:59:00+08:00', 'close': 13365.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260203, 'close': 13185.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 27. br2605 20260420 night （contaminated_audit）

- Episode：`br:20260420`
- 决策时点：`2026-04-17T20:59:00+08:00`
- 执行时点：`2026-04-17T21:01:00+08:00`
- label 窗口：`2026-04-17T21:01:00+08:00` → `2026-04-17T23:00:00+08:00`
- 目标值：0.0057434746 = ln(15715 / 15625)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-04-17T14:59:00+08:00', 'close': 15950.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260417, 'close': 15950.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T20:58:27+08:00` | 33 | {'title': '【深圳市发改委与澳门特区政府低空经济发展工作组开展低空经济交流】', 'labels': 'TMT行业观察 民航机场 快递物流 无人机 低空经济'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 53940 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 28. br2609 20260702 day （contaminated_audit）

- Episode：`br:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：-0.011965955 = ln(11630 / 11770)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-01T22:59:00+08:00', 'close': 11815.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260701, 'close': 11825.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. br2609 20260716 day （contaminated_audit）

- Episode：`br:20260716`
- 决策时点：`2026-07-16T08:59:00+08:00`
- 执行时点：`2026-07-16T09:01:00+08:00`
- label 窗口：`2026-07-16T09:01:00+08:00` → `2026-07-16T15:00:00+08:00`
- 目标值：-0.0018178518 = ln(13740 / 13765)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-15T22:59:00+08:00', 'close': 13760.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260715, 'close': 13880.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2434540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-13', 'value': 81.62} |
