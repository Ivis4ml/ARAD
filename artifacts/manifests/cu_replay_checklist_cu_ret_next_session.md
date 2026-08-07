# SC Temporal Spine 人工回放清单（cu_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`dfc505a9e73627ddde1976ff72a66c5932a32b18b261b2739fadf14470f0b712`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. cu2301 20221209 night （discovery）

- Episode：`cu:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-09T01:00:00+08:00`
- 目标值：-0.0017999105 = ln(66610 / 66730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 66360.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 66360.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. cu2301 20221209 day （discovery）

- Episode：`cu:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.0089794078 = ln(67120 / 66520)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-09T01:00:00+08:00` | 28740 | {'bar_start': '2022-12-09T00:59:00+08:00', 'close': 66610.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 66360.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. cu2303 20230117 day （discovery）

- Episode：`cu:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：-0.00073072711 = ln(68400 / 68450)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-17T01:00:00+08:00` | 28740 | {'bar_start': '2023-01-17T00:59:00+08:00', 'close': 68400.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 68640.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. cu2303 20230216 day （discovery）

- Episode：`cu:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0023381568 = ln(68510 / 68350)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-16T01:00:00+08:00` | 28740 | {'bar_start': '2023-02-16T00:59:00+08:00', 'close': 68240.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 68640.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. cu2307 20230523 night （discovery）

- Episode：`cu:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-23T01:00:00+08:00`
- 目标值：-0.0020050905 = ln(64770 / 64900)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 64860.00000000001, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 64860.00000000001} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. cu2307 20230615 night （discovery）

- Episode：`cu:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-15T01:00:00+08:00`
- 目标值：0.0016151534 = ln(68160 / 68050)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 67730.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 67730.0} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. cu2308 20230714 day （discovery）

- Episode：`cu:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.0056127369 = ln(69290 / 69680)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-14T01:00:00+08:00` | 28740 | {'bar_start': '2023-07-14T00:59:00+08:00', 'close': 69580.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 68610.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. cu2308 20230724 day （discovery）

- Episode：`cu:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：-0.0019018366 = ln(68290 / 68420)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-22T01:00:00+08:00` | 201540 | {'bar_start': '2023-07-22T00:59:00+08:00', 'close': 68380.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 68720.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. cu2403 20240117 night （discovery）

- Episode：`cu:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-17T01:00:00+08:00`
- 目标值：-0.00088183427 = ln(68010 / 68070)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 67810.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 67810.0} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. cu2404 20240301 day （discovery）

- Episode：`cu:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.00072521578 = ln(68920 / 68970)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-01T01:00:00+08:00` | 28740 | {'bar_start': '2024-03-01T00:59:00+08:00', 'close': 69050.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 68990.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. cu2405 20240401 night （discovery）

- Episode：`cu:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-30T01:00:00+08:00`
- 目标值：0.0012402675 = ln(72610 / 72520)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 72530.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 72530.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. cu2407 20240527 day （discovery）

- Episode：`cu:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.0029884668 = ln(83530 / 83780)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-25T01:00:00+08:00` | 201540 | {'bar_start': '2024-05-25T00:59:00+08:00', 'close': 83490.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 84050.00000000001} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. cu2408 20240709 day （discovery）

- Episode：`cu:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：0.0037345991 = ln(80480 / 80180)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T01:00:00+08:00` | 28740 | {'bar_start': '2024-07-09T00:59:00+08:00', 'close': 80170.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 79930.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. cu2410 20240918 night （discovery）

- Episode：`cu:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-14T01:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 73960.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 73960.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. cu2410 20240924 day （discovery）

- Episode：`cu:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.015491973 = ln(76760 / 75580)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-24T01:00:00+08:00` | 28740 | {'bar_start': '2024-09-24T00:59:00+08:00', 'close': 75640.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 75310.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. cu2501 20241206 day （discovery）

- Episode：`cu:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.0037538588 = ln(74730 / 74450)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-06T01:00:00+08:00` | 28740 | {'bar_start': '2024-12-06T00:59:00+08:00', 'close': 74400.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 74530.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. cu2502 20241230 day （discovery）

- Episode：`cu:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.0025615113 = ln(74270 / 74080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-28T01:00:00+08:00` | 201540 | {'bar_start': '2024-12-28T00:59:00+08:00', 'close': 74070.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 74090.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. cu2503 20250211 night （historical_validation）

- Episode：`cu:20250211`
- 决策时点：`2025-02-10T20:59:00+08:00`
- 执行时点：`2025-02-10T21:01:00+08:00`
- label 窗口：`2025-02-10T21:01:00+08:00` → `2025-02-11T01:00:00+08:00`
- 目标值：0.0021939739 = ln(77570 / 77400)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-02-10T14:59:00+08:00', 'close': 77370.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250210, 'close': 77370.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-10T20:51:29+08:00` | 451 | {'title': '', 'labels': '比特币'} |
| brent_last_close | intl_brent | `2025-02-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-02-07', 'value': 74.68} |

## 18. cu2506 20250416 day （historical_validation）

- Episode：`cu:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:01:00+08:00`
- label 窗口：`2025-04-16T09:01:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：-0.0055651396 = ln(75260 / 75680)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T01:00:00+08:00` | 28740 | {'bar_start': '2025-04-16T00:59:00+08:00', 'close': 75830.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250415, 'close': 75870.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. cu2509 20250731 night （historical_validation）

- Episode：`cu:20250731`
- 决策时点：`2025-07-30T20:59:00+08:00`
- 执行时点：`2025-07-30T21:01:00+08:00`
- label 窗口：`2025-07-30T21:01:00+08:00` → `2025-07-31T01:00:00+08:00`
- 目标值：0.0002541619 = ln(78700 / 78680)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 78930.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250730, 'close': 78930.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-30T20:58:30+08:00` | 30 | {'title': '【俄堪察加半岛强震后火山喷发】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-07-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-07-29', 'value': 73.21} |

## 20. cu2509 20250807 night （historical_validation）

- Episode：`cu:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:01:00+08:00`
- label 窗口：`2025-08-06T21:01:00+08:00` → `2025-08-07T01:00:00+08:00`
- 目标值：-0.0002551997 = ln(78360 / 78380)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 78280.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250806, 'close': 78280.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

## 21. cu2510 20250915 day （historical_validation）

- Episode：`cu:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:01:00+08:00`
- label 窗口：`2025-09-15T09:01:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.0023501773 = ln(80940 / 80750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-13T01:00:00+08:00` | 201540 | {'bar_start': '2025-09-13T00:59:00+08:00', 'close': 80810.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250912, 'close': 81060.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. cu2512 20251112 night （historical_validation）

- Episode：`cu:20251112`
- 决策时点：`2025-11-11T20:59:00+08:00`
- 执行时点：`2025-11-11T21:01:00+08:00`
- label 窗口：`2025-11-11T21:01:00+08:00` → `2025-11-12T01:00:00+08:00`
- 目标值：0.0019611242 = ln(86770 / 86600)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 86630.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251111, 'close': 86630.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-11T20:56:54+08:00` | 126 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2025-11-11T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-10', 'value': 63.01} |

## 23. cu2601 20251128 night （historical_validation）

- Episode：`cu:20251128`
- 决策时点：`2025-11-27T20:59:00+08:00`
- 执行时点：`2025-11-27T21:01:00+08:00`
- label 窗口：`2025-11-27T21:01:00+08:00` → `2025-11-28T01:00:00+08:00`
- 目标值：0.0034522474 = ln(87050 / 86750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 86990.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251127, 'close': 86990.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T20:57:18+08:00` | 102 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 24. cu2602 20251226 day （historical_validation）

- Episode：`cu:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：0.0069120015 = ln(98720 / 98040)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T01:00:00+08:00` | 28740 | {'bar_start': '2025-12-26T00:59:00+08:00', 'close': 97680.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251225, 'close': 96210.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. cu2602 20260108 day （contaminated_audit）

- Episode：`cu:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0049275748 = ln(101220 / 101720)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-08T00:59:00+08:00', 'close': 102030.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 103410.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. cu2603 20260116 day （contaminated_audit）

- Episode：`cu:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：-0.019263495 = ln(100770 / 102730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-16T00:59:00+08:00', 'close': 102860.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 102810.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. cu2607 20260602 night （contaminated_audit）

- Episode：`cu:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:01:00+08:00`
- label 窗口：`2026-06-01T21:01:00+08:00` → `2026-06-02T01:00:00+08:00`
- 目标值：0.00047252281 = ln(105840 / 105790)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 104680.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 104680.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |

## 28. cu2608 20260702 night （contaminated_audit）

- Episode：`cu:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:01:00+08:00`
- label 窗口：`2026-07-01T21:01:00+08:00` → `2026-07-02T01:00:00+08:00`
- 目标值：0.0044970259 = ln(102520 / 102060)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 101920.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 101920.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 29. cu2609 20260720 night （contaminated_audit）

- Episode：`cu:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:01:00+08:00`
- label 窗口：`2026-07-17T21:01:00+08:00` → `2026-07-18T01:00:00+08:00`
- 目标值：0.0063737541 = ln(103880 / 103220)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 103370.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 103370.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
