# SC Temporal Spine 人工回放清单（jd_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`ac59497106b6566fecca402238ea810408e895a89b300efa5fac668178c94f90`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. jd2301 20221209 day （discovery）

- Episode：`jd:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:01:00+08:00`
- label 窗口：`2022-12-09T09:01:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：-0.0038431154 = ln(4415 / 4432)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 64740 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 4442.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.030000+08:00` | 64739 | {'trading_day': 20221208, 'close': 4442.0} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

## 01. jd2305 20230117 day （discovery）

- Episode：`jd:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:01:00+08:00`
- label 窗口：`2023-01-17T09:01:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.0022634686 = ln(4423 / 4413)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-16T15:00:00+08:00` | 64740 | {'bar_start': '2023-01-16T14:59:00+08:00', 'close': 4414.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.022000+08:00` | 64739 | {'trading_day': 20230116, 'close': 4414.0} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

## 02. jd2305 20230216 day （discovery）

- Episode：`jd:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:01:00+08:00`
- label 窗口：`2023-02-16T09:01:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.005048198 = ln(4369 / 4347)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-15T15:00:00+08:00` | 64740 | {'bar_start': '2023-02-15T14:59:00+08:00', 'close': 4381.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.045000+08:00` | 64739 | {'trading_day': 20230215, 'close': 4381.0} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

## 03. jd2305 20230314 day （discovery）

- Episode：`jd:20230314`
- 决策时点：`2023-03-14T08:59:00+08:00`
- 执行时点：`2023-03-14T09:01:00+08:00`
- label 窗口：`2023-03-14T09:01:00+08:00` → `2023-03-14T15:00:00+08:00`
- 目标值：0.0095023339 = ln(4441 / 4399)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-03-13T15:00:00+08:00` | 64740 | {'bar_start': '2023-03-13T14:59:00+08:00', 'close': 4373.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-03-13T15:00:00.016000+08:00` | 64739 | {'trading_day': 20230313, 'close': 4373.0} |
| cls_last_telegraph | cls_telegraph | `2023-03-14T08:56:24+08:00` | 156 | {'title': '【比亚迪：“特斯拉叫停与比亚迪合作”为不实信息】', 'labels': '美股动态 特斯拉'} |
| brent_last_close | intl_brent | `2023-03-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-03-13', 'value': 79.67} |

## 04. jd2309 20230523 day （discovery）

- Episode：`jd:20230523`
- 决策时点：`2023-05-23T08:59:00+08:00`
- 执行时点：`2023-05-23T09:01:00+08:00`
- label 窗口：`2023-05-23T09:01:00+08:00` → `2023-05-23T15:00:00+08:00`
- 目标值：-0.00097513416 = ln(4100 / 4104)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 64740 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 4092.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.022000+08:00` | 64739 | {'trading_day': 20230522, 'close': 4092.0} |
| cls_last_telegraph | cls_telegraph | `2023-05-23T08:51:27+08:00` | 453 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2023-05-23T06:00:00+08:00` | 10740 | {'quote_date': '2023-05-22', 'value': 75.77} |

## 05. jd2309 20230615 day （discovery）

- Episode：`jd:20230615`
- 决策时点：`2023-06-15T08:59:00+08:00`
- 执行时点：`2023-06-15T09:01:00+08:00`
- label 窗口：`2023-06-15T09:01:00+08:00` → `2023-06-15T15:00:00+08:00`
- 目标值：0.0017273292 = ln(4056 / 4049)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 64740 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 4046.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.010000+08:00` | 64739 | {'trading_day': 20230614, 'close': 4046.0} |
| cls_last_telegraph | cls_telegraph | `2023-06-15T08:50:12+08:00` | 528 | {'title': '【两市融资余额减少11.11亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2023-06-15T06:00:00+08:00` | 10740 | {'quote_date': '2023-06-14', 'value': 73.39} |

## 06. jd2309 20230714 day （discovery）

- Episode：`jd:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:01:00+08:00`
- label 窗口：`2023-07-14T09:01:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：-0.010643545 = ln(4112 / 4156)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-13T15:00:00+08:00` | 64740 | {'bar_start': '2023-07-13T14:59:00+08:00', 'close': 4145.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.018000+08:00` | 64739 | {'trading_day': 20230713, 'close': 4145.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

## 07. jd2309 20230724 day （discovery）

- Episode：`jd:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:01:00+08:00`
- label 窗口：`2023-07-24T09:01:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：0.0060255107 = ln(4328 / 4302)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-21T15:00:00+08:00` | 237540 | {'bar_start': '2023-07-21T14:59:00+08:00', 'close': 4247.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.040000+08:00` | 237539 | {'trading_day': 20230721, 'close': 4247.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

## 08. jd2403 20240117 day （discovery）

- Episode：`jd:20240117`
- 决策时点：`2024-01-17T08:59:00+08:00`
- 执行时点：`2024-01-17T09:01:00+08:00`
- label 窗口：`2024-01-17T09:01:00+08:00` → `2024-01-17T15:00:00+08:00`
- 目标值：-0.014273213 = ln(3339 / 3387)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 64740 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 3377.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.049000+08:00` | 64739 | {'trading_day': 20240116, 'close': 3377.0} |
| cls_last_telegraph | cls_telegraph | `2024-01-17T08:57:11+08:00` | 109 | {'title': '【Gartner：2023年全球半导体收入总额为5330亿美元 同比下降11.1', 'labels': '半导体芯片'} |
| brent_last_close | intl_brent | `2024-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2024-01-16', 'value': 80.15} |

## 09. jd2405 20240301 day （discovery）

- Episode：`jd:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:01:00+08:00`
- label 窗口：`2024-03-01T09:01:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：-0.0030859893 = ln(3559 / 3570)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-02-29T15:00:00+08:00` | 64740 | {'bar_start': '2024-02-29T14:59:00+08:00', 'close': 3524.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.008000+08:00` | 64739 | {'trading_day': 20240229, 'close': 3524.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

## 10. jd2405 20240401 day （discovery）

- Episode：`jd:20240401`
- 决策时点：`2024-04-01T08:59:00+08:00`
- 执行时点：`2024-04-01T09:01:00+08:00`
- label 窗口：`2024-04-01T09:01:00+08:00` → `2024-04-01T15:00:00+08:00`
- 目标值：-0.0089327561 = ln(3232 / 3261)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 237540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 3287.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.043000+08:00` | 237539 | {'trading_day': 20240329, 'close': 3287.0} |
| cls_last_telegraph | cls_telegraph | `2024-04-01T08:47:28+08:00` | 692 | {'title': '【MCU库存去化今年Q2落底 产业迈入传统旺季】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 269940 | {'quote_date': '2024-03-28', 'value': 86.17} |

## 11. jd2409 20240527 day （discovery）

- Episode：`jd:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:01:00+08:00`
- label 窗口：`2024-05-27T09:01:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：-0.0047541688 = ln(3987 / 4006)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-24T15:00:00+08:00` | 237540 | {'bar_start': '2024-05-24T14:59:00+08:00', 'close': 3996.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.005000+08:00` | 237539 | {'trading_day': 20240524, 'close': 3996.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

## 12. jd2409 20240709 day （discovery）

- Episode：`jd:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:01:00+08:00`
- label 窗口：`2024-07-09T09:01:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：0.0085879561 = ln(4093 / 4058)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-08T15:00:00+08:00` | 64740 | {'bar_start': '2024-07-08T14:59:00+08:00', 'close': 4071.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.032000+08:00` | 64739 | {'trading_day': 20240708, 'close': 4071.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

## 13. jd2501 20240918 day （discovery）

- Episode：`jd:20240918`
- 决策时点：`2024-09-18T08:59:00+08:00`
- 执行时点：`2024-09-18T09:01:00+08:00`
- label 窗口：`2024-09-18T09:01:00+08:00` → `2024-09-18T15:00:00+08:00`
- 目标值：-0.0030938008 = ln(3550 / 3561)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 410340 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 3556.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.032000+08:00` | 410339 | {'trading_day': 20240913, 'close': 3556.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-18T08:55:34+08:00` | 206 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-09-18T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-17', 'value': 74.55} |

## 14. jd2501 20240924 day （discovery）

- Episode：`jd:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:01:00+08:00`
- label 窗口：`2024-09-24T09:01:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.0011267607 = ln(3552 / 3548)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-23T15:00:00+08:00` | 64740 | {'bar_start': '2024-09-23T14:59:00+08:00', 'close': 3539.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.007000+08:00` | 64739 | {'trading_day': 20240923, 'close': 3539.0} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

## 15. jd2501 20241206 day （discovery）

- Episode：`jd:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:01:00+08:00`
- label 窗口：`2024-12-06T09:01:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：-0.0039138993 = ln(3570 / 3584)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-05T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-05T14:59:00+08:00', 'close': 3591.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.047000+08:00` | 64739 | {'trading_day': 20241205, 'close': 3591.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

## 16. jd2502 20241230 day （discovery）

- Episode：`jd:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:01:00+08:00`
- label 窗口：`2024-12-30T09:01:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：-0.023137655 = ln(3375 / 3454)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-27T15:00:00+08:00` | 237540 | {'bar_start': '2024-12-27T14:59:00+08:00', 'close': 3463.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.040000+08:00` | 237539 | {'trading_day': 20241227, 'close': 3463.0} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

## 17. jd2506 20250416 day （historical_validation）

- Episode：`jd:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:01:00+08:00`
- label 窗口：`2025-04-16T09:01:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：0.01803032 = ln(3078 / 3023)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-15T15:00:00+08:00` | 64740 | {'bar_start': '2025-04-15T14:59:00+08:00', 'close': 2995.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.030000+08:00` | 64739 | {'trading_day': 20250415, 'close': 2995.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

## 18. jd2509 20250731 day （historical_validation）

- Episode：`jd:20250731`
- 决策时点：`2025-07-31T08:59:00+08:00`
- 执行时点：`2025-07-31T09:01:00+08:00`
- label 窗口：`2025-07-31T09:01:00+08:00` → `2025-07-31T15:00:00+08:00`
- 目标值：-0.011293175 = ln(3522 / 3562)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 64740 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 3570.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.040000+08:00` | 64739 | {'trading_day': 20250730, 'close': 3570.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-31T08:56:02+08:00` | 178 | {'title': '【台风“竹节草”继续给华东带来强风雨 中东部大范围高温仍将持续】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-07-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-30', 'value': 73.98} |

## 19. jd2509 20250807 day （historical_validation）

- Episode：`jd:20250807`
- 决策时点：`2025-08-07T08:59:00+08:00`
- 执行时点：`2025-08-07T09:01:00+08:00`
- label 窗口：`2025-08-07T09:01:00+08:00` → `2025-08-07T15:00:00+08:00`
- 目标值：0.005618823 = ln(3391 / 3372)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 3378.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.031000+08:00` | 64739 | {'trading_day': 20250806, 'close': 3378.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-07T08:57:03+08:00` | 117 | {'title': '【因技术故障 美联航多个航班被下令停飞】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-07T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-06', 'value': 67.97} |

## 20. jd2511 20250915 day （historical_validation）

- Episode：`jd:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:01:00+08:00`
- label 窗口：`2025-09-15T09:01:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.017330344 = ln(3143 / 3089)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-12T15:00:00+08:00` | 237540 | {'bar_start': '2025-09-12T14:59:00+08:00', 'close': 3040.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.023000+08:00` | 237539 | {'trading_day': 20250912, 'close': 3040.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

## 21. jd2512 20251112 day （historical_validation）

- Episode：`jd:20251112`
- 决策时点：`2025-11-12T08:59:00+08:00`
- 执行时点：`2025-11-12T09:01:00+08:00`
- label 窗口：`2025-11-12T09:01:00+08:00` → `2025-11-12T15:00:00+08:00`
- 目标值：-0.023872101 = ln(3063 / 3137)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 3152.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.041000+08:00` | 64739 | {'trading_day': 20251111, 'close': 3152.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-12T08:58:56+08:00` | 4 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-11-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-11', 'value': 63.86} |

## 22. jd2601 20251127 day （historical_validation）

- Episode：`jd:20251127`
- 决策时点：`2025-11-27T08:59:00+08:00`
- 执行时点：`2025-11-27T09:01:00+08:00`
- label 窗口：`2025-11-27T09:01:00+08:00` → `2025-11-27T15:00:00+08:00`
- 目标值：0.012571069 = ln(3282 / 3241)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-26T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-26T14:59:00+08:00', 'close': 3225.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-26T15:00:00.002000+08:00` | 64739 | {'trading_day': 20251126, 'close': 3225.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T08:58:38+08:00` | 22 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-26', 'value': 64.81} |

## 23. jd2601 20251128 day （historical_validation）

- Episode：`jd:20251128`
- 决策时点：`2025-11-28T08:59:00+08:00`
- 执行时点：`2025-11-28T09:01:00+08:00`
- label 窗口：`2025-11-28T09:01:00+08:00` → `2025-11-28T15:00:00+08:00`
- 目标值：0.003955581 = ln(3293 / 3280)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 3282.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.006000+08:00` | 64739 | {'trading_day': 20251127, 'close': 3282.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-28T08:53:33+08:00` | 327 | {'title': '【四川民企造出高超音速导弹？凌空天行：基本型已量产】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2025-11-28T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-27', 'value': 64.18} |

## 24. jd2602 20251226 day （historical_validation）

- Episode：`jd:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:01:00+08:00`
- label 窗口：`2025-12-26T09:01:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：0.0064461631 = ln(2957 / 2938)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-25T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-25T14:59:00+08:00', 'close': 2946.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.010000+08:00` | 64739 | {'trading_day': 20251225, 'close': 2946.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 25. jd2603 20260108 day （contaminated_audit）

- Episode：`jd:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0076146701 = ln(3009 / 3032)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-07T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-07T14:59:00+08:00', 'close': 3011.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.020000+08:00` | 64739 | {'trading_day': 20260107, 'close': 3011.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 26. jd2603 20260116 day （contaminated_audit）

- Episode：`jd:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：0 = ln(3072 / 3072)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-15T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-15T14:59:00+08:00', 'close': 3066.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.046000+08:00` | 64739 | {'trading_day': 20260115, 'close': 3066.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 27. jd2607 20260602 day （contaminated_audit）

- Episode：`jd:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：-0.0034002073 = ln(4404 / 4419)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 4391.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.004000+08:00` | 64739 | {'trading_day': 20260601, 'close': 4391.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 28. jd2608 20260702 day （contaminated_audit）

- Episode：`jd:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：0.0095503224 = ln(4524 / 4481)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 4468.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.045000+08:00` | 64739 | {'trading_day': 20260701, 'close': 4468.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 29. jd2609 20260720 day （contaminated_audit）

- Episode：`jd:20260720`
- 决策时点：`2026-07-20T08:59:00+08:00`
- 执行时点：`2026-07-20T09:01:00+08:00`
- label 窗口：`2026-07-20T09:01:00+08:00` → `2026-07-20T15:00:00+08:00`
- 目标值：-0.035165367 = ln(4191 / 4341)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 237540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 4342.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.044000+08:00` | 237539 | {'trading_day': 20260717, 'close': 4342.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2780140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 529140 | {'quote_date': '2026-07-13', 'value': 81.62} |
