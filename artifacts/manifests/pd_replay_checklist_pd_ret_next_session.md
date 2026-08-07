# SC Temporal Spine 人工回放清单（pd_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`a60589003e4cd7937d666a834874972b7a6d278b5d39c6748847f42d670b86a3`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. pd2606 20251204 day （historical_validation）

- Episode：`pd:20251204`
- 决策时点：`2025-12-04T08:59:00+08:00`
- 执行时点：`2025-12-04T09:01:00+08:00`
- label 窗口：`2025-12-04T09:01:00+08:00` → `2025-12-04T15:00:00+08:00`
- 目标值：-0.010883212 = ln(379.25 / 383.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-03T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-03T14:59:00+08:00', 'close': 381.5, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-03T15:00:00.015000+08:00` | 64739 | {'trading_day': 20251203, 'close': 381.5} |
| cls_last_telegraph | cls_telegraph | `2025-12-04T08:53:35+08:00` | 325 | {'title': '【日本称干扰他国卫星技术取得进展】', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-04T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-03', 'value': 63.75} |

## 01. pd2606 20251205 day （historical_validation）

- Episode：`pd:20251205`
- 决策时点：`2025-12-05T08:59:00+08:00`
- 执行时点：`2025-12-05T09:01:00+08:00`
- label 窗口：`2025-12-05T09:01:00+08:00` → `2025-12-05T15:00:00+08:00`
- 目标值：0.012122958 = ln(381.75 / 377.15)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-04T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-04T14:59:00+08:00', 'close': 379.25, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-04T15:00:00.012000+08:00` | 64739 | {'trading_day': 20251204, 'close': 379.25} |
| cls_last_telegraph | cls_telegraph | `2025-12-05T08:49:31+08:00` | 569 | {'title': '', 'labels': '医疗器械 脑科学 人脑工程'} |
| brent_last_close | intl_brent | `2025-12-05T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-04', 'value': 64.15} |

## 02. pd2606 20251222 day （historical_validation）

- Episode：`pd:20251222`
- 决策时点：`2025-12-22T08:59:00+08:00`
- 执行时点：`2025-12-22T09:01:00+08:00`
- label 窗口：`2025-12-22T09:01:00+08:00` → `2025-12-22T15:00:00+08:00`
- 目标值：NULL（no-trade：exit_at_price_limit）

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-19T15:00:00+08:00` | 237540 | {'bar_start': '2025-12-19T14:59:00+08:00', 'close': 480.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-19T15:00:00.023000+08:00` | 237539 | {'trading_day': 20251219, 'close': 480.2} |
| cls_last_telegraph | cls_telegraph | `2025-12-22T08:53:42+08:00` | 318 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-20T06:00:00+08:00` | 183540 | {'quote_date': '2025-12-19', 'value': 61.35} |

## 03. pd2606 20251231 day （historical_validation）

- Episode：`pd:20251231`
- 决策时点：`2025-12-31T08:59:00+08:00`
- 执行时点：`2025-12-31T09:01:00+08:00`
- label 窗口：`2025-12-31T09:01:00+08:00` → `2025-12-31T15:00:00+08:00`
- 目标值：-0.00070530155 = ln(425.2 / 425.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-30T15:00:00+08:00` | 64740 | {'bar_start': '2025-12-30T14:59:00+08:00', 'close': 447.45, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-30T15:00:00.021000+08:00` | 64739 | {'trading_day': 20251230, 'close': 447.45} |
| cls_last_telegraph | cls_telegraph | `2025-12-31T08:56:59+08:00` | 121 | {'title': '【雷军：跨年直播推迟到1月3日晚7点】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-30', 'value': 62.3} |

## 04. pd2606 20260108 day （contaminated_audit）

- Episode：`pd:20260108`
- 决策时点：`2026-01-08T08:59:00+08:00`
- 执行时点：`2026-01-08T09:01:00+08:00`
- label 窗口：`2026-01-08T09:01:00+08:00` → `2026-01-08T15:00:00+08:00`
- 目标值：-0.016468808 = ln(460.7 / 468.35)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-07T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-07T14:59:00+08:00', 'close': 475.95, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-07T15:00:00.115000+08:00` | 64739 | {'trading_day': 20260107, 'close': 475.95} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T08:57:24+08:00` | 96 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 05. pd2606 20260113 day （contaminated_audit）

- Episode：`pd:20260113`
- 决策时点：`2026-01-13T08:59:00+08:00`
- 执行时点：`2026-01-13T09:01:00+08:00`
- label 窗口：`2026-01-13T09:01:00+08:00` → `2026-01-13T15:00:00+08:00`
- 目标值：-0.0067027835 = ln(483.25 / 486.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-12T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-12T14:59:00+08:00', 'close': 505.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-12T15:00:00.005000+08:00` | 64739 | {'trading_day': 20260112, 'close': 505.1} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T08:58:22+08:00` | 38 | {'title': '【芝商所将于1月13日收盘后调整贵金属保证金要求】', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 06. pd2606 20260120 day （contaminated_audit）

- Episode：`pd:20260120`
- 决策时点：`2026-01-20T08:59:00+08:00`
- 执行时点：`2026-01-20T09:01:00+08:00`
- label 窗口：`2026-01-20T09:01:00+08:00` → `2026-01-20T15:00:00+08:00`
- 目标值：0.013250669 = ln(490 / 483.55)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-19T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-19T14:59:00+08:00', 'close': 477.95, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-19T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260119, 'close': 477.95} |
| cls_last_telegraph | cls_telegraph | `2026-01-20T08:58:24+08:00` | 36 | {'title': '', 'labels': '期货市场情报 天然气 能源类期货'} |
| brent_last_close | intl_brent | `2026-01-20T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-19', 'value': 66.91} |

## 07. pd2606 20260122 day （contaminated_audit）

- Episode：`pd:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.02331888 = ln(483.75 / 472.6)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-21T14:59:00+08:00', 'close': 485.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.023000+08:00` | 64739 | {'trading_day': 20260121, 'close': 485.8} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 08. pd2606 20260128 day （contaminated_audit）

- Episode：`pd:20260128`
- 决策时点：`2026-01-28T08:59:00+08:00`
- 执行时点：`2026-01-28T09:01:00+08:00`
- label 窗口：`2026-01-28T09:01:00+08:00` → `2026-01-28T15:00:00+08:00`
- 目标值：-0.027398974 = ln(504 / 518)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-27T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-27T14:59:00+08:00', 'close': 523.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-27T15:00:00.004000+08:00` | 64739 | {'trading_day': 20260127, 'close': 523.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-28T08:51:42+08:00` | 438 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-01-28T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-27', 'value': 70.28} |

## 09. pd2606 20260129 day （contaminated_audit）

- Episode：`pd:20260129`
- 决策时点：`2026-01-29T08:59:00+08:00`
- 执行时点：`2026-01-29T09:01:00+08:00`
- label 窗口：`2026-01-29T09:01:00+08:00` → `2026-01-29T15:00:00+08:00`
- 目标值：0.018495089 = ln(526.6 / 516.95)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-01-28T14:59:00+08:00', 'close': 504.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-28T15:00:00.127000+08:00` | 64739 | {'trading_day': 20260128, 'close': 504.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-29T08:57:44+08:00` | 76 | {'title': '【家得宝在美裁员并要求员工每周五天到岗办公】', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-28', 'value': 70.9} |

## 10. pd2606 20260227 day （contaminated_audit）

- Episode：`pd:20260227`
- 决策时点：`2026-02-27T08:59:00+08:00`
- 执行时点：`2026-02-27T09:01:00+08:00`
- label 窗口：`2026-02-27T09:01:00+08:00` → `2026-02-27T15:00:00+08:00`
- 目标值：0.040387361 = ln(464.85 / 446.45)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-26T15:00:00+08:00` | 64740 | {'bar_start': '2026-02-26T14:59:00+08:00', 'close': 446.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-02-26T15:00:00.011000+08:00` | 64739 | {'trading_day': 20260226, 'close': 446.55} |
| cls_last_telegraph | cls_telegraph | `2026-02-27T08:56:26+08:00` | 154 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2026-02-27T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-26', 'value': 71.66} |

## 11. pd2606 20260316 day （contaminated_audit）

- Episode：`pd:20260316`
- 决策时点：`2026-03-16T08:59:00+08:00`
- 执行时点：`2026-03-16T09:01:00+08:00`
- label 窗口：`2026-03-16T09:01:00+08:00` → `2026-03-16T15:00:00+08:00`
- 目标值：-0.0020052645 = ln(398.55 / 399.35)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-13T15:00:00+08:00` | 237540 | {'bar_start': '2026-03-13T14:59:00+08:00', 'close': 408.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-13T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260313, 'close': 408.1} |
| cls_last_telegraph | cls_telegraph | `2026-03-16T08:58:48+08:00` | 12 | {'title': '【俄称受中东局势影响 乌克兰问题谈判暂停】', 'labels': '俄乌冲突快报'} |
| brent_last_close | intl_brent | `2026-03-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-03-13', 'value': 103.23} |

## 12. pd2606 20260403 day （contaminated_audit）

- Episode：`pd:20260403`
- 决策时点：`2026-04-03T08:59:00+08:00`
- 执行时点：`2026-04-03T09:01:00+08:00`
- label 窗口：`2026-04-03T09:01:00+08:00` → `2026-04-03T15:00:00+08:00`
- 目标值：0.017144808 = ln(376.5 / 370.1)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-02T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-02T14:59:00+08:00', 'close': 362.85, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-02T15:00:00.189000+08:00` | 64739 | {'trading_day': 20260402, 'close': 362.85} |
| cls_last_telegraph | cls_telegraph | `2026-04-03T08:54:49+08:00` | 251 | {'title': '【古巴政府宣布赦免超2000名囚犯】', 'labels': ''} |
| brent_last_close | intl_brent | `2026-04-03T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-02', 'value': 127.61} |

## 13. pd2606 20260413 day （contaminated_audit）

- Episode：`pd:20260413`
- 决策时点：`2026-04-13T08:59:00+08:00`
- 执行时点：`2026-04-13T09:01:00+08:00`
- label 窗口：`2026-04-13T09:01:00+08:00` → `2026-04-13T15:00:00+08:00`
- 目标值：-0.0061289883 = ln(382.25 / 384.6)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-10T15:00:00+08:00` | 237540 | {'bar_start': '2026-04-10T14:59:00+08:00', 'close': 385.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-10T15:00:00.037000+08:00` | 237539 | {'trading_day': 20260410, 'close': 385.05} |
| cls_last_telegraph | cls_telegraph | `2026-04-13T08:57:03+08:00` | 117 | {'title': '【荣耀与字节跳动接洽“豆包手机”合作】', 'labels': 'TMT行业观察 人工智能'} |
| brent_last_close | intl_brent | `2026-04-11T06:00:00+08:00` | 183540 | {'quote_date': '2026-04-10', 'value': 119.07} |

## 14. pd2606 20260421 day （contaminated_audit）

- Episode：`pd:20260421`
- 决策时点：`2026-04-21T08:59:00+08:00`
- 执行时点：`2026-04-21T09:01:00+08:00`
- label 窗口：`2026-04-21T09:01:00+08:00` → `2026-04-21T15:00:00+08:00`
- 目标值：-0.015983707 = ln(381.7 / 387.85)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-20T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-20T14:59:00+08:00', 'close': 384.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-20T15:00:00.016000+08:00` | 64739 | {'trading_day': 20260420, 'close': 384.05} |
| cls_last_telegraph | cls_telegraph | `2026-04-21T08:56:50+08:00` | 130 | {'title': '【报道称美国副总统万斯21日前往巴基斯坦】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-04-21T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-20', 'value': 103.4} |

## 15. pd2606 20260424 day （contaminated_audit）

- Episode：`pd:20260424`
- 决策时点：`2026-04-24T08:59:00+08:00`
- 执行时点：`2026-04-24T09:01:00+08:00`
- label 窗口：`2026-04-24T09:01:00+08:00` → `2026-04-24T15:00:00+08:00`
- 目标值：-0.013395215 = ln(359.65 / 364.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-23T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-23T14:59:00+08:00', 'close': 374.75, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-23T15:00:00.218000+08:00` | 64739 | {'trading_day': 20260423, 'close': 374.75} |
| cls_last_telegraph | cls_telegraph | `2026-04-24T08:55:03+08:00` | 237 | {'title': '【伊朗领导层齐斥特朗普“内斗”论：“我们都是伊朗人”“没有强硬派或温和派”】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-04-24T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-23', 'value': 113.25} |

## 16. pd2606 20260428 day （contaminated_audit）

- Episode：`pd:20260428`
- 决策时点：`2026-04-28T08:59:00+08:00`
- 执行时点：`2026-04-28T09:01:00+08:00`
- label 窗口：`2026-04-28T09:01:00+08:00` → `2026-04-28T15:00:00+08:00`
- 目标值：-0.010433426 = ln(357.55 / 361.3)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-27T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-27T14:59:00+08:00', 'close': 364.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-27T15:00:00.035000+08:00` | 64739 | {'trading_day': 20260427, 'close': 364.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-28T08:57:47+08:00` | 73 | {'title': '【宁德时代50亿美元股票配售据悉获得超过150名投资者认购】', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2026-04-28T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-27', 'value': 113.89} |

## 17. pd2606 20260429 day （contaminated_audit）

- Episode：`pd:20260429`
- 决策时点：`2026-04-29T08:59:00+08:00`
- 执行时点：`2026-04-29T09:01:00+08:00`
- label 窗口：`2026-04-29T09:01:00+08:00` → `2026-04-29T15:00:00+08:00`
- 目标值：-0.0029575404 = ln(354.5 / 355.55)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-04-28T14:59:00+08:00', 'close': 357.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-28T15:00:00.011000+08:00` | 64739 | {'trading_day': 20260428, 'close': 357.55} |
| cls_last_telegraph | cls_telegraph | `2026-04-29T08:52:40+08:00` | 380 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2026-04-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-04-28', 'value': 117.62} |

## 18. pd2606 20260511 day （contaminated_audit）

- Episode：`pd:20260511`
- 决策时点：`2026-05-11T08:59:00+08:00`
- 执行时点：`2026-05-11T09:01:00+08:00`
- label 窗口：`2026-05-11T09:01:00+08:00` → `2026-05-11T15:00:00+08:00`
- 目标值：0.0031457319 = ln(366.15 / 365)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-08T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-08T14:59:00+08:00', 'close': 372.3, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-08T15:00:00.017000+08:00` | 237539 | {'trading_day': 20260508, 'close': 372.3} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T08:57:06+08:00` | 114 | {'title': '【伊朗媒体公布伊朗回应美方要点】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 19. pd2606 20260518 day （contaminated_audit）

- Episode：`pd:20260518`
- 决策时点：`2026-05-18T08:59:00+08:00`
- 执行时点：`2026-05-18T09:01:00+08:00`
- label 窗口：`2026-05-18T09:01:00+08:00` → `2026-05-18T15:00:00+08:00`
- 目标值：0.0051474487 = ln(340.85 / 339.1)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-15T15:00:00+08:00` | 237540 | {'bar_start': '2026-05-15T14:59:00+08:00', 'close': 345.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-15T15:00:00.154000+08:00` | 237539 | {'trading_day': 20260515, 'close': 345.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T08:57:46+08:00` | 74 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 183540 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 20. pd2606 20260520 day （contaminated_audit）

- Episode：`pd:20260520`
- 决策时点：`2026-05-20T08:59:00+08:00`
- 执行时点：`2026-05-20T09:01:00+08:00`
- label 窗口：`2026-05-20T09:01:00+08:00` → `2026-05-20T15:00:00+08:00`
- 目标值：0.0013534854 = ln(332.7 / 332.25)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-19T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-19T14:59:00+08:00', 'close': 338.8, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-19T15:00:00.019000+08:00` | 64739 | {'trading_day': 20260519, 'close': 338.8} |
| cls_last_telegraph | cls_telegraph | `2026-05-20T08:58:22+08:00` | 38 | {'title': '【江苏：实施提振消费专项行动 培育壮大智能穿戴设备、首发首店经济、AI流量消费等', 'labels': '人工智能 能源行业新闻 促消费举措 智能穿戴 新质生产力'} |
| brent_last_close | intl_brent | `2026-05-20T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-19', 'value': 114.64} |

## 21. pd2608 20260529 day （contaminated_audit）

- Episode：`pd:20260529`
- 决策时点：`2026-05-29T08:59:00+08:00`
- 执行时点：`2026-05-29T09:01:00+08:00`
- label 窗口：`2026-05-29T09:01:00+08:00` → `2026-05-29T15:00:00+08:00`
- 目标值：-0.0019836735 = ln(327.35 / 328)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-28T15:00:00+08:00` | 64740 | {'bar_start': '2026-05-28T14:59:00+08:00', 'close': 328.75, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-28T15:00:00.021000+08:00` | 64739 | {'trading_day': 20260528, 'close': 328.75} |
| cls_last_telegraph | cls_telegraph | `2026-05-29T08:57:30+08:00` | 90 | {'title': '【江苏省政府召开智能机器人具身智能产业高质量发展专题推进会议】', 'labels': '机器人'} |
| brent_last_close | intl_brent | `2026-05-29T06:00:00+08:00` | 10740 | {'quote_date': '2026-05-28', 'value': 95.47} |

## 22. pd2608 20260610 day （contaminated_audit）

- Episode：`pd:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：0.020763199 = ln(289.55 / 283.6)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-09T14:59:00+08:00', 'close': 290.9, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260609, 'close': 290.9} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 23. pd2608 20260611 day （contaminated_audit）

- Episode：`pd:20260611`
- 决策时点：`2026-06-11T08:59:00+08:00`
- 执行时点：`2026-06-11T09:01:00+08:00`
- label 窗口：`2026-06-11T09:01:00+08:00` → `2026-06-11T15:00:00+08:00`
- 目标值：0.030305349 = ln(301.5 / 292.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-10T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-10T14:59:00+08:00', 'close': 289.55, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-10T15:00:00.074000+08:00` | 64739 | {'trading_day': 20260610, 'close': 289.55} |
| cls_last_telegraph | cls_telegraph | `2026-06-11T08:48:20+08:00` | 640 | {'title': '【两市融资余额减少80.91亿元】', 'labels': '盘面直播'} |
| brent_last_close | intl_brent | `2026-06-11T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-10', 'value': 95.73} |

## 24. pd2608 20260622 day （contaminated_audit）

- Episode：`pd:20260622`
- 决策时点：`2026-06-22T08:59:00+08:00`
- 执行时点：`2026-06-22T09:01:00+08:00`
- label 窗口：`2026-06-22T09:01:00+08:00` → `2026-06-22T15:00:00+08:00`
- 目标值：0.017237561 = ln(307.2 / 301.95)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-18T15:00:00+08:00` | 323940 | {'bar_start': '2026-06-18T14:59:00+08:00', 'close': 311.05, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-18T15:00:00.015000+08:00` | 323939 | {'trading_day': 20260618, 'close': 311.05} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 360940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-20T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-19', 'value': 80.46} |

## 25. pd2608 20260629 day （contaminated_audit）

- Episode：`pd:20260629`
- 决策时点：`2026-06-29T08:59:00+08:00`
- 执行时点：`2026-06-29T09:01:00+08:00`
- label 窗口：`2026-06-29T09:01:00+08:00` → `2026-06-29T15:00:00+08:00`
- 目标值：0.026082467 = ln(295.2 / 287.6)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T15:00:00+08:00` | 237540 | {'bar_start': '2026-06-26T14:59:00+08:00', 'close': 285.25, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00.022000+08:00` | 237539 | {'trading_day': 20260626, 'close': 285.25} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 965740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-27T06:00:00+08:00` | 183540 | {'quote_date': '2026-06-26', 'value': 70.16} |

## 26. pd2608 20260630 day （contaminated_audit）

- Episode：`pd:20260630`
- 决策时点：`2026-06-30T08:59:00+08:00`
- 执行时点：`2026-06-30T09:01:00+08:00`
- label 窗口：`2026-06-30T09:01:00+08:00` → `2026-06-30T15:00:00+08:00`
- 目标值：0.013475684 = ln(295.1 / 291.15)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-29T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-29T14:59:00+08:00', 'close': 295.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-29T15:00:00.014000+08:00` | 64739 | {'trading_day': 20260629, 'close': 295.2} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1052140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-30T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-29', 'value': 71.59} |

## 27. pd2608 20260701 day （contaminated_audit）

- Episode：`pd:20260701`
- 决策时点：`2026-07-01T08:59:00+08:00`
- 执行时点：`2026-07-01T09:01:00+08:00`
- label 窗口：`2026-07-01T09:01:00+08:00` → `2026-07-01T15:00:00+08:00`
- 目标值：-0.010978589 = ln(285.35 / 288.5)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-30T15:00:00+08:00` | 64740 | {'bar_start': '2026-06-30T14:59:00+08:00', 'close': 295.1, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-30T15:00:00.015000+08:00` | 64739 | {'trading_day': 20260630, 'close': 295.1} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1138540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-01T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-30', 'value': 70.46} |

## 28. pd2608 20260706 day （contaminated_audit）

- Episode：`pd:20260706`
- 决策时点：`2026-07-06T08:59:00+08:00`
- 执行时点：`2026-07-06T09:01:00+08:00`
- label 窗口：`2026-07-06T09:01:00+08:00` → `2026-07-06T15:00:00+08:00`
- 目标值：-0.010793236 = ln(304.1 / 307.4)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-03T15:00:00+08:00` | 237540 | {'bar_start': '2026-07-03T14:59:00+08:00', 'close': 307.2, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-03T15:00:00.102000+08:00` | 237539 | {'trading_day': 20260703, 'close': 307.2} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1570540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-04T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-03', 'value': 68.68} |

## 29. pd2608 20260717 day （contaminated_audit）

- Episode：`pd:20260717`
- 决策时点：`2026-07-17T08:59:00+08:00`
- 执行时点：`2026-07-17T09:01:00+08:00`
- label 窗口：`2026-07-17T09:01:00+08:00` → `2026-07-17T15:00:00+08:00`
- 目标值：-0.024820996 = ln(294.45 / 301.85)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-16T15:00:00+08:00` | 64740 | {'bar_start': '2026-07-16T14:59:00+08:00', 'close': 309.6, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-07-16T15:00:00.032000+08:00` | 64739 | {'trading_day': 20260716, 'close': 309.6} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2520940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 269940 | {'quote_date': '2026-07-13', 'value': 81.62} |
