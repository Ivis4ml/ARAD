# SC Temporal Spine 人工回放清单（op_ret_next_session）

- 抽样种子：`20260805`（按样本段分层，结果可复现）
- 样本量：30
- spine 指纹：`c1ec9cff561e8ddad9ac638551146bd26b9cf321cc64f1eee8932dffd5bd9caf`

核对方法：逐条确认每个 feature 的 `availability_time` 严格早于 `decision_time`，
且 `decision_time` 严格早于 `label_start`。`lead_seconds` 为两者之差，必须为正。

## 00. op2601 20250923 day （historical_validation）

- Episode：`op:20250923`
- 决策时点：`2025-09-23T08:59:00+08:00`
- 执行时点：`2025-09-23T09:01:00+08:00`
- label 窗口：`2025-09-23T09:01:00+08:00` → `2025-09-23T15:00:00+08:00`
- 目标值：-0.0018912535 = ln(4226 / 4234)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-09-22T23:00:00+08:00` | 35940 | {'bar_start': '2025-09-22T22:59:00+08:00', 'close': 4234.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-09-22T15:00:00.500000+08:00` | 64739 | {'trading_day': 20250922, 'close': 4234.0} |
| cls_last_telegraph | cls_telegraph | `2025-09-23T08:58:58+08:00` | 2 | {'title': '', 'labels': '港股动态'} |
| brent_last_close | intl_brent | `2025-09-23T06:00:00+08:00` | 10740 | {'quote_date': '2025-09-22', 'value': 66.87} |

## 01. op2601 20251013 day （historical_validation）

- Episode：`op:20251013`
- 决策时点：`2025-10-13T08:59:00+08:00`
- 执行时点：`2025-10-13T09:01:00+08:00`
- label 窗口：`2025-10-13T09:01:00+08:00` → `2025-10-13T15:00:00+08:00`
- 目标值：-0.0023724804 = ln(4210 / 4220)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-10T23:00:00+08:00` | 208740 | {'bar_start': '2025-10-10T22:59:00+08:00', 'close': 4224.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-10-10T15:00:00.500000+08:00` | 237539 | {'trading_day': 20251010, 'close': 4226.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-13T08:51:35+08:00` | 445 | {'title': '【广西将自然灾害救助四级应急响应调整为三级】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2025-10-11T06:00:00+08:00` | 183540 | {'quote_date': '2025-10-10', 'value': 64.41} |

## 02. op2601 20251020 night （historical_validation）

- Episode：`op:20251020`
- 决策时点：`2025-10-17T20:59:00+08:00`
- 执行时点：`2025-10-17T21:01:00+08:00`
- label 窗口：`2025-10-17T21:01:00+08:00` → `2025-10-17T23:00:00+08:00`
- 目标值：-0.0062067518 = ln(4176 / 4202)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-17T15:00:00+08:00` | 21540 | {'bar_start': '2025-10-17T14:59:00+08:00', 'close': 4202.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251017, 'close': 4202.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-17T20:58:39+08:00` | 21 | {'title': '【豪鹏科技：已向某全球领先的服务器客户出货BBU电池产品】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-10-17T06:00:00+08:00` | 53940 | {'quote_date': '2025-10-16', 'value': 61.08} |

## 03. op2601 20251021 night （historical_validation）

- Episode：`op:20251021`
- 决策时点：`2025-10-20T20:59:00+08:00`
- 执行时点：`2025-10-20T21:01:00+08:00`
- label 窗口：`2025-10-20T21:01:00+08:00` → `2025-10-20T23:00:00+08:00`
- 目标值：0.0038480086 = ln(4166 / 4150)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-10-20T15:00:00+08:00` | 21540 | {'bar_start': '2025-10-20T14:59:00+08:00', 'close': 4166.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-10-20T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251020, 'close': 4166.0} |
| cls_last_telegraph | cls_telegraph | `2025-10-20T20:57:50+08:00` | 70 | {'title': '【扬杰科技：已有多项产品技术可用于人形机器人的小型关节电机及感知系统中】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-10-18T06:00:00+08:00` | 226740 | {'quote_date': '2025-10-17', 'value': 61.23} |

## 04. op2601 20251111 night （historical_validation）

- Episode：`op:20251111`
- 决策时点：`2025-11-10T20:59:00+08:00`
- 执行时点：`2025-11-10T21:01:00+08:00`
- label 窗口：`2025-11-10T21:01:00+08:00` → `2025-11-10T23:00:00+08:00`
- 目标值：-0.0046403796 = ln(4300 / 4320)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-10T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-10T14:59:00+08:00', 'close': 4314.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-10T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251110, 'close': 4314.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-10T20:53:51+08:00` | 309 | {'title': '【佳电股份：公司系徐圩核电站项目关键电气设备供应商】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2025-11-08T06:00:00+08:00` | 226740 | {'quote_date': '2025-11-07', 'value': 63.72} |

## 05. op2602 20251125 night （historical_validation）

- Episode：`op:20251125`
- 决策时点：`2025-11-24T20:59:00+08:00`
- 执行时点：`2025-11-24T21:01:00+08:00`
- label 窗口：`2025-11-24T21:01:00+08:00` → `2025-11-24T23:00:00+08:00`
- 目标值：0.0024289543 = ln(4122 / 4112)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-11-24T15:00:00+08:00` | 21540 | {'bar_start': '2025-11-24T14:59:00+08:00', 'close': 4110.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-11-24T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251124, 'close': 4110.0} |
| cls_last_telegraph | cls_telegraph | `2025-11-24T20:56:13+08:00` | 167 | {'title': '【欧盟举行非正式会议 评估乌克兰和平进程】', 'labels': '俄乌冲突快报 环球市场情报'} |
| brent_last_close | intl_brent | `2025-11-22T06:00:00+08:00` | 226740 | {'quote_date': '2025-11-21', 'value': 62.78} |

## 06. op2602 20251209 night （historical_validation）

- Episode：`op:20251209`
- 决策时点：`2025-12-08T20:59:00+08:00`
- 执行时点：`2025-12-08T21:01:00+08:00`
- label 窗口：`2025-12-08T21:01:00+08:00` → `2025-12-08T23:00:00+08:00`
- 目标值：-0.0014921664 = ln(4018 / 4024)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-08T15:00:00+08:00` | 21540 | {'bar_start': '2025-12-08T14:59:00+08:00', 'close': 4024.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2025-12-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20251208, 'close': 4024.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-08T20:58:37+08:00` | 23 | {'title': '', 'labels': '环球市场情报 农产品期货'} |
| brent_last_close | intl_brent | `2025-12-06T06:00:00+08:00` | 226740 | {'quote_date': '2025-12-05', 'value': 64.42} |

## 07. op2602 20251209 day （historical_validation）

- Episode：`op:20251209`
- 决策时点：`2025-12-09T08:59:00+08:00`
- 执行时点：`2025-12-09T09:01:00+08:00`
- label 窗口：`2025-12-09T09:01:00+08:00` → `2025-12-09T15:00:00+08:00`
- 目标值：-0.0024919026 = ln(4008 / 4018)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-08T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-08T22:59:00+08:00', 'close': 4018.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-08T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251208, 'close': 4024.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-09T08:58:19+08:00` | 41 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-09T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-08', 'value': 63.3} |

## 08. op2602 20251219 day （historical_validation）

- Episode：`op:20251219`
- 决策时点：`2025-12-19T08:59:00+08:00`
- 执行时点：`2025-12-19T09:01:00+08:00`
- label 窗口：`2025-12-19T09:01:00+08:00` → `2025-12-19T15:00:00+08:00`
- 目标值：-0.00403837 = ln(3954 / 3970)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-18T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-18T22:59:00+08:00', 'close': 3970.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-18T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251218, 'close': 3970.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-19T08:53:41+08:00` | 319 | {'title': '【白羽肉鸡毛鸡价格逼近年内高点 业内人士称后市或仍有空间】', 'labels': '家禽'} |
| brent_last_close | intl_brent | `2025-12-19T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-18', 'value': 60.69} |

## 09. op2602 20251225 day （historical_validation）

- Episode：`op:20251225`
- 决策时点：`2025-12-25T08:59:00+08:00`
- 执行时点：`2025-12-25T09:01:00+08:00`
- label 窗口：`2025-12-25T09:01:00+08:00` → `2025-12-25T15:00:00+08:00`
- 目标值：0.0093619802 = ln(4078 / 4040)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-24T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-24T22:59:00+08:00', 'close': 4042.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-24T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251224, 'close': 4032.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-25T08:53:06+08:00` | 354 | {'title': '', 'labels': '环球市场情报'} |
| brent_last_close | intl_brent | `2025-12-25T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-24', 'value': 63.7} |

## 10. op2602 20251231 day （historical_validation）

- Episode：`op:20251231`
- 决策时点：`2025-12-31T08:59:00+08:00`
- 执行时点：`2025-12-31T09:01:00+08:00`
- label 窗口：`2025-12-31T09:01:00+08:00` → `2025-12-31T15:00:00+08:00`
- 目标值：0.001437126 = ln(4178 / 4172)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2025-12-30T23:00:00+08:00` | 35940 | {'bar_start': '2025-12-30T22:59:00+08:00', 'close': 4164.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2025-12-30T15:00:00.500000+08:00` | 64739 | {'trading_day': 20251230, 'close': 4162.0} |
| cls_last_telegraph | cls_telegraph | `2025-12-31T08:56:59+08:00` | 121 | {'title': '【雷军：跨年直播推迟到1月3日晚7点】', 'labels': ''} |
| brent_last_close | intl_brent | `2025-12-31T06:00:00+08:00` | 10740 | {'quote_date': '2025-12-30', 'value': 62.3} |

## 11. op2603 20260109 night （contaminated_audit）

- Episode：`op:20260109`
- 决策时点：`2026-01-08T20:59:00+08:00`
- 执行时点：`2026-01-08T21:01:00+08:00`
- label 窗口：`2026-01-08T21:01:00+08:00` → `2026-01-08T23:00:00+08:00`
- 目标值：-0.0099739606 = ln(4190 / 4232)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-08T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-08T14:59:00+08:00', 'close': 4212.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-08T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260108, 'close': 4212.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-08T20:56:34+08:00` | 146 | {'title': '【华西股份：参股公司联储证券通过其投资主体持有星河动力部分股权】', 'labels': '互动平台精选'} |
| brent_last_close | intl_brent | `2026-01-08T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-07', 'value': 61.08} |

## 12. op2603 20260112 day （contaminated_audit）

- Episode：`op:20260112`
- 决策时点：`2026-01-12T08:59:00+08:00`
- 执行时点：`2026-01-12T09:01:00+08:00`
- label 窗口：`2026-01-12T09:01:00+08:00` → `2026-01-12T15:00:00+08:00`
- 目标值：0.0038095284 = ln(4208 / 4192)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-09T23:00:00+08:00` | 208740 | {'bar_start': '2026-01-09T22:59:00+08:00', 'close': 4188.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-09T15:00:00.500000+08:00` | 237539 | {'trading_day': 20260109, 'close': 4210.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-12T08:57:44+08:00` | 76 | {'title': '', 'labels': '期货市场情报 黄金 有色金属'} |
| brent_last_close | intl_brent | `2026-01-10T06:00:00+08:00` | 183540 | {'quote_date': '2026-01-09', 'value': 65.11} |

## 13. op2603 20260114 night （contaminated_audit）

- Episode：`op:20260114`
- 决策时点：`2026-01-13T20:59:00+08:00`
- 执行时点：`2026-01-13T21:01:00+08:00`
- label 窗口：`2026-01-13T21:01:00+08:00` → `2026-01-13T23:00:00+08:00`
- 目标值：0.0062817312 = ln(4152 / 4126)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-13T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-13T14:59:00+08:00', 'close': 4100.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-13T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260113, 'close': 4100.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-13T20:53:46+08:00` | 314 | {'title': '', 'labels': '港股IPO动态'} |
| brent_last_close | intl_brent | `2026-01-13T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-12', 'value': 65.4} |

## 14. op2603 20260119 night （contaminated_audit）

- Episode：`op:20260119`
- 决策时点：`2026-01-16T20:59:00+08:00`
- 执行时点：`2026-01-16T21:01:00+08:00`
- label 窗口：`2026-01-16T21:01:00+08:00` → `2026-01-16T23:00:00+08:00`
- 目标值：0.0029368597 = ln(4092 / 4080)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-01-16T14:59:00+08:00', 'close': 4066.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-01-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260116, 'close': 4066.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-16T20:57:39+08:00` | 81 | {'title': '', 'labels': '美股动态'} |
| brent_last_close | intl_brent | `2026-01-16T06:00:00+08:00` | 53940 | {'quote_date': '2026-01-15', 'value': 66.16} |

## 15. op2603 20260122 day （contaminated_audit）

- Episode：`op:20260122`
- 决策时点：`2026-01-22T08:59:00+08:00`
- 执行时点：`2026-01-22T09:01:00+08:00`
- label 窗口：`2026-01-22T09:01:00+08:00` → `2026-01-22T15:00:00+08:00`
- 目标值：0.015534293 = ln(4152 / 4088)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-01-21T23:00:00+08:00` | 35940 | {'bar_start': '2026-01-21T22:59:00+08:00', 'close': 4096.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-01-21T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260121, 'close': 4052.0} |
| cls_last_telegraph | cls_telegraph | `2026-01-22T08:54:05+08:00` | 295 | {'title': '【第三届北京商业航天产业高质量发展推进会将在北京经开区举办】', 'labels': '商业航天'} |
| brent_last_close | intl_brent | `2026-01-22T06:00:00+08:00` | 10740 | {'quote_date': '2026-01-21', 'value': 66.72} |

## 16. op2604 20260204 day （contaminated_audit）

- Episode：`op:20260204`
- 决策时点：`2026-02-04T08:59:00+08:00`
- 执行时点：`2026-02-04T09:01:00+08:00`
- label 窗口：`2026-02-04T09:01:00+08:00` → `2026-02-04T15:00:00+08:00`
- 目标值：0.0014789256 = ln(4060 / 4054)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-03T23:00:00+08:00` | 35940 | {'bar_start': '2026-02-03T22:59:00+08:00', 'close': 4054.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-02-03T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260203, 'close': 4040.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-04T08:58:25+08:00` | 35 | {'title': '', 'labels': '期货市场情报'} |
| brent_last_close | intl_brent | `2026-02-04T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-03', 'value': 70.01} |

## 17. op2604 20260210 day （contaminated_audit）

- Episode：`op:20260210`
- 决策时点：`2026-02-10T08:59:00+08:00`
- 执行时点：`2026-02-10T09:01:00+08:00`
- label 窗口：`2026-02-10T09:01:00+08:00` → `2026-02-10T15:00:00+08:00`
- 目标值：0.0024491807 = ln(4088 / 4078)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-02-09T23:00:00+08:00` | 35940 | {'bar_start': '2026-02-09T22:59:00+08:00', 'close': 4086.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-02-09T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260209, 'close': 4080.0} |
| cls_last_telegraph | cls_telegraph | `2026-02-10T08:58:50+08:00` | 10 | {'title': '【物流体系持续迭代升级 2025年我国物流业总收入同比增长4.1%】', 'labels': '快递物流'} |
| brent_last_close | intl_brent | `2026-02-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-02-09', 'value': 71.19} |

## 18. op2604 20260306 night （contaminated_audit）

- Episode：`op:20260306`
- 决策时点：`2026-03-05T20:59:00+08:00`
- 执行时点：`2026-03-05T21:01:00+08:00`
- label 窗口：`2026-03-05T21:01:00+08:00` → `2026-03-05T23:00:00+08:00`
- 目标值：-0.0023724804 = ln(4210 / 4220)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-05T15:00:00+08:00` | 21540 | {'bar_start': '2026-03-05T14:59:00+08:00', 'close': 4218.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-05T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260305, 'close': 4218.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-05T20:52:54+08:00` | 366 | {'title': '【阿塞拜疆称遭到伊朗发动的“恐怖袭击”】', 'labels': '无人机 中东冲突 环球市场情报'} |
| brent_last_close | intl_brent | `2026-03-05T06:00:00+08:00` | 53940 | {'quote_date': '2026-03-04', 'value': 81.56} |

## 19. op2604 20260317 night （contaminated_audit）

- Episode：`op:20260317`
- 决策时点：`2026-03-16T20:59:00+08:00`
- 执行时点：`2026-03-16T21:01:00+08:00`
- label 窗口：`2026-03-16T21:01:00+08:00` → `2026-03-16T23:00:00+08:00`
- 目标值：-0.0096386288 = ln(4130 / 4170)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-16T15:00:00+08:00` | 21540 | {'bar_start': '2026-03-16T14:59:00+08:00', 'close': 4188.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-16T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260316, 'close': 4188.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-16T20:55:47+08:00` | 193 | {'title': '【中美已就一些议题取得初步共识】', 'labels': '头条新闻 中美经贸磋商'} |
| brent_last_close | intl_brent | `2026-03-14T06:00:00+08:00` | 226740 | {'quote_date': '2026-03-13', 'value': 103.23} |

## 20. op2606 20260401 night （contaminated_audit）

- Episode：`op:20260401`
- 决策时点：`2026-03-31T20:59:00+08:00`
- 执行时点：`2026-03-31T21:01:00+08:00`
- label 窗口：`2026-03-31T21:01:00+08:00` → `2026-03-31T23:00:00+08:00`
- 目标值：-0.010276577 = ln(4066 / 4108)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-03-31T15:00:00+08:00` | 21540 | {'bar_start': '2026-03-31T14:59:00+08:00', 'close': 4128.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-03-31T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260331, 'close': 4128.0} |
| cls_last_telegraph | cls_telegraph | `2026-03-31T20:57:31+08:00` | 89 | {'title': '【以总理称以军正系统性打击伊朗基础设施】', 'labels': '中东冲突 基建投资'} |
| brent_last_close | intl_brent | `2026-03-31T06:00:00+08:00` | 53940 | {'quote_date': '2026-03-30', 'value': 121.88} |

## 21. op2606 20260420 night （contaminated_audit）

- Episode：`op:20260420`
- 决策时点：`2026-04-17T20:59:00+08:00`
- 执行时点：`2026-04-17T21:01:00+08:00`
- label 窗口：`2026-04-17T21:01:00+08:00` → `2026-04-17T23:00:00+08:00`
- 目标值：-0.0019733603 = ln(4050 / 4058)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-04-17T15:00:00+08:00` | 21540 | {'bar_start': '2026-04-17T14:59:00+08:00', 'close': 4056.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-04-17T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260417, 'close': 4056.0} |
| cls_last_telegraph | cls_telegraph | `2026-04-17T20:58:27+08:00` | 33 | {'title': '【深圳市发改委与澳门特区政府低空经济发展工作组开展低空经济交流】', 'labels': 'TMT行业观察 民航机场 快递物流 无人机 低空经济'} |
| brent_last_close | intl_brent | `2026-04-17T06:00:00+08:00` | 53940 | {'quote_date': '2026-04-16', 'value': 116.63} |

## 22. op2607 20260512 night （contaminated_audit）

- Episode：`op:20260512`
- 决策时点：`2026-05-11T20:59:00+08:00`
- 执行时点：`2026-05-11T21:01:00+08:00`
- label 窗口：`2026-05-11T21:01:00+08:00` → `2026-05-11T23:00:00+08:00`
- 目标值：0.0014716706 = ln(4080 / 4074)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-11T15:00:00+08:00` | 21540 | {'bar_start': '2026-05-11T14:59:00+08:00', 'close': 4072.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-11T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260511, 'close': 4072.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-11T20:57:57+08:00` | 63 | {'title': '', 'labels': ''} |
| brent_last_close | intl_brent | `2026-05-09T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-08', 'value': 103.48} |

## 23. op2607 20260519 night （contaminated_audit）

- Episode：`op:20260519`
- 决策时点：`2026-05-18T20:59:00+08:00`
- 执行时点：`2026-05-18T21:01:00+08:00`
- label 窗口：`2026-05-18T21:01:00+08:00` → `2026-05-18T23:00:00+08:00`
- 目标值：0 = ln(4024 / 4024)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-05-18T15:00:00+08:00` | 21540 | {'bar_start': '2026-05-18T14:59:00+08:00', 'close': 4004.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-05-18T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260518, 'close': 4004.0} |
| cls_last_telegraph | cls_telegraph | `2026-05-18T20:57:20+08:00` | 100 | {'title': '', 'labels': '美国政治'} |
| brent_last_close | intl_brent | `2026-05-16T06:00:00+08:00` | 226740 | {'quote_date': '2026-05-15', 'value': 113.96} |

## 24. op2608 20260602 day （contaminated_audit）

- Episode：`op:20260602`
- 决策时点：`2026-06-02T08:59:00+08:00`
- 执行时点：`2026-06-02T09:01:00+08:00`
- label 窗口：`2026-06-02T09:01:00+08:00` → `2026-06-02T15:00:00+08:00`
- 目标值：-0.0014996254 = ln(3998 / 4004)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-01T22:59:00+08:00', 'close': 4002.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-01T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260601, 'close': 4002.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-02T08:58:59+08:00` | 1 | {'title': '【国家能源局：4月核发绿证2.37亿个】', 'labels': '能源行业新闻 电力'} |
| brent_last_close | intl_brent | `2026-06-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-01', 'value': 98.29} |

## 25. op2608 20260610 day （contaminated_audit）

- Episode：`op:20260610`
- 决策时点：`2026-06-10T08:59:00+08:00`
- 执行时点：`2026-06-10T09:01:00+08:00`
- label 窗口：`2026-06-10T09:01:00+08:00` → `2026-06-10T15:00:00+08:00`
- 目标值：0.0010055305 = ln(3980 / 3976)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-09T23:00:00+08:00` | 35940 | {'bar_start': '2026-06-09T22:59:00+08:00', 'close': 3976.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-06-09T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260609, 'close': 3980.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-10T08:57:09+08:00` | 111 | {'title': '【今明天南方多地升温降雨缩减 后天起新一轮降雨开启】', 'labels': '天气变化'} |
| brent_last_close | intl_brent | `2026-06-10T06:00:00+08:00` | 10740 | {'quote_date': '2026-06-09', 'value': 94.15} |

## 26. op2609 20260629 night （contaminated_audit）

- Episode：`op:20260629`
- 决策时点：`2026-06-26T20:59:00+08:00`
- 执行时点：`2026-06-26T21:01:00+08:00`
- label 窗口：`2026-06-26T21:01:00+08:00` → `2026-06-26T23:00:00+08:00`
- 目标值：0.0072239736 = ln(3890 / 3862)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-06-26T15:00:00+08:00` | 21540 | {'bar_start': '2026-06-26T14:59:00+08:00', 'close': 3868.0, 'session_name': 'day'} |
| sc_bar_daily_close | commodity_tick | `2026-06-26T15:00:00.500000+08:00` | 21539 | {'trading_day': 20260626, 'close': 3868.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 749740 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-06-26T06:00:00+08:00` | 53940 | {'quote_date': '2026-06-25', 'value': 73.74} |

## 27. op2609 20260702 day （contaminated_audit）

- Episode：`op:20260702`
- 决策时点：`2026-07-02T08:59:00+08:00`
- 执行时点：`2026-07-02T09:01:00+08:00`
- label 窗口：`2026-07-02T09:01:00+08:00` → `2026-07-02T15:00:00+08:00`
- 目标值：0.011156302 = ln(3966 / 3922)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-01T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-01T22:59:00+08:00', 'close': 3916.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-01T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260701, 'close': 3906.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 1224940 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-02T06:00:00+08:00` | 10740 | {'quote_date': '2026-07-01', 'value': 69.24} |

## 28. op2609 20260716 day （contaminated_audit）

- Episode：`op:20260716`
- 决策时点：`2026-07-16T08:59:00+08:00`
- 执行时点：`2026-07-16T09:01:00+08:00`
- label 窗口：`2026-07-16T09:01:00+08:00` → `2026-07-16T15:00:00+08:00`
- 目标值：0.0045789955 = ln(3940 / 3922)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-15T23:00:00+08:00` | 35940 | {'bar_start': '2026-07-15T22:59:00+08:00', 'close': 3922.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-15T15:00:00.500000+08:00` | 64739 | {'trading_day': 20260715, 'close': 3932.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2434540 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 183540 | {'quote_date': '2026-07-13', 'value': 81.62} |

## 29. op2609 20260720 day （contaminated_audit）

- Episode：`op:20260720`
- 决策时点：`2026-07-20T08:59:00+08:00`
- 执行时点：`2026-07-20T09:01:00+08:00`
- label 窗口：`2026-07-20T09:01:00+08:00` → `2026-07-20T15:00:00+08:00`
- 目标值：0.011607498 = ln(3986 / 3940)
  - 请人工核对：入场价是否为**执行时点那一分钟最后一笔**的收盘，出场价是否为 session 最后一根 bar 的收盘，两者是否都不在涨跌停上

| feature | 来源 | availability_time | 提前量(秒) | 取值 |
|---|---|---|---:|---|
| sc_bar_1min_close | commodity_tick | `2026-07-17T23:00:00+08:00` | 208740 | {'bar_start': '2026-07-17T22:59:00+08:00', 'close': 3934.0, 'session_name': 'night'} |
| sc_bar_daily_close | commodity_tick | `2026-07-17T15:00:00.500000+08:00` | 237539 | {'trading_day': 20260717, 'close': 3914.0} |
| cls_last_telegraph | cls_telegraph | `2026-06-18T04:43:20+08:00` | 2780140 | {'title': '【伊朗方面披露美伊谅解备忘录文本内容】', 'labels': '中东冲突'} |
| brent_last_close | intl_brent | `2026-07-14T06:00:00+08:00` | 529140 | {'quote_date': '2026-07-13', 'value': 81.62} |
