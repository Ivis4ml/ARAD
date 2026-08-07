# SC Temporal Spine 人工回放清单（ad_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`4ac79ceebe92e2f644fe2b744738242f39bcdbf2eb7ddd7c2fa8db6f4012ceb3`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. ad2511 20250619 day （historical_validation）

- Episode：`ad:20250619`
- 决策时点：`2025-06-19T08:59:00+08:00`
- 执行时点：`2025-06-19T09:01:00+08:00`
- label 窗口：`2025-06-19T09:01:00+08:00` → `2025-06-19T15:00:00+08:00`
- 目标值：-0.0017679004 = ln(19780 / 19815)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-19T01:00:00+08:00` | 28740 | {'bar_start': '2025-06-19T00:59:00+08:00', 'close': 19810.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-06-18T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250618, 'close': 19730.0} |
| cls_last_telegraph | cls_telegraph | `2025-06-19T08:58:47+08:00` | 13 | {'title': '【以军炮击加沙地带中部致多人死伤】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-06-19T06:00:00+08:00` | 10740 | {'quote_date': '2025-06-18', 'value': 78.38} |

## 01. ad2511 20250630 night （historical_validation）

- Episode：`ad:20250630`
- 决策时点：`2025-06-27T20:59:00+08:00`
- 执行时点：`2025-06-27T21:01:00+08:00`
- label 窗口：`2025-06-27T21:01:00+08:00` → `2025-06-28T01:00:00+08:00`
- 目标值：-0.0012627859 = ln(19785 / 19810)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-27T15:00:00+08:00` | 21540 | {'bar_start': '2025-06-27T14:59:00+08:00', 'close': 19790.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-06-27T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250627, 'close': 19790.0} |
| cls_last_telegraph | cls_telegraph | `2025-06-27T20:56:36+08:00` | 144 | {'title': '【自然资源部全力推进新一轮找矿突破战略行动】', 'labels': '能源行业新闻'} |
| brent_last_close | intl_brent | `2025-06-27T06:00:00+08:00` | 53940 | {'quote_date': '2025-06-26', 'value': 68.57} |

## 02. ad2511 20250704 day （historical_validation）

- Episode：`ad:20250704`
- 决策时点：`2025-07-04T08:59:00+08:00`
- 执行时点：`2025-07-04T09:01:00+08:00`
- label 窗口：`2025-07-04T09:01:00+08:00` → `2025-07-04T15:00:00+08:00`
- 目标值：-0.0030128067 = ln(19885 / 19945)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-04T01:00:00+08:00` | 28740 | {'bar_start': '2025-07-04T00:59:00+08:00', 'close': 19925.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-07-03T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250703, 'close': 19965.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-04T08:52:48+08:00` | 372 | {'title': '【韩智库：韩国人口百年内或锐减85%】', 'labels': '环球市场情报 婴童'} |
| brent_last_close | intl_brent | `2025-07-04T06:00:00+08:00` | 10740 | {'quote_date': '2025-07-03', 'value': 70.42} |

## 03. ad2511 20250728 day （historical_validation）

- Episode：`ad:20250728`
- 决策时点：`2025-07-28T08:59:00+08:00`
- 执行时点：`2025-07-28T09:01:00+08:00`
- label 窗口：`2025-07-28T09:01:00+08:00` → `2025-07-28T15:00:00+08:00`
- 目标值：0.0017493444 = ln(20025 / 19990)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-07-26T01:00:00+08:00` | 201540 | {'bar_start': '2025-07-26T00:59:00+08:00', 'close': 19995.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-07-25T15:00:00.500000+08:00` | 237539 | {'trading_day': 20250725, 'close': 20135.0} |
| cls_last_telegraph | cls_telegraph | `2025-07-28T08:56:46+08:00` | 134 | {'title': '【中信证券：随着自动驾驶相关法律法规的逐步完善 汽车智能化产业链有望受益】', 'labels': '汽车大新闻 人工智能 智能驾驶'} |
| brent_last_close | intl_brent | `2025-07-26T06:00:00+08:00` | 183540 | {'quote_date': '2025-07-25', 'value': 69.23} |

## 04. ad2511 20250808 day （historical_validation）

- Episode：`ad:20250808`
- 决策时点：`2025-08-08T08:59:00+08:00`
- 执行时点：`2025-08-08T09:01:00+08:00`
- label 窗口：`2025-08-08T09:01:00+08:00` → `2025-08-08T15:00:00+08:00`
- 目标值：0.0024894213 = ln(20110 / 20060)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-08T01:00:00+08:00` | 28740 | {'bar_start': '2025-08-08T00:59:00+08:00', 'close': 20070.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-08-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250807, 'close': 20135.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-08T08:58:13+08:00` | 47 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2025-08-08T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-07', 'value': 66.99} |

## 05. ad2511 20250812 night （historical_validation）

- Episode：`ad:20250812`
- 决策时点：`2025-08-11T20:59:00+08:00`
- 执行时点：`2025-08-11T21:01:00+08:00`
- label 窗口：`2025-08-11T21:01:00+08:00` → `2025-08-12T01:00:00+08:00`
- 目标值：0 = ln(20050 / 20050)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T15:00:00+08:00` | 21540 | {'bar_start': '2025-08-11T14:59:00+08:00', 'close': 20135.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250811, 'close': 20135.0} |
| cls_last_telegraph | cls_telegraph | `2025-08-11T20:57:26+08:00` | 94 | {'title': '【雅创电子：人形机器人处于持续推进中 预计2025年下半年部分分销产品可批量出货', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-08-09T06:00:00+08:00` | 226740 | {'quote_date': '2025-08-08', 'value': 67.17} |

## 06. ad2512 20250923 night （historical_validation）

- Episode：`ad:20250923`
- 决策时点：`2025-09-22T20:59:00+08:00`
- 执行时点：`2025-09-22T21:01:00+08:00`
- label 窗口：`2025-09-22T21:01:00+08:00` → `2025-09-23T01:00:00+08:00`
- 目标值：0.00098643658 = ln(20285 / 20265)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-22T15:00:00+08:00` | 21540 | {'bar_start': '2025-09-22T14:59:00+08:00', 'close': 20340.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-22T15:00:00.500000+08:00` | 21539 | {'trading_day': 20250922, 'close': 20340.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-22T20:55:57+08:00` | 183 | {'title': '', 'labels': '环球市场情报 期货市场情报 原油市场动态 海外大宗商品 能源'} |
| brent_last_close | intl_brent | `2025-09-20T06:00:00+08:00` | 226740 | {'quote_date': '2025-09-19', 'value': 67.05} |

## 07. ad2512 20251009 day （historical_validation）

- Episode：`ad:20251009`
- 决策时点：`2025-10-09T08:59:00+08:00`
- 执行时点：`2025-10-09T09:01:00+08:00`
- label 窗口：`2025-10-09T09:01:00+08:00` → `2025-10-09T15:00:00+08:00`
- 目标值：0.01121963 = ln(20615 / 20385)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-30T15:00:00+08:00` | 755940 | {'bar_start': '2025-09-30T14:59:00+08:00', 'close': 20210.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-30T15:00:00.500000+08:00` | 755939 | {'trading_day': 20250930, 'close': 20210.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-09T08:54:11+08:00` | 289 | {'title': '【预告】', 'labels': '提醒电报'} |
| brent_last_close | intl_brent | `2025-10-09T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-08', 'value': 67.42} |

## 08. ad2512 20251016 day （historical_validation）

- Episode：`ad:20251016`
- 决策时点：`2025-10-16T08:59:00+08:00`
- 执行时点：`2025-10-16T09:01:00+08:00`
- label 窗口：`2025-10-16T09:01:00+08:00` → `2025-10-16T15:00:00+08:00`
- 目标值：0.0034221495 = ln(20490 / 20420)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-16T01:00:00+08:00` | 28740 | {'bar_start': '2025-10-16T00:59:00+08:00', 'close': 20425.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-10-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251015, 'close': 20410.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-16T08:57:13+08:00` | 107 | {'title': '【预告】', 'labels': '提醒电报'} |
| brent_last_close | intl_brent | `2025-10-16T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-15', 'value': 62.33} |

## 09. ad2512 20251029 day （historical_validation）

- Episode：`ad:20251029`
- 决策时点：`2025-10-29T08:59:00+08:00`
- 执行时点：`2025-10-29T09:01:00+08:00`
- label 窗口：`2025-10-29T09:01:00+08:00` → `2025-10-29T15:00:00+08:00`
- 目标值：0.0016930709 = ln(20690 / 20655)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-29T01:00:00+08:00` | 28740 | {'bar_start': '2025-10-29T00:59:00+08:00', 'close': 20680.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-10-28T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251028, 'close': 20575.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-29T08:54:25+08:00` | 275 | {'title': '【2025年APEC工商领导人峰会开幕】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-10-29T06:00:00+08:00` | 10740 | {'quote_date': '2025-10-28', 'value': 64.03} |

## 10. ad2601 20251110 night （historical_validation）

- Episode：`ad:20251110`
- 决策时点：`2025-11-07T20:59:00+08:00`
- 执行时点：`2025-11-07T21:01:00+08:00`
- label 窗口：`2025-11-07T21:01:00+08:00` → `2025-11-08T01:00:00+08:00`
- 目标值：-0.0042857208 = ln(20955 / 21045)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-07T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-07T14:59:00+08:00', 'close': 21010.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-07T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251107, 'close': 21010.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-07T20:53:31+08:00` | 329 | {'title': '', 'labels': '美股动态 存储器 半导体设备'} |
| brent_last_close | intl_brent | `2025-11-07T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-06', 'value': 63.41} |

## 11. ad2601 20251126 night （historical_validation）

- Episode：`ad:20251126`
- 决策时点：`2025-11-25T20:59:00+08:00`
- 执行时点：`2025-11-25T21:01:00+08:00`
- label 窗口：`2025-11-25T21:01:00+08:00` → `2025-11-26T01:00:00+08:00`
- 目标值：-0.0031419965 = ln(20655 / 20720)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-25T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-25T14:59:00+08:00', 'close': 20705.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-25T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251125, 'close': 20705.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-25T20:58:30+08:00` | 30 | {'title': '【智度股份：向谷歌等企业提供流量变现服务】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-11-25T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-24', 'value': 64.83} |

## 12. ad2601 20251127 night （historical_validation）

- Episode：`ad:20251127`
- 决策时点：`2025-11-26T20:59:00+08:00`
- 执行时点：`2025-11-26T21:01:00+08:00`
- label 窗口：`2025-11-26T21:01:00+08:00` → `2025-11-27T01:00:00+08:00`
- 目标值：-0.0012009128 = ln(20805 / 20830)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-26T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-26T14:59:00+08:00', 'close': 20695.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-26T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251126, 'close': 20695.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-26T20:50:10+08:00` | 530 | {'title': '【北京启动专项行动重点整治六类金融领域网络乱象】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-11-26T06:00:00+08:00` | 53940 | {'quote_date': '2025-11-25', 'value': 63.99} |

## 13. ad2602 20251219 night （historical_validation）

- Episode：`ad:20251219`
- 决策时点：`2025-12-18T20:59:00+08:00`
- 执行时点：`2025-12-18T21:01:00+08:00`
- label 窗口：`2025-12-18T21:01:00+08:00` → `2025-12-19T01:00:00+08:00`
- 目标值：0.0016577861 = ln(21130 / 21095)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-18T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-18T14:59:00+08:00', 'close': 21110.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-18T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251218, 'close': 21110.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-18T20:56:27+08:00` | 153 | {'title': '', 'labels': '期货市场情报 核电'} |
| brent_last_close | intl_brent | `2025-12-18T06:00:00+08:00` | 53940 | {'quote_date': '2025-12-17', 'value': 60.61} |

## 14. ad2603 20251231 night （historical_validation）

- Episode：`ad:20251231`
- 决策时点：`2025-12-30T20:59:00+08:00`
- 执行时点：`2025-12-30T21:01:00+08:00`
- label 窗口：`2025-12-30T21:01:00+08:00` → `2025-12-31T01:00:00+08:00`
- 目标值：-0.0032490166 = ln(21510 / 21580)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-30T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-30T14:59:00+08:00', 'close': 21475.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-30T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251230, 'close': 21475.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-30T20:58:01+08:00` | 59 | {'title': '【农业农村部：多油并举提高大豆油料产能和自给率 大力发展现代畜牧业、现代渔业】', 'labels': '期货市场情报 农业种植 期货监管单位 油脂油料期货'} |
| brent_last_close | intl_brent | `2025-12-30T06:00:00+08:00` | 53940 | {'quote_date': '2025-12-29', 'value': 63.1} |

## 15. ad2603 20260108 day （contaminated_audit）

- Episode：`ad:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.0079382997 = ln(22585 / 22765)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-08T00:59:00+08:00', 'close': 22965.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260107, 'close': 23035.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 16. ad2603 20260112 night （contaminated_audit）

- Episode：`ad:20260112`
- 决策时点：`2026-01-09T20:59:00+08:00`
- 执行时点：`2026-01-09T21:01:00+08:00`
- label 窗口：`2026-01-09T21:01:00+08:00` → `2026-01-10T01:00:00+08:00`
- 目标值：-0.0030342459 = ln(23035 / 23105)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-09T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-09T14:59:00+08:00', 'close': 22985.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-09T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260109, 'close': 22985.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-09T20:58:10+08:00` | 50 | {'title': '【迪拜机场确认多趟飞往伊朗航班被取消】', 'labels': '民航机场 机场 中东冲突'} |
| brent_last_close | intl_brent | `2026-01-09T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-08', 'value': 63.34} |

## 17. ad2603 20260113 day （contaminated_audit）

- Episode：`ad:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：-0.010307156 = ln(23165 / 23405)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-13T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-13T00:59:00+08:00', 'close': 23445.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260112, 'close': 23340.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 18. ad2603 20260116 day （contaminated_audit）

- Episode：`ad:20260116`
- 决策时点：`2026-01-16T08:59:00+08:00`
- 执行时点：`2026-01-16T09:01:00+08:00`
- label 窗口：`2026-01-16T09:01:00+08:00` → `2026-01-16T15:00:00+08:00`
- 目标值：-0.013326249 = ln(22735 / 23040)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T01:00:00+08:00` | 28740 | {'bar_start': '2026-01-16T00:59:00+08:00', 'close': 23070.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260115, 'close': 23155.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T08:57:15+08:00` | 105 | {'title': '【景瑞控股：法院作出清盘令 股份暂停买卖】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 19. ad2603 20260204 night （contaminated_audit）

- Episode：`ad:20260204`
- 决策时点：`2026-02-03T20:59:00+08:00`
- 执行时点：`2026-02-03T21:01:00+08:00`
- label 窗口：`2026-02-03T21:01:00+08:00` → `2026-02-04T01:00:00+08:00`
- 目标值：0.00089726341 = ln(22300 / 22280)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T15:00:00+08:00` | 21540 | {'bar_start': '2026-02-03T14:59:00+08:00', 'close': 22215.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260203, 'close': 22215.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-03T20:57:39+08:00` | 81 | {'title': '【英国海上贸易行动办公室：霍尔木兹海峡发生一起可疑活动事件】', 'labels': '期货市场情报 船舶 中东冲突 航运期货'} |
| brent_last_close | intl_brent | `2026-02-03T06:00:00+08:00` | 53940 | {'quote_date': '2026-02-02', 'value': 67.72} |

## 20. ad2604 20260210 night （contaminated_audit）

- Episode：`ad:20260210`
- 决策时点：`2026-02-09T20:59:00+08:00`
- 执行时点：`2026-02-09T21:01:00+08:00`
- label 窗口：`2026-02-09T21:01:00+08:00` → `2026-02-10T01:00:00+08:00`
- 目标值：0.0033802849 = ln(22225 / 22150)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-09T15:00:00+08:00` | 21540 | {'bar_start': '2026-02-09T14:59:00+08:00', 'close': 22165.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-09T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260209, 'close': 22165.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-09T20:56:46+08:00` | 134 | {'title': '', 'labels': '欧洲央行动态'} |
| brent_last_close | intl_brent | `2026-02-07T06:00:00+08:00` | 226740 | {'quote_date': '2026-02-06', 'value': 70.45} |

## 21. ad2604 20260305 day （contaminated_audit）

- Episode：`ad:20260305`
- 决策时点：`2026-03-05T08:59:00+08:00`
- 执行时点：`2026-03-05T09:01:00+08:00`
- label 窗口：`2026-03-05T09:01:00+08:00` → `2026-03-05T15:00:00+08:00`
- 目标值：-0.013571031 = ln(23420 / 23740)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-05T01:00:00+08:00` | 28740 | {'bar_start': '2026-03-05T00:59:00+08:00', 'close': 23670.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-03-04T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260304, 'close': 23400.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-05T08:53:55+08:00` | 305 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-03-05T06:00:00+08:00` | 10740 | {'quote_date': '2026-03-04', 'value': 81.56} |

## 22. ad2604 20260316 day （contaminated_audit）

- Episode：`ad:20260316`
- 决策时点：`2026-03-16T08:59:00+08:00`
- 执行时点：`2026-03-16T09:01:00+08:00`
- label 窗口：`2026-03-16T09:01:00+08:00` → `2026-03-16T15:00:00+08:00`
- 目标值：-0.00041955109 = ln(23830 / 23840)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-14T01:00:00+08:00` | 201540 | {'bar_start': '2026-03-14T00:59:00+08:00', 'close': 23635.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-03-13T15:00:00.500000+08:00` | 237539 | {'trading_day': 20260313, 'close': 23655.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-16T08:58:48+08:00` | 12 | {'title': '【俄称受中东局势影响 乌克兰问题谈判暂停】', 'labels': '俄乌冲突快报'} |
| brent_last_close | intl_brent | `2026-03-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-03-13', 'value': 103.23} |

## 23. ad2605 20260331 day （contaminated_audit）

- Episode：`ad:20260331`
- 决策时点：`2026-03-31T08:59:00+08:00`
- 执行时点：`2026-03-31T09:01:00+08:00`
- label 窗口：`2026-03-31T09:01:00+08:00` → `2026-03-31T15:00:00+08:00`
- 目标值：0.0046531387 = ln(23695 / 23585)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-31T01:00:00+08:00` | 28740 | {'bar_start': '2026-03-31T00:59:00+08:00', 'close': 23585.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-03-30T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260330, 'close': 23630.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-31T08:56:56+08:00` | 124 | {'title': '【特朗普称即使霍尔木兹海峡仍关闭也愿结束战争】', 'labels': '中东冲突 航运期货 环球市场情报 期货市场情报 原油市场动态'} |
| brent_last_close | intl_brent | `2026-03-31T06:00:00+08:00` | 10740 | {'quote_date': '2026-03-30', 'value': 121.88} |

## 24. ad2606 20260417 day （contaminated_audit）

- Episode：`ad:20260417`
- 决策时点：`2026-04-17T08:59:00+08:00`
- 执行时点：`2026-04-17T09:01:00+08:00`
- label 窗口：`2026-04-17T09:01:00+08:00` → `2026-04-17T15:00:00+08:00`
- 目标值：-0.0055999317 = ln(24040 / 24175)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-17T01:00:00+08:00` | 28740 | {'bar_start': '2026-04-17T00:59:00+08:00', 'close': 24155.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-04-16T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260416, 'close': 24145.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T08:48:12+08:00` | 648 | {'title': '【两市融资余额增加107.35亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 25. ad2608 20260602 night （contaminated_audit）

- Episode：`ad:20260602`
- 决策时点：`2026-06-01T20:59:00+08:00`
- 执行时点：`2026-06-01T21:01:00+08:00`
- label 窗口：`2026-06-01T21:01:00+08:00` → `2026-06-02T01:00:00+08:00`
- 目标值：0 = ln(23145 / 23145)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-01T14:59:00+08:00', 'close': 23060.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260601, 'close': 23060.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-01T20:55:39+08:00` | 201 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-05-30T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-29', 'value': 92.88} |

## 26. ad2608 20260626 day （contaminated_audit）

- Episode：`ad:20260626`
- 决策时点：`2026-06-26T08:59:00+08:00`
- 执行时点：`2026-06-26T09:01:00+08:00`
- label 窗口：`2026-06-26T09:01:00+08:00` → `2026-06-26T15:00:00+08:00`
- 目标值：-0.00044179369 = ln(22630 / 22640)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T01:00:00+08:00` | 28740 | {'bar_start': '2026-06-26T00:59:00+08:00', 'close': 22580.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-25T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260625, 'close': 22585.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 706540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-26T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-25', 'value': 73.74} |

## 27. ad2609 20260702 night （contaminated_audit）

- Episode：`ad:20260702`
- 决策时点：`2026-07-01T20:59:00+08:00`
- 执行时点：`2026-07-01T21:01:00+08:00`
- label 窗口：`2026-07-01T21:01:00+08:00` → `2026-07-02T01:00:00+08:00`
- 目标值：-0.0013327412 = ln(22495 / 22525)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-01T14:59:00+08:00', 'close': 22270.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260701, 'close': 22270.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1181740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 28. ad2609 20260716 night （contaminated_audit）

- Episode：`ad:20260716`
- 决策时点：`2026-07-15T20:59:00+08:00`
- 执行时点：`2026-07-15T21:01:00+08:00`
- label 窗口：`2026-07-15T21:01:00+08:00` → `2026-07-16T01:00:00+08:00`
- 目标值：-0.0023983441 = ln(22905 / 22960)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-15T14:59:00+08:00', 'close': 22970.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260715, 'close': 22970.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2391340 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 140340 | {'quote_date': '2026-07-13', 'value': 81.62} |

## 29. ad2609 20260720 night （contaminated_audit）

- Episode：`ad:20260720`
- 决策时点：`2026-07-17T20:59:00+08:00`
- 执行时点：`2026-07-17T21:01:00+08:00`
- label 窗口：`2026-07-17T21:01:00+08:00` → `2026-07-18T01:00:00+08:00`
- 目标值：0.008449839 = ln(23175 / 22980)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-07-17T14:59:00+08:00', 'close': 23025.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260717, 'close': 23025.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2564140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 313140 | {'quote_date': '2026-07-13', 'value': 81.62} |
