# SC Temporal Spine 人工回放清单（bb_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`5b2f712849e6e36a79498ff9305d781ef73b8c3c8574e62d175f95514375510f`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. bb2504 20240524 day （discovery）

- Episode：`bb:20240524`
- 决策时点：`2024-05-24T08:59:00+08:00`
- 执行时点：`2024-05-24T09:01:00+08:00`
- label 窗口：`2024-05-24T09:01:00+08:00` → `2024-05-24T15:00:00+08:00`
- 目标值：NULL（no-trade：no_entry_price）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-05-23T15:00:00+08:00` | 64740 | {'bar_start': '2024-05-23T14:59:00+08:00', 'close': 190.65, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-05-23T15:00:00.048000+08:00` | 64739 | {'trading_day': 20240523, 'close': 190.65} |
| cls_last_telegraph | cls_telegraph | `2024-05-24T08:58:37+08:00` | 23 | {'title': '【中国海油子公司与莫桑比克能矿部等签署石油特许合同】', 'labels': ''} |
| brent_last_close | intl_brent | `2024-05-24T06:00:00+08:00` | 10740 | {'quote_date': '2024-05-23', 'value': 79.25} |

## 01. bb2504 20240618 day （discovery）

- Episode：`bb:20240618`
- 决策时点：`2024-06-18T08:59:00+08:00`
- 执行时点：`2024-06-18T09:01:00+08:00`
- label 窗口：`2024-06-18T09:01:00+08:00` → `2024-06-18T15:00:00+08:00`
- 目标值：-0.048790164 = ln(175 / 183.75)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-06-17T15:00:00+08:00` | 64740 | {'bar_start': '2024-06-17T14:59:00+08:00', 'close': 186.75, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-06-17T15:00:00+08:00` | 64740 | {'trading_day': 20240617, 'close': 186.75} |
| cls_last_telegraph | cls_telegraph | `2024-06-18T08:58:38+08:00` | 22 | {'title': '【国资委：强化企业创新主体地位 加大基础研究投入力度】', 'labels': 'TMT行业观察 国企改革'} |
| brent_last_close | intl_brent | `2024-06-18T06:00:00+08:00` | 10740 | {'quote_date': '2024-06-17', 'value': 82.45} |

## 02. bb2504 20240701 day （discovery）

- Episode：`bb:20240701`
- 决策时点：`2024-07-01T08:59:00+08:00`
- 执行时点：`2024-07-01T09:01:00+08:00`
- label 窗口：`2024-07-01T09:01:00+08:00` → `2024-07-01T15:00:00+08:00`
- 目标值：-0.0086684148 = ln(166.55 / 168)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-06-28T14:57:00+08:00` | 237720 | {'bar_start': '2024-06-28T14:56:00+08:00', 'close': 168.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-06-28T15:00:00+08:00` | 237540 | {'trading_day': 20240628, 'close': 168.0} |
| cls_last_telegraph | cls_telegraph | `2024-07-01T08:52:59+08:00` | 361 | {'title': '【两市融资余额减少62.14亿】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2024-06-29T06:00:00+08:00` | 183540 | {'quote_date': '2024-06-28', 'value': 87.26} |

## 03. bb2504 20240703 day （discovery）

- Episode：`bb:20240703`
- 决策时点：`2024-07-03T08:59:00+08:00`
- 执行时点：`2024-07-03T09:01:00+08:00`
- label 窗口：`2024-07-03T09:01:00+08:00` → `2024-07-03T15:00:00+08:00`
- 目标值：0.01121054 = ln(165.95 / 164.1)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-07-02T15:00:00+08:00` | 64740 | {'bar_start': '2024-07-02T14:59:00+08:00', 'close': 164.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-07-02T15:00:00.022000+08:00` | 64739 | {'trading_day': 20240702, 'close': 164.1} |
| cls_last_telegraph | cls_telegraph | `2024-07-03T08:58:45+08:00` | 15 | {'title': '【三星在第9代V-NAND金属化工艺中应用钼】', 'labels': '化工 有色·钼 半导体芯片'} |
| brent_last_close | intl_brent | `2024-07-03T06:00:00+08:00` | 10740 | {'quote_date': '2024-07-02', 'value': 88.28} |

## 04. bb2504 20240814 day （discovery）

- Episode：`bb:20240814`
- 决策时点：`2024-08-14T08:59:00+08:00`
- 执行时点：`2024-08-14T09:01:00+08:00`
- label 窗口：`2024-08-14T09:01:00+08:00` → `2024-08-14T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-08-13T15:00:00+08:00` | 64740 | {'bar_start': '2024-08-13T14:59:00+08:00', 'close': 161.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-08-13T15:00:00.035000+08:00` | 64739 | {'trading_day': 20240813, 'close': 161.0} |
| cls_last_telegraph | cls_telegraph | `2024-08-14T08:57:45+08:00` | 75 | {'title': '【美国汽车工人联合会因反罢工言论对特朗普和马斯克提出指控】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-08-14T06:00:00+08:00` | 10740 | {'quote_date': '2024-08-13', 'value': 82.51} |

## 05. bb2504 20241106 day （discovery）

- Episode：`bb:20241106`
- 决策时点：`2024-11-06T08:59:00+08:00`
- 执行时点：`2024-11-06T09:01:00+08:00`
- label 窗口：`2024-11-06T09:01:00+08:00` → `2024-11-06T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-11-05T14:37:00+08:00` | 66120 | {'bar_start': '2024-11-05T14:36:00+08:00', 'close': 175.15, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-11-05T15:00:00+08:00` | 64740 | {'trading_day': 20241105, 'close': 175.15} |
| cls_last_telegraph | cls_telegraph | `2024-11-06T08:57:49+08:00` | 71 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2024-11-06T06:00:00+08:00` | 10740 | {'quote_date': '2024-11-05', 'value': 76.98} |

## 06. bb2504 20241107 day （discovery）

- Episode：`bb:20241107`
- 决策时点：`2024-11-07T08:59:00+08:00`
- 执行时点：`2024-11-07T09:01:00+08:00`
- label 窗口：`2024-11-07T09:01:00+08:00` → `2024-11-07T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-11-06T14:30:00+08:00` | 66540 | {'bar_start': '2024-11-06T14:29:00+08:00', 'close': 168.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-11-06T15:00:00+08:00` | 64740 | {'trading_day': 20241106, 'close': 168.5} |
| cls_last_telegraph | cls_telegraph | `2024-11-07T08:49:24+08:00` | 576 | {'title': '【两市融资余额增加224.77亿元】', 'labels': '期货市场情报 融资融券 沪深交易所动态'} |
| brent_last_close | intl_brent | `2024-11-07T06:00:00+08:00` | 10740 | {'quote_date': '2024-11-06', 'value': 76.52} |

## 07. bb2504 20241129 day （discovery）

- Episode：`bb:20241129`
- 决策时点：`2024-11-29T08:59:00+08:00`
- 执行时点：`2024-11-29T09:01:00+08:00`
- label 窗口：`2024-11-29T09:01:00+08:00` → `2024-11-29T15:00:00+08:00`
- 目标值：NULL（no-trade：no_entry_price）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-11-28T15:00:00+08:00` | 64740 | {'bar_start': '2024-11-28T14:59:00+08:00', 'close': 151.15, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-11-28T15:00:00+08:00` | 64740 | {'trading_day': 20241128, 'close': 151.15} |
| cls_last_telegraph | cls_telegraph | `2024-11-29T08:57:19+08:00` | 101 | {'title': '【深交所将召开深市交易结算技术运行和协同工作碰头会】', 'labels': '沪深交易所动态'} |
| brent_last_close | intl_brent | `2024-11-29T06:00:00+08:00` | 10740 | {'quote_date': '2024-11-28', 'value': 73.92} |

## 08. bb2504 20241211 day （discovery）

- Episode：`bb:20241211`
- 决策时点：`2024-12-11T08:59:00+08:00`
- 执行时点：`2024-12-11T09:01:00+08:00`
- label 窗口：`2024-12-11T09:01:00+08:00` → `2024-12-11T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-10T15:00:00+08:00` | 64740 | {'bar_start': '2024-12-10T14:59:00+08:00', 'close': 158.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-10T15:00:00+08:00` | 64740 | {'trading_day': 20241210, 'close': 158.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-11T08:57:18+08:00` | 102 | {'title': '', 'labels': '期货市场情报 原油市场动态'} |
| brent_last_close | intl_brent | `2024-12-11T06:00:00+08:00` | 10740 | {'quote_date': '2024-12-10', 'value': 73.64} |

## 09. bb2504 20241223 day （discovery）

- Episode：`bb:20241223`
- 决策时点：`2024-12-23T08:59:00+08:00`
- 执行时点：`2024-12-23T09:01:00+08:00`
- label 窗口：`2024-12-23T09:01:00+08:00` → `2024-12-23T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2024-12-20T14:06:00+08:00` | 240780 | {'bar_start': '2024-12-20T14:05:00+08:00', 'close': 158.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2024-12-20T15:00:00+08:00` | 237540 | {'trading_day': 20241220, 'close': 158.5} |
| cls_last_telegraph | cls_telegraph | `2024-12-23T08:55:29+08:00` | 211 | {'title': '【中国人寿105亿入股鞍钢集团下属企业】', 'labels': '钢铁'} |
| brent_last_close | intl_brent | `2024-12-21T06:00:00+08:00` | 183540 | {'quote_date': '2024-12-20', 'value': 73.19} |

## 10. bb2504 20250110 day （historical_validation）

- Episode：`bb:20250110`
- 决策时点：`2025-01-10T08:59:00+08:00`
- 执行时点：`2025-01-10T09:01:00+08:00`
- label 窗口：`2025-01-10T09:01:00+08:00` → `2025-01-10T15:00:00+08:00`
- 目标值：-0.020699316 = ln(153 / 156.2)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-09T15:00:00+08:00` | 64740 | {'bar_start': '2025-01-09T14:59:00+08:00', 'close': 154.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-09T15:00:00+08:00` | 64740 | {'trading_day': 20250109, 'close': 154.1} |
| cls_last_telegraph | cls_telegraph | `2025-01-10T08:56:38+08:00` | 142 | {'title': '【预告】', 'labels': '提醒电报'} |
| brent_last_close | intl_brent | `2025-01-10T06:00:00+08:00` | 10740 | {'quote_date': '2025-01-09', 'value': 78.44} |

## 11. bb2504 20250121 day （historical_validation）

- Episode：`bb:20250121`
- 决策时点：`2025-01-21T08:59:00+08:00`
- 执行时点：`2025-01-21T09:01:00+08:00`
- label 窗口：`2025-01-21T09:01:00+08:00` → `2025-01-21T15:00:00+08:00`
- 目标值：0.040315537 = ln(164.5 / 158)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-01-20T15:00:00+08:00` | 64740 | {'bar_start': '2025-01-20T14:59:00+08:00', 'close': 158.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-01-20T15:00:00.045000+08:00` | 64739 | {'trading_day': 20250120, 'close': 158.0} |
| cls_last_telegraph | cls_telegraph | `2025-01-21T08:53:50+08:00` | 310 | {'title': '【特朗普：考虑在2月1日对加拿大和墨西哥采取25%的关税措施】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-01-21T06:00:00+08:00` | 10740 | {'quote_date': '2025-01-20', 'value': 81.68} |

## 12. bb2601 20250311 day （historical_validation）

- Episode：`bb:20250311`
- 决策时点：`2025-03-11T08:59:00+08:00`
- 执行时点：`2025-03-11T09:01:00+08:00`
- label 窗口：`2025-03-11T09:01:00+08:00` → `2025-03-11T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_daily_close | commodity_tick | `2025-03-10T15:00:00+08:00` | 64740 | {'trading_day': 20250310, 'close': None} |
| cls_last_telegraph | cls_telegraph | `2025-03-11T08:57:10+08:00` | 110 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-03-11T06:00:00+08:00` | 10740 | {'quote_date': '2025-03-10', 'value': 71.08} |

> 该决策时点之前无可用观测的来源：commodity_tick

## 13. bb2601 20250613 day （historical_validation）

- Episode：`bb:20250613`
- 决策时点：`2025-06-13T08:59:00+08:00`
- 执行时点：`2025-06-13T09:01:00+08:00`
- label 窗口：`2025-06-13T09:01:00+08:00` → `2025-06-13T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-06-12T09:22:00+08:00` | 85020 | {'bar_start': '2025-06-12T09:21:00+08:00', 'close': 164.95, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-06-12T15:00:00+08:00` | 64740 | {'trading_day': 20250612, 'close': 164.95} |
| cls_last_telegraph | cls_telegraph | `2025-06-13T08:58:56+08:00` | 4 | {'title': '【美国称不参与以色列对伊朗的打击】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-06-13T06:00:00+08:00` | 10740 | {'quote_date': '2025-06-12', 'value': 70.84} |

## 14. bb2601 20250812 day （historical_validation）

- Episode：`bb:20250812`
- 决策时点：`2025-08-12T08:59:00+08:00`
- 执行时点：`2025-08-12T09:01:00+08:00`
- label 窗口：`2025-08-12T09:01:00+08:00` → `2025-08-12T15:00:00+08:00`
- 目标值：0.00067453628 = ln(148.3 / 148.2)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-11T14:59:00+08:00', 'close': 148.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-11T15:00:00.004000+08:00` | 64739 | {'trading_day': 20250811, 'close': 148.2} |
| cls_last_telegraph | cls_telegraph | `2025-08-12T08:52:43+08:00` | 377 | {'title': '【德国7月破产企业数量同比大幅增加】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-08-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-11', 'value': 67.36} |

## 15. bb2601 20250829 day （historical_validation）

- Episode：`bb:20250829`
- 决策时点：`2025-08-29T08:59:00+08:00`
- 执行时点：`2025-08-29T09:01:00+08:00`
- label 窗口：`2025-08-29T09:01:00+08:00` → `2025-08-29T15:00:00+08:00`
- 目标值：0.0027201649 = ln(147.25 / 146.85)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-08-28T15:00:00+08:00` | 64740 | {'bar_start': '2025-08-28T14:59:00+08:00', 'close': 146.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-08-28T15:00:00.047000+08:00` | 64739 | {'trading_day': 20250828, 'close': 146.85} |
| cls_last_telegraph | cls_telegraph | `2025-08-29T08:49:10+08:00` | 590 | {'title': '【两市融资余额增加161.76亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-08-29T06:00:00+08:00` | 10740 | {'quote_date': '2025-08-28', 'value': 68.61} |

## 16. bb2601 20250905 day （historical_validation）

- Episode：`bb:20250905`
- 决策时点：`2025-09-05T08:59:00+08:00`
- 执行时点：`2025-09-05T09:01:00+08:00`
- label 窗口：`2025-09-05T09:01:00+08:00` → `2025-09-05T15:00:00+08:00`
- 目标值：0.0027322421 = ln(146.6 / 146.2)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-04T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-04T14:59:00+08:00', 'close': 146.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-04T15:00:00.050000+08:00` | 64739 | {'trading_day': 20250904, 'close': 146.2} |
| cls_last_telegraph | cls_telegraph | `2025-09-05T08:51:10+08:00` | 470 | {'title': '【财政部安排救灾资金9.4亿元 支持北京、甘肃等地积极应对洪涝灾害】', 'labels': '水利'} |
| brent_last_close | intl_brent | `2025-09-05T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-04', 'value': 66.41} |

## 17. bb2603 20250918 day （historical_validation）

- Episode：`bb:20250918`
- 决策时点：`2025-09-18T08:59:00+08:00`
- 执行时点：`2025-09-18T09:01:00+08:00`
- label 窗口：`2025-09-18T09:01:00+08:00` → `2025-09-18T15:00:00+08:00`
- 目标值：NULL（no-trade：no_entry_price）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-17T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-17T14:59:00+08:00', 'close': 146.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-17T15:00:00+08:00` | 64740 | {'trading_day': 20250917, 'close': 146.85} |
| cls_last_telegraph | cls_telegraph | `2025-09-18T08:48:12+08:00` | 648 | {'title': '【两市融资余额增加126.46亿元】', 'labels': '融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-09-18T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-17', 'value': 69.19} |

## 18. bb2603 20250930 day （historical_validation）

- Episode：`bb:20250930`
- 决策时点：`2025-09-30T08:59:00+08:00`
- 执行时点：`2025-09-30T09:01:00+08:00`
- label 窗口：`2025-09-30T09:01:00+08:00` → `2025-09-30T15:00:00+08:00`
- 目标值：0.0040830271 = ln(147.25 / 146.65)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-29T15:00:00+08:00` | 64740 | {'bar_start': '2025-09-29T14:59:00+08:00', 'close': 146.65, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-09-29T15:00:00.043000+08:00` | 64739 | {'trading_day': 20250929, 'close': 146.65} |
| cls_last_telegraph | cls_telegraph | `2025-09-30T08:58:52+08:00` | 8 | {'title': '【上海发布雷电黄色、大风蓝色预警信号】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-09-30T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-29', 'value': 69.0} |

## 19. bb2605 20251112 day （historical_validation）

- Episode：`bb:20251112`
- 决策时点：`2025-11-12T08:59:00+08:00`
- 执行时点：`2025-11-12T09:01:00+08:00`
- label 窗口：`2025-11-12T09:01:00+08:00` → `2025-11-12T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-11T15:00:00+08:00` | 64740 | {'bar_start': '2025-11-11T14:59:00+08:00', 'close': 146.6, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-11T15:00:00.041000+08:00` | 64739 | {'trading_day': 20251111, 'close': 146.6} |
| cls_last_telegraph | cls_telegraph | `2025-11-12T08:58:56+08:00` | 4 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-11-12T06:00:00+08:00` | 10740 | {'quote_date': '2025-11-11', 'value': 63.86} |

## 20. bb2605 20251210 day （historical_validation）

- Episode：`bb:20251210`
- 决策时点：`2025-12-10T08:59:00+08:00`
- 执行时点：`2025-12-10T09:01:00+08:00`
- label 窗口：`2025-12-10T09:01:00+08:00` → `2025-12-10T15:00:00+08:00`
- 目标值：0.0003411223 = ln(146.6 / 146.55)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-09T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-09T14:59:00+08:00', 'close': 146.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-09T15:00:00.049000+08:00` | 64739 | {'trading_day': 20251209, 'close': 146.55} |
| cls_last_telegraph | cls_telegraph | `2025-12-10T08:51:16+08:00` | 464 | {'title': '【三星SDI子公司与美国客户签署13.6亿美元磷酸铁锂电池协议】', 'labels': '盐湖提锂 锂电池 磷酸铁锂'} |
| brent_last_close | intl_brent | `2025-12-10T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-09', 'value': 62.62} |

## 21. bb2607 20251223 day （historical_validation）

- Episode：`bb:20251223`
- 决策时点：`2025-12-23T08:59:00+08:00`
- 执行时点：`2025-12-23T09:01:00+08:00`
- label 窗口：`2025-12-23T09:01:00+08:00` → `2025-12-23T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-22T09:01:00+08:00` | 86280 | {'bar_start': '2025-12-22T09:00:00+08:00', 'close': 146.25, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-22T15:00:00+08:00` | 64740 | {'trading_day': 20251222, 'close': 146.25} |
| cls_last_telegraph | cls_telegraph | `2025-12-23T08:48:26+08:00` | 634 | {'title': '【两市融资余额增加125.34亿元】', 'labels': '期货市场情报 融资融券 盘面直播'} |
| brent_last_close | intl_brent | `2025-12-23T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-22', 'value': 62.22} |

## 22. bb2701 20260408 day （contaminated_audit）

- Episode：`bb:20260408`
- 决策时点：`2026-04-08T08:59:00+08:00`
- 执行时点：`2026-04-08T09:01:00+08:00`
- label 窗口：`2026-04-08T09:01:00+08:00` → `2026-04-08T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-07T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-07T14:59:00+08:00', 'close': 148.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-07T15:00:00+08:00` | 64740 | {'trading_day': 20260407, 'close': 148.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-08T08:56:04+08:00` | 176 | {'title': '', 'labels': '环球市场情报 美股动态'} |
| brent_last_close | intl_brent | `2026-04-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-07', 'value': 138.21} |

## 23. bb2701 20260423 day （contaminated_audit）

- Episode：`bb:20260423`
- 决策时点：`2026-04-23T08:59:00+08:00`
- 执行时点：`2026-04-23T09:01:00+08:00`
- label 窗口：`2026-04-23T09:01:00+08:00` → `2026-04-23T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-22T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-22T14:59:00+08:00', 'close': 147.75, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-22T15:00:00+08:00` | 64740 | {'trading_day': 20260422, 'close': 147.75} |
| cls_last_telegraph | cls_telegraph | `2026-04-23T08:56:00+08:00` | 180 | {'title': '【乐普医疗：介入型多通道脑机接口产品已完成动物实验 进入人体ITT临床研究阶段】', 'labels': '医疗器械'} |
| brent_last_close | intl_brent | `2026-04-23T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-22', 'value': 113.44} |

## 24. bb2701 20260428 day （contaminated_audit）

- Episode：`bb:20260428`
- 决策时点：`2026-04-28T08:59:00+08:00`
- 执行时点：`2026-04-28T09:01:00+08:00`
- label 窗口：`2026-04-28T09:01:00+08:00` → `2026-04-28T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-27T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-27T14:59:00+08:00', 'close': 147.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-27T15:00:00+08:00` | 64740 | {'trading_day': 20260427, 'close': 147.85} |
| cls_last_telegraph | cls_telegraph | `2026-04-28T08:57:47+08:00` | 73 | {'title': '【宁德时代50亿美元股票配售据悉获得超过150名投资者认购】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-04-28T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-27', 'value': 113.89} |

## 25. bb2701 20260506 day （contaminated_audit）

- Episode：`bb:20260506`
- 决策时点：`2026-05-06T08:59:00+08:00`
- 执行时点：`2026-05-06T09:01:00+08:00`
- label 窗口：`2026-05-06T09:01:00+08:00` → `2026-05-06T15:00:00+08:00`
- 目标值：NULL（no-trade：no_entry_price）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-30T15:00:00+08:00` | 496740 | {'bar_start': '2026-04-30T14:59:00+08:00', 'close': 147.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-30T15:00:00+08:00` | 496740 | {'trading_day': 20260430, 'close': 147.85} |
| cls_last_telegraph | cls_telegraph | `2026-05-06T08:58:08+08:00` | 52 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-05-06T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-05', 'value': 114.51} |

## 26. bb2705 20260623 day （contaminated_audit）

- Episode：`bb:20260623`
- 决策时点：`2026-06-23T08:59:00+08:00`
- 执行时点：`2026-06-23T09:01:00+08:00`
- label 窗口：`2026-06-23T09:01:00+08:00` → `2026-06-23T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_daily_close | commodity_tick | `2026-06-22T15:00:00+08:00` | 64740 | {'trading_day': 20260622, 'close': None} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 447340 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-23T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-22', 'value': 76.49} |

> 该决策时点之前无可用观测的来源：commodity_tick

## 27. bb2705 20260629 day （contaminated_audit）

- Episode：`bb:20260629`
- 决策时点：`2026-06-29T08:59:00+08:00`
- 执行时点：`2026-06-29T09:01:00+08:00`
- label 窗口：`2026-06-29T09:01:00+08:00` → `2026-06-29T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00+08:00` | 237540 | {'trading_day': 20260626, 'close': None} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 965740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-27T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-26', 'value': 70.16} |

> 该决策时点之前无可用观测的来源：commodity_tick

## 28. bb2705 20260706 day （contaminated_audit）

- Episode：`bb:20260706`
- 决策时点：`2026-07-06T08:59:00+08:00`
- 执行时点：`2026-07-06T09:01:00+08:00`
- label 窗口：`2026-07-06T09:01:00+08:00` → `2026-07-06T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-03T14:53:00+08:00` | 237960 | {'bar_start': '2026-07-03T14:52:00+08:00', 'close': 147.65, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-03T15:00:00+08:00` | 237540 | {'trading_day': 20260703, 'close': 147.65} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1570540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-04T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-03', 'value': 68.68} |

## 29. bb2705 20260723 day （contaminated_audit）

- Episode：`bb:20260723`
- 决策时点：`2026-07-23T08:59:00+08:00`
- 执行时点：`2026-07-23T09:01:00+08:00`
- label 窗口：`2026-07-23T09:01:00+08:00` → `2026-07-23T15:00:00+08:00`
- 目标值：NULL（no-trade：zero_volume）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-22T09:32:00+08:00` | 84420 | {'bar_start': '2026-07-22T09:31:00+08:00', 'close': 147.4, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-22T15:00:00+08:00` | 64740 | {'trading_day': 20260722, 'close': 147.4} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 3039340 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 788340 | {'quote_date': '2026-07-13', 'value': 81.62} |
