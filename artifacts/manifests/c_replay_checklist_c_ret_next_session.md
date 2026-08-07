# SC Temporal Spine 人工回放清单（c_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`d3daef711fc43424134ea5faa25e0281fa9c3e49f59f0b5ee209f3bbd42ddcd2`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. c2303 20221209 night （discovery）

- Episode：`c:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:01:00+08:00`
- label 窗口：`2022-12-08T21:01:00+08:00` → `2022-12-08T23:00:00+08:00`
- 目标值：-0.0024791938 = ln(2820 / 2827)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 2829.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.030000+08:00` | 21539 | {'trading_day': 20221208, 'close': 2829.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

## 01. c2303 20221209 day （discovery）

- Episode：`c:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0 = ln(2817 / 2817)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T23:00:00+08:00` | 35940 | {'bar_start': '2022-12-08T22:59:00+08:00', 'close': 2820.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.030000+08:00` | 64739 | {'trading_day': 20221208, 'close': 2829.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 02. c2303 20230117 day （discovery）

- Episode：`c:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.00034680077 = ln(2884 / 2883)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-16T23:00:00+08:00` | 35940 | {'bar_start': '2023-01-16T22:59:00+08:00', 'close': 2886.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.022000+08:00` | 64739 | {'trading_day': 20230116, 'close': 2880.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 03. c2305 20230216 day （discovery）

- Episode：`c:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0028050509 = ln(2856 / 2848)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-15T23:00:00+08:00` | 35940 | {'bar_start': '2023-02-15T22:59:00+08:00', 'close': 2847.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.045000+08:00` | 64739 | {'trading_day': 20230215, 'close': 2846.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 04. c2307 20230523 night （discovery）

- Episode：`c:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:01:00+08:00`
- label 窗口：`2023-05-22T21:01:00+08:00` → `2023-05-22T23:00:00+08:00`
- 目标值：0.0058491101 = ln(2572 / 2557)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 2554.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.022000+08:00` | 21539 | {'trading_day': 20230522, 'close': 2554.0} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

## 05. c2309 20230615 night （discovery）

- Episode：`c:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:01:00+08:00`
- label 窗口：`2023-06-14T21:01:00+08:00` → `2023-06-14T23:00:00+08:00`
- 目标值：0.0034410281 = ln(2620 / 2611)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 2607.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.010000+08:00` | 21539 | {'trading_day': 20230614, 'close': 2607.0} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

## 06. c2309 20230714 day （discovery）

- Episode：`c:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.0025533481 = ln(2738 / 2745)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-13T23:00:00+08:00` | 35940 | {'bar_start': '2023-07-13T22:59:00+08:00', 'close': 2740.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.018000+08:00` | 64739 | {'trading_day': 20230713, 'close': 2736.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. c2309 20230724 day （discovery）

- Episode：`c:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：-0.00074515652 = ln(2683 / 2685)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-21T23:00:00+08:00` | 208740 | {'bar_start': '2023-07-21T22:59:00+08:00', 'close': 2682.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.040000+08:00` | 237539 | {'trading_day': 20230721, 'close': 2690.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. c2405 20240117 night （discovery）

- Episode：`c:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:01:00+08:00`
- label 窗口：`2024-01-16T21:01:00+08:00` → `2024-01-16T23:00:00+08:00`
- 目标值：-0.00042025636 = ln(2379 / 2380)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 2386.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.049000+08:00` | 21539 | {'trading_day': 20240116, 'close': 2386.0} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

## 09. c2405 20240301 day （discovery）

- Episode：`c:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.0028391826 = ln(2462 / 2469)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-02-29T23:00:00+08:00` | 35940 | {'bar_start': '2024-02-29T22:59:00+08:00', 'close': 2471.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.008000+08:00` | 64739 | {'trading_day': 20240229, 'close': 2462.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. c2405 20240401 night （discovery）

- Episode：`c:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:01:00+08:00`
- label 窗口：`2024-03-29T21:01:00+08:00` → `2024-03-29T23:00:00+08:00`
- 目标值：0.0029015564 = ln(2416 / 2409)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 2415.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.043000+08:00` | 21539 | {'trading_day': 20240329, 'close': 2415.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. c2407 20240527 day （discovery）

- Episode：`c:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.00081566073 = ln(2451 / 2453)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-24T23:00:00+08:00` | 208740 | {'bar_start': '2024-05-24T22:59:00+08:00', 'close': 2457.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.005000+08:00` | 237539 | {'trading_day': 20240524, 'close': 2462.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. c2409 20240709 day （discovery）

- Episode：`c:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：-0.0065466682 = ln(2436 / 2452)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-08T23:00:00+08:00` | 35940 | {'bar_start': '2024-07-08T22:59:00+08:00', 'close': 2455.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.032000+08:00` | 64739 | {'trading_day': 20240708, 'close': 2459.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. c2411 20240918 night （discovery）

- Episode：`c:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:01:00+08:00`
- label 窗口：`2024-09-13T21:01:00+08:00` → `2024-09-13T23:00:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 2200.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.032000+08:00` | 21539 | {'trading_day': 20240913, 'close': 2200.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

## 14. c2411 20240924 day （discovery）

- Episode：`c:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.012637659 = ln(2150 / 2123)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-23T23:00:00+08:00` | 35940 | {'bar_start': '2024-09-23T22:59:00+08:00', 'close': 2132.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.007000+08:00` | 64739 | {'trading_day': 20240923, 'close': 2138.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. c2501 20241206 day （discovery）

- Episode：`c:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：-0.0042990274 = ln(2089 / 2098)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-05T23:00:00+08:00` | 35940 | {'bar_start': '2024-12-05T22:59:00+08:00', 'close': 2099.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.047000+08:00` | 64739 | {'trading_day': 20241205, 'close': 2099.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. c2505 20241230 day （discovery）

- Episode：`c:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.00044752742 = ln(2235 / 2234)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-27T23:00:00+08:00` | 208740 | {'bar_start': '2024-12-27T22:59:00+08:00', 'close': 2240.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.040000+08:00` | 237539 | {'trading_day': 20241227, 'close': 2234.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. c2505 20250211 day （historical_validation）

- Episode：`c:20250211`
- 决策时点：`2025-02-11T08:59:00+08:00`
- 执行时点：`2025-02-11T09:01:00+08:00`
- label 窗口：`2025-02-11T09:01:00+08:00` → `2025-02-11T15:00:00+08:00`
- 目标值：0.0017436796 = ln(2296 / 2292)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T23:00:00+08:00` | 35940 | {'bar_start': '2025-02-10T22:59:00+08:00', 'close': 2291.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.025000+08:00` | 64739 | {'trading_day': 20250210, 'close': 2294.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-11T08:48:29+08:00` | 631 | {'title': '【两市融资余额增加190.57亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-02-11T06:00:00+08:00` | 10740 | {'quote_date': '2025-02-10', 'value': 76.23} |

## 18. c2507 20250417 night （historical_validation）

- Episode：`c:20250417`
- 决策时点：`2025-04-16T20:59:00+08:00`
- 执行时点：`2025-04-16T21:01:00+08:00`
- label 窗口：`2025-04-16T21:01:00+08:00` → `2025-04-16T23:00:00+08:00`
- 目标值：0.000434122 = ln(2304 / 2303)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T15:00:00+08:00` | 21540 | {'bar_start': '2025-04-16T14:59:00+08:00', 'close': 2304.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-16T15:00:00.025000+08:00` | 21539 | {'trading_day': 20250416, 'close': 2304.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T20:58:39+08:00` | 21 | {'title': '【众智科技：拟4100万元认购广监云12%股权】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 53940 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 19. c2509 20250731 day （historical_validation）

- Episode：`c:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.011299555 = ln(2288 / 2314)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T23:00:00+08:00` | 35940 | {'bar_start': '2025-07-30T22:59:00+08:00', 'close': 2313.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250730, 'close': 2312.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 20. c2509 20250807 day （historical_validation）

- Episode：`c:20250807`
- 决策时点：`2025-08-07T08:59:00+08:00`
- 执行时点：`2025-08-07T09:01:00+08:00`
- label 窗口：`2025-08-07T09:01:00+08:00` → `2025-08-07T15:00:00+08:00`
- 目标值：0.00044120892 = ln(2267 / 2266)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T23:00:00+08:00` | 35940 | {'bar_start': '2025-08-06T22:59:00+08:00', 'close': 2267.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.031000+08:00` | 64739 | {'trading_day': 20250806, 'close': 2259.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-07T08:57:03+08:00` | 117 | {'title': '【因技术故障 美联航多个航班被下令停飞】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-07T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-06', 'value': 67.97} |

## 21. c2511 20250916 night （historical_validation）

- Episode：`c:20250916`
- 决策时点：`2025-09-15T20:59:00+08:00`
- 执行时点：`2025-09-15T21:01:00+08:00`
- label 窗口：`2025-09-15T21:01:00+08:00` → `2025-09-15T23:00:00+08:00`
- 目标值：0.0013840833 = ln(2169 / 2166)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-15T15:00:00+08:00` | 21540 | {'bar_start': '2025-09-15T14:59:00+08:00', 'close': 2167.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-15T15:00:00.016000+08:00` | 21539 | {'trading_day': 20250915, 'close': 2167.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T20:57:47+08:00` | 73 | {'title': '【龙蟠科技：与宁德时代签署磷酸铁锂正极材料采购合作协议 合同总销售金额超60亿元', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 226740 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 22. c2601 20251112 day （historical_validation）

- Episode：`c:20251112`
- 决策时点：`2025-11-12T08:59:00+08:00`
- 执行时点：`2025-11-12T09:01:00+08:00`
- label 窗口：`2025-11-12T09:01:00+08:00` → `2025-11-12T15:00:00+08:00`
- 目标值：-0.0027522953 = ln(2177 / 2183)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T23:00:00+08:00` | 35940 | {'bar_start': '2025-11-11T22:59:00+08:00', 'close': 2180.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.041000+08:00` | 64739 | {'trading_day': 20251111, 'close': 2177.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-12T08:58:56+08:00` | 4 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-11-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-11', 'value': 63.86} |

## 23. c2601 20251128 day （historical_validation）

- Episode：`c:20251128`
- 决策时点：`2025-11-28T08:59:00+08:00`
- 执行时点：`2025-11-28T09:01:00+08:00`
- label 窗口：`2025-11-28T09:01:00+08:00` → `2025-11-28T15:00:00+08:00`
- 目标值：0.0031243052 = ln(2244 / 2237)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T23:00:00+08:00` | 35940 | {'bar_start': '2025-11-27T22:59:00+08:00', 'close': 2240.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.006000+08:00` | 64739 | {'trading_day': 20251127, 'close': 2243.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-28T08:53:33+08:00` | 327 | {'title': '【四川民企造出高超音速导弹？凌空天行：基本型已量产】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2025-11-28T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-27', 'value': 64.18} |

## 24. c2603 20251229 night （historical_validation）

- Episode：`c:20251229`
- 决策时点：`2025-12-26T20:59:00+08:00`
- 执行时点：`2025-12-26T21:01:00+08:00`
- label 窗口：`2025-12-26T21:01:00+08:00` → `2025-12-26T23:00:00+08:00`
- 目标值：0.0044943896 = ln(2230 / 2220)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-26T14:59:00+08:00', 'close': 2222.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-26T15:00:00.015000+08:00` | 21539 | {'trading_day': 20251226, 'close': 2222.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T20:57:24+08:00` | 96 | {'title': '【德福科技：HVLP5铜箔处于研发送样阶段 HVLP3/4已量产出货】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 140340 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. c2603 20260109 night （contaminated_audit）

- Episode：`c:20260109`
- 决策时点：`2026-01-08T20:59:00+08:00`
- 执行时点：`2026-01-08T21:01:00+08:00`
- label 窗口：`2026-01-08T21:01:00+08:00` → `2026-01-08T23:00:00+08:00`
- 目标值：-0.0017660049 = ln(2263 / 2267)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-08T14:59:00+08:00', 'close': 2266.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-08T15:00:00.007000+08:00` | 21539 | {'trading_day': 20260108, 'close': 2266.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T20:56:34+08:00` | 146 | {'title': '【华西股份：参股公司联储证券通过其投资主体持有星河动力部分股权】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. c2603 20260119 night （contaminated_audit）

- Episode：`c:20260119`
- 决策时点：`2026-01-16T20:59:00+08:00`
- 执行时点：`2026-01-16T21:01:00+08:00`
- label 窗口：`2026-01-16T21:01:00+08:00` → `2026-01-16T23:00:00+08:00`
- 目标值：-0.00043773255 = ln(2284 / 2285)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-16T14:59:00+08:00', 'close': 2281.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-16T15:00:00.003000+08:00` | 21539 | {'trading_day': 20260116, 'close': 2281.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T20:57:39+08:00` | 81 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. c2607 20260602 day （contaminated_audit）

- Episode：`c:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：0.0012867255 = ln(2333 / 2330)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-01T22:59:00+08:00', 'close': 2332.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.004000+08:00` | 64739 | {'trading_day': 20260601, 'close': 2330.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 28. c2609 20260702 day （contaminated_audit）

- Episode：`c:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：-0.0017160021 = ln(2329 / 2333)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-01T22:59:00+08:00', 'close': 2335.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.045000+08:00` | 64739 | {'trading_day': 20260701, 'close': 2333.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. c2609 20260720 day （contaminated_audit）

- Episode：`c:20260720`
- 决策时点：`2026-07-20T08:59:00+08:00`
- 执行时点：`2026-07-20T09:01:00+08:00`
- label 窗口：`2026-07-20T09:01:00+08:00` → `2026-07-20T15:00:00+08:00`
- 目标值：-0.0039499722 = ln(2274 / 2283)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T23:00:00+08:00` | 208740 | {'bar_start': '2026-07-17T22:59:00+08:00', 'close': 2289.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.044000+08:00` | 237539 | {'trading_day': 20260717, 'close': 2287.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2780140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 529140 | {'quote_date': '2026-07-13', 'value': 81.62} |
