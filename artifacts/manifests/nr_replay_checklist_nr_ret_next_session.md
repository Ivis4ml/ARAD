# SC Temporal Spine 人工回放清单（nr_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`bc7a426939580b67b91590f2ea5ff3d69e557a0b1b0ccbddf9a5c165f9d5db93`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. nr2302 20221209 night （discovery）

- Episode：`nr:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-08T23:00:00+08:00`
- 目标值：0.007021092 = ln(10005 / 9935)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 9960.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 9960.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. nr2302 20221209 day （discovery）

- Episode：`nr:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0 = ln(10010 / 10010)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T23:00:00+08:00` | 35940 | {'bar_start': '2022-12-08T22:59:00+08:00', 'close': 10005.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 9960.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. nr2304 20230117 day （discovery）

- Episode：`nr:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.015427029 = ln(10125 / 9970)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-16T23:00:00+08:00` | 35940 | {'bar_start': '2023-01-16T22:59:00+08:00', 'close': 9970.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 9820.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. nr2305 20230216 day （discovery）

- Episode：`nr:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0 = ln(9970 / 9970)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-15T23:00:00+08:00` | 35940 | {'bar_start': '2023-02-15T22:59:00+08:00', 'close': 9965.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 9935.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. nr2308 20230523 night （discovery）

- Episode：`nr:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-22T23:00:00+08:00`
- 目标值：-0.0030880107 = ln(9700 / 9730)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 9720.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 9720.0} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. nr2309 20230615 night （discovery）

- Episode：`nr:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-14T23:00:00+08:00`
- 目标值：0.0025793153 = ln(9705 / 9680)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 9720.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 9720.0} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. nr2310 20230714 day （discovery）

- Episode：`nr:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.00052424641 = ln(9535 / 9540)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-13T23:00:00+08:00` | 35940 | {'bar_start': '2023-07-13T22:59:00+08:00', 'close': 9515.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 9570.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. nr2310 20230724 day （discovery）

- Episode：`nr:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：-0.0063626938 = ln(9400 / 9460)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-21T23:00:00+08:00` | 208740 | {'bar_start': '2023-07-21T22:59:00+08:00', 'close': 9465.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 9340.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. nr2403 20240117 night （discovery）

- Episode：`nr:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-16T23:00:00+08:00`
- 目标值：-0.00044513689 = ln(11230 / 11235)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 11240.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 11240.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. nr2404 20240301 day （discovery）

- Episode：`nr:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：0.011580657 = ln(11725 / 11590)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-02-29T23:00:00+08:00` | 35940 | {'bar_start': '2024-02-29T22:59:00+08:00', 'close': 11560.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 11785.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. nr2405 20240401 night （discovery）

- Episode：`nr:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-29T23:00:00+08:00`
- 目标值：-0.0025273813 = ln(11855 / 11885)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 11865.000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 11865.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. nr2407 20240527 day （discovery）

- Episode：`nr:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.00078926602 = ln(12665 / 12675)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-24T23:00:00+08:00` | 208740 | {'bar_start': '2024-05-24T22:59:00+08:00', 'close': 12605.000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 12700.000000000002} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. nr2409 20240709 day （discovery）

- Episode：`nr:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：0.0057049869 = ln(12305 / 12235)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-08T23:00:00+08:00` | 35940 | {'bar_start': '2024-07-08T22:59:00+08:00', 'close': 12255.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 12215.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. nr2411 20240918 night （discovery）

- Episode：`nr:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-13T23:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 13345.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 13345.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. nr2411 20240924 day （discovery）

- Episode：`nr:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.03733384 = ln(14190 / 13670)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-23T23:00:00+08:00` | 35940 | {'bar_start': '2024-09-23T22:59:00+08:00', 'close': 13685.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 13585.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. nr2502 20241206 day （discovery）

- Episode：`nr:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.022063245 = ln(15810 / 15465)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-05T23:00:00+08:00` | 35940 | {'bar_start': '2024-12-05T22:59:00+08:00', 'close': 15445.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 15260.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. nr2502 20241230 day （discovery）

- Episode：`nr:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.013164747 = ln(14910 / 14715)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-27T23:00:00+08:00` | 208740 | {'bar_start': '2024-12-27T22:59:00+08:00', 'close': 14775.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 14745.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. nr2503 20250211 day （historical_validation）

- Episode：`nr:20250211`
- 决策时点：`2025-02-11T08:59:00+08:00`
- 执行时点：`2025-02-11T09:01:00+08:00`
- label 窗口：`2025-02-11T09:01:00+08:00` → `2025-02-11T15:00:00+08:00`
- 目标值：-0.005376357 = ln(14840 / 14920)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T23:00:00+08:00` | 35940 | {'bar_start': '2025-02-10T22:59:00+08:00', 'close': 14905.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250210, 'close': 14955.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-11T08:48:29+08:00` | 631 | {'title': '【两市融资余额增加190.57亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-02-11T06:00:00+08:00` | 10740 | {'quote_date': '2025-02-10', 'value': 76.23} |

## 18. nr2506 20250417 night （historical_validation）

- Episode：`nr:20250417`
- 决策时点：`2025-04-16T20:59:00+08:00`
- 执行时点：`2025-04-16T21:01:00+08:00`
- label 窗口：`2025-04-16T21:01:00+08:00` → `2025-04-16T23:00:00+08:00`
- 目标值：-0.0056520134 = ln(12350 / 12420)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T15:00:00+08:00` | 21540 | {'bar_start': '2025-04-16T14:59:00+08:00', 'close': 12350.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250416, 'close': 12350.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T20:58:39+08:00` | 21 | {'title': '【众智科技：拟4100万元认购广监云12%股权】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 53940 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. nr2509 20250731 day （historical_validation）

- Episode：`nr:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.009325022 = ln(12275 / 12390)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T23:00:00+08:00` | 35940 | {'bar_start': '2025-07-30T22:59:00+08:00', 'close': 12380.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250730, 'close': 12575.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 20. nr2509 20250807 day （historical_validation）

- Episode：`nr:20250807`
- 决策时点：`2025-08-07T08:59:00+08:00`
- 执行时点：`2025-08-07T09:01:00+08:00`
- label 窗口：`2025-08-07T09:01:00+08:00` → `2025-08-07T15:00:00+08:00`
- 目标值：0.0069063854 = ln(12350 / 12265)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T23:00:00+08:00` | 35940 | {'bar_start': '2025-08-06T22:59:00+08:00', 'close': 12280.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250806, 'close': 12320.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-07T08:57:03+08:00` | 117 | {'title': '【因技术故障 美联航多个航班被下令停飞】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-07T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-06', 'value': 67.97} |

## 21. nr2511 20250916 night （historical_validation）

- Episode：`nr:20250916`
- 决策时点：`2025-09-15T20:59:00+08:00`
- 执行时点：`2025-09-15T21:01:00+08:00`
- label 窗口：`2025-09-15T21:01:00+08:00` → `2025-09-15T23:00:00+08:00`
- 目标值：0.0015779096 = ln(12685 / 12665)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-15T15:00:00+08:00` | 21540 | {'bar_start': '2025-09-15T14:59:00+08:00', 'close': 12710.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-15T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250915, 'close': 12710.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T20:57:47+08:00` | 73 | {'title': '【龙蟠科技：与宁德时代签署磷酸铁锂正极材料采购合作协议 合同总销售金额超60亿元', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 226740 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. nr2601 20251112 day （historical_validation）

- Episode：`nr:20251112`
- 决策时点：`2025-11-12T08:59:00+08:00`
- 执行时点：`2025-11-12T09:01:00+08:00`
- label 窗口：`2025-11-12T09:01:00+08:00` → `2025-11-12T15:00:00+08:00`
- 目标值：0.00082135528 = ln(12180 / 12170)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T23:00:00+08:00` | 35940 | {'bar_start': '2025-11-11T22:59:00+08:00', 'close': 12150.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251111, 'close': 12125.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-12T08:58:56+08:00` | 4 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-11-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-11', 'value': 63.86} |

## 23. nr2601 20251128 day （historical_validation）

- Episode：`nr:20251128`
- 决策时点：`2025-11-28T08:59:00+08:00`
- 执行时点：`2025-11-28T09:01:00+08:00`
- label 窗口：`2025-11-28T09:01:00+08:00` → `2025-11-28T15:00:00+08:00`
- 目标值：0.0020387367 = ln(12275 / 12250)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T23:00:00+08:00` | 35940 | {'bar_start': '2025-11-27T22:59:00+08:00', 'close': 12275.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251127, 'close': 12205.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-28T08:53:33+08:00` | 327 | {'title': '【四川民企造出高超音速导弹？凌空天行：基本型已量产】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2025-11-28T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-27', 'value': 64.18} |

## 24. nr2602 20251229 night （historical_validation）

- Episode：`nr:20251229`
- 决策时点：`2025-12-26T20:59:00+08:00`
- 执行时点：`2025-12-26T21:01:00+08:00`
- label 窗口：`2025-12-26T21:01:00+08:00` → `2025-12-26T23:00:00+08:00`
- 目标值：-0.0015673984 = ln(12750 / 12770)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-26T14:59:00+08:00', 'close': 12755.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-26T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251226, 'close': 12755.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T20:57:24+08:00` | 96 | {'title': '【德福科技：HVLP5铜箔处于研发送样阶段 HVLP3/4已量产出货】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 140340 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. nr2603 20260109 night （contaminated_audit）

- Episode：`nr:20260109`
- 决策时点：`2026-01-08T20:59:00+08:00`
- 执行时点：`2026-01-08T21:01:00+08:00`
- label 窗口：`2026-01-08T21:01:00+08:00` → `2026-01-08T23:00:00+08:00`
- 目标值：-0.0088752271 = ln(12900 / 13015)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-08T14:59:00+08:00', 'close': 13065.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260108, 'close': 13065.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T20:56:34+08:00` | 146 | {'title': '【华西股份：参股公司联储证券通过其投资主体持有星河动力部分股权】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. nr2603 20260119 night （contaminated_audit）

- Episode：`nr:20260119`
- 决策时点：`2026-01-16T20:59:00+08:00`
- 执行时点：`2026-01-16T21:01:00+08:00`
- label 窗口：`2026-01-16T21:01:00+08:00` → `2026-01-16T23:00:00+08:00`
- 目标值：-0.010607053 = ln(12660 / 12795)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-16T14:59:00+08:00', 'close': 12745.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260116, 'close': 12745.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T20:57:39+08:00` | 81 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. nr2607 20260602 day （contaminated_audit）

- Episode：`nr:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：0.014379542 = ln(15760 / 15535)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-01T22:59:00+08:00', 'close': 15520.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260601, 'close': 15685.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 28. nr2608 20260702 day （contaminated_audit）

- Episode：`nr:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：-0.0013981128 = ln(14295 / 14315)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-01T22:59:00+08:00', 'close': 14340.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260701, 'close': 14340.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. nr2609 20260720 day （contaminated_audit）

- Episode：`nr:20260720`
- 决策时点：`2026-07-20T08:59:00+08:00`
- 执行时点：`2026-07-20T09:01:00+08:00`
- label 窗口：`2026-07-20T09:01:00+08:00` → `2026-07-20T15:00:00+08:00`
- 目标值：-0.0020359695 = ln(14720 / 14750)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T23:00:00+08:00` | 208740 | {'bar_start': '2026-07-17T22:59:00+08:00', 'close': 14670.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 237539 | {'trading_day': 20260717, 'close': 14575.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2780140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 529140 | {'quote_date': '2026-07-13', 'value': 81.62} |
