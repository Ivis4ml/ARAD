# SC Temporal Spine 人工回放清单（lc_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`a9c2ca994bd4018e06ee7c1673156236fcd7c52832984c5dd6c9b7b5b9b0f0e8`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. lc2401 20230829 day （discovery）

- Episode：`lc:20230829`
- 决策时点：`2023-08-29T08:59:00+08:00`
- 执行时点：`2023-08-29T09:01:00+08:00`
- label 窗口：`2023-08-29T09:01:00+08:00` → `2023-08-29T15:00:00+08:00`
- 目标值：0.017594174 = ln(186350 / 183100)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-08-28T15:00:00+08:00` | 64740 | {'bar_start': '2023-08-28T14:59:00+08:00', 'close': 185700.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-08-28T15:00:00.059000+08:00` | 64739 | {'trading_day': 20230828, 'close': 185700.0} |
| cls_last_telegraph | cls_telegraph | `2023-08-29T08:53:35+08:00` | 325 | {'title': '【两市融资余额增加61.62亿元】', 'labels': '融资融券 地产融资 盘面直播'} |
| brent_last_close | intl_brent | `2023-08-26T06:00:00+08:00` | 269940 | {'quote_date': '2023-08-25', 'value': 85.42} |

## 01. lc2401 20230911 day （discovery）

- Episode：`lc:20230911`
- 决策时点：`2023-09-11T08:59:00+08:00`
- 执行时点：`2023-09-11T09:01:00+08:00`
- label 窗口：`2023-09-11T09:01:00+08:00` → `2023-09-11T15:00:00+08:00`
- 目标值：0.026660683 = ln(178650 / 173950)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-09-08T15:00:00+08:00` | 237540 | {'bar_start': '2023-09-08T14:59:00+08:00', 'close': 176500.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-09-08T15:00:00.052000+08:00` | 237539 | {'trading_day': 20230908, 'close': 176500.0} |
| cls_last_telegraph | cls_telegraph | `2023-09-11T08:56:27+08:00` | 153 | {'title': '【早间公告：黄河旋风控股股东筹划重大事项 股票停牌】', 'labels': 'A股公告速递 停复牌动态'} |
| brent_last_close | intl_brent | `2023-09-09T06:00:00+08:00` | 183540 | {'quote_date': '2023-09-08', 'value': 91.85} |

## 02. lc2401 20231102 day （discovery）

- Episode：`lc:20231102`
- 决策时点：`2023-11-02T08:59:00+08:00`
- 执行时点：`2023-11-02T09:01:00+08:00`
- label 窗口：`2023-11-02T09:01:00+08:00` → `2023-11-02T15:00:00+08:00`
- 目标值：-0.010119231 = ln(152400 / 153950)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-11-01T15:00:00+08:00` | 64740 | {'bar_start': '2023-11-01T14:59:00+08:00', 'close': 154000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-11-01T15:00:00.005000+08:00` | 64739 | {'trading_day': 20231101, 'close': 154000.0} |
| cls_last_telegraph | cls_telegraph | `2023-11-02T08:54:49+08:00` | 251 | {'title': '【34家基金、券商资管自购金额达28.62亿 均投向权益基金】', 'labels': '公募基金动态'} |
| brent_last_close | intl_brent | `2023-11-02T06:00:00+08:00` | 10740 | {'quote_date': '2023-11-01', 'value': 86.92} |

## 03. lc2401 20231128 day （discovery）

- Episode：`lc:20231128`
- 决策时点：`2023-11-28T08:59:00+08:00`
- 执行时点：`2023-11-28T09:01:00+08:00`
- label 窗口：`2023-11-28T09:01:00+08:00` → `2023-11-28T15:00:00+08:00`
- 目标值：-0.014906019 = ln(113200 / 114900)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-11-27T15:00:00+08:00` | 64740 | {'bar_start': '2023-11-27T14:59:00+08:00', 'close': 116650.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-11-27T15:00:00.004000+08:00` | 64739 | {'trading_day': 20231127, 'close': 116650.0} |
| cls_last_telegraph | cls_telegraph | `2023-11-28T08:52:56+08:00` | 364 | {'title': '【中国煤炭工业协会：今年煤炭进口增加较快 年底预计进口量将达4.5亿吨】', 'labels': '煤炭'} |
| brent_last_close | intl_brent | `2023-11-28T06:00:00+08:00` | 10740 | {'quote_date': '2023-11-27', 'value': 79.49} |

## 04. lc2401 20231201 day （discovery）

- Episode：`lc:20231201`
- 决策时点：`2023-12-01T08:59:00+08:00`
- 执行时点：`2023-12-01T09:01:00+08:00`
- label 窗口：`2023-12-01T09:01:00+08:00` → `2023-12-01T15:00:00+08:00`
- 目标值：-0.044216717 = ln(101750 / 106350)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-11-30T15:00:00+08:00` | 64740 | {'bar_start': '2023-11-30T14:59:00+08:00', 'close': 106200.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-11-30T15:00:00.005000+08:00` | 64739 | {'trading_day': 20231130, 'close': 106200.0} |
| cls_last_telegraph | cls_telegraph | `2023-12-01T08:57:43+08:00` | 77 | {'title': '【一汽丰田限时购置税补贴5000元】', 'labels': '汽车大新闻'} |
| brent_last_close | intl_brent | `2023-12-01T06:00:00+08:00` | 10740 | {'quote_date': '2023-11-30', 'value': 81.72} |

## 05. lc2407 20240305 day （discovery）

- Episode：`lc:20240305`
- 决策时点：`2024-03-05T08:59:00+08:00`
- 执行时点：`2024-03-05T09:01:00+08:00`
- label 窗口：`2024-03-05T09:01:00+08:00` → `2024-03-05T15:00:00+08:00`
- 目标值：-0.055363887 = ln(111550 / 117900)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-04T15:00:00+08:00` | 64740 | {'bar_start': '2024-03-04T14:59:00+08:00', 'close': 117600.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-04T15:00:00.029000+08:00` | 64739 | {'trading_day': 20240304, 'close': 117600.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-05T08:47:56+08:00` | 664 | {'title': '【2月上海新房成交1347套 外环外成交占比76%】', 'labels': '房地产头条'} |
| brent_last_close | intl_brent | `2024-03-05T06:00:00+08:00` | 10740 | {'quote_date': '2024-03-04', 'value': 86.58} |

## 06. lc2407 20240508 day （discovery）

- Episode：`lc:20240508`
- 决策时点：`2024-05-08T08:59:00+08:00`
- 执行时点：`2024-05-08T09:01:00+08:00`
- label 窗口：`2024-05-08T09:01:00+08:00` → `2024-05-08T15:00:00+08:00`
- 目标值：-0.014618201 = ln(112050 / 113700)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-07T15:00:00+08:00` | 64740 | {'bar_start': '2024-05-07T14:59:00+08:00', 'close': 113900.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-07T15:00:00.005000+08:00` | 64739 | {'trading_day': 20240507, 'close': 113900.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-08T08:49:17+08:00` | 583 | {'title': '【两市融资余额增加29.49亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-08T06:00:00+08:00` | 10740 | {'quote_date': '2024-05-07', 'value': 82.69} |

## 07. lc2407 20240529 day （discovery）

- Episode：`lc:20240529`
- 决策时点：`2024-05-29T08:59:00+08:00`
- 执行时点：`2024-05-29T09:01:00+08:00`
- label 窗口：`2024-05-29T09:01:00+08:00` → `2024-05-29T15:00:00+08:00`
- 目标值：0.0061978744 = ln(105200 / 104550)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-28T15:00:00+08:00` | 64740 | {'bar_start': '2024-05-28T14:59:00+08:00', 'close': 105000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-28T15:00:00.018000+08:00` | 64739 | {'trading_day': 20240528, 'close': 105000.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-29T08:53:42+08:00` | 318 | {'title': '【LG Display已获得批准为iPhone 16 Pro供应OLED】', 'labels': '面板 LED OLED'} |
| brent_last_close | intl_brent | `2024-05-29T06:00:00+08:00` | 10740 | {'quote_date': '2024-05-28', 'value': 81.34} |

## 08. lc2411 20240703 day （discovery）

- Episode：`lc:20240703`
- 决策时点：`2024-07-03T08:59:00+08:00`
- 执行时点：`2024-07-03T09:01:00+08:00`
- label 窗口：`2024-07-03T09:01:00+08:00` → `2024-07-03T15:00:00+08:00`
- 目标值：0.0068984089 = ln(94550 / 93900)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-02T15:00:00+08:00` | 64740 | {'bar_start': '2024-07-02T14:59:00+08:00', 'close': 94050.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-07-02T15:00:00.004000+08:00` | 64739 | {'trading_day': 20240702, 'close': 94050.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-03T08:58:45+08:00` | 15 | {'title': '【三星在第9代V-NAND金属化工艺中应用钼】', 'labels': '化工 有色·钼 半导体芯片'} |
| brent_last_close | intl_brent | `2024-07-03T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-02', 'value': 88.28} |

## 09. lc2411 20240705 day （discovery）

- Episode：`lc:20240705`
- 决策时点：`2024-07-05T08:59:00+08:00`
- 执行时点：`2024-07-05T09:01:00+08:00`
- label 窗口：`2024-07-05T09:01:00+08:00` → `2024-07-05T15:00:00+08:00`
- 目标值：0.0074826645 = ln(93900 / 93200)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-04T15:00:00+08:00` | 64740 | {'bar_start': '2024-07-04T14:59:00+08:00', 'close': 93950.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-07-04T15:00:00.004000+08:00` | 64739 | {'trading_day': 20240704, 'close': 93950.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-05T08:50:31+08:00` | 509 | {'title': '【新一轮强降雨来袭 江南华南高温“超长待机”】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2024-07-05T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-04', 'value': 88.34} |

## 10. lc2411 20240820 day （discovery）

- Episode：`lc:20240820`
- 决策时点：`2024-08-20T08:59:00+08:00`
- 执行时点：`2024-08-20T09:01:00+08:00`
- label 窗口：`2024-08-20T09:01:00+08:00` → `2024-08-20T15:00:00+08:00`
- 目标值：0.020202707 = ln(75000 / 73500)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-08-19T15:00:00+08:00` | 64740 | {'bar_start': '2024-08-19T14:59:00+08:00', 'close': 73400.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-08-19T15:00:00.004000+08:00` | 64739 | {'trading_day': 20240819, 'close': 73400.0} |
| cls_last_telegraph | cls_telegraph | `2024-08-20T08:54:06+08:00` | 294 | {'title': '【成都市足球协会原主席兼秘书长辜建明获刑六年】', 'labels': '足球盛宴2026'} |
| brent_last_close | intl_brent | `2024-08-20T06:00:00+08:00` | 10740 | {'quote_date': '2024-08-19', 'value': 81.09} |

## 11. lc2411 20240911 day （discovery）

- Episode：`lc:20240911`
- 决策时点：`2024-09-11T08:59:00+08:00`
- 执行时点：`2024-09-11T09:01:00+08:00`
- label 窗口：`2024-09-11T09:01:00+08:00` → `2024-09-11T15:00:00+08:00`
- 目标值：0.055023701 = ln(78450 / 74250)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-10T15:00:00+08:00` | 64740 | {'bar_start': '2024-09-10T14:59:00+08:00', 'close': 72150.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-10T15:00:00.019000+08:00` | 64739 | {'trading_day': 20240910, 'close': 72150.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-11T08:57:25+08:00` | 95 | {'title': '【台风摩羯已致越南140余人死亡】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-09-11T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-10', 'value': 70.34} |

## 12. lc2411 20241015 day （discovery）

- Episode：`lc:20241015`
- 决策时点：`2024-10-15T08:59:00+08:00`
- 执行时点：`2024-10-15T09:01:00+08:00`
- label 窗口：`2024-10-15T09:01:00+08:00` → `2024-10-15T15:00:00+08:00`
- 目标值：-0.000680967 = ln(73400 / 73450)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-10-14T15:00:00+08:00` | 64740 | {'bar_start': '2024-10-14T14:59:00+08:00', 'close': 73100.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-10-14T15:00:00.016000+08:00` | 64739 | {'trading_day': 20241014, 'close': 73100.0} |
| cls_last_telegraph | cls_telegraph | `2024-10-15T08:51:31+08:00` | 449 | {'title': '【美国政府据悉考虑限制英伟达、AMD向部分国家销售AI芯片 重点针对波斯湾国家】', 'labels': '半导体芯片 人工智能 盘面直播'} |
| brent_last_close | intl_brent | `2024-10-15T06:00:00+08:00` | 10740 | {'quote_date': '2024-10-14', 'value': 78.47} |

## 13. lc2501 20241107 day （discovery）

- Episode：`lc:20241107`
- 决策时点：`2024-11-07T08:59:00+08:00`
- 执行时点：`2024-11-07T09:01:00+08:00`
- label 窗口：`2024-11-07T09:01:00+08:00` → `2024-11-07T15:00:00+08:00`
- 目标值：0.017722814 = ln(76850 / 75500)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-11-06T15:00:00+08:00` | 64740 | {'bar_start': '2024-11-06T14:59:00+08:00', 'close': 75900.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-11-06T15:00:00.135000+08:00` | 64739 | {'trading_day': 20241106, 'close': 75900.0} |
| cls_last_telegraph | cls_telegraph | `2024-11-07T08:49:24+08:00` | 576 | {'title': '【两市融资余额增加224.77亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态'} |
| brent_last_close | intl_brent | `2024-11-07T06:00:00+08:00` | 10740 | {'quote_date': '2024-11-06', 'value': 76.52} |

## 14. lc2505 20250110 day （historical_validation）

- Episode：`lc:20250110`
- 决策时点：`2025-01-10T08:59:00+08:00`
- 执行时点：`2025-01-10T09:01:00+08:00`
- label 窗口：`2025-01-10T09:01:00+08:00` → `2025-01-10T15:00:00+08:00`
- 目标值：0.00051347883 = ln(77920 / 77880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-09T15:00:00+08:00` | 64740 | {'bar_start': '2025-01-09T14:59:00+08:00', 'close': 78240.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-09T15:00:00.005000+08:00` | 64739 | {'trading_day': 20250109, 'close': 78240.0} |
| cls_last_telegraph | cls_telegraph | `2025-01-10T08:56:38+08:00` | 142 | {'title': '【预告】', 'labels': '提醒电报'} |
| brent_last_close | intl_brent | `2025-01-10T06:00:00+08:00` | 10740 | {'quote_date': '2025-01-09', 'value': 78.44} |

## 15. lc2505 20250304 day （historical_validation）

- Episode：`lc:20250304`
- 决策时点：`2025-03-04T08:59:00+08:00`
- 执行时点：`2025-03-04T09:01:00+08:00`
- label 窗口：`2025-03-04T09:01:00+08:00` → `2025-03-04T15:00:00+08:00`
- 目标值：-0.0013278451 = ln(75260 / 75360)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-03-03T15:00:00+08:00` | 64740 | {'bar_start': '2025-03-03T14:59:00+08:00', 'close': 75400.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-03-03T15:00:00.004000+08:00` | 64739 | {'trading_day': 20250303, 'close': 75400.0} |
| cls_last_telegraph | cls_telegraph | `2025-03-04T08:52:39+08:00` | 381 | {'title': '【东部战区海军舰艇编队开展实战化训练】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-03-04T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-03', 'value': 72.85} |

## 16. lc2507 20250508 day （historical_validation）

- Episode：`lc:20250508`
- 决策时点：`2025-05-08T08:59:00+08:00`
- 执行时点：`2025-05-08T09:01:00+08:00`
- label 窗口：`2025-05-08T09:01:00+08:00` → `2025-05-08T15:00:00+08:00`
- 目标值：0.0078088793 = ln(64280 / 63780)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-05-07T15:00:00+08:00` | 64740 | {'bar_start': '2025-05-07T14:59:00+08:00', 'close': 64160.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-05-07T15:00:00.017000+08:00` | 64739 | {'trading_day': 20250507, 'close': 64160.0} |
| cls_last_telegraph | cls_telegraph | `2025-05-08T08:56:49+08:00` | 131 | {'title': '【深交所：将陆控调出港股通标的证券名单】', 'labels': '港股动态 港股通'} |
| brent_last_close | intl_brent | `2025-05-08T06:00:00+08:00` | 10740 | {'quote_date': '2025-05-07', 'value': 60.31} |

## 17. lc2507 20250515 day （historical_validation）

- Episode：`lc:20250515`
- 决策时点：`2025-05-15T08:59:00+08:00`
- 执行时点：`2025-05-15T09:01:00+08:00`
- label 窗口：`2025-05-15T09:01:00+08:00` → `2025-05-15T15:00:00+08:00`
- 目标值：-0.010549276 = ln(64120 / 64800)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-05-14T15:00:00+08:00` | 64740 | {'bar_start': '2025-05-14T14:59:00+08:00', 'close': 65200.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-05-14T15:00:00.063000+08:00` | 64739 | {'trading_day': 20250514, 'close': 65200.0} |
| cls_last_telegraph | cls_telegraph | `2025-05-15T08:52:14+08:00` | 406 | {'title': '【OpenAI宣布向ChatGPT用户开放GPT-4.1模型】', 'labels': '人工智能 ChatGPT'} |
| brent_last_close | intl_brent | `2025-05-15T06:00:00+08:00` | 10740 | {'quote_date': '2025-05-14', 'value': 65.91} |

## 18. lc2509 20250715 day （historical_validation）

- Episode：`lc:20250715`
- 决策时点：`2025-07-15T08:59:00+08:00`
- 执行时点：`2025-07-15T09:01:00+08:00`
- label 窗口：`2025-07-15T09:01:00+08:00` → `2025-07-15T15:00:00+08:00`
- 目标值：0.0090416529 = ln(66660 / 66060)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-14T15:00:00+08:00` | 64740 | {'bar_start': '2025-07-14T14:59:00+08:00', 'close': 66480.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-14T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250714, 'close': 66480.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-15T08:49:08+08:00` | 592 | {'title': '【天舟九号成功对接空间站】', 'labels': '太空探索'} |
| brent_last_close | intl_brent | `2025-07-15T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-14', 'value': 70.96} |

## 19. lc2511 20250812 day （historical_validation）

- Episode：`lc:20250812`
- 决策时点：`2025-08-12T08:59:00+08:00`
- 执行时点：`2025-08-12T09:01:00+08:00`
- label 窗口：`2025-08-12T09:01:00+08:00` → `2025-08-12T15:00:00+08:00`
- 目标值：-0.051717344 = ln(82520 / 86900)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-11T14:59:00+08:00', 'close': 81000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.019000+08:00` | 64739 | {'trading_day': 20250811, 'close': 81000.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-12T08:52:43+08:00` | 377 | {'title': '【德国7月破产企业数量同比大幅增加】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-11', 'value': 67.36} |

## 20. lc2511 20250912 day （historical_validation）

- Episode：`lc:20250912`
- 决策时点：`2025-09-12T08:59:00+08:00`
- 执行时点：`2025-09-12T09:01:00+08:00`
- label 窗口：`2025-09-12T09:01:00+08:00` → `2025-09-12T15:00:00+08:00`
- 目标值：0.0033783816 = ln(71160 / 70920)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-11T14:59:00+08:00', 'close': 71000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-11T15:00:00.017000+08:00` | 64739 | {'trading_day': 20250911, 'close': 71000.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-12T08:58:04+08:00` | 56 | {'title': '【江苏重庆云南等地需防范暴雨 北方多地秋意渐浓 全国天气速览】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-09-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-11', 'value': 67.25} |

## 21. lc2511 20250919 day （historical_validation）

- Episode：`lc:20250919`
- 决策时点：`2025-09-19T08:59:00+08:00`
- 执行时点：`2025-09-19T09:01:00+08:00`
- label 窗口：`2025-09-19T09:01:00+08:00` → `2025-09-19T15:00:00+08:00`
- 目标值：0.015259152 = ln(73960 / 72840)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-18T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-18T14:59:00+08:00', 'close': 72880.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-18T15:00:00.072000+08:00` | 64739 | {'trading_day': 20250918, 'close': 72880.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-19T08:49:35+08:00` | 565 | {'title': '【两市融资余额减少26.28亿元】', 'labels': '盘面直播 融资融券'} |
| brent_last_close | intl_brent | `2025-09-19T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-18', 'value': 67.83} |

## 22. lc2605 20251209 day （historical_validation）

- Episode：`lc:20251209`
- 决策时点：`2025-12-09T08:59:00+08:00`
- 执行时点：`2025-12-09T09:01:00+08:00`
- label 窗口：`2025-12-09T09:01:00+08:00` → `2025-12-09T15:00:00+08:00`
- 目标值：-0.016670615 = ln(92800 / 94360)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-08T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-08T14:59:00+08:00', 'close': 94840.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-08T15:00:00.109000+08:00` | 64739 | {'trading_day': 20251208, 'close': 94840.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-09T08:58:19+08:00` | 41 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-08', 'value': 63.3} |

## 23. lc2605 20251217 day （historical_validation）

- Episode：`lc:20251217`
- 决策时点：`2025-12-17T08:59:00+08:00`
- 执行时点：`2025-12-17T09:01:00+08:00`
- label 窗口：`2025-12-17T09:01:00+08:00` → `2025-12-17T15:00:00+08:00`
- 目标值：0.052350167 = ln(108620 / 103080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-16T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-16T14:59:00+08:00', 'close': 100600.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-16T15:00:00.031000+08:00` | 64739 | {'trading_day': 20251216, 'close': 100600.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-17T08:56:14+08:00` | 166 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-17T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-16', 'value': 59.93} |

## 24. lc2605 20260113 day （contaminated_audit）

- Episode：`lc:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：0.011928571 = ln(166980 / 165000)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-12T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-12T14:59:00+08:00', 'close': 156060.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.005000+08:00` | 64739 | {'trading_day': 20260112, 'close': 156060.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 25. lc2605 20260116 day （contaminated_audit）

- Episode：`lc:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：NULL（no-trade：exit_at_price_limit）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-15T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-15T14:59:00+08:00', 'close': 163220.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.007000+08:00` | 64739 | {'trading_day': 20260115, 'close': 163220.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 26. lc2605 20260204 day （contaminated_audit）

- Episode：`lc:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：-0.024291606 = ln(147220 / 150840)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T15:00:00+08:00` | 64740 | {'bar_start': '2026-02-03T14:59:00+08:00', 'close': 148100.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.028000+08:00` | 64739 | {'trading_day': 20260203, 'close': 148100.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 27. lc2609 20260417 day （contaminated_audit）

- Episode：`lc:20260417`
- 决策时点：`2026-04-17T08:59:00+08:00`
- 执行时点：`2026-04-17T09:01:00+08:00`
- label 窗口：`2026-04-17T09:01:00+08:00` → `2026-04-17T15:00:00+08:00`
- 目标值：0.00045065346 = ln(177560 / 177480)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-16T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-16T14:59:00+08:00', 'close': 176000.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-16T15:00:00.018000+08:00` | 64739 | {'trading_day': 20260416, 'close': 176000.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T08:48:12+08:00` | 648 | {'title': '【两市融资余额增加107.35亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 28. lc2609 20260602 day （contaminated_audit）

- Episode：`lc:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：-0.028495204 = ln(172980 / 177980)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 178900.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260601, 'close': 178900.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 29. lc2609 20260702 day （contaminated_audit）

- Episode：`lc:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：-0.00024381324 = ln(164040 / 164080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 164560.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.010000+08:00` | 64739 | {'trading_day': 20260701, 'close': 164560.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |
