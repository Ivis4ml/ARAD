# SC Temporal Spine 人工回放清单（bz_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`3fed731808d67672437e22a065a0d3f70f81ed3af14bf5781c7ec3dedb88b27f`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. bz2603 20250731 day （historical_validation）

- Episode：`bz:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.0061772589 = ln(6294 / 6333)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T23:00:00+08:00` | 35940 | {'bar_start': '2025-07-30T22:59:00+08:00', 'close': 6330.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250730, 'close': 6307.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 01. bz2603 20250807 night （historical_validation）

- Episode：`bz:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:01:00+08:00`
- label 窗口：`2025-08-06T21:01:00+08:00` → `2025-08-06T23:00:00+08:00`
- 目标值：0.0007977663 = ln(6270 / 6265)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 6246.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.031000+08:00` | 21539 | {'trading_day': 20250806, 'close': 6246.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

## 02. bz2603 20250829 night （historical_validation）

- Episode：`bz:20250829`
- 决策时点：`2025-08-28T20:59:00+08:00`
- 执行时点：`2025-08-28T21:01:00+08:00`
- label 窗口：`2025-08-28T21:01:00+08:00` → `2025-08-28T23:00:00+08:00`
- 目标值：-0.0070660059 = ln(6064 / 6107)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-28T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-28T14:59:00+08:00', 'close': 6095.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-28T15:00:00.047000+08:00` | 21539 | {'trading_day': 20250828, 'close': 6095.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-28T20:58:39+08:00` | 21 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2025-08-28T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-27', 'value': 67.75} |

## 03. bz2603 20250926 day （historical_validation）

- Episode：`bz:20250926`
- 决策时点：`2025-09-26T08:59:00+08:00`
- 执行时点：`2025-09-26T09:01:00+08:00`
- label 窗口：`2025-09-26T09:01:00+08:00` → `2025-09-26T15:00:00+08:00`
- 目标值：-0.0013543256 = ln(5903 / 5911)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-25T23:00:00+08:00` | 35940 | {'bar_start': '2025-09-25T22:59:00+08:00', 'close': 5894.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-25T15:00:00.016000+08:00` | 64739 | {'trading_day': 20250925, 'close': 5922.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-26T08:48:56+08:00` | 604 | {'title': '【两市融资余额增加132.79亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-09-26T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-25', 'value': 70.48} |

## 04. bz2603 20251016 day （historical_validation）

- Episode：`bz:20251016`
- 决策时点：`2025-10-16T08:59:00+08:00`
- 执行时点：`2025-10-16T09:01:00+08:00`
- label 窗口：`2025-10-16T09:01:00+08:00` → `2025-10-16T15:00:00+08:00`
- 目标值：0.019682153 = ln(5644 / 5534)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-15T23:00:00+08:00` | 35940 | {'bar_start': '2025-10-15T22:59:00+08:00', 'close': 5524.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-10-15T15:00:00.039000+08:00` | 64739 | {'trading_day': 20251015, 'close': 5579.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-16T08:57:13+08:00` | 107 | {'title': '【预告】', 'labels': '提醒电报'} |
| brent_last_close | intl_brent | `2025-10-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-15', 'value': 62.33} |

## 05. bz2603 20251022 day （historical_validation）

- Episode：`bz:20251022`
- 决策时点：`2025-10-22T08:59:00+08:00`
- 执行时点：`2025-10-22T09:01:00+08:00`
- label 窗口：`2025-10-22T09:01:00+08:00` → `2025-10-22T15:00:00+08:00`
- 目标值：0.013027143 = ln(5563 / 5491)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-21T23:00:00+08:00` | 35940 | {'bar_start': '2025-10-21T22:59:00+08:00', 'close': 5484.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-10-21T15:00:00.008000+08:00` | 64739 | {'trading_day': 20251021, 'close': 5476.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-22T08:56:56+08:00` | 124 | {'title': '【芯华章宣布开放免费使用商用级仿真器GalaxSim】', 'labels': 'TMT行业观察 半导体芯片 EDA'} |
| brent_last_close | intl_brent | `2025-10-22T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-21', 'value': 61.0} |

## 06. bz2603 20251121 night （historical_validation）

- Episode：`bz:20251121`
- 决策时点：`2025-11-20T20:59:00+08:00`
- 执行时点：`2025-11-20T21:01:00+08:00`
- label 窗口：`2025-11-20T21:01:00+08:00` → `2025-11-20T23:00:00+08:00`
- 目标值：0.0019655148 = ln(5602 / 5591)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-20T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-20T14:59:00+08:00', 'close': 5596.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-20T15:00:00.013000+08:00` | 21539 | {'trading_day': 20251120, 'close': 5596.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-20T20:57:57+08:00` | 63 | {'title': '【华为乾崑连发“两境”：奕境、启境首款车型明年推出】', 'labels': 'TMT行业观察 华为最新动态'} |
| brent_last_close | intl_brent | `2025-11-20T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-19', 'value': 63.78} |

## 07. bz2603 20251125 day （historical_validation）

- Episode：`bz:20251125`
- 决策时点：`2025-11-25T08:59:00+08:00`
- 执行时点：`2025-11-25T09:01:00+08:00`
- label 窗口：`2025-11-25T09:01:00+08:00` → `2025-11-25T15:00:00+08:00`
- 目标值：-0.0042415923 = ln(5411 / 5434)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-24T23:00:00+08:00` | 35940 | {'bar_start': '2025-11-24T22:59:00+08:00', 'close': 5433.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-11-24T15:00:00.014000+08:00` | 64739 | {'trading_day': 20251124, 'close': 5435.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-25T08:53:20+08:00` | 340 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-24', 'value': 64.83} |

## 08. bz2603 20251127 night （historical_validation）

- Episode：`bz:20251127`
- 决策时点：`2025-11-26T20:59:00+08:00`
- 执行时点：`2025-11-26T21:01:00+08:00`
- label 窗口：`2025-11-26T21:01:00+08:00` → `2025-11-26T23:00:00+08:00`
- 目标值：0.0023781224 = ln(5473 / 5460)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-26T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-26T14:59:00+08:00', 'close': 5463.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-26T15:00:00.002000+08:00` | 21539 | {'trading_day': 20251126, 'close': 5463.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-26T20:50:10+08:00` | 530 | {'title': '【北京启动专项行动重点整治六类金融领域网络乱象】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-11-26T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-25', 'value': 63.99} |

## 09. bz2603 20251201 night （historical_validation）

- Episode：`bz:20251201`
- 决策时点：`2025-11-28T20:59:00+08:00`
- 执行时点：`2025-11-28T21:01:00+08:00`
- label 窗口：`2025-11-28T21:01:00+08:00` → `2025-11-28T23:00:00+08:00`
- 目标值：0.00054899809 = ln(5466 / 5463)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-28T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-28T14:59:00+08:00', 'close': 5479.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-28T15:00:00.045000+08:00` | 21539 | {'trading_day': 20251128, 'close': 5479.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-28T20:55:11+08:00` | 229 | {'title': '', 'labels': '期货市场情报 期权'} |
| brent_last_close | intl_brent | `2025-11-28T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-27', 'value': 64.18} |

## 10. bz2603 20251210 day （historical_validation）

- Episode：`bz:20251210`
- 决策时点：`2025-12-10T08:59:00+08:00`
- 执行时点：`2025-12-10T09:01:00+08:00`
- label 窗口：`2025-12-10T09:01:00+08:00` → `2025-12-10T15:00:00+08:00`
- 目标值：0.0012875933 = ln(5440 / 5433)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-09T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-09T22:59:00+08:00', 'close': 5431.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-09T15:00:00.049000+08:00` | 64739 | {'trading_day': 20251209, 'close': 5492.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-10T08:51:16+08:00` | 464 | {'title': '【三星SDI子公司与美国客户签署13.6亿美元磷酸铁锂电池协议】', 'labels': '盐湖提锂 锂电池 磷酸铁锂'} |
| brent_last_close | intl_brent | `2025-12-10T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-09', 'value': 62.62} |

## 11. bz2603 20251217 night （historical_validation）

- Episode：`bz:20251217`
- 决策时点：`2025-12-16T20:59:00+08:00`
- 执行时点：`2025-12-16T21:01:00+08:00`
- label 窗口：`2025-12-16T21:01:00+08:00` → `2025-12-16T23:00:00+08:00`
- 目标值：-0.0053500727 = ln(5406 / 5435)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-16T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-16T14:59:00+08:00', 'close': 5440.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-16T15:00:00.041000+08:00` | 21539 | {'trading_day': 20251216, 'close': 5440.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-16T20:58:30+08:00` | 30 | {'title': '【中航成飞：全资子公司签署投资合作协议书】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-12-16T06:00:00+08:00` | 53940 | {'quote_date': '2025-12-15', 'value': 61.55} |

## 12. bz2603 20251225 day （historical_validation）

- Episode：`bz:20251225`
- 决策时点：`2025-12-25T08:59:00+08:00`
- 执行时点：`2025-12-25T09:01:00+08:00`
- label 窗口：`2025-12-25T09:01:00+08:00` → `2025-12-25T15:00:00+08:00`
- 目标值：0.0029487673 = ln(5434 / 5418)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-24T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-24T22:59:00+08:00', 'close': 5419.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-24T15:00:00.024000+08:00` | 64739 | {'trading_day': 20251224, 'close': 5461.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-25T08:53:06+08:00` | 354 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 13. bz2603 20251231 day （historical_validation）

- Episode：`bz:20251231`
- 决策时点：`2025-12-31T08:59:00+08:00`
- 执行时点：`2025-12-31T09:01:00+08:00`
- label 窗口：`2025-12-31T09:01:00+08:00` → `2025-12-31T15:00:00+08:00`
- 目标值：-0.0034719085 = ln(5463 / 5482)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-30T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-30T22:59:00+08:00', 'close': 5498.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-30T15:00:00.004000+08:00` | 64739 | {'trading_day': 20251230, 'close': 5487.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-31T08:56:59+08:00` | 121 | {'title': '【雷军：跨年直播推迟到1月3日晚7点】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-30', 'value': 62.3} |

## 14. bz2603 20260114 night （contaminated_audit）

- Episode：`bz:20260114`
- 决策时点：`2026-01-13T20:59:00+08:00`
- 执行时点：`2026-01-13T21:01:00+08:00`
- label 窗口：`2026-01-13T21:01:00+08:00` → `2026-01-13T23:00:00+08:00`
- 目标值：0.014723104 = ln(5679 / 5596)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-13T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-13T14:59:00+08:00', 'close': 5584.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-13T15:00:00.004000+08:00` | 21539 | {'trading_day': 20260113, 'close': 5584.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T20:53:46+08:00` | 314 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 15. bz2603 20260119 night （contaminated_audit）

- Episode：`bz:20260119`
- 决策时点：`2026-01-16T20:59:00+08:00`
- 执行时点：`2026-01-16T21:01:00+08:00`
- label 窗口：`2026-01-16T21:01:00+08:00` → `2026-01-16T23:00:00+08:00`
- 目标值：0.0028139308 = ln(5694 / 5678)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-16T14:59:00+08:00', 'close': 5656.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-16T15:00:00.003000+08:00` | 21539 | {'trading_day': 20260116, 'close': 5656.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T20:57:39+08:00` | 81 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 16. bz2603 20260122 day （contaminated_audit）

- Episode：`bz:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.020883211 = ln(6000 / 5876)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T23:00:00+08:00` | 35940 | {'bar_start': '2026-01-21T22:59:00+08:00', 'close': 5876.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.033000+08:00` | 64739 | {'trading_day': 20260121, 'close': 5805.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 17. bz2603 20260129 night （contaminated_audit）

- Episode：`bz:20260129`
- 决策时点：`2026-01-28T20:59:00+08:00`
- 执行时点：`2026-01-28T21:01:00+08:00`
- label 窗口：`2026-01-28T21:01:00+08:00` → `2026-01-28T23:00:00+08:00`
- 目标值：0.00227976 = ln(6148 / 6134)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-28T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-28T14:59:00+08:00', 'close': 6130.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-28T15:00:00.025000+08:00` | 21539 | {'trading_day': 20260128, 'close': 6130.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-28T20:54:26+08:00` | 274 | {'title': '【荷兰国际集团CEO：今年欧洲将迎来一波本土银行并购浪潮】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-28T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-27', 'value': 70.28} |

## 18. bz2603 20260204 day （contaminated_audit）

- Episode：`bz:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：0.0061379614 = ln(6210 / 6172)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T23:00:00+08:00` | 35940 | {'bar_start': '2026-02-03T22:59:00+08:00', 'close': 6137.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.019000+08:00` | 64739 | {'trading_day': 20260203, 'close': 6096.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 19. bz2604 20260306 night （contaminated_audit）

- Episode：`bz:20260306`
- 决策时点：`2026-03-05T20:59:00+08:00`
- 执行时点：`2026-03-05T21:01:00+08:00`
- label 窗口：`2026-03-05T21:01:00+08:00` → `2026-03-05T23:00:00+08:00`
- 目标值：0.0012244067 = ln(7355 / 7346)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-05T15:00:00+08:00` | 21540 | {'bar_start': '2026-03-05T14:59:00+08:00', 'close': 7251.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-05T15:00:00.044000+08:00` | 21539 | {'trading_day': 20260305, 'close': 7251.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-05T20:52:54+08:00` | 366 | {'title': '【阿塞拜疆称遭到伊朗发动的“恐怖袭击”】', 'labels': '无人机 中东冲突 环球市场情报'} |
| brent_last_close | intl_brent | `2026-03-05T06:00:00+08:00` | 53940 | {'quote_date': '2026-03-04', 'value': 81.56} |

## 20. bz2604 20260316 day （contaminated_audit）

- Episode：`bz:20260316`
- 决策时点：`2026-03-16T08:59:00+08:00`
- 执行时点：`2026-03-16T09:01:00+08:00`
- label 窗口：`2026-03-16T09:01:00+08:00` → `2026-03-16T15:00:00+08:00`
- 目标值：0.012023239 = ln(8451 / 8350)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-13T23:00:00+08:00` | 208740 | {'bar_start': '2026-03-13T22:59:00+08:00', 'close': 8490.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-03-13T15:00:00.003000+08:00` | 237539 | {'trading_day': 20260313, 'close': 8288.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-16T08:58:48+08:00` | 12 | {'title': '【俄称受中东局势影响 乌克兰问题谈判暂停】', 'labels': '俄乌冲突快报'} |
| brent_last_close | intl_brent | `2026-03-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-03-13', 'value': 103.23} |

## 21. bz2605 20260420 night （contaminated_audit）

- Episode：`bz:20260420`
- 决策时点：`2026-04-17T20:59:00+08:00`
- 执行时点：`2026-04-17T21:01:00+08:00`
- label 窗口：`2026-04-17T21:01:00+08:00` → `2026-04-17T23:00:00+08:00`
- 目标值：-0.00035118525 = ln(8541 / 8544)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-04-17T14:59:00+08:00', 'close': 8723.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-17T15:00:00.038000+08:00` | 21539 | {'trading_day': 20260417, 'close': 8723.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T20:58:27+08:00` | 33 | {'title': '【深圳市发改委与澳门特区政府低空经济发展工作组开展低空经济交流】', 'labels': 'TMT行业观察 民航机场 快递物流 无人机 低空经济'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 53940 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 22. bz2606 20260512 night （contaminated_audit）

- Episode：`bz:20260512`
- 决策时点：`2026-05-11T20:59:00+08:00`
- 执行时点：`2026-05-11T21:01:00+08:00`
- label 窗口：`2026-05-11T21:01:00+08:00` → `2026-05-11T23:00:00+08:00`
- 目标值：-0.0075971447 = ln(8130 / 8192)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-11T15:00:00+08:00` | 21540 | {'bar_start': '2026-05-11T14:59:00+08:00', 'close': 8235.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-11T15:00:00.049000+08:00` | 21539 | {'trading_day': 20260511, 'close': 8235.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T20:57:57+08:00` | 63 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 23. bz2606 20260519 night （contaminated_audit）

- Episode：`bz:20260519`
- 决策时点：`2026-05-18T20:59:00+08:00`
- 执行时点：`2026-05-18T21:01:00+08:00`
- label 窗口：`2026-05-18T21:01:00+08:00` → `2026-05-18T23:00:00+08:00`
- 目标值：0.011686073 = ln(8263 / 8167)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-18T15:00:00+08:00` | 21540 | {'bar_start': '2026-05-18T14:59:00+08:00', 'close': 8304.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-18T15:00:00.042000+08:00` | 21539 | {'trading_day': 20260518, 'close': 8304.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T20:57:20+08:00` | 100 | {'title': '', 'labels': '美国政治'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 24. bz2607 20260601 night （contaminated_audit）

- Episode：`bz:20260601`
- 决策时点：`2026-05-29T20:59:00+08:00`
- 执行时点：`2026-05-29T21:01:00+08:00`
- label 窗口：`2026-05-29T21:01:00+08:00` → `2026-05-29T23:00:00+08:00`
- 目标值：-0.0043068707 = ln(7414 / 7446)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-29T15:00:00+08:00` | 21540 | {'bar_start': '2026-05-29T14:59:00+08:00', 'close': 7461.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-29T15:00:00.035000+08:00` | 21539 | {'trading_day': 20260529, 'close': 7461.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-29T20:58:40+08:00` | 20 | {'title': '【利通电子：暂无token分成业务的具体实施计划】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2026-05-29T06:00:00+08:00` | 53940 | {'quote_date': '2026-05-28', 'value': 95.47} |

## 25. bz2607 20260602 day （contaminated_audit）

- Episode：`bz:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：-0.0058293753 = ln(7526 / 7570)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-01T22:59:00+08:00', 'close': 7639.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.004000+08:00` | 64739 | {'trading_day': 20260601, 'close': 7532.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 26. bz2607 20260610 day （contaminated_audit）

- Episode：`bz:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：0.0013308493 = ln(7519 / 7509)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-09T22:59:00+08:00', 'close': 7478.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260609, 'close': 7494.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 27. bz2608 20260629 day （contaminated_audit）

- Episode：`bz:20260629`
- 决策时点：`2026-06-29T08:59:00+08:00`
- 执行时点：`2026-06-29T09:01:00+08:00`
- label 窗口：`2026-06-29T09:01:00+08:00` → `2026-06-29T15:00:00+08:00`
- 目标值：0.013879141 = ln(6312 / 6225)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T23:00:00+08:00` | 208740 | {'bar_start': '2026-06-26T22:59:00+08:00', 'close': 6231.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260626, 'close': 6170.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 965740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-27T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-26', 'value': 70.16} |

## 28. bz2608 20260702 day （contaminated_audit）

- Episode：`bz:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：0.0069204428 = ln(6380 / 6336)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-01T22:59:00+08:00', 'close': 6380.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.045000+08:00` | 64739 | {'trading_day': 20260701, 'close': 6350.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. bz2608 20260716 day （contaminated_audit）

- Episode：`bz:20260716`
- 决策时点：`2026-07-16T08:59:00+08:00`
- 执行时点：`2026-07-16T09:01:00+08:00`
- label 窗口：`2026-07-16T09:01:00+08:00` → `2026-07-16T15:00:00+08:00`
- 目标值：-0.0080440171 = ln(7429 / 7489)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-15T22:59:00+08:00', 'close': 7449.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.012000+08:00` | 64739 | {'trading_day': 20260715, 'close': 7470.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2434540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-13', 'value': 81.62} |
