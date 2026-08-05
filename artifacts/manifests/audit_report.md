# ARAD 数据源审计报告（M1）

## commodity_tick

- 根路径：`/Users/xinyu/Code/AR-Polymarket/chinese-commodity`
- 指纹：`9274edb0b7ffbda7…`  生成于 2026-08-05T19:24:29.061418+00:00
- 内容身份：`zip_central_directory_sha256` = `7852e168131679aa…`
  - 保证等级：对每个 zip 条目的 (解码文件名, CRC32, 原始大小) 按序聚合 sha256。可检测：任何改变条目 CRC 的内容修改（含等长替换）、条目增删与改名。不可检测：CRC32 碰撞级别的构造性篡改。
- zip_count: 66
- csv_files: 802975
- uncompressed_bytes: 1370295508555
- trading_days: 909
- first_day: 20221101
- last_day: 20260730
- products_nominal: [88 items]
- product_count_nominal: 88

| 严重度 | 代码 | 说明 |
|---|---|---|
| info | `commodity.filename_encoding` | zip 条目文件名编码分布（cp437/gbk 需转码） |
| warning | `commodity.provisional_facts` | 以下事实为 provisional，待内容级审计确认：郑商所 Turnover 口径与倒退频率、空壳文件比例、各品种可用区间、主力连续文件与逐合约文件的全史对应关系 |

质量闸门：通过

## polymarket_tape

- 根路径：`/Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/polymarket/daily_aligned + /Users/xinyu/Code/AR-Polymarket/AlternativeAR/Alpha-Data/data/polymarket/features/extension_tape`
- 指纹：`85c32698ad823146…`  生成于 2026-08-05T19:24:31.987214+00:00
- 内容身份：`parquet_footer_sha256` = `ab281d5d20706fa3…`
  - 保证等级：parquet footer 字节聚合哈希（含全部行组的列统计、偏移与布局）加文件大小。可检测：schema 变化、行组增删、任何改变列统计或布局的内容修改。不可检测：等长且不改变任何列 min/max 统计与页偏移的数据页篡改。
- hf: {'partitions': 1248, 'rows': 601934424, 'first_date': '2022-11-21', 'last_date': '2026-04-28', 'schema_signatures': 1}
- extension: {'partitions': 78, 'rows': 253680029, 'first_date': '2026-04-28', 'last_date': '2026-07-14', 'schema_signatures': 1}
- schema_conflicts: {'asset_id': {'hf': 'large_string', 'ext': 'string'}, 'category': {'hf': 'large_string', 'ext': 'string'}, 'category_refined': {'hf': 'large_string', 'ext': 'string'}, 'close_at': {'hf': 'timestamp[us, tz=UTC]', 'ext': 'timestamp[us]'}, 'condition_id': {'hf': 'large_string', 'ext': 'string'}, 'maker': {'hf': 'large_string', 'ext': 'string'}, 'market_slug': {'hf': 'large_string', 'ext': 'string'}, 'neg_risk': {'hf': 'large_string', 'ext': 'bool'}, 'opens_at': {'hf': 'timestamp[us, tz=UTC]', 'ext': 'timestamp[us]'}, 'outcome_label': {'hf': 'large_string', 'ext': 'string'}, 'resolution_status': {'hf': 'large_string', 'ext': 'string'}, 'resolved_at': {'hf': 'timestamp[us, tz=UTC]', 'ext': 'timestamp[us]'}, 'taker': {'hf': 'large_string', 'ext': 'string'}, 'taker_direction': {'hf': 'large_string', 'ext': 'string'}, 'winning_outcome_label': {'hf': 'large_string', 'ext': 'string'}}
- **禁用字段**：resolution_status, resolved_at, winning_outcome_label

| 严重度 | 代码 | 说明 |
|---|---|---|
| warning | `polymarket.schema_conflict` | 两段 tape 存在 15 处列类型冲突，UNION 前必须统一 |
| info | `polymarket.seam` | 接缝无重叠：范围间隔 248 秒，复合键交集为 0 |
| warning | `polymarket.provisional_facts` | 以下事实为 provisional：relay legs 清理完备性、unknown venue 分布、negRisk 在扩展段的覆盖率；HF 段确定不含 negRisk tape |

质量闸门：通过

## cls_telegraph

- 根路径：`/Users/xinyu/Code/AR-Polymarket/Crawler/cls-data/data/output`
- 指纹：`75a41c172ef67a10…`  生成于 2026-08-05T19:24:33.729204+00:00
- 内容身份：`content_sha256` = `2a2418f159858ec0…`
  - 保证等级：对全部 CSV 文件的原始字节按文件名序聚合 sha256（全文哈希）。可检测：任何内容修改（含等长替换）、文件增删。无已知盲区。
- files: 2361
- rows: 894220
- first_day: 2020-01-01
- last_day: 2026-06-18
- calendar_gaps: 0
- **禁用字段**：Comments, Reads, Shares

| 严重度 | 代码 | 说明 |
|---|---|---|
| info | `cls.content_sample` | 内容抽样：Time 格式与 Content 非空检查 |
| info | `cls.in_roll_universe` | 覆盖率限定：历史回填只见 in_roll=1 的可见母体；相对实时快照并集的内容覆盖率经归日比对为 99% 至 100%（scripts/verify_cls_coverage.py），未进入滚动列表的条目两个来源都不可见 |
| info | `cls.coverage_end` | 数据止于最后覆盖日；此后缺口的回爬属于 acquisition 流程，需人类授权 |

质量闸门：通过
