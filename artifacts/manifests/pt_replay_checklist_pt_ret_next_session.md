# SC Temporal Spine 人工回放清单（pt_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`511c707cc8d11fdf6ce52dd896e6133b45d4f424cb8906433fde0e3bc4ac677e`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. pt2606 20251204 day （historical_validation）

- Episode：`pt:20251204`
- 决策时点：`2025-12-04T08:59:00+08:00`
- 执行时点：`2025-12-04T09:01:00+08:00`
- label 窗口：`2025-12-04T09:01:00+08:00` → `2025-12-04T15:00:00+08:00`
- 目标值：-0.0086061 = ln(439.65 / 443.45)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-03T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-03T14:59:00+08:00', 'close': 440.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-03T15:00:00.015000+08:00` | 64739 | {'trading_day': 20251203, 'close': 440.55} |
| cls_last_telegraph | cls_telegraph | `2025-12-04T08:53:35+08:00` | 325 | {'title': '【日本称干扰他国卫星技术取得进展】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-04T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-03', 'value': 63.75} |

## 01. pt2606 20251205 day （historical_validation）

- Episode：`pt:20251205`
- 决策时点：`2025-12-05T08:59:00+08:00`
- 执行时点：`2025-12-05T09:01:00+08:00`
- label 窗口：`2025-12-05T09:01:00+08:00` → `2025-12-05T15:00:00+08:00`
- 目标值：0.0090847774 = ln(442.3 / 438.3)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-04T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-04T14:59:00+08:00', 'close': 439.65, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-04T15:00:00.012000+08:00` | 64739 | {'trading_day': 20251204, 'close': 439.65} |
| cls_last_telegraph | cls_telegraph | `2025-12-05T08:49:31+08:00` | 569 | {'title': '', 'labels': '医疗器械 脑科学 人脑工程'} |
| brent_last_close | intl_brent | `2025-12-05T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-04', 'value': 64.15} |

## 02. pt2606 20251222 day （historical_validation）

- Episode：`pt:20251222`
- 决策时点：`2025-12-22T08:59:00+08:00`
- 执行时点：`2025-12-22T09:01:00+08:00`
- label 窗口：`2025-12-22T09:01:00+08:00` → `2025-12-22T15:00:00+08:00`
- 目标值：NULL（no-trade：exit_at_price_limit）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-19T15:00:00+08:00` | 237540 | {'bar_start': '2025-12-19T14:59:00+08:00', 'close': 533.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-19T15:00:00.023000+08:00` | 237539 | {'trading_day': 20251219, 'close': 533.55} |
| cls_last_telegraph | cls_telegraph | `2025-12-22T08:53:42+08:00` | 318 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-20T06:00:00+08:00` | 183540 | {'quote_date': '2025-12-19', 'value': 61.35} |

## 03. pt2606 20251231 day （historical_validation）

- Episode：`pt:20251231`
- 决策时点：`2025-12-31T08:59:00+08:00`
- 执行时点：`2025-12-31T09:01:00+08:00`
- label 窗口：`2025-12-31T09:01:00+08:00` → `2025-12-31T15:00:00+08:00`
- 目标值：-0.067290776 = ln(527.25 / 563.95)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-30T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-30T14:59:00+08:00', 'close': 589.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-30T15:00:00.021000+08:00` | 64739 | {'trading_day': 20251230, 'close': 589.85} |
| cls_last_telegraph | cls_telegraph | `2025-12-31T08:56:59+08:00` | 121 | {'title': '【雷军：跨年直播推迟到1月3日晚7点】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-30', 'value': 62.3} |

## 04. pt2606 20260108 day （contaminated_audit）

- Episode：`pt:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.023376795 = ln(575 / 588.6)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-07T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-07T14:59:00+08:00', 'close': 598.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.115000+08:00` | 64739 | {'trading_day': 20260107, 'close': 598.5} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 05. pt2606 20260113 day （contaminated_audit）

- Episode：`pt:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：-0.0065071685 = ln(605.05 / 609)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-12T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-12T14:59:00+08:00', 'close': 622.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.005000+08:00` | 64739 | {'trading_day': 20260112, 'close': 622.8} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 06. pt2606 20260120 day （contaminated_audit）

- Episode：`pt:20260120`
- 决策时点：`2026-01-20T08:59:00+08:00`
- 执行时点：`2026-01-20T09:01:00+08:00`
- label 窗口：`2026-01-20T09:01:00+08:00` → `2026-01-20T15:00:00+08:00`
- 目标值：0.00080762401 = ln(619.35 / 618.85)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-19T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-19T14:59:00+08:00', 'close': 615.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-19T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260119, 'close': 615.1} |
| cls_last_telegraph | cls_telegraph | `2026-01-20T08:58:24+08:00` | 36 | {'title': '', 'labels': '期货市场情报 天然气 能源类期货'} |
| brent_last_close | intl_brent | `2026-01-20T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-19', 'value': 66.91} |

## 07. pt2606 20260122 day （contaminated_audit）

- Episode：`pt:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.038189455 = ln(633.85 / 610.1)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-21T14:59:00+08:00', 'close': 628.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.023000+08:00` | 64739 | {'trading_day': 20260121, 'close': 628.5} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 08. pt2606 20260128 day （contaminated_audit）

- Episode：`pt:20260128`
- 决策时点：`2026-01-28T08:59:00+08:00`
- 执行时点：`2026-01-28T09:01:00+08:00`
- label 窗口：`2026-01-28T09:01:00+08:00` → `2026-01-28T15:00:00+08:00`
- 目标值：-0.018890678 = ln(694.8 / 708.05)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-27T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-27T14:59:00+08:00', 'close': 705.7, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-27T15:00:00.004000+08:00` | 64739 | {'trading_day': 20260127, 'close': 705.7} |
| cls_last_telegraph | cls_telegraph | `2026-01-28T08:51:42+08:00` | 438 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-28T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-27', 'value': 70.28} |

## 09. pt2606 20260129 day （contaminated_audit）

- Episode：`pt:20260129`
- 决策时点：`2026-01-29T08:59:00+08:00`
- 执行时点：`2026-01-29T09:01:00+08:00`
- label 窗口：`2026-01-29T09:01:00+08:00` → `2026-01-29T15:00:00+08:00`
- 目标值：0.020871676 = ln(714.1 / 699.35)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-28T14:59:00+08:00', 'close': 694.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-28T15:00:00.127000+08:00` | 64739 | {'trading_day': 20260128, 'close': 694.8} |
| cls_last_telegraph | cls_telegraph | `2026-01-29T08:57:44+08:00` | 76 | {'title': '【家得宝在美裁员并要求员工每周五天到岗办公】', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-28', 'value': 70.9} |

## 10. pt2606 20260227 day （contaminated_audit）

- Episode：`pt:20260227`
- 决策时点：`2026-02-27T08:59:00+08:00`
- 执行时点：`2026-02-27T09:01:00+08:00`
- label 窗口：`2026-02-27T09:01:00+08:00` → `2026-02-27T15:00:00+08:00`
- 目标值：0.060128753 = ln(623.75 / 587.35)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-26T15:00:00+08:00` | 64740 | {'bar_start': '2026-02-26T14:59:00+08:00', 'close': 589.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-26T15:00:00.011000+08:00` | 64739 | {'trading_day': 20260226, 'close': 589.5} |
| cls_last_telegraph | cls_telegraph | `2026-02-27T08:56:26+08:00` | 154 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-02-27T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-26', 'value': 71.66} |

## 11. pt2606 20260316 day （contaminated_audit）

- Episode：`pt:20260316`
- 决策时点：`2026-03-16T08:59:00+08:00`
- 执行时点：`2026-03-16T09:01:00+08:00`
- label 窗口：`2026-03-16T09:01:00+08:00` → `2026-03-16T15:00:00+08:00`
- 目标值：-0.0048680119 = ln(532.8 / 535.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-13T15:00:00+08:00` | 237540 | {'bar_start': '2026-03-13T14:59:00+08:00', 'close': 541.6, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-13T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260313, 'close': 541.6} |
| cls_last_telegraph | cls_telegraph | `2026-03-16T08:58:48+08:00` | 12 | {'title': '【俄称受中东局势影响 乌克兰问题谈判暂停】', 'labels': '俄乌冲突快报'} |
| brent_last_close | intl_brent | `2026-03-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-03-13', 'value': 103.23} |

## 12. pt2606 20260403 day （contaminated_audit）

- Episode：`pt:20260403`
- 决策时点：`2026-04-03T08:59:00+08:00`
- 执行时点：`2026-04-03T09:01:00+08:00`
- label 窗口：`2026-04-03T09:01:00+08:00` → `2026-04-03T15:00:00+08:00`
- 目标值：0.01102547 = ln(501.6 / 496.1)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-02T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-02T14:59:00+08:00', 'close': 486.9, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-02T15:00:00.189000+08:00` | 64739 | {'trading_day': 20260402, 'close': 486.9} |
| cls_last_telegraph | cls_telegraph | `2026-04-03T08:54:49+08:00` | 251 | {'title': '【古巴政府宣布赦免超2000名囚犯】', 'labels': ''} |
| brent_last_close | intl_brent | `2026-04-03T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-02', 'value': 127.61} |

## 13. pt2606 20260413 day （contaminated_audit）

- Episode：`pt:20260413`
- 决策时点：`2026-04-13T08:59:00+08:00`
- 执行时点：`2026-04-13T09:01:00+08:00`
- label 窗口：`2026-04-13T09:01:00+08:00` → `2026-04-13T15:00:00+08:00`
- 目标值：0.0090068886 = ln(518.6 / 513.95)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-10T15:00:00+08:00` | 237540 | {'bar_start': '2026-04-10T14:59:00+08:00', 'close': 521.45, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-10T15:00:00.037000+08:00` | 237539 | {'trading_day': 20260410, 'close': 521.45} |
| cls_last_telegraph | cls_telegraph | `2026-04-13T08:57:03+08:00` | 117 | {'title': '【荣耀与字节跳动接洽“豆包手机”合作】', 'labels': 'TMT行业观察 人工智能'} |
| brent_last_close | intl_brent | `2026-04-11T06:00:00+08:00` | 183540 | {'quote_date': '2026-04-10', 'value': 119.07} |

## 14. pt2606 20260421 day （contaminated_audit）

- Episode：`pt:20260421`
- 决策时点：`2026-04-21T08:59:00+08:00`
- 执行时点：`2026-04-21T09:01:00+08:00`
- label 窗口：`2026-04-21T09:01:00+08:00` → `2026-04-21T15:00:00+08:00`
- 目标值：-0.0090446658 = ln(522.8 / 527.55)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-20T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-20T14:59:00+08:00', 'close': 525.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-20T15:00:00.016000+08:00` | 64739 | {'trading_day': 20260420, 'close': 525.55} |
| cls_last_telegraph | cls_telegraph | `2026-04-21T08:56:50+08:00` | 130 | {'title': '【报道称美国副总统万斯21日前往巴基斯坦】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-04-21T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-20', 'value': 103.4} |

## 15. pt2606 20260424 day （contaminated_audit）

- Episode：`pt:20260424`
- 决策时点：`2026-04-24T08:59:00+08:00`
- 执行时点：`2026-04-24T09:01:00+08:00`
- label 窗口：`2026-04-24T09:01:00+08:00` → `2026-04-24T15:00:00+08:00`
- 目标值：-0.022227547 = ln(498.3 / 509.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-23T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-23T14:59:00+08:00', 'close': 515.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-23T15:00:00.218000+08:00` | 64739 | {'trading_day': 20260423, 'close': 515.8} |
| cls_last_telegraph | cls_telegraph | `2026-04-24T08:55:03+08:00` | 237 | {'title': '【伊朗领导层齐斥特朗普“内斗”论：“我们都是伊朗人”“没有强硬派或温和派”】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-04-24T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-23', 'value': 113.25} |

## 16. pt2606 20260428 day （contaminated_audit）

- Episode：`pt:20260428`
- 决策时点：`2026-04-28T08:59:00+08:00`
- 执行时点：`2026-04-28T09:01:00+08:00`
- label 窗口：`2026-04-28T09:01:00+08:00` → `2026-04-28T15:00:00+08:00`
- 目标值：-0.020834087 = ln(494 / 504.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-27T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-27T14:59:00+08:00', 'close': 509.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-27T15:00:00.035000+08:00` | 64739 | {'trading_day': 20260427, 'close': 509.05} |
| cls_last_telegraph | cls_telegraph | `2026-04-28T08:57:47+08:00` | 73 | {'title': '【宁德时代50亿美元股票配售据悉获得超过150名投资者认购】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-04-28T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-27', 'value': 113.89} |

## 17. pt2606 20260429 day （contaminated_audit）

- Episode：`pt:20260429`
- 决策时点：`2026-04-29T08:59:00+08:00`
- 执行时点：`2026-04-29T09:01:00+08:00`
- label 窗口：`2026-04-29T09:01:00+08:00` → `2026-04-29T15:00:00+08:00`
- 目标值：-0.0071465337 = ln(488 / 491.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-28T14:59:00+08:00', 'close': 494.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-28T15:00:00.011000+08:00` | 64739 | {'trading_day': 20260428, 'close': 494.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-29T08:52:40+08:00` | 380 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2026-04-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-28', 'value': 117.62} |

## 18. pt2606 20260511 day （contaminated_audit）

- Episode：`pt:20260511`
- 决策时点：`2026-05-11T08:59:00+08:00`
- 执行时点：`2026-05-11T09:01:00+08:00`
- label 窗口：`2026-05-11T09:01:00+08:00` → `2026-05-11T15:00:00+08:00`
- 目标值：0.0080321717 = ln(512.5 / 508.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-08T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-08T14:59:00+08:00', 'close': 514.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-08T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260508, 'close': 514.05} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T08:57:06+08:00` | 114 | {'title': '【伊朗媒体公布伊朗回应美方要点】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 19. pt2606 20260518 day （contaminated_audit）

- Episode：`pt:20260518`
- 决策时点：`2026-05-18T08:59:00+08:00`
- 执行时点：`2026-05-18T09:01:00+08:00`
- label 窗口：`2026-05-18T09:01:00+08:00` → `2026-05-18T15:00:00+08:00`
- 目标值：0.0059081358 = ln(492.3 / 489.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-15T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-15T14:59:00+08:00', 'close': 499.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-15T15:00:00.154000+08:00` | 237539 | {'trading_day': 20260515, 'close': 499.05} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T08:57:46+08:00` | 74 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 20. pt2606 20260520 day （contaminated_audit）

- Episode：`pt:20260520`
- 决策时点：`2026-05-20T08:59:00+08:00`
- 执行时点：`2026-05-20T09:01:00+08:00`
- label 窗口：`2026-05-20T09:01:00+08:00` → `2026-05-20T15:00:00+08:00`
- 目标值：-0.0015562591 = ln(481.55 / 482.3)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-19T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-19T14:59:00+08:00', 'close': 492.45, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-19T15:00:00.019000+08:00` | 64739 | {'trading_day': 20260519, 'close': 492.45} |
| cls_last_telegraph | cls_telegraph | `2026-05-20T08:58:22+08:00` | 38 | {'title': '【江苏：实施提振消费专项行动 培育壮大智能穿戴设备、首发首店经济、AI流量消费等', 'labels': '人工智能 能源行业新闻 促消费举措 智能穿戴 新质生产力'} |
| brent_last_close | intl_brent | `2026-05-20T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-19', 'value': 114.64} |

## 21. pt2608 20260529 day （contaminated_audit）

- Episode：`pt:20260529`
- 决策时点：`2026-05-29T08:59:00+08:00`
- 执行时点：`2026-05-29T09:01:00+08:00`
- label 窗口：`2026-05-29T09:01:00+08:00` → `2026-05-29T15:00:00+08:00`
- 目标值：0.0016927638 = ln(473 / 472.2)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-28T14:59:00+08:00', 'close': 467.75, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-28T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260528, 'close': 467.75} |
| cls_last_telegraph | cls_telegraph | `2026-05-29T08:57:30+08:00` | 90 | {'title': '【江苏省政府召开智能机器人具身智能产业高质量发展专题推进会议】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2026-05-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-28', 'value': 95.47} |

## 22. pt2608 20260610 day （contaminated_audit）

- Episode：`pt:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：-0.0059773041 = ln(417 / 419.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-09T14:59:00+08:00', 'close': 436.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260609, 'close': 436.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 23. pt2608 20260611 day （contaminated_audit）

- Episode：`pt:20260611`
- 决策时点：`2026-06-11T08:59:00+08:00`
- 执行时点：`2026-06-11T09:01:00+08:00`
- label 窗口：`2026-06-11T09:01:00+08:00` → `2026-06-11T15:00:00+08:00`
- 目标值：0.010345335 = ln(417.8 / 413.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-10T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-10T14:59:00+08:00', 'close': 417.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-10T15:00:00.074000+08:00` | 64739 | {'trading_day': 20260610, 'close': 417.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-11T08:48:20+08:00` | 640 | {'title': '【两市融资余额减少80.91亿元】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2026-06-11T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-10', 'value': 95.73} |

## 24. pt2608 20260622 day （contaminated_audit）

- Episode：`pt:20260622`
- 决策时点：`2026-06-22T08:59:00+08:00`
- 执行时点：`2026-06-22T09:01:00+08:00`
- label 窗口：`2026-06-22T09:01:00+08:00` → `2026-06-22T15:00:00+08:00`
- 目标值：-0.0047562515 = ln(419.5 / 421.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-18T15:00:00+08:00` | 323940 | {'bar_start': '2026-06-18T14:59:00+08:00', 'close': 431.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-18T15:00:00.015000+08:00` | 323939 | {'trading_day': 20260618, 'close': 431.2} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 360940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-20T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-19', 'value': 80.46} |

## 25. pt2608 20260629 day （contaminated_audit）

- Episode：`pt:20260629`
- 决策时点：`2026-06-29T08:59:00+08:00`
- 执行时点：`2026-06-29T09:01:00+08:00`
- label 窗口：`2026-06-29T09:01:00+08:00` → `2026-06-29T15:00:00+08:00`
- 目标值：-0.006214288 = ln(401.05 / 403.55)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T15:00:00+08:00` | 237540 | {'bar_start': '2026-06-26T14:59:00+08:00', 'close': 399.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00.022000+08:00` | 237539 | {'trading_day': 20260626, 'close': 399.85} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 965740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-27T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-26', 'value': 70.16} |

## 26. pt2608 20260630 day （contaminated_audit）

- Episode：`pt:20260630`
- 决策时点：`2026-06-30T08:59:00+08:00`
- 执行时点：`2026-06-30T09:01:00+08:00`
- label 窗口：`2026-06-30T09:01:00+08:00` → `2026-06-30T15:00:00+08:00`
- 目标值：0.0043517284 = ln(391.5 / 389.8)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-29T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-29T14:59:00+08:00', 'close': 401.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-29T15:00:00.014000+08:00` | 64739 | {'trading_day': 20260629, 'close': 401.05} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1052140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-30T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-29', 'value': 71.59} |

## 27. pt2608 20260701 day （contaminated_audit）

- Episode：`pt:20260701`
- 决策时点：`2026-07-01T08:59:00+08:00`
- 执行时点：`2026-07-01T09:01:00+08:00`
- label 窗口：`2026-07-01T09:01:00+08:00` → `2026-07-01T15:00:00+08:00`
- 目标值：-0.0036572664 = ln(382.1 / 383.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-30T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-30T14:59:00+08:00', 'close': 391.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-30T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260630, 'close': 391.5} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1138540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 28. pt2608 20260706 day （contaminated_audit）

- Episode：`pt:20260706`
- 决策时点：`2026-07-06T08:59:00+08:00`
- 执行时点：`2026-07-06T09:01:00+08:00`
- label 窗口：`2026-07-06T09:01:00+08:00` → `2026-07-06T15:00:00+08:00`
- 目标值：-0.015050758 = ln(405.55 / 411.7)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-03T15:00:00+08:00` | 237540 | {'bar_start': '2026-07-03T14:59:00+08:00', 'close': 410.45, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-03T15:00:00.102000+08:00` | 237539 | {'trading_day': 20260703, 'close': 410.45} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1570540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-04T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-03', 'value': 68.68} |

## 29. pt2608 20260717 day （contaminated_audit）

- Episode：`pt:20260717`
- 决策时点：`2026-07-17T08:59:00+08:00`
- 执行时点：`2026-07-17T09:01:00+08:00`
- label 窗口：`2026-07-17T09:01:00+08:00` → `2026-07-17T15:00:00+08:00`
- 目标值：-0.023189445 = ln(392.15 / 401.35)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-16T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-16T14:59:00+08:00', 'close': 409.45, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-16T15:00:00.032000+08:00` | 64739 | {'trading_day': 20260716, 'close': 409.45} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2520940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 269940 | {'quote_date': '2026-07-13', 'value': 81.62} |
