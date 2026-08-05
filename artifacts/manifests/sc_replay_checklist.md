# SC Temporal Spine 人工回放清单（sc_rv_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`b50f9d29fc6c06cad31f47b28f7535fcb416d30c4ec5cbb9a83b173c43be8cff`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. sc2301 20221209 night （discovery）

- Episode：`sc:20221209`
- 决策时点：`2022-12-08T20:59:00+08:00`
- 执行时点：`2022-12-08T21:00:00+08:00`
- label 窗口：`2022-12-08T21:00:00+08:00` → `2022-12-09T02:30:00+08:00`
- 目标值：0.027464618（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2022-12-08T14:59:00+08:00', 'close': 511.7, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20221208, 'close': 511.7} |
| cls_last_telegraph | cls_telegraph | `2022-12-08T20:58:04+08:00` | 56 | {'title': '【北京市部署应用京抗原小程序】', 'labels': '抗原检测 小程序'} |
| brent_last_close | intl_brent | `2022-12-08T06:00:00+08:00` | 53940 | {'quote_date': '2022-12-07', 'value': 77.11} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 01. sc2301 20221209 day （discovery）

- Episode：`sc:20221209`
- 决策时点：`2022-12-09T08:59:00+08:00`
- 执行时点：`2022-12-09T09:00:00+08:00`
- label 窗口：`2022-12-09T09:00:00+08:00` → `2022-12-09T15:00:00+08:00`
- 目标值：0.015223897（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2022-12-09T02:30:00+08:00` | 23340 | {'bar_start': '2022-12-09T02:29:00+08:00', 'close': 505.4, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2022-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20221208, 'close': 511.7} |
| cls_last_telegraph | cls_telegraph | `2022-12-09T08:56:11+08:00` | 169 | {'title': '【两市融资余额减少0.54亿元】', 'labels': '沪深交易所动态 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2022-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2022-12-08', 'value': 76.02} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 02. sc2303 20230117 day （discovery）

- Episode：`sc:20230117`
- 决策时点：`2023-01-17T08:59:00+08:00`
- 执行时点：`2023-01-17T09:00:00+08:00`
- label 窗口：`2023-01-17T09:00:00+08:00` → `2023-01-17T15:00:00+08:00`
- 目标值：0.0096162321（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-01-17T02:30:00+08:00` | 23340 | {'bar_start': '2023-01-17T02:29:00+08:00', 'close': 540.5, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-01-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230116, 'close': 542.3} |
| cls_last_telegraph | cls_telegraph | `2023-01-17T08:54:16+08:00` | 284 | {'title': '【德方纳米：年产11万吨磷酸锰铁锂项目已投产】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-01-17T06:00:00+08:00` | 10740 | {'quote_date': '2023-01-16', 'value': 82.65} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 03. sc2304 20230216 day （discovery）

- Episode：`sc:20230216`
- 决策时点：`2023-02-16T08:59:00+08:00`
- 执行时点：`2023-02-16T09:00:00+08:00`
- label 窗口：`2023-02-16T09:00:00+08:00` → `2023-02-16T15:00:00+08:00`
- 目标值：0.0080933616（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-02-16T02:30:00+08:00` | 23340 | {'bar_start': '2023-02-16T02:29:00+08:00', 'close': 567.8, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-02-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230215, 'close': 562.3} |
| cls_last_telegraph | cls_telegraph | `2023-02-16T08:56:54+08:00` | 126 | {'title': '【韩国检方对最大在野党党首李在明申请拘捕令】', 'labels': ''} |
| brent_last_close | intl_brent | `2023-02-16T06:00:00+08:00` | 10740 | {'quote_date': '2023-02-15', 'value': 84.11} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 04. sc2307 20230523 night （discovery）

- Episode：`sc:20230523`
- 决策时点：`2023-05-22T20:59:00+08:00`
- 执行时点：`2023-05-22T21:00:00+08:00`
- label 窗口：`2023-05-22T21:00:00+08:00` → `2023-05-23T02:30:00+08:00`
- 目标值：0.013498059（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-05-22T15:00:00+08:00` | 21540 | {'bar_start': '2023-05-22T14:59:00+08:00', 'close': 507.00000000000006, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-05-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230522, 'close': 507.00000000000006} |
| cls_last_telegraph | cls_telegraph | `2023-05-22T20:57:35+08:00` | 85 | {'title': '【普莱得中签号出炉 共3.8万个】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2023-05-20T06:00:00+08:00` | 226740 | {'quote_date': '2023-05-19', 'value': 75.42} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 05. sc2307 20230615 night （discovery）

- Episode：`sc:20230615`
- 决策时点：`2023-06-14T20:59:00+08:00`
- 执行时点：`2023-06-14T21:00:00+08:00`
- label 窗口：`2023-06-14T21:00:00+08:00` → `2023-06-15T02:30:00+08:00`
- 目标值：0.014465379（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-06-14T15:00:00+08:00` | 21540 | {'bar_start': '2023-06-14T14:59:00+08:00', 'close': 524.4000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2023-06-14T15:00:00.500000+08:00` | 21539 | {'trading_day': 20230614, 'close': 524.4000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-06-14T20:56:19+08:00` | 161 | {'title': '【金新农：预计第三季度生猪价格可能略有上涨 但很难突破去年高点】', 'labels': '机构调研动向'} |
| brent_last_close | intl_brent | `2023-06-14T06:00:00+08:00` | 53940 | {'quote_date': '2023-06-13', 'value': 74.24} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 06. sc2308 20230714 day （discovery）

- Episode：`sc:20230714`
- 决策时点：`2023-07-14T08:59:00+08:00`
- 执行时点：`2023-07-14T09:00:00+08:00`
- label 窗口：`2023-07-14T09:00:00+08:00` → `2023-07-14T15:00:00+08:00`
- 目标值：0.0059027314（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-14T02:30:00+08:00` | 23340 | {'bar_start': '2023-07-14T02:29:00+08:00', 'close': 588.1, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-13T15:00:00.500000+08:00` | 64739 | {'trading_day': 20230713, 'close': 580.0} |
| cls_last_telegraph | cls_telegraph | `2023-07-14T08:58:18+08:00` | 42 | {'title': '【英伟达订单喷发 消息称台积电23Q3产能利用率回升至八成】', 'labels': '台积电 半导体芯片'} |
| brent_last_close | intl_brent | `2023-07-14T06:00:00+08:00` | 10740 | {'quote_date': '2023-07-13', 'value': 81.31} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 07. sc2309 20230724 day （discovery）

- Episode：`sc:20230724`
- 决策时点：`2023-07-24T08:59:00+08:00`
- 执行时点：`2023-07-24T09:00:00+08:00`
- label 窗口：`2023-07-24T09:00:00+08:00` → `2023-07-24T15:00:00+08:00`
- 目标值：0.0058466076（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2023-07-22T02:30:00+08:00` | 196140 | {'bar_start': '2023-07-22T02:29:00+08:00', 'close': 591.6, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2023-07-21T15:00:00.500000+08:00` | 237539 | {'trading_day': 20230721, 'close': 588.8000000000002} |
| cls_last_telegraph | cls_telegraph | `2023-07-24T08:56:27+08:00` | 153 | {'title': '【防范台风“杜苏芮” 福建沿海已停运9条客运航线】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2023-07-22T06:00:00+08:00` | 183540 | {'quote_date': '2023-07-21', 'value': 81.06} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 08. sc2402 20240117 night （discovery）

- Episode：`sc:20240117`
- 决策时点：`2024-01-16T20:59:00+08:00`
- 执行时点：`2024-01-16T21:00:00+08:00`
- label 窗口：`2024-01-16T21:00:00+08:00` → `2024-01-17T02:30:00+08:00`
- 目标值：0.013823231（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2024-01-16T14:59:00+08:00', 'close': 556.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240116, 'close': 556.1} |
| cls_last_telegraph | cls_telegraph | `2024-01-16T20:58:15+08:00` | 45 | {'title': '【李强出席世界经济论坛2024年年会并发表特别致辞】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2024-01-15', 'value': 79.76} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 09. sc2404 20240301 day （discovery）

- Episode：`sc:20240301`
- 决策时点：`2024-03-01T08:59:00+08:00`
- 执行时点：`2024-03-01T09:00:00+08:00`
- label 窗口：`2024-03-01T09:00:00+08:00` → `2024-03-01T15:00:00+08:00`
- 目标值：0.0036267556（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-01T02:30:00+08:00` | 23340 | {'bar_start': '2024-03-01T02:29:00+08:00', 'close': 605.9000000000002, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-02-29T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240229, 'close': 606.0} |
| cls_last_telegraph | cls_telegraph | `2024-03-01T08:56:27+08:00` | 153 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-03-01T06:00:00+08:00` | 10740 | {'quote_date': '2024-02-29', 'value': 84.57} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 10. sc2405 20240401 night （discovery）

- Episode：`sc:20240401`
- 决策时点：`2024-03-29T20:59:00+08:00`
- 执行时点：`2024-03-29T21:00:00+08:00`
- label 窗口：`2024-03-29T21:00:00+08:00` → `2024-03-30T02:30:00+08:00`
- 目标值：0.0048508488（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-03-29T15:00:00+08:00` | 21540 | {'bar_start': '2024-03-29T14:59:00+08:00', 'close': 645.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-03-29T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240329, 'close': 645.5} |
| cls_last_telegraph | cls_telegraph | `2024-03-29T20:56:57+08:00` | 123 | {'title': '【兆威机电：2023年净利同比增19.55% 拟10转4派5.5元】', 'labels': 'A股公告速递'} |
| brent_last_close | intl_brent | `2024-03-29T06:00:00+08:00` | 53940 | {'quote_date': '2024-03-28', 'value': 86.17} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 11. sc2407 20240527 day （discovery）

- Episode：`sc:20240527`
- 决策时点：`2024-05-27T08:59:00+08:00`
- 执行时点：`2024-05-27T09:00:00+08:00`
- label 窗口：`2024-05-27T09:00:00+08:00` → `2024-05-27T15:00:00+08:00`
- 目标值：0.0049198747（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-25T02:30:00+08:00` | 196140 | {'bar_start': '2024-05-25T02:29:00+08:00', 'close': 606.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-05-24T15:00:00.500000+08:00` | 237539 | {'trading_day': 20240524, 'close': 599.0} |
| cls_last_telegraph | cls_telegraph | `2024-05-27T08:48:17+08:00` | 643 | {'title': '【两市融资余额减少66.03亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-05-25T06:00:00+08:00` | 183540 | {'quote_date': '2024-05-24', 'value': 78.92} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 12. sc2408 20240709 day （discovery）

- Episode：`sc:20240709`
- 决策时点：`2024-07-09T08:59:00+08:00`
- 执行时点：`2024-07-09T09:00:00+08:00`
- label 窗口：`2024-07-09T09:00:00+08:00` → `2024-07-09T15:00:00+08:00`
- 目标值：0.0038203175（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-09T02:30:00+08:00` | 23340 | {'bar_start': '2024-07-09T02:29:00+08:00', 'close': 625.6, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-07-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240708, 'close': 628.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-09T08:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-07-09T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-08', 'value': 87.15} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 13. sc2410 20240918 night （discovery）

- Episode：`sc:20240918`
- 决策时点：`2024-09-13T20:59:00+08:00`
- 执行时点：`2024-09-13T21:00:00+08:00`
- label 窗口：`2024-09-13T21:00:00+08:00` → `2024-09-14T02:30:00+08:00`
- 目标值：NULL（no-trade：no_ticks）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-13T15:00:00+08:00` | 21540 | {'bar_start': '2024-09-13T14:59:00+08:00', 'close': 513.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-09-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20240913, 'close': 513.1} |
| cls_last_telegraph | cls_telegraph | `2024-09-13T20:58:12+08:00` | 48 | {'title': '【西班牙主办欧盟和阿拉伯国家外长会 讨论巴以冲突解决方案】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2024-09-13T06:00:00+08:00` | 53940 | {'quote_date': '2024-09-12', 'value': 73.81} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 14. sc2411 20240924 day （discovery）

- Episode：`sc:20240924`
- 决策时点：`2024-09-24T08:59:00+08:00`
- 执行时点：`2024-09-24T09:00:00+08:00`
- label 窗口：`2024-09-24T09:00:00+08:00` → `2024-09-24T15:00:00+08:00`
- 目标值：0.0068602159（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-09-24T02:30:00+08:00` | 23340 | {'bar_start': '2024-09-24T02:29:00+08:00', 'close': 520.8, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-09-23T15:00:00.500000+08:00` | 64739 | {'trading_day': 20240923, 'close': 525.1} |
| cls_last_telegraph | cls_telegraph | `2024-09-24T08:48:21+08:00` | 639 | {'title': '【两市融资余额减少4.44亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-09-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-09-23', 'value': 74.95} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 15. sc2501 20241206 day （discovery）

- Episode：`sc:20241206`
- 决策时点：`2024-12-06T08:59:00+08:00`
- 执行时点：`2024-12-06T09:00:00+08:00`
- label 窗口：`2024-12-06T09:00:00+08:00` → `2024-12-06T15:00:00+08:00`
- 目标值：0.0043815188（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-06T02:30:00+08:00` | 23340 | {'bar_start': '2024-12-06T02:29:00+08:00', 'close': 528.4, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-05T15:00:00.500000+08:00` | 64739 | {'trading_day': 20241205, 'close': 529.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-06T08:54:45+08:00` | 255 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-12-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-05', 'value': 73.78} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 16. sc2502 20241230 day （discovery）

- Episode：`sc:20241230`
- 决策时点：`2024-12-30T08:59:00+08:00`
- 执行时点：`2024-12-30T09:00:00+08:00`
- label 窗口：`2024-12-30T09:00:00+08:00` → `2024-12-30T15:00:00+08:00`
- 目标值：0.0039656572（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-28T02:30:00+08:00` | 196140 | {'bar_start': '2024-12-28T02:29:00+08:00', 'close': 549.2, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2024-12-27T15:00:00.500000+08:00` | 237539 | {'trading_day': 20241227, 'close': 544.9} |
| cls_last_telegraph | cls_telegraph | `2024-12-30T08:58:31+08:00` | 29 | {'title': '【安徽正式启动基金份额转让试点】', 'labels': 'TMT行业观察 创投风向标 创投'} |
| brent_last_close | intl_brent | `2024-12-28T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-27', 'value': 73.77} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 17. sc2503 20250211 night （historical_validation）

- Episode：`sc:20250211`
- 决策时点：`2025-02-10T20:59:00+08:00`
- 执行时点：`2025-02-10T21:00:00+08:00`
- label 窗口：`2025-02-10T21:00:00+08:00` → `2025-02-11T02:30:00+08:00`
- 目标值：0.007699365（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-02-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-02-10T14:59:00+08:00', 'close': 607.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-02-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250210, 'close': 607.0} |
| cls_last_telegraph | cls_telegraph | `2025-02-10T20:51:29+08:00` | 451 | {'title': '', 'labels': '比特币'} |
| brent_last_close | intl_brent | `2025-02-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-02-07', 'value': 74.68} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 18. sc2505 20250416 day （historical_validation）

- Episode：`sc:20250416`
- 决策时点：`2025-04-16T08:59:00+08:00`
- 执行时点：`2025-04-16T09:00:00+08:00`
- label 窗口：`2025-04-16T09:00:00+08:00` → `2025-04-16T15:00:00+08:00`
- 目标值：0.0095070119（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-04-16T02:30:00+08:00` | 23340 | {'bar_start': '2025-04-16T02:29:00+08:00', 'close': 474.8, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-04-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250415, 'close': 477.0} |
| cls_last_telegraph | cls_telegraph | `2025-04-16T08:48:45+08:00` | 615 | {'title': '【两市融资余额增加4.1亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态 盘面直播'} |
| brent_last_close | intl_brent | `2025-04-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-04-15', 'value': 66.58} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 19. sc2509 20250731 night （historical_validation）

- Episode：`sc:20250731`
- 决策时点：`2025-07-30T20:59:00+08:00`
- 执行时点：`2025-07-30T21:00:00+08:00`
- label 窗口：`2025-07-30T21:00:00+08:00` → `2025-07-31T02:30:00+08:00`
- 目标值：0.0086263618（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-07-30T14:59:00+08:00', 'close': 528.6, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-07-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250730, 'close': 528.6} |
| cls_last_telegraph | cls_telegraph | `2025-07-30T20:58:30+08:00` | 30 | {'title': '【俄堪察加半岛强震后火山喷发】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-07-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-07-29', 'value': 73.21} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 20. sc2509 20250807 night （historical_validation）

- Episode：`sc:20250807`
- 决策时点：`2025-08-06T20:59:00+08:00`
- 执行时点：`2025-08-06T21:00:00+08:00`
- label 窗口：`2025-08-06T21:00:00+08:00` → `2025-08-07T02:30:00+08:00`
- 目标值：0.012476404（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-06T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-06T14:59:00+08:00', 'close': 505.9, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-06T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250806, 'close': 505.9} |
| cls_last_telegraph | cls_telegraph | `2025-08-06T20:57:38+08:00` | 82 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-06T06:00:00+08:00` | 53940 | {'quote_date': '2025-08-05', 'value': 69.14} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 21. sc2510 20250915 day （historical_validation）

- Episode：`sc:20250915`
- 决策时点：`2025-09-15T08:59:00+08:00`
- 执行时点：`2025-09-15T09:00:00+08:00`
- label 窗口：`2025-09-15T09:00:00+08:00` → `2025-09-15T15:00:00+08:00`
- 目标值：0.0065321544（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-13T02:30:00+08:00` | 196140 | {'bar_start': '2025-09-13T02:29:00+08:00', 'close': 486.8, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-12T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250912, 'close': 475.3} |
| cls_last_telegraph | cls_telegraph | `2025-09-15T08:58:42+08:00` | 18 | {'title': '【中信证券：上调2025-2027年国内储能装机预测至130/165/190GW', 'labels': '能源行业新闻 储能'} |
| brent_last_close | intl_brent | `2025-09-13T06:00:00+08:00` | 183540 | {'quote_date': '2025-09-12', 'value': 67.87} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 22. sc2512 20251112 night （historical_validation）

- Episode：`sc:20251112`
- 决策时点：`2025-11-11T20:59:00+08:00`
- 执行时点：`2025-11-11T21:00:00+08:00`
- label 窗口：`2025-11-11T21:00:00+08:00` → `2025-11-12T02:30:00+08:00`
- 目标值：0.0082141188（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 458.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251111, 'close': 458.8} |
| cls_last_telegraph | cls_telegraph | `2025-11-11T20:56:54+08:00` | 126 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2025-11-11T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-10', 'value': 63.01} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 23. sc2601 20251128 night （historical_validation）

- Episode：`sc:20251128`
- 决策时点：`2025-11-27T20:59:00+08:00`
- 执行时点：`2025-11-27T21:00:00+08:00`
- label 窗口：`2025-11-27T21:00:00+08:00` → `2025-11-28T02:30:00+08:00`
- 目标值：0.006881339（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-27T14:59:00+08:00', 'close': 447.6, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251127, 'close': 447.6} |
| cls_last_telegraph | cls_telegraph | `2025-11-27T20:57:18+08:00` | 102 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-26', 'value': 64.81} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 24. sc2602 20251226 day （historical_validation）

- Episode：`sc:20251226`
- 决策时点：`2025-12-26T08:59:00+08:00`
- 执行时点：`2025-12-26T09:00:00+08:00`
- label 窗口：`2025-12-26T09:00:00+08:00` → `2025-12-26T15:00:00+08:00`
- 目标值：0.0054860743（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-26T02:30:00+08:00` | 23340 | {'bar_start': '2025-12-26T02:29:00+08:00', 'close': 444.7, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251225, 'close': 442.70000000000016} |
| cls_last_telegraph | cls_telegraph | `2025-12-26T08:56:10+08:00` | 170 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 97140 | {'quote_date': '2025-12-24', 'value': 63.7} |

> 该决策时点之前无可用观测的来源：pm_cn_registry_v3

## 25. sc2602 20260108 day （contaminated_audit）

- Episode：`sc:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:00:00+08:00`
- label 窗口：`2026-01-08T09:00:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：0.0066624381（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T02:30:00+08:00` | 23340 | {'bar_start': '2026-01-08T02:29:00+08:00', 'close': 415.5, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 416.3} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |
| pm_admitted_markets | pm_cn_registry_v3 | `2026-01-08T07:25:19+08:00` | 5621 | {'admitted_markets': 18, 'last_slug': 'israel-strikes-iran-by-january-16-2026-4', 'theme': 'mideast_conflict'} |

## 26. sc2603 20260116 day （contaminated_audit）

- Episode：`sc:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:00:00+08:00`
- label 窗口：`2026-01-16T09:00:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：0.0068153845（222 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T02:30:00+08:00` | 23340 | {'bar_start': '2026-01-16T02:29:00+08:00', 'close': 441.8, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 446.6} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |
| pm_admitted_markets | pm_cn_registry_v3 | `2026-01-16T07:23:22+08:00` | 5738 | {'admitted_markets': 35, 'last_slug': 'israel-strikes-iran-by-january-23-2026', 'theme': 'mideast_conflict'} |

## 27. sc2607 20260602 night （contaminated_audit）

- Episode：`sc:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:00:00+08:00`
- label 窗口：`2026-06-01T21:00:00+08:00` → `2026-06-02T02:30:00+08:00`
- 目标值：0.022516236（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 595.9000000000002, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 595.9000000000002} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |
| pm_admitted_markets | pm_cn_registry_v3 | `2026-06-01T15:03:41+08:00` | 21319 | {'admitted_markets': 328, 'last_slug': 'will-russia-capture-lyman-by-december-31', 'theme': 'russia_ukraine'} |

## 28. sc2608 20260702 night （contaminated_audit）

- Episode：`sc:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:00:00+08:00`
- label 窗口：`2026-07-01T21:00:00+08:00` → `2026-07-02T02:30:00+08:00`
- 目标值：0.01206849（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 451.3, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 451.3} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |
| pm_admitted_markets | pm_cn_registry_v3 | `2026-06-28T17:39:35+08:00` | 271165 | {'admitted_markets': 362, 'last_slug': 'strait-of-hormuz-traffic-returns-to-norm', 'theme': 'mideast_conflict'} |

## 29. sc2609 20260720 night （contaminated_audit）

- Episode：`sc:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:00:00+08:00`
- label 窗口：`2026-07-17T21:00:00+08:00` → `2026-07-18T02:30:00+08:00`
- 目标值：0.020375035（329 个 1 分钟收益）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 510.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 510.5} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
| pm_admitted_markets | pm_cn_registry_v3 | `2026-07-12T21:24:26+08:00` | 430474 | {'admitted_markets': 370, 'last_slug': 'strait-of-hormuz-traffic-returns-to-norm', 'theme': 'mideast_conflict'} |
