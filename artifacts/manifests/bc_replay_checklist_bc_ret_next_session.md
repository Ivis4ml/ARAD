# SC Temporal Spine 人工回放清单（bc_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`7aa8bf566437c1aeba1a7fdda1521f1254fee12e713a2b1df6b654faf4195a6f`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. bc2302 20221209 night （discovery）

- Episode：`bc:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-09T01:00:00+08:00`
- 目标值：0 = ln(59810 / 59810)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 59470.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 59470.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. bc2302 20221209 day （discovery）

- Episode：`bc:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.0090030618 = ln(60250 / 59710)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-09T01:00:00+08:00` | 28740 | {'bar_start': '2022-12-09T00:59:00+08:00', 'close': 59810.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 59470.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. bc2303 20230117 day （discovery）

- Episode：`bc:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：-0.0037511257 = ln(61200 / 61430)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-17T01:00:00+08:00` | 28740 | {'bar_start': '2023-01-17T00:59:00+08:00', 'close': 61370.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 61650.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. bc2304 20230216 day （discovery）

- Episode：`bc:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0026199458 = ln(61150 / 60990)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-16T01:00:00+08:00` | 28740 | {'bar_start': '2023-02-16T00:59:00+08:00', 'close': 60950.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 61290.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. bc2309 20230523 night （discovery）

- Episode：`bc:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-23T01:00:00+08:00`
- 目标值：-0.00052360591 = ln(57280 / 57310)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 57320.00000000001, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 57320.00000000001} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. bc2310 20230615 night （discovery）

- Episode：`bc:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-15T01:00:00+08:00`
- 目标值：0.0029821096 = ln(60450 / 60270)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 59960.00000000001, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 59960.00000000001} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. bc2310 20230714 day （discovery）

- Episode：`bc:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.0056730843 = ln(61520 / 61870)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-14T01:00:00+08:00` | 28740 | {'bar_start': '2023-07-14T00:59:00+08:00', 'close': 61790.00000000001, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 60870.00000000001} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. bc2310 20230724 day （discovery）

- Episode：`bc:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：-0.0019811794 = ln(60510 / 60630)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-22T01:00:00+08:00` | 201540 | {'bar_start': '2023-07-22T00:59:00+08:00', 'close': 60590.00000000001, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 61020.00000000001} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. bc2403 20240117 night （discovery）

- Episode：`bc:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-17T01:00:00+08:00`
- 目标值：-0.00033129038 = ln(60360 / 60380)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 60110.00000000001, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 60110.00000000001} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. bc2404 20240301 day （discovery）

- Episode：`bc:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.0011436975 = ln(61170 / 61240)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-01T01:00:00+08:00` | 28740 | {'bar_start': '2024-03-01T00:59:00+08:00', 'close': 61290.00000000001, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 61280.00000000001} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. bc2405 20240401 night （discovery）

- Episode：`bc:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-30T01:00:00+08:00`
- 目标值：0.0010838431 = ln(64620 / 64550)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 64570.00000000001, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 64570.00000000001} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. bc2407 20240527 day （discovery）

- Episode：`bc:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.0038803822 = ln(74590 / 74880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-25T01:00:00+08:00` | 201540 | {'bar_start': '2024-05-25T00:59:00+08:00', 'close': 74570.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 75180.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. bc2408 20240709 day （discovery）

- Episode：`bc:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：0.0040477409 = ln(71790 / 71500)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T01:00:00+08:00` | 28740 | {'bar_start': '2024-07-09T00:59:00+08:00', 'close': 71520.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 71240.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. bc2410 20240918 night （discovery）

- Episode：`bc:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-14T01:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 65580.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 65580.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. bc2411 20240924 day （discovery）

- Episode：`bc:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.015962503 = ln(68200 / 67120)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-24T01:00:00+08:00` | 28740 | {'bar_start': '2024-09-24T00:59:00+08:00', 'close': 67220.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 66820.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. bc2501 20241206 day （discovery）

- Episode：`bc:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.0048462915 = ln(66190 / 65870)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-06T01:00:00+08:00` | 28740 | {'bar_start': '2024-12-06T00:59:00+08:00', 'close': 65830.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 65990.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. bc2502 20241230 day （discovery）

- Episode：`bc:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.0030446058 = ln(65790 / 65590)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-28T01:00:00+08:00` | 201540 | {'bar_start': '2024-12-28T00:59:00+08:00', 'close': 65520.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 65620.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. bc2503 20250211 night （historical_validation）

- Episode：`bc:20250211`
- 决策时点：`2025-02-10T20:59:00+08:00`
- 执行时点：`2025-02-10T21:01:00+08:00`
- label 窗口：`2025-02-10T21:01:00+08:00` → `2025-02-11T01:00:00+08:00`
- 目标值：0.0010158915 = ln(68940 / 68870)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-02-10T14:59:00+08:00', 'close': 68790.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250210, 'close': 68790.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-10T20:51:29+08:00` | 451 | {'title': '', 'labels': '比特币'} |
| brent_last_close | intl_brent | `2025-02-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-02-07', 'value': 74.68} |

## 18. bc2505 20250416 day （historical_validation）

- Episode：`bc:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:01:00+08:00`
- label 窗口：`2025-04-16T09:01:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：-0.0073041988 = ln(66840 / 67330)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T01:00:00+08:00` | 28740 | {'bar_start': '2025-04-16T00:59:00+08:00', 'close': 67460.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250415, 'close': 67500.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. bc2509 20250731 night （historical_validation）

- Episode：`bc:20250731`
- 决策时点：`2025-07-30T20:59:00+08:00`
- 执行时点：`2025-07-30T21:01:00+08:00`
- label 窗口：`2025-07-30T21:01:00+08:00` → `2025-07-31T01:00:00+08:00`
- 目标值：-0.00071587089 = ln(69820 / 69870)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 70070.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250730, 'close': 70070.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-30T20:58:30+08:00` | 30 | {'title': '【俄堪察加半岛强震后火山喷发】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-07-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-07-29', 'value': 73.21} |

## 20. bc2509 20250807 night （historical_validation）

- Episode：`bc:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:01:00+08:00`
- label 窗口：`2025-08-06T21:01:00+08:00` → `2025-08-07T01:00:00+08:00`
- 目标值：-0.000287687 = ln(69510 / 69530)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 69470.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250806, 'close': 69470.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

## 21. bc2510 20250915 day （historical_validation）

- Episode：`bc:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:01:00+08:00`
- label 窗口：`2025-09-15T09:01:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.001531927 = ln(71860 / 71750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-13T01:00:00+08:00` | 201540 | {'bar_start': '2025-09-13T00:59:00+08:00', 'close': 71780.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250912, 'close': 72030.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. bc2512 20251112 night （historical_validation）

- Episode：`bc:20251112`
- 决策时点：`2025-11-11T20:59:00+08:00`
- 执行时点：`2025-11-11T21:01:00+08:00`
- label 窗口：`2025-11-11T21:01:00+08:00` → `2025-11-12T01:00:00+08:00`
- 目标值：0.0019436352 = ln(77250 / 77100)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 77140.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251111, 'close': 77140.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-11T20:56:54+08:00` | 126 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2025-11-11T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-10', 'value': 63.01} |

## 23. bc2512 20251128 night （historical_validation）

- Episode：`bc:20251128`
- 决策时点：`2025-11-27T20:59:00+08:00`
- 执行时点：`2025-11-27T21:01:00+08:00`
- label 窗口：`2025-11-27T21:01:00+08:00` → `2025-11-28T01:00:00+08:00`
- 目标值：0.018928817 = ln(78930 / 77450)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 77780.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251127, 'close': 77780.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T20:57:18+08:00` | 102 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 24. bc2601 20251226 day （historical_validation）

- Episode：`bc:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：0.0052036317 = ln(88630 / 88170)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T01:00:00+08:00` | 28740 | {'bar_start': '2025-12-26T00:59:00+08:00', 'close': 87940.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251225, 'close': 87310.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. bc2602 20260108 day （contaminated_audit）

- Episode：`bc:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0052144124 = ln(89900 / 90370)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-08T00:59:00+08:00', 'close': 90690.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 92090.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. bc2602 20260116 day （contaminated_audit）

- Episode：`bc:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：-0.020644328 = ln(89650 / 91520)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-16T00:59:00+08:00', 'close': 91690.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 91520.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. bc2607 20260602 night （contaminated_audit）

- Episode：`bc:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:01:00+08:00`
- label 窗口：`2026-06-01T21:01:00+08:00` → `2026-06-02T01:00:00+08:00`
- 目标值：-0.0010642828 = ln(93910 / 94010)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 92920.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 92920.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |

## 28. bc2608 20260702 night （contaminated_audit）

- Episode：`bc:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:01:00+08:00`
- label 窗口：`2026-07-01T21:01:00+08:00` → `2026-07-02T01:00:00+08:00`
- 目标值：0.0058489379 = ln(90880 / 90350)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 90260.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 90260.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 29. bc2608 20260720 night （contaminated_audit）

- Episode：`bc:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:01:00+08:00`
- label 窗口：`2026-07-17T21:01:00+08:00` → `2026-07-18T01:00:00+08:00`
- 目标值：0.0069535265 = ln(92360 / 91720)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 91870.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 91870.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
