# SC Temporal Spine 人工回放清单（ni_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`7053d901b5c41c58250cd3d5fb01b0fe12d3d197f3c3baf02696de50d09e3836`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. ni2301 20221209 night （discovery）

- Episode：`ni:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-09T01:00:00+08:00`
- 目标值：-0.023660051 = ln(217190 / 222390)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 218810.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 218810.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. ni2301 20221209 day （discovery）

- Episode：`ni:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.02213742 = ln(221520 / 216670)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-09T01:00:00+08:00` | 28740 | {'bar_start': '2022-12-09T00:59:00+08:00', 'close': 217190.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 218810.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. ni2302 20230117 day （discovery）

- Episode：`ni:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：-0.0055995277 = ln(204800 / 205950)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-17T01:00:00+08:00` | 28740 | {'bar_start': '2023-01-17T00:59:00+08:00', 'close': 205870.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 203250.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. ni2303 20230216 day （discovery）

- Episode：`ni:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0059199273 = ln(205000 / 203790)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-16T01:00:00+08:00` | 28740 | {'bar_start': '2023-02-16T00:59:00+08:00', 'close': 203970.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 205060.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. ni2306 20230523 night （discovery）

- Episode：`ni:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-23T01:00:00+08:00`
- 目标值：0.0010186656 = ln(166970 / 166800)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 166310.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 166310.0} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. ni2307 20230615 night （discovery）

- Episode：`ni:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-15T01:00:00+08:00`
- 目标值：0.0065581617 = ln(172870 / 171740)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 169950.00000000006, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 169950.00000000006} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. ni2308 20230714 day （discovery）

- Episode：`ni:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.0052808572 = ln(166200 / 167080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-14T01:00:00+08:00` | 28740 | {'bar_start': '2023-07-14T00:59:00+08:00', 'close': 166580.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 166890.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. ni2308 20230724 day （discovery）

- Episode：`ni:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：-0.0040177307 = ln(168910 / 169590)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-22T01:00:00+08:00` | 201540 | {'bar_start': '2023-07-22T00:59:00+08:00', 'close': 168420.00000000006, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 170530.00000000006} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. ni2402 20240117 night （discovery）

- Episode：`ni:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-17T01:00:00+08:00`
- 目标值：0.0038426899 = ln(127760 / 127270)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 126850.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 126850.0} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. ni2405 20240301 day （discovery）

- Episode：`ni:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.0046582805 = ln(137070 / 137710)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-01T01:00:00+08:00` | 28740 | {'bar_start': '2024-03-01T00:59:00+08:00', 'close': 138020.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 137710.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. ni2405 20240401 night （discovery）

- Episode：`ni:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-30T01:00:00+08:00`
- 目标值：-0.0066797438 = ln(129810 / 130680)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 130920.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 130920.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. ni2406 20240527 day （discovery）

- Episode：`ni:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：0.0038654354 = ln(152930 / 152340)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-25T01:00:00+08:00` | 201540 | {'bar_start': '2024-05-25T00:59:00+08:00', 'close': 152020.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 152780.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. ni2409 20240709 day （discovery）

- Episode：`ni:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：-0.0042114497 = ln(137430 / 138010)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T01:00:00+08:00` | 28740 | {'bar_start': '2024-07-09T00:59:00+08:00', 'close': 137870.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 138610.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. ni2410 20240918 night （discovery）

- Episode：`ni:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-14T01:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 124110.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 124110.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. ni2410 20240924 day （discovery）

- Episode：`ni:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.011431418 = ln(126690 / 125250)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-24T01:00:00+08:00` | 28740 | {'bar_start': '2024-09-24T00:59:00+08:00', 'close': 125410.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 124830.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. ni2501 20241206 day （discovery）

- Episode：`ni:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.0097049525 = ln(126320 / 125100)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-06T01:00:00+08:00` | 28740 | {'bar_start': '2024-12-06T00:59:00+08:00', 'close': 125170.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 125070.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. ni2502 20241230 day （discovery）

- Episode：`ni:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.0066717823 = ln(124820 / 123990)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-28T01:00:00+08:00` | 201540 | {'bar_start': '2024-12-28T00:59:00+08:00', 'close': 124270.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 124800.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. ni2503 20250211 night （historical_validation）

- Episode：`ni:20250211`
- 决策时点：`2025-02-10T20:59:00+08:00`
- 执行时点：`2025-02-10T21:01:00+08:00`
- label 窗口：`2025-02-10T21:01:00+08:00` → `2025-02-11T01:00:00+08:00`
- 目标值：-0.014441257 = ln(125120 / 126940)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-02-10T14:59:00+08:00', 'close': 127680.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250210, 'close': 127680.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-10T20:51:29+08:00` | 451 | {'title': '', 'labels': '比特币'} |
| brent_last_close | intl_brent | `2025-02-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-02-07', 'value': 74.68} |

## 18. ni2505 20250416 day （historical_validation）

- Episode：`ni:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:01:00+08:00`
- label 窗口：`2025-04-16T09:01:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：-0.0048216101 = ln(124140 / 124740)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T01:00:00+08:00` | 28740 | {'bar_start': '2025-04-16T00:59:00+08:00', 'close': 124830.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250415, 'close': 124240.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. ni2509 20250731 night （historical_validation）

- Episode：`ni:20250731`
- 决策时点：`2025-07-30T20:59:00+08:00`
- 执行时点：`2025-07-30T21:01:00+08:00`
- label 窗口：`2025-07-30T21:01:00+08:00` → `2025-07-31T01:00:00+08:00`
- 目标值：-0.00099189957 = ln(120920 / 121040)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 121720.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250730, 'close': 121720.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-30T20:58:30+08:00` | 30 | {'title': '【俄堪察加半岛强震后火山喷发】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-07-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-07-29', 'value': 73.21} |

## 20. ni2509 20250807 night （historical_validation）

- Episode：`ni:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:01:00+08:00`
- label 窗口：`2025-08-06T21:01:00+08:00` → `2025-08-07T01:00:00+08:00`
- 目标值：-0.0023068061 = ln(121240 / 121520)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 121070.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250806, 'close': 121070.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

## 21. ni2510 20250915 day （historical_validation）

- Episode：`ni:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:01:00+08:00`
- label 窗口：`2025-09-15T09:01:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.0057269239 = ln(122580 / 121880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-13T01:00:00+08:00` | 201540 | {'bar_start': '2025-09-13T00:59:00+08:00', 'close': 122010.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250912, 'close': 121980.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. ni2512 20251112 night （historical_validation）

- Episode：`ni:20251112`
- 决策时点：`2025-11-11T20:59:00+08:00`
- 执行时点：`2025-11-11T21:01:00+08:00`
- label 窗口：`2025-11-11T21:01:00+08:00` → `2025-11-12T01:00:00+08:00`
- 目标值：-0.0017609329 = ln(119150 / 119360)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 119380.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251111, 'close': 119380.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-11T20:56:54+08:00` | 126 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2025-11-11T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-10', 'value': 63.01} |

## 23. ni2601 20251128 night （historical_validation）

- Episode：`ni:20251128`
- 决策时点：`2025-11-27T20:59:00+08:00`
- 执行时点：`2025-11-27T21:01:00+08:00`
- label 窗口：`2025-11-27T21:01:00+08:00` → `2025-11-28T01:00:00+08:00`
- 目标值：0.0019650568 = ln(117160 / 116930)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 116900.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251127, 'close': 116900.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T20:57:18+08:00` | 102 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 24. ni2602 20251226 day （historical_validation）

- Episode：`ni:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：-0.0054290231 = ln(126750 / 127440)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T01:00:00+08:00` | 28740 | {'bar_start': '2025-12-26T00:59:00+08:00', 'close': 126800.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251225, 'close': 125410.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. ni2602 20260108 day （contaminated_audit）

- Episode：`ni:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.038603176 = ln(136440 / 141810)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-08T00:59:00+08:00', 'close': 143280.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 147720.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. ni2602 20260116 day （contaminated_audit）

- Episode：`ni:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：-0.033668061 = ln(141350 / 146190)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-16T00:59:00+08:00', 'close': 146880.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 146750.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. ni2607 20260602 night （contaminated_audit）

- Episode：`ni:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:01:00+08:00`
- label 窗口：`2026-06-01T21:01:00+08:00` → `2026-06-02T01:00:00+08:00`
- 目标值：0.0050461518 = ln(145030 / 144300)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 143580.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 143580.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |

## 28. ni2609 20260702 night （contaminated_audit）

- Episode：`ni:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:01:00+08:00`
- label 窗口：`2026-07-01T21:01:00+08:00` → `2026-07-02T01:00:00+08:00`
- 目标值：-0.0073381795 = ln(126270 / 127200)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 125580.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 125580.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 29. ni2609 20260720 night （contaminated_audit）

- Episode：`ni:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:01:00+08:00`
- label 窗口：`2026-07-17T21:01:00+08:00` → `2026-07-18T01:00:00+08:00`
- 目标值：0.011170718 = ln(130530 / 129080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 128890.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 128890.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
