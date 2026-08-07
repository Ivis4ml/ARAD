# SC Temporal Spine 人工回放清单（fb_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`663e61028d37851af89ac24cd42928d950680debe25ebea203b9d567408b5fbe`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. fb2301 20221209 day （discovery）

- Episode：`fb:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.0012353306 = ln(1215 / 1213.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 64740 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 1214.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.030000+08:00` | 64739 | {'trading_day': 20221208, 'close': 1214.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 01. fb2303 20230117 day （discovery）

- Episode：`fb:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.0055226965 = ln(1271 / 1264)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-16T15:00:00+08:00` | 64740 | {'bar_start': '2023-01-16T14:59:00+08:00', 'close': 1265.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.022000+08:00` | 64739 | {'trading_day': 20230116, 'close': 1265.5} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 02. fb2303 20230216 day （discovery）

- Episode：`fb:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.011751017 = ln(1284 / 1269)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-15T15:00:00+08:00` | 64740 | {'bar_start': '2023-02-15T14:59:00+08:00', 'close': 1282.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00+08:00` | 64740 | {'trading_day': 20230215, 'close': 1282.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 03. fb2305 20230314 day （discovery）

- Episode：`fb:20230314`
- 决策时点：`2023-03-14T08:59:00+08:00`
- 执行时点：`2023-03-14T09:01:00+08:00`
- label 窗口：`2023-03-14T09:01:00+08:00` → `2023-03-14T15:00:00+08:00`
- 目标值：-0.0052792001 = ln(1228 / 1234.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-03-13T15:00:00+08:00` | 64740 | {'bar_start': '2023-03-13T14:59:00+08:00', 'close': 1233.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-03-13T15:00:00.016000+08:00` | 64739 | {'trading_day': 20230313, 'close': 1233.5} |
| cls_last_telegraph | cls_telegraph | `2023-03-14T08:56:24+08:00` | 156 | {'title': '【比亚迪：“特斯拉叫停与比亚迪合作”为不实信息】', 'labels': '美股动态 特斯拉'} |
| brent_last_close | intl_brent | `2023-03-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-03-13', 'value': 79.67} |

## 04. fb2309 20230523 day （discovery）

- Episode：`fb:20230523`
- 决策时点：`2023-05-23T08:59:00+08:00`
- 执行时点：`2023-05-23T09:01:00+08:00`
- label 窗口：`2023-05-23T09:01:00+08:00` → `2023-05-23T15:00:00+08:00`
- 目标值：-0.0028163366 = ln(1241 / 1244.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 64740 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 1234.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.022000+08:00` | 64739 | {'trading_day': 20230522, 'close': 1234.5} |
| cls_last_telegraph | cls_telegraph | `2023-05-23T08:51:27+08:00` | 453 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2023-05-23T06:00:00+08:00` | 10740 | {'quote_date': '2023-05-22', 'value': 75.77} |

## 05. fb2309 20230615 day （discovery）

- Episode：`fb:20230615`
- 决策时点：`2023-06-15T08:59:00+08:00`
- 执行时点：`2023-06-15T09:01:00+08:00`
- label 窗口：`2023-06-15T09:01:00+08:00` → `2023-06-15T15:00:00+08:00`
- 目标值：-0.0019948141 = ln(1252 / 1254.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 64740 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 1254.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.010000+08:00` | 64739 | {'trading_day': 20230614, 'close': 1254.5} |
| cls_last_telegraph | cls_telegraph | `2023-06-15T08:50:12+08:00` | 528 | {'title': '【两市融资余额减少11.11亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2023-06-15T06:00:00+08:00` | 10740 | {'quote_date': '2023-06-14', 'value': 73.39} |

## 06. fb2309 20230714 day （discovery）

- Episode：`fb:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.0053224281 = ln(1218 / 1224.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-13T15:00:00+08:00` | 64740 | {'bar_start': '2023-07-13T14:59:00+08:00', 'close': 1223.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.018000+08:00` | 64739 | {'trading_day': 20230713, 'close': 1223.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. fb2309 20230724 day （discovery）

- Episode：`fb:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：0.0024885952 = ln(1207 / 1204)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-21T15:00:00+08:00` | 237540 | {'bar_start': '2023-07-21T14:59:00+08:00', 'close': 1205.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.040000+08:00` | 237539 | {'trading_day': 20230721, 'close': 1205.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. fb2402 20240117 day （discovery）

- Episode：`fb:20240117`
- 决策时点：`2024-01-17T08:59:00+08:00`
- 执行时点：`2024-01-17T09:01:00+08:00`
- label 窗口：`2024-01-17T09:01:00+08:00` → `2024-01-17T15:00:00+08:00`
- 目标值：-0.020046932 = ln(1284 / 1310)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 64740 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 1301.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.049000+08:00` | 64739 | {'trading_day': 20240116, 'close': 1301.5} |
| cls_last_telegraph | cls_telegraph | `2024-01-17T08:57:11+08:00` | 109 | {'title': '【Gartner：2023年全球半导体收入总额为5330亿美元 同比下降11.1', 'labels': '半导体芯片'} |
| brent_last_close | intl_brent | `2024-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2024-01-16', 'value': 80.15} |

## 09. fb2403 20240301 day （discovery）

- Episode：`fb:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：0.026322478 = ln(1289.5 / 1256)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-02-29T15:00:00+08:00` | 64740 | {'bar_start': '2024-02-29T14:59:00+08:00', 'close': 1258.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.008000+08:00` | 64739 | {'trading_day': 20240229, 'close': 1258.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. fb2405 20240401 day （discovery）

- Episode：`fb:20240401`
- 决策时点：`2024-04-01T08:59:00+08:00`
- 执行时点：`2024-04-01T09:01:00+08:00`
- label 窗口：`2024-04-01T09:01:00+08:00` → `2024-04-01T15:00:00+08:00`
- 目标值：-0.0070450389 = ln(1273 / 1282)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 237540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 1281.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.043000+08:00` | 237539 | {'trading_day': 20240329, 'close': 1281.5} |
| cls_last_telegraph | cls_telegraph | `2024-04-01T08:47:28+08:00` | 692 | {'title': '【MCU库存去化今年Q2落底 产业迈入传统旺季】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 269940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. fb2409 20240527 day （discovery）

- Episode：`fb:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.0033241028 = ln(1351.5 / 1356)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-24T15:00:00+08:00` | 237540 | {'bar_start': '2024-05-24T14:59:00+08:00', 'close': 1357.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.005000+08:00` | 237539 | {'trading_day': 20240524, 'close': 1357.5} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. fb2409 20240709 day （discovery）

- Episode：`fb:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：-0.016497593 = ln(1292.5 / 1314)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-08T15:00:00+08:00` | 64740 | {'bar_start': '2024-07-08T14:59:00+08:00', 'close': 1310.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.032000+08:00` | 64739 | {'trading_day': 20240708, 'close': 1310.5} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. fb2501 20240918 day （discovery）

- Episode：`fb:20240918`
- 决策时点：`2024-09-18T08:59:00+08:00`
- 执行时点：`2024-09-18T09:01:00+08:00`
- label 窗口：`2024-09-18T09:01:00+08:00` → `2024-09-18T15:00:00+08:00`
- 目标值：0.0062305498 = ln(1288 / 1280)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 410340 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 1285.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.032000+08:00` | 410339 | {'trading_day': 20240913, 'close': 1285.5} |
| cls_last_telegraph | cls_telegraph | `2024-09-18T08:55:34+08:00` | 206 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-09-18T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-17', 'value': 74.55} |

## 14. fb2501 20240924 day （discovery）

- Episode：`fb:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.0093567934 = ln(1288.5 / 1276.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-23T15:00:00+08:00` | 64740 | {'bar_start': '2024-09-23T14:59:00+08:00', 'close': 1278.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.007000+08:00` | 64739 | {'trading_day': 20240923, 'close': 1278.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. fb2501 20241206 day （discovery）

- Episode：`fb:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.0030476214 = ln(1314.5 / 1310.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-05T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-05T14:59:00+08:00', 'close': 1310.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.047000+08:00` | 64739 | {'trading_day': 20241205, 'close': 1310.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. fb2501 20241230 day （discovery）

- Episode：`fb:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：-0.00114657 = ln(1307.5 / 1309)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-27T15:00:00+08:00` | 237540 | {'bar_start': '2024-12-27T14:59:00+08:00', 'close': 1313.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.040000+08:00` | 237539 | {'trading_day': 20241227, 'close': 1313.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. fb2505 20250417 day （historical_validation）

- Episode：`fb:20250417`
- 决策时点：`2025-04-17T08:59:00+08:00`
- 执行时点：`2025-04-17T09:01:00+08:00`
- label 窗口：`2025-04-17T09:01:00+08:00` → `2025-04-17T15:00:00+08:00`
- 目标值：0.0023837914 = ln(1260 / 1257)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T15:00:00+08:00` | 64740 | {'bar_start': '2025-04-16T14:59:00+08:00', 'close': 1258.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-16T15:00:00.025000+08:00` | 64739 | {'trading_day': 20250416, 'close': 1258.5} |
| cls_last_telegraph | cls_telegraph | `2025-04-17T08:57:31+08:00` | 89 | {'title': '【凯德投资申报旗下首支中国消费基础设施公募REIT  资产规模约28亿元】', 'labels': '公募基金动态 基建投资 信托动态'} |
| brent_last_close | intl_brent | `2025-04-17T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-16', 'value': 67.94} |

## 18. fb2601 20250801 day （historical_validation）

- Episode：`fb:20250801`
- 决策时点：`2025-08-01T08:59:00+08:00`
- 执行时点：`2025-08-01T09:01:00+08:00`
- label 窗口：`2025-08-01T09:01:00+08:00` → `2025-08-01T15:00:00+08:00`
- 目标值：0.0015209128 = ln(1316 / 1314)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-31T15:00:00+08:00` | 64740 | {'bar_start': '2025-07-31T14:59:00+08:00', 'close': 1314.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-31T15:00:00.046000+08:00` | 64739 | {'trading_day': 20250731, 'close': 1314.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-01T08:55:39+08:00` | 201 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-01T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-31', 'value': 73.43} |

## 19. fb2602 20250808 day （historical_validation）

- Episode：`fb:20250808`
- 决策时点：`2025-08-08T08:59:00+08:00`
- 执行时点：`2025-08-08T09:01:00+08:00`
- label 窗口：`2025-08-08T09:01:00+08:00` → `2025-08-08T15:00:00+08:00`
- 目标值：0 = ln(1298.5 / 1298.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-07T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-07T14:59:00+08:00', 'close': 1298.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-07T15:00:00.043000+08:00` | 64739 | {'trading_day': 20250807, 'close': 1298.5} |
| cls_last_telegraph | cls_telegraph | `2025-08-08T08:58:13+08:00` | 47 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-08-08T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-07', 'value': 66.99} |

## 20. fb2603 20250916 day （historical_validation）

- Episode：`fb:20250916`
- 决策时点：`2025-09-16T08:59:00+08:00`
- 执行时点：`2025-09-16T09:01:00+08:00`
- label 窗口：`2025-09-16T09:01:00+08:00` → `2025-09-16T15:00:00+08:00`
- 目标值：-0.0035964075 = ln(1249 / 1253.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-15T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-15T14:59:00+08:00', 'close': 1253.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-15T15:00:00.016000+08:00` | 64739 | {'trading_day': 20250915, 'close': 1253.5} |
| cls_last_telegraph | cls_telegraph | `2025-09-16T08:56:30+08:00` | 150 | {'title': '', 'labels': '腾讯最新动态 TMT行业观察'} |
| brent_last_close | intl_brent | `2025-09-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-15', 'value': 67.88} |

## 21. fb2605 20251113 day （historical_validation）

- Episode：`fb:20251113`
- 决策时点：`2025-11-13T08:59:00+08:00`
- 执行时点：`2025-11-13T09:01:00+08:00`
- label 窗口：`2025-11-13T09:01:00+08:00` → `2025-11-13T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-12T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-12T14:59:00+08:00', 'close': 1272.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-12T15:00:00.014000+08:00` | 64739 | {'trading_day': 20251112, 'close': 1272.5} |
| cls_last_telegraph | cls_telegraph | `2025-11-13T08:55:20+08:00` | 220 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-11-13T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-12', 'value': 61.88} |

## 22. fb2611 20251128 day （historical_validation）

- Episode：`fb:20251128`
- 决策时点：`2025-11-28T08:59:00+08:00`
- 执行时点：`2025-11-28T09:01:00+08:00`
- label 窗口：`2025-11-28T09:01:00+08:00` → `2025-11-28T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 1255.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 64740 | {'trading_day': 20251127, 'close': 1255.5} |
| cls_last_telegraph | cls_telegraph | `2025-11-28T08:53:33+08:00` | 327 | {'title': '【四川民企造出高超音速导弹？凌空天行：基本型已量产】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2025-11-28T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-27', 'value': 64.18} |

## 23. fb2611 20251201 day （historical_validation）

- Episode：`fb:20251201`
- 决策时点：`2025-12-01T08:59:00+08:00`
- 执行时点：`2025-12-01T09:01:00+08:00`
- label 窗口：`2025-12-01T09:01:00+08:00` → `2025-12-01T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-28T15:00:00+08:00` | 237540 | {'bar_start': '2025-11-28T14:59:00+08:00', 'close': 1255.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-28T15:00:00+08:00` | 237540 | {'trading_day': 20251128, 'close': 1255.5} |
| cls_last_telegraph | cls_telegraph | `2025-12-01T08:58:37+08:00` | 23 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-29T06:00:00+08:00` | 183540 | {'quote_date': '2025-11-28', 'value': 64.07} |

## 24. fb2611 20251229 day （historical_validation）

- Episode：`fb:20251229`
- 决策时点：`2025-12-29T08:59:00+08:00`
- 执行时点：`2025-12-29T09:01:00+08:00`
- label 窗口：`2025-12-29T09:01:00+08:00` → `2025-12-29T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T14:27:00+08:00` | 239520 | {'bar_start': '2025-12-26T14:26:00+08:00', 'close': 1281.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-26T15:00:00+08:00` | 237540 | {'trading_day': 20251226, 'close': 1281.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-29T08:58:25+08:00` | 35 | {'title': '【深圳“十五五”规划建议：推动第六代移动通信、生物制造、具身智能等成为新的经济增', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 356340 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. fb2611 20260108 day （contaminated_audit）

- Episode：`fb:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0022892036 = ln(1309 / 1312)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-07T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-07T14:59:00+08:00', 'close': 1310.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00+08:00` | 64740 | {'trading_day': 20260107, 'close': 1310.5} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. fb2612 20260116 day （contaminated_audit）

- Episode：`fb:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-15T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-15T14:59:00+08:00', 'close': 1256.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00+08:00` | 64740 | {'trading_day': 20260115, 'close': 1256.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. fb2704 20260602 day （contaminated_audit）

- Episode：`fb:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 1290.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 64740 | {'trading_day': 20260601, 'close': 1290.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 28. fb2706 20260702 day （contaminated_audit）

- Episode：`fb:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T14:51:00+08:00` | 65280 | {'bar_start': '2026-07-01T14:50:00+08:00', 'close': 1308.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 64740 | {'trading_day': 20260701, 'close': 1308.5} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. fb2706 20260720 day （contaminated_audit）

- Episode：`fb:20260720`
- 决策时点：`2026-07-20T08:59:00+08:00`
- 执行时点：`2026-07-20T09:01:00+08:00`
- label 窗口：`2026-07-20T09:01:00+08:00` → `2026-07-20T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 237540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 1318.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 237540 | {'trading_day': 20260717, 'close': 1318.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2780140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 529140 | {'quote_date': '2026-07-13', 'value': 81.62} |
