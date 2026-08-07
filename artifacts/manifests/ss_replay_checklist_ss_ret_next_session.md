# SC Temporal Spine 人工回放清单（ss_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`ae5bce819a0f750136bb12a43d7d0b304be7793f919a54d78178ee9aa0a78888`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. ss2301 20221209 night （discovery）

- Episode：`ss:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-09T01:00:00+08:00`
- 目标值：-0.0072119164 = ln(17270 / 17395)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 17265.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 17265.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. ss2301 20221209 day （discovery）

- Episode：`ss:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.012966613 = ln(17465 / 17240)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-09T01:00:00+08:00` | 28740 | {'bar_start': '2022-12-09T00:59:00+08:00', 'close': 17270.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 17265.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. ss2302 20230117 day （discovery）

- Episode：`ss:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.0026296582 = ln(17135 / 17090)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-17T01:00:00+08:00` | 28740 | {'bar_start': '2023-01-17T00:59:00+08:00', 'close': 17100.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 17040.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. ss2303 20230216 day （discovery）

- Episode：`ss:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0015172207 = ln(16490 / 16465)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-16T01:00:00+08:00` | 28740 | {'bar_start': '2023-02-16T00:59:00+08:00', 'close': 16450.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 16475.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. ss2306 20230523 night （discovery）

- Episode：`ss:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-23T01:00:00+08:00`
- 目标值：-0.002021564 = ln(14825 / 14855)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 14845.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 14845.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. ss2307 20230615 night （discovery）

- Episode：`ss:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-15T01:00:00+08:00`
- 目标值：-0.0003270646 = ln(15285 / 15290)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 15315.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 15315.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. ss2308 20230714 day （discovery）

- Episode：`ss:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.00066822589 = ln(14960 / 14970)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-14T01:00:00+08:00` | 28740 | {'bar_start': '2023-07-14T00:59:00+08:00', 'close': 14985.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 14970.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. ss2309 20230724 day （discovery）

- Episode：`ss:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：0.002259888 = ln(15505 / 15470)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-22T01:00:00+08:00` | 201540 | {'bar_start': '2023-07-22T00:59:00+08:00', 'close': 15420.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 15340.000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. ss2403 20240117 night （discovery）

- Episode：`ss:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-17T01:00:00+08:00`
- 目标值：0.01742886 = ln(14180 / 13935)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 13895.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 13895.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. ss2405 20240301 day （discovery）

- Episode：`ss:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.01033693 = ln(13955 / 14100)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-01T01:00:00+08:00` | 28740 | {'bar_start': '2024-03-01T00:59:00+08:00', 'close': 14090.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 14145.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. ss2405 20240401 night （discovery）

- Episode：`ss:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-30T01:00:00+08:00`
- 目标值：-0.012782129 = ln(13215 / 13385)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 13435.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 13435.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. ss2409 20240527 day （discovery）

- Episode：`ss:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：0.0010205818 = ln(14705 / 14690)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-25T01:00:00+08:00` | 201540 | {'bar_start': '2024-05-25T00:59:00+08:00', 'close': 14690.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 14640.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. ss2409 20240709 day （discovery）

- Episode：`ss:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：-0.016985546 = ln(14010 / 14250)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T01:00:00+08:00` | 28740 | {'bar_start': '2024-07-09T00:59:00+08:00', 'close': 14235.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 14225.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. ss2411 20240918 night （discovery）

- Episode：`ss:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-14T01:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 13350.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 13350.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. ss2411 20240924 day （discovery）

- Episode：`ss:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.015157547 = ln(13295 / 13095)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-24T01:00:00+08:00` | 28740 | {'bar_start': '2024-09-24T00:59:00+08:00', 'close': 13100.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 13110.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. ss2501 20241206 day （discovery）

- Episode：`ss:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：-0.0023319093 = ln(12850 / 12880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-06T01:00:00+08:00` | 28740 | {'bar_start': '2024-12-06T00:59:00+08:00', 'close': 12875.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 12835.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. ss2502 20241230 day （discovery）

- Episode：`ss:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.0084844319 = ln(13020 / 12910)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-28T01:00:00+08:00` | 201540 | {'bar_start': '2024-12-28T00:59:00+08:00', 'close': 12935.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 12935.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. ss2503 20250211 night （historical_validation）

- Episode：`ss:20250211`
- 决策时点：`2025-02-10T20:59:00+08:00`
- 执行时点：`2025-02-10T21:01:00+08:00`
- label 窗口：`2025-02-10T21:01:00+08:00` → `2025-02-11T01:00:00+08:00`
- 目标值：-0.0060195818 = ln(13250 / 13330)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-02-10T14:59:00+08:00', 'close': 13340.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250210, 'close': 13340.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-10T20:51:29+08:00` | 451 | {'title': '', 'labels': '比特币'} |
| brent_last_close | intl_brent | `2025-02-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-02-07', 'value': 74.68} |

## 18. ss2506 20250416 day （historical_validation）

- Episode：`ss:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:01:00+08:00`
- label 窗口：`2025-04-16T09:01:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：-0.0023373598 = ln(12820 / 12850)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T01:00:00+08:00` | 28740 | {'bar_start': '2025-04-16T00:59:00+08:00', 'close': 12850.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250415, 'close': 12860.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. ss2509 20250731 night （historical_validation）

- Episode：`ss:20250731`
- 决策时点：`2025-07-30T20:59:00+08:00`
- 执行时点：`2025-07-30T21:01:00+08:00`
- label 窗口：`2025-07-30T21:01:00+08:00` → `2025-07-31T01:00:00+08:00`
- 目标值：-0.00038827413 = ln(12875 / 12880)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 12920.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250730, 'close': 12920.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-30T20:58:30+08:00` | 30 | {'title': '【俄堪察加半岛强震后火山喷发】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-07-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-07-29', 'value': 73.21} |

## 20. ss2509 20250807 night （historical_validation）

- Episode：`ss:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:01:00+08:00`
- label 窗口：`2025-08-06T21:01:00+08:00` → `2025-08-07T01:00:00+08:00`
- 目标值：-0.0034728956 = ln(12935 / 12980)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 12935.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250806, 'close': 12935.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

## 21. ss2511 20250915 day （historical_validation）

- Episode：`ss:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:01:00+08:00`
- label 窗口：`2025-09-15T09:01:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.0092237395 = ln(13070 / 12950)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-13T01:00:00+08:00` | 201540 | {'bar_start': '2025-09-13T00:59:00+08:00', 'close': 12945.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250912, 'close': 12950.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. ss2512 20251112 night （historical_validation）

- Episode：`ss:20251112`
- 决策时点：`2025-11-11T20:59:00+08:00`
- 执行时点：`2025-11-11T21:01:00+08:00`
- label 窗口：`2025-11-11T21:01:00+08:00` → `2025-11-12T01:00:00+08:00`
- 目标值：0.00040168709 = ln(12450 / 12445)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 12465.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251111, 'close': 12465.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-11T20:56:54+08:00` | 126 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2025-11-11T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-10', 'value': 63.01} |

## 23. ss2601 20251128 night （historical_validation）

- Episode：`ss:20251128`
- 决策时点：`2025-11-27T20:59:00+08:00`
- 执行时点：`2025-11-27T21:01:00+08:00`
- label 窗口：`2025-11-27T21:01:00+08:00` → `2025-11-28T01:00:00+08:00`
- 目标值：-0.003232326 = ln(12355 / 12395)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 12410.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251127, 'close': 12410.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T20:57:18+08:00` | 102 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 24. ss2602 20251226 day （historical_validation）

- Episode：`ss:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：-0.00077160498 = ln(12955 / 12965)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T01:00:00+08:00` | 28740 | {'bar_start': '2025-12-26T00:59:00+08:00', 'close': 12965.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251225, 'close': 12990.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. ss2603 20260108 day （contaminated_audit）

- Episode：`ss:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0087368594 = ln(13675 / 13795)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-08T00:59:00+08:00', 'close': 13860.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 14025.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. ss2603 20260116 day （contaminated_audit）

- Episode：`ss:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：-0.0052401867 = ln(14275 / 14350)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-16T00:59:00+08:00', 'close': 14335.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 14415.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. ss2607 20260602 night （contaminated_audit）

- Episode：`ss:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:01:00+08:00`
- label 窗口：`2026-06-01T21:01:00+08:00` → `2026-06-02T01:00:00+08:00`
- 目标值：0.0046713465 = ln(15020 / 14950)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 14850.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 14850.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |

## 28. ss2608 20260702 night （contaminated_audit）

- Episode：`ss:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:01:00+08:00`
- label 窗口：`2026-07-01T21:01:00+08:00` → `2026-07-02T01:00:00+08:00`
- 目标值：-0.0061454615 = ln(14600 / 14690)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 14615.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 14615.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 29. ss2609 20260720 night （contaminated_audit）

- Episode：`ss:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:01:00+08:00`
- label 窗口：`2026-07-17T21:01:00+08:00` → `2026-07-18T01:00:00+08:00`
- 目标值：0.0054514615 = ln(14715 / 14635)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 14650.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 14650.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
