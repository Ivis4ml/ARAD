# 工程票 M8：多品种与横截面 IC

> **来源与核实状态。**本票由一次四路只读勘察产出（2026-08-07），尚未实施任何改动。
> 我独立复核了其中三条最要紧的事实，均属实：
>
> - `temporal/build.py` 的 `_CONTRACT_RE` 是 `^([a-z]{1,2})(\d{3,4})_(20\d{6})\.csv$`，
>   而 M1 扫描器 `data_catalog/commodity.py:36` 用的是 `[A-Za-z]{1,2}`。实测
>   `MA609_20260730.csv` 与 `IF2608_20260730.csv` 均不匹配，`sc2601_...` 匹配；
> - `demo.py:381` 与 `evaluation/baseline.py:62` 都用 `row["contract"][:2]` 切品种，
>   实测 `'a2601'[:2] == 'a2'`、`'T2412'[:2] == 'T2'`，而目标表 schema 第 4 列
>   **本来就有 `product` 列**。`'sc'[:2] == 'sc'` 恰好正确，所以这个缺陷至今没暴露；
> - `sessions.PRODUCTS` 实测为 `['sc']`；
> - **两份项目文档在扩品种的立项理由上直接矛盾**（本票「必须先由人决定的事项」第九条）：
>   `docs/01-goal.md:115` 写「日频横截面……n 从几十升到数万量级」，而
>   `Merge-Plan-2.md:224` 写「不能把『50 个品种 × 900 日』直接当数万独立样本」。
>   两处均逐字核对属实。扩品种的立项理由目前正以 canonical 禁止的形式写在目标文档里，
>   这一条必须在开工前更正，否则会被引回来当作依据。
>
> 引用中的 `Merge-Plan-2.md` 位于**仓库根目录**，不在 `docs/` 下。
>
> 其余数字（909 个交易日、88 个品种、6 类时段几何、24 个停夜盘交易日等）未逐条复核，
> 使用前请自行验证。第一层起的全部步骤**被取数授权阻塞**，见文末「必须先由人决定的事项」。


2026-08-07 立，草案。前置：M2 SC Temporal Spine、M3 评价机、M7 判决语义、决定 0005。
本票的全部证据来自四路只读勘察，尚未实施任何改动；三个源仓库
（`chinese-commodity`、`AlternativeAR/Alpha-Data`、`Crawler`）本次只读与统计，未写入、
未重新抓取。计数语义的裁决另立决定 0006（见「必须先由人决定的事项」第三条）。

## 为什么

每一条已记录的判决都带着同一句阻塞理由：

```
cluster_b 维只有一组，双向 cluster 退化，已降级为 cluster_a 单向；
单品种样本的横截面相关结构无法识别
```

来源是 `src/arad/evaluation/stats.py:66` 的 `if n_a < 2 or n_b < 2:` 与
`src/arad/evaluation/kernel.py:394-399`。实测
`grep -o '"product_clusters":[^,}]*' -r artifacts/ runs/ | sort | uniq -c` 的结果
**全部为 1**，覆盖两次真实模型运行、服务运行与 baseline manifest。按决定 0005 的
`REASON_INVALIDATES`，`cluster_structure_insufficient` 只使 candidate 失效，因此这条
理由在每一条 Study 上都在压制 candidate。M3 的最小 Baseline Control 判 blocked 的
理由同样是它（`docs/DECISION_MAP.md:126`）。

更根本的是，因子研究的核心指标不可得。`src/arad/evaluation/stats.py:276-293` 的
`information_coefficient` 把 `kind` 硬编码为 `"time_series"`，并附一句
「截面 IC 需要同一时点多个标的，本样本不具备该维度」。两张票已明写这件事被推迟而非
被否定：`docs/tickets/M2.1-return-target.md:102`「多品种横截面，因此截面 IC 仍不可得」；
`docs/tickets/M9.1-evolution-app.md:83`「截面 IC（需要多标的横截面，属 M5 之后的宇宙扩展）」。

单品种是刻意的窄切片范围限制，不是数据卡住。`docs/tickets/M2-sc-temporal-spine.md:9`
写「品种：仅 SC」，`:33` 写不做「全品种 ETL」。数据侧实测：`chinese-commodity` 共 66 个
zip、802,975 个 CSV 条目、909 个交易日、区间 20221101 至 20260730，与
`artifacts/manifests/commodity_tick.json` 的 facts 完全一致；其中逐合约 tick 703,524 个、
主力连续别名 71,764 个；88 个名义品种中 57 个覆盖全部 909 天。扩展到多品种在数据获取侧
没有缺口。

## 一条特征在 N 个品种上评一次，算 1 次检验

**裁决：算 1 次检验，当且仅当 universe 在 Hypothesis Lock 中被冻结为一个面板对象，
且判决只由该面板的单一汇总估计量导出。逐品种各评一次算 N 次。两者不得混用。**

四条理由，前两条是强制的，后两条是记账一致性。

**一、截面 IC 在逐品种口径下不存在。** 逐日 IC 要求同一时点上有多个可排序标的；
逐品种跑，每个时点只有一个标的，没有可排的对象。本票存在的理由就是这个指标，因此
面板不是偏好而是唯一能定义它的形态，1 是结论而不是选择。

**二、统计分母计的是实际读取 outcome 的次数，不是品种数。**
`Merge-Plan-2.md:197`：「所有实际读取 outcome 的检验与变体」。
`docs/decisions/0005-verdict-invalidation-sets.md:94` 记录 `record_outcome_read` 在
`evaluate` 之前执行。一次面板评价读一次 outcome，因此是 1；十次逐品种评价读十次，
因此是 10。这条不需要新机制，现有实现已经这样计。

**三、一个估计量对应的多重性就是 1；它汇总了 N 个品种这件事体现在它的方差里，
而双向 cluster 已经在处理方差。** `stats.py` 的 `two_way_cluster_se` 按日期与品种两维
计算，`Merge-Plan-2.md:222-233`（§5.4）要求同时报告 date cluster、product cluster、
Independent Episode、序列相关与块长、cross-sectional effective breadth。逐品种口径是
N 个估计量，每个只需按日期成组，分母加 N。两套记账各自自洽，**被禁止的是宽松的混用**：
先跑面板、再看逐品种、报告其中最好的那个。那是 `Merge-Plan-2.md` §5.5 已禁止的事后检验。

**四、三个参考实现全部走逐品种，这不构成反例。** Alpha-Data 把品种写进分母
（连续 IC 840 加离散事件 636 合计 1,476 个检验，扩展后 2,742 个，门槛由 4.146 升至 4.285，
`AlternativeAR/Alpha-Data/docs/concise/main.tex:735-746`、`:1060-1073`）；ADAR 的分母是
「配对数 × 通道数」而一个配对就是一个（市场，品种）对
（`AlternativeAR/ADAR/src/altresearch/pairing/registry.py:139-158`）；LBG-Agent 把整个
(factor, asset) 组合当作一个 BH 族（`LBG-Agent/scripts/multi_asset_significance_probe.py:189-197`）。
它们跑的都是逐品种网格，对它们各自的对象而言分母是对的。ARAD 选面板不是更宽松的选择，
而是另一个对象，代价是**不得报告最好的那个品种**。

### 这条裁决在代价上的实测量级

换 universe 属于看过 outcome 之后的变体，按 `Merge-Plan-2.md:192`（§5.1）归入同一
outcome-exposed discovery family，`src/arad/evaluation/selection.py:174-178` 按族累计
`tests_so_far`。当前服务链的统计分母是 15（`docs/DECISION_MAP.md:417`：16 轮，第 0 版
被语义审计拦下且没读 outcome）。实测
`expected_max_abs_z`：15 → 2.0734，16 → 2.0999，25 → 2.2763，40 → 2.4511。
因此面板口径的第一次多品种评价从 2.100 起步；10 个品种的逐品种口径一次就把分母推到 25，
门槛 2.276；40 个品种推到 55 以上。扩展**继承既有分母而不是重置**，这一点必须在扩展前
算清楚而不是事后发现。

### 强制形态：面板模式不产出逐品种效果估计

§5.4 要求报告 cross-sectional effective breadth，因此不能一概压制逐品种诊断。界线是：
**覆盖数、Kish n_eff、可排序品种数照出；逐品种的斜率、t、IC 不出。**仓库里已有同形的
先例，因此这条是结构而不是约定：提案器看得到 verdict 分类但看不到效果字段
（`test_proposer_sees_verdict_categories_but_not_effects`）；M7 的 `blinded_history`
只把按判决词的**计数**放进提示词，不放逐 Study 的判决
（`docs/tickets/M7-verdict-semantics.md` 的「一次撤回」一节）。

## 实施步骤（按依赖排序）

### 第 0 层：让「读不到」不再是静默的

无需任何人工参照，可立即实施。

**S0.1 合约与别名正则统一为 `[A-Za-z]`，并让空扫描显式失败。**
`src/arad/temporal/build.py:34-35` 当前是
`_CONTRACT_RE = re.compile(r"^([a-z]{1,2})(\d{3,4})_(20\d{6})\.csv$")` 与同型的
`_ALIAS_RE`，而 M1 的 `src/arad/data_catalog/commodity.py:36` 用的是 `[A-Za-z]{1,2}`，
两处不一致。实测 `_CONTRACT_RE.match('MA609_20260730.csv')` 与
`match('IF2608_20260730.csv')` 均为 False，`scan_product_entries(root, ['2022/*.zip'], 'MA')`
返回 days=0 entries=0，而 `'sc'` 返回 days=44 entries=880。
**解锁**：本步不引入任何新品种，它解锁的是「后面每一步的失败都看得见」。当前 35 个大写
前缀品种（郑商所 27、中金所 8）会得到一个空 spine 加 INFO 级提示而不报错，这是本次勘察
里最危险的一条。

**S0.2 `product_cluster` 改用目标表已有的 `product` 列。**
`src/arad/harness/demo.py:381` 与 `src/arad/evaluation/baseline.py:62` 都用
`row["contract"][:2]` 切品种，而 pyarrow 读
`data/spine/sc/target_sc_rv_next_session.parquet` 的 schema 第 4 列即 `product: string`。
88 个品种中 10 个是单字母小写代码（a、b、c、i、j、l、m、p、v、y）加一个单字母大写 T，
实测 `'a2601'[:2] == 'a2'`、`'c2509'[:2] == 'c2'`、`'T2412'[:2] == 'T2'`。sc 下
`'sc'[:2] == 'sc'` 恰好正确，因此这个缺陷至今没有暴露。
**解锁**：双向 cluster 的分组正确。必须先于任何以 cluster 数为依据的结论，否则上面全部
推断建立在伪造的分组上。

**S0.3 `dominant.py:119` 与 `:126` 调用 `ContractCode.parse` 时传入 `trading_day`。**
`src/arad/temporal/contracts.py:47-62` 对三位年码在缺交易日时主动抛 ValueError（实测
`ContractCode.parse('MA609')` 抛「使用三位年码，缺少交易日无法还原世纪与十位年；拒绝猜测」），
因此主力选择对全部 27 个郑商所品种硬失败。传入交易日后实测全样本 10,879 组（三位码，年月）
全部解析成功、零错误，交割月相对交易日的距离全部落在 -1 至 24 个月。
**解锁**：本票不引入郑商所品种，但这一步把 M8.1 的成本由「未知」变为「已量」。

### 第 1 层：品种参照与 session 结构（被人工授权阻塞）

**S1.1 录入第一批品种的四项人工参照。**`src/arad/temporal/sessions.py:361` 是
`PRODUCTS: dict[str, ProductReference] = {"sc": SC}`，实测 `list(PRODUCTS.keys()) == ['sc']`。
每个新品种需要合约乘数、最小变动价位、时段几何与**非空的权威出处**，
`sessions.py:86-91` 的 `__post_init__` 在出处为空时抛异常。时段几何本次已从 tick 实测
归纳为 6 类，sc 所属的一类（夜盘至 02:30，含 au/ag）已存在；若第一批限于小写前缀，
最多再录 3 张表（夜盘至 01:00 共 10 个品种、夜盘至 23:00、仅日盘），中金所那两类全是
大写前缀，不在本票内。该归纳与
`AlternativeAR/Alpha-Data/data/cn_futures/product_specs.parquet` 的
(exchange, night_end, has_night) 分组独立互证，两者完全一致。
**解锁**：`PRODUCTS` 能有第二个条目。**这一步被取数授权阻塞**，见下文第一条。

**S1.2 把写死的 `night`/`day` 两个 session 名与 seq 0/1 通用化。**
六处：`build.py:296-301`（实测对无夜盘品种表调用 `table.session('night')` 抛
`SessionTableError`）、`bars.py:283` 的 `for name, seq in (("night", 0), ("day", 1))`、
`bars.py:223` 的 `w.name == "day"`、`build.py:130-137` 的 seq 判别、`pipeline.py:241` 的
`night_open_sod` 判别，以及 `bars.py:64-69` 的 `BARS_DAILY_SCHEMA` 把两个 session 展开成
六个固定列。
**解锁**：24 个仅日盘品种与 43 个夜盘 23:00 收盘品种。
**代价**：schema 变更使 sc 已物化的 909 天日频 bar 必须重建，全部数据集指纹失效并需要
重新登记。

**S1.3 修复夜盘不跨零点时声明收盘时刻永不被校验。**`build.py:130-137` 以 sod 43200 为界
把夜盘拆成 evening 与 morning，morning 为空时 `night_close_sod` 置 None，而
`build.py:290` 的校验循环用 `if env.get(k) is not None` 跳过 None。实测传入 21:00/22:00/23:00
三笔夜盘 tick，`_observed_envelope` 返回 `night_close_sod=None`；传入 sc 型跨零点数据返回 9000。
受影响的是 43 个 `night_end=23:00` 的品种，占有夜盘品种的 77%。
**解锁**：「权威参照加实测校验」这条原则在新增品种上真正生效。不修这一条，新录入的时段表
等于没有校验。

**S1.4 全市场共用一张停夜盘日期表，并给 calendar 加正向断言。**
`calendar.py:115-144` 的 `night_gap_findings` 只遍历 `days_with_night`，因此只报告
「有夜盘但间隔异常」，不报告「该有夜盘却没有」。实测 909 个 `_days` JSON 中 24 个交易日
`night_open_sod` 为 None，逐日核对与前一交易日的自然日间隔，22 个大于 3 天（长假）、
2 个为 2 天（2023-04-06 清明、2025-01-02 元旦），反向检查全部 22 个长假后的交易日无一
有夜盘，例外为 0。两个独立来源一致表明停夜盘是全市场统一而非品种级：`product_specs` 中
全部 56 个有夜盘品种的 `night_day_ratio` 均为 0.96，sc 在同一 125 天窗口独立统计为 120/125 = 0.96。
**解锁**：区分「假期停夜盘」「归档缺文件」「该品种当晚零成交」，三者当前都表现为
`night_present=False` 并最终变成 no-trade 标签。

**S1.5 目标名与主力视图 schema 参数化。**`targets.py:146`、`:163`、`:177` 的
`name="sc_rv_next_session"` 等改为按 `product.product` 拼接；`dominant.py:20-33` 的
`DOMINANT_SERIES_SCHEMA` 补 `product` 列，与 `bars.py:22`、`:48`、`targets.py:49` 的做法
一致。sc 的目标名参数化后取值不变，因此 M2.1 引入的 `target_name` 进 digest 一事不受影响。
**解锁**：多品种产物不互相覆盖。`bars.py`、`targets.py`、`pipeline.py` 其余部分已按
`ProductReference` 参数化（`pipeline.py:193,456,594` 均为 `PRODUCTS[cfg["product"]]`，
`:374` 与 `:430` 的产物名由 `product.product` 拼接），无需改造；交易日历从全归档条目日期
构造（`calendar.py:38-60`），与品种无关，不需要新日历。

### 第 2 层：截面单位与 universe 的规格化

**S2.1 定义截面单位。**候选是 `(trading_day, session_name)` 或一张声明的公共 cutoff 网格。
当前 `date_cluster` 是 `str(trading_day)`，会把同一交易日的夜盘与日盘并到一组，不能直接
当截面单位；而 `targets.py:315` 的窗口由各品种自己的时段表导出
（`windows = product.sessions.windows(trading_day, prev_trading_day=prev)`），不同交易所的
session 边界不同，因此不存在现成的共同 cutoff 网格。实测 sc 目标表 1,816 行、1,816 个互异
`decision_time`，每个 `decision_time` 恰好 1 行。
**解锁**：截面 IC 的分组键、面板对象的定义本身，以及 `configs/pm_index.yaml:37-38` 那个
写死的 `sc:` 配置键（被 `pm_pipeline.py:142` 与 `:587` 直接索引）。这三件是同一个问题，
必须一并确定。

**S2.2 `ProposalSpec.universe` 由自由字符串升为结构化对象，并新增 `universe_mode`。**
实测 `ProposalSpec.model_fields` 为 9 项、无任何版本字段（`FeatureSpec` 有 `spec_version`
而它没有），`universe: str` 只有非空校验（`src/arad/registry/specs.py:112`）。结构化对象承载
品种集合、成员资格规则与生效时点；`universe_mode ∈ {panel, per_product}` 进 `content_id`。
**解锁**：上文的裁决由约定变成结构。Hypothesis Lock 冻结项本就含 universe
（`Merge-Plan-2.md:188`），但当前的字符串表达不了面板与逐品种的区别，因此这条裁决今天
无法被冻结、也无法被审计。
**代价与前置**：全部已记录 `ProposalSpec` 的 `content_id` 改变，已记录的 `HypothesisLock`
按 `proposal_id` 指向的旧 id 无法由新 schema 重算。本步必须同时引入
`PROPOSAL_SPEC_VERSION`，并按 M7 的先例处理（账本只增不改，口径按版本区分）。旧记录是
标注为不可重算还是回填，需要人裁定。

### 第 3 层：求值与评价

**S3.1 解释器的序列容器加品种维，重写 demo 的数据装配。**
`src/arad/features/interpreter.py:110` 的 `series` 键是 `(Source, field)` 二元组，
`evaluate_series` 只接受一条决策时点列表；`demo.py:270-284` 的 `_load_sc` 把目标表全部行按
`label_end` 排序后汇入单条 `BarSeries`。实测构造逐小时、取值交替 1.0 与 100.0 的
`BarSeries`，`op=mean/window=21600` 的规格返回 **50.5**，不报错也不判无定义。
**解锁**：多品种取值不再静默混算。这是多品种下最典型的无声错误形态，也是本票风险的主体：
加品种不会让现有测试变红（实测 `pytest tests/ -q` 当前 **642 通过**；
`tests/contracts/test_sessions.py:55` 是唯一断言 `PRODUCTS` 内容的地方，只查单键存在、
不查长度）。
**代价**：序列键的形状是解释器的合同，`INTERPRETER_VERSION` 须由 0.3.0 升至 0.4.0
（`interpreter.py:35`，取值写进 `:340` 的 payload）。不升版本，多品种求值会被盖上一个
语义与之不符的版本戳。

**S3.2 `FeatureSpec` 表达「同一条规格在 universe 的每个品种上各求一次」。**
实测 `FeatureSpec.model_fields` 与 `Step.model_fields` 里没有任何分组构造。
**明确排除把品种编进字段名的捷径**：`interpreter.py:36-39` 与 `demo.py:337` 对 pm_market
用 `cand:iran:p` 这种做法，照搬到品种上会把一条特征拆成 N 个 `feature_id` 与 N 个
`content_id`，「同一条特征跨品种」不再是一个可审计的对象，与本票的面板裁决直接冲突。
**解锁**：面板对象在规格层有名字。
**代价**：`FEATURE_SPEC_VERSION` 由 0.3.0 升至 0.4.0；
`tests/contracts/test_feature_spec.py:260-271` 钉住的金标 `content_id`
（`89500f58...78f4ac`）会立即失败，这是预期结果而不是缺陷，
`src/arad/features/spec.py:24-27` 已声明新增字段会改变全部 content id。
**同时必须裁定 codegen 的处理方式**：本仓库把生成代码当作与解释器并列的一条路径，
并用逐位一致的等价测试守着（M4.2 的 rank_pct 跨 240 小时逐点比对，差值上限 1e-12）。
新的分组构造要么由 `codegen.py` 支持并补一条等价测试，要么在生成期**显式拒绝**携带该构造
的规格。二者必居其一，`CODEGEN_VERSION` 相应由 0.1.0 升级。默认什么都不做会让解释器与
生成代码在多品种上静默分歧，那与本票要防的是同一类无声错误。

**S3.3 截面 IC 与时序 IC 并列出具，不做替换。**逐日 IC，对日序列求 ICIR，
按 `t = ICIR × sqrt(D)` 推断并给 HAC t；pooled RankIC 另作一个口径并列。该数学定义取自
`AlternativeAR/Alpha-Data/docs/concise/main.tex:620-634`。
`stats.py:288` 的 `kind="time_series"` 与 `:289-292` 的说明文本**原样保留**：它们已经进入
证据记录，改动它们等于改动账本内容。仓库里现成的正确形态是 `kernel.py:464-465`，
分位组合与 sign_unit 始终同时记录、不做二选一。
**解锁**：因子研究的核心指标第一次有定义。这一步必须先于任何多品种评价，否则多品种面板
送进现有函数会得到一个 pooled Spearman 却仍标为时序 IC，而读者会按截面 IC 的直觉理解它的
量级与显著性，这正是 M9.1 当初添加那句说明要防止的误读。

**S3.4 新增 `min_product_clusters` 下限，并把置换检验的块单位改为截面单位。**
`stats.py:66` 的 `n_a < 2 or n_b < 2` 是唯一判据，因此品种数达到 2 时退化提示直接消失。
实测同一组 x/resid/dates：k=1 时 degenerate=cluster_b、se=0.16343；k=2 时 degenerate=None、
se=0.32423；k=3 时 0.28090；k=5 时 0.23969。**提示消失是一次错误的放行信号**：
Cameron-Gelbach-Miller 双向 cluster 在 2 至 3 组上的渐近性质并不可靠，而标准误在 k=1 与
k=2 之间变了两倍。新闸门与 `kernel.py:171` 的 `min_clusters: int = 10` 并列。
置换检验方面，`kernel.py:336` 以 episode 为整块置换单位，而 `episode.py:37-44` 的
`episode_id` 以 product 开头，多品种下同一交易日会被拆成 N 个块，跨品种同日的相关结构在
置换中被打散，零分布因此偏窄；`kernel.py:369` 的 `placebo_exceed_rate > 0.1` 是
`REASON_INVALIDATES` 里通往 NULL 判决的唯一路径，块被拆细会使否定结论变少、判决整体偏
宽松。此外 `kernel.py:318-322` 的 `min_clusters` 数的是 `len(set(episodes))`，N 个品种会把
同一批交易日的 episode 数放大 N 倍，功效闸门被稀释。
**解锁**：防止 k=2 的假放行，防止零分布偏窄，防止功效闸门被品种数灌水。
（本条中「置换零分布偏窄」是按代码结构做的推断，合成数据里没有内建的跨品种相关，演示
不出真实效应，标注为未做数值验证。）

**S3.5 `EvaluationRow` 增截面分组键，`EVALUATOR_VERSION` 由 0.3.0 升至 0.4.0。**
`kernel.py:180-222` 的 `digest()` 逐行序列化全部字段，
`tests/contracts/test_evaluator.py:174-185` 守着 digest 的确定性与敏感性。
**代价**：全部既有 evidence 记录与新记录不可比，处理方式按 M7 的先例声明。

### 第 4 层：控制（属 M5，本票只声明依赖）

**S4.1 Baseline Control Library 的截面版本、截面去均值与中性化原语、`residualise`、多元回归。**
`Merge-Plan-2.md:405` 把 Baseline Control Library 排在 M5；`docs/DECISION_MAP.md:464-466`
记录 `residualise` 仍抛 `StepNotImplemented`（解释器不持有控制序列），回归仍是一元的。
**这一步不解锁而是限制**：在它完成之前，多品种面板只能做未中性化的汇总回归，共同因子会
伪装成截面信号。动量、反转、期限结构、持仓、成交量、流动性正是标准横截面因子，§3.1
要求另类因子不得只是量价代理，这条约束在截面下才真正可检验。

## 本票不做

- **郑商所 27 个品种与中金所 8 个品种**，另立 M8.1。郑商所有三个独立阻塞：大写前缀
  （S0.1）、三位年码（S0.3）、夜盘 TradingDay 标注口径。第三条实测：郑商所把夜盘 tick 的
  TradingDay 标为前一交易日，单个 CSV 内含两个 TradingDay 值（`MA609_20260730.csv` 为
  20260729:14298 与 20260730:26631，而 `sc2612_20260730.csv` 为 20260730:63560 单值），
  `src/arad/temporal/ticks.py:73` 的单值断言直接抛 ValueError。受影响 14 个品种：
  CF、CY、FG、MA、OI、PF、PL、PR、PX、RM、SA、SH、SR、TA。修复形态是在 `ProductReference`
  上加一个按交易所的 `trading_day_stamp` 约定字段并放宽该断言，自然日锚定逻辑本身已经算对
  （`sessions.py:157-172` 的 `natural_date_windows` 对郑商所夜盘返回的锚与偏移是正确的），
  不需要结构性改造。中金所另需裁决决策时点语义，见下文第五条。
- **交易成本与容量模型（M5）**。本票**不解锁 candidate**：`cost_model_missing` 对每一条
  Study 仍然成立。M8 做的是把 `cluster_structure_insufficient` 这条阻塞换成一条更严的闸门
  （`min_product_clusters`），不是把它去掉。
- **Alternative Factor 的任何截面主张**。解释器只接入 `commodity_bar`，`pm_market` 与
  `cls_telegraph` 未接入（`docs/DECISION_MAP.md:462-463`），因此扩品种只会让 Baseline
  Control 的截面版本先跑起来，Alternative Factor Inventory 一条也不会增加。决定 0004
  连带约束 3 记录的功效限制与 universe 宽度正交：商品机制在 Polymarket 上是 2026 现象，
  discovery 段仅占成交 0.84%，**扩品种不能被当作解决另类数据功效不足的手段**。
- **分钟频截面**。tick 密度足以支撑 1 分钟 bar（抽样 28 个品种每分钟 tick 数在 50 至 119
  之间，接近 500 毫秒快照的理论上限 120），但截面单位一旦定在分钟上，跨交易所的 session
  边界差异会成为主要噪声来源。
- **按日期分版本的时段表**。909 日历史里临时时段调整为零，现有代码路径对它零经验。
- **全局优质品种表**。M2.5 已裁决成员资格不得由流动性判定、不建立全局筛选表、门槛逐
  Study 冻结（`docs/DECISION_MAP.md:76-93`），同一原则适用于品种。
- **任何写入或重新抓取**。三个源仓库严格只读。

## 出口条件

- `universe_mode` 的两种取值各有合同测试，且有两条负向测试：panel 模式下逐品种的斜率、
  t、IC 不出现在任何产出与账本 payload 里；per_product 模式下 N 次评价使统计分母增加 N
  而不是 1；
- 截面 IC 与时序 IC 在同一份证据里并列且 `kind` 互异；负向测试：某个截面单位上只有一个
  品种时截面 IC 无定义，而不是退化成时序 IC；
- 无夜盘品种与 23:00 收盘品种各有一条 spine 构建测试；**23:00 品种的夜盘收盘校验必须真的
  执行**（负向测试：声明 22:00 而实测 23:00 必须报 finding，当前实现会静默通过）；
- 主力规则在新增品种上与来源别名的一致率作为 QA 对照报出，别名不参与选择（sc 上实测
  898/908 = 98.9%，分歧集中在 2024-10 与 2026-01 两段，见
  `artifacts/manifests/sc_temporal_spine.json` 的 `dominant.alias_agreement`）；
- sc 的 909 天产物按新 schema 重建，新指纹登记且旧指纹在 manifest 中保留并标注版本；
- 五个版本常量的升级各自有理由记录，实测当前取值如下：`PROPOSAL_SPEC_VERSION`（不存在，
  本票新增）、`FEATURE_SPEC_VERSION` 0.3.0 → 0.4.0（`spec.py:30`）、
  `INTERPRETER_VERSION` 0.3.0 → 0.4.0（`interpreter.py:35`）、
  `CODEGEN_VERSION` 0.1.0 → 0.2.0（`codegen.py:16`）、
  `EVALUATOR_VERSION` 0.3.0 → 0.4.0（`kernel.py:29`）；
- 全仓 ruff 与 pytest 通过（当前基线 642 通过）；`docs/DECISION_MAP.md` 更新；
  `docs/01-goal.md:115` 按下文第九条更正。

## 必须先由人决定的事项

**一、合约乘数与最小变动价位的取数授权。这属于取数流程，需要单独的人工授权，不是本票的
工程步骤。** 实测三个只读源仓库中都不存在任何合约规格元数据文件：
`find /Users/xinyu/Code/AR-Polymarket/Crawler /Users/xinyu/Code/AR-Polymarket/chinese-commodity -type f \( -iname '*合约*' -o -iname '*contract*' -o -iname '*spec*' -o -iname '*multiplier*' -o -iname '*乘数*' -o -iname '*品种*' \)`
返回空；`chinese-commodity` 只有 tick zip、README、`.gitattributes`、3 个 `.gitkeep` 与一份
只声明 15 个 tick 字段的 `dataset_infos.json`；`Alpha-Data` 的 `product_specs.parquet`
经 schema 检索 mult/tick/size/unit/lot 关键字为 NONE。因此这些参照必须从交易所公告引入，
是新的取数。M2.5 已确立先例：acquisition 不作为前置条件，需单独申请授权。
**本次从 tick 实测出的乘数（sc=1000、ag=15、cu=5、rb=10、i=100、m=10、jd=10、si=5、
ec=50、IF=300、T=10000、lc=1）只能作核对，不能作出处**，`sessions.py:296-302` 的
reference 字符串与 `Merge-Plan-2.md:297` 的数据建设原则第 6 条都要求权威参照而非数据反推。
`SessionTable.__post_init__` 在出处为空时抛异常，因此这是硬闸门：在人工提供之前，
`PRODUCTS` 一个新条目也加不进来，本票过不了第 1 层。

**二、第一批品种的清单。这是一次 universe 冻结，不是工程选择。** 可核实的筛选条件如下，
组合方式与最终名单需要人定：88 个名义品种中小写前缀 53 个、大写 35 个（本票只取小写）；
LR、ZC、JR、RI、PM 在全样本期为纯空壳（小文件占比 100%），WH 98.9%、bb 82.7%；
ao、ec、lc、si、ad、ps、pt、pd 在样本期内才上市（755、713、733、872、279、385、163 天）；
57 个品种覆盖全部 909 天。**不能用文件存在性做筛选**：`agg3.py` 的 gaps 列对全部 88 个
品种均为 0，包括那 5 个纯空壳品种，文件级缺口只衡量文件存在与否、不衡量内容。
后上市品种若不给出显式的 listed-from 规则会重现 sc manifest 已记录的幸存者偏差；只取
909 天全覆盖的品种可以回避该问题。按决定 0004 的同一逻辑（选择变量与目标结果相关时选择
偏差变成估计偏差），若成员资格由历史流动性归纳得出，前向门可能需要新增 `universe_freeze_at`。
交易所上市与退市是外生的，流动性筛选不是。
另需一并处理：`program.md:235` 指向的 `configs/universe.yaml` 在 `configs/` 下不存在
（实测只有 `data_sources.yaml`、`pm_index.yaml`、`spine_sc.yaml`）；
`docs/archive/02-plan.md:131-132` 的「按日均成交量与有效 tick 数动态筛选、新上市品种
60 个交易日后进入截面」与 M2.5 的裁决直接冲突，需要作废或改写。

**三、把 1 次与 N 次的裁决立为决定 0006。** 本票给出的答案与三个参考实现全部相反
（它们都走逐品种且分母随品种数相乘），因此不能只写在票里，需要一份可被引用、可被推翻的
决定。

**四、跨品种符号一致率是否作为闸门。** Alpha-Data 用它把多品种当作一致性检验而不是额外
检验（跨 5 品种 × 6 视界共 30 个格，纯噪声下期望 57%，「跨品种符号稳定 ≥ 60%」为因子七关
之一，`main.tex:800-812`、`:1046-1052`）。若采纳，形态是决定 0005 的
`REASON_INVALIDATES` 新增一个键映射到 `{"candidate"}`：只能使结论失效、不能使其成立的
闸门，在预注册下不抬高 max|z|，因此不增加零假设带的计数。是否采纳需要批准。

**五、中金所 8 个品种（IC、IF、IH、IM、T、TF、TS、TL）是否属于本项目的研究范围。**
它们四位码、无夜盘、909 天全覆盖，工程成本比郑商所低（只需 S0.1 加两张时段表）。这是研究
口径选择（金融期货而非商品）而不是数据限制；**若不显式裁决，它们会因为「大写前缀」被
连带排除，那等于让一个实现细节替人做了研究范围决定**。裁决前还需解决决策时点语义：
`targets.py:103` 的 `decision_time = window.open - 60s`，商品品种 open=09:00 得
cutoff=08:59:00，恰好等于实测的竞价成交打印时刻（`day_open_sod=32340` 出现在 775 日），
as-of 的严格小于把它排除在信息集之外；中金所按 `day_bar_mode=240` 推断 open=09:30，
cutoff=09:29:00，若交易所规则的竞价窗口为 09:25-09:30 则 cutoff 落在竞价窗口内部。
同一个 `execution_lag_seconds=60` 在两类品种下经济含义不同，而该裁决依赖尚不存在的交易所
规则来源。

**六、l、pp、v 的 F 后缀平行合约序列是否同一标的。** 实测 36 个互异代码、20251201 至
20260730 共 161 天、文件中位 2,022,204 字节。现有正则不匹配所以不会污染现有结果，但这三个
品种若进第一批，需要人工判定该序列是否参与主力选择。若不愿裁决，把这三个品种排除在第一批
之外。

**七、Alpha-Data 与 tick 归档矛盾时以哪个为权威。** `qc_summary` 中 PM、RI、WH 为
n_days=124、missing_days=1，而 tick 归档中这三个是纯空壳。这说明两者是**独立来源**而不是
校验关系。同时 `Alpha-Data/data/cn_futures` 不能作为捷径：只覆盖 2026-01-05 至 2026-07-13
共 125 个交易日（909 天的 13.7%），`product_specs` 无乘数与最小变动价位，
`dominant_table` 的 rule 全部为 `provider_9999_continuous`，即供应商当日口径的事后别名，
正是 `dominant.py:1-8` 声明「只用于报告一致率，不参与选择，也不用于调参」的来源类别；
其 `night_end` 由分钟 bar 众数反推（`build_cn_futures_db.py:174-182`），session 划分只是
`hour >= 8 and hour <= 16` 的粗判（同文件 231 行），日盘开盘统一写死 09:00
（`alpha_data/cn_futures/sessions.py:26`）。它可以做交叉校验，不能做权威参照。

**八、已记录 `ProposalSpec` 的 `content_id` 变更如何处理。** 见 S2.2。标注为不可重算，
还是按新 schema 回填一次并同时保留旧 id，需要裁定。

**九、`docs/01-goal.md:115` 的更正。** 该行把日频横截面的收益写成「n 从几十升到数万量级」，
而 canonical 的 `Merge-Plan-2.md:224` 明确禁止这种读法。按本票的答案它在两处都错：
Episode 缺省按交易日成组，`kernel.py:318-322` 的功效闸门读 Episode 数而不是行数，因此
Episode 与日期维仍是约 909；截面带来的改善是逐日估计噪声下降，不是独立样本数增加。
`Merge-Plan-2.md:537`（§14）虽把 `01-goal.md` 列入需归一化文档，列举的修正项不含这一条。
**扩品种的立项理由目前正是以被禁止的形式写在目标文档里**，这一条必须在本票开工前更正，
否则会被引回来当作依据。

**十、Alternative Factor Inventory 的覆盖目标按什么计数。** §3.2 要求最多 5 个低相关因子
且至少覆盖两个机制族与两个时域。若按品种计数，同一机制在 10 个品种上的 10 个实例可以凑满
5 个而完全不满足机制族覆盖要求。建议按 (mechanism, target, horizon, universe) 计一条，
与「Signal 必须绑定 target、horizon、direction 和 universe」的既有约定一致
（`docs/ENGINEERING_PROMPT.md:47`），但这需要明文裁决。

## 新增的阻塞事项

- **`min_product_clusters` 的阈值需要先验来源。** 双向 cluster 在 2 至 3 组上的渐近性质
  不可靠，但「至少几组」是我无法从本仓库数据定出的数。按 M6.2 对 `max_leverage` 的同一
  理由，事后定阈值等于看过结果之后定阈值，因此必须在第一次多品种评价之前由人凭先验定下。
- **截面广度与功效的关系没有可用估计。** 功效改善来自 `sd(IC_d)` 随可排序品种数下降，
  下降幅度由跨品种残差相关决定（LBG 的 `eff_N = k / (1 + (k-1) × rho_bar)`，
  `multi_asset_significance_probe.py:269-272`）。`rho_bar` 在本仓库从未测过，因此
  「加到多少个品种才够」目前无法回答，第一批规模只能是一个待检验的选择。
- **时段表的存在形式未定。** 当前是 Python 源码常量（`sessions.py:295-328`），加品种意味着
  改源码而不是加配置，且没有任何机制保证新增条目的正确性。改成带版本与出处的数据文件是一次
  结构变更，需要单独裁定。
- **临时时段调整无法表达。** 单一 `SessionTable` 表达不了按日期分版本；
  `verify_session_table`（`sessions.py:257-288`）与 `_session_verification_findings`
  （`build.py:280-344`）产生的都是 WARNING 级 QualityFinding。若某个新品种在 909 日区间内
  发生过夜盘时段变更，实测包络会在变更点两侧各报一次 warning，而没有正确的表可用。
  相关的已知事实：郑商所日盘末 tick 从 14:59:59（2022、2024）变为 15:00:00（2026），
  无夜盘品种首 tick 从 08:55 变为 08:59，按后期约定录表会触发
  `sessions.observed_outside_declared`。
- **`Turnover` 是否含乘数的约定字段必须现在就加，即使第一批不触发。** 实测上期所、大商所、
  能源中心、广期所、中金所的 Turnover 已含乘数，郑商所不含（MA/TA/SR/OI 的比值约 1.00）。
  第一批若全为小写前缀则不触发，但 `ProductReference` 中没有该字段，M8.1 引入郑商所时
  所有成交额、VWAP、名义额口径特征会**系统性错一个乘数倍且不报错**。
- **盘后 tick 的 OUTSIDE 判据是按 sc 的 15:00 收盘调出来的。** 实测 909 个 `_days` JSON 中
  903 日存在时段表外 tick，分钟分布从 15:10 延伸到 15:58，峰值 15:16（123 日）、
  15:14（105 日）、15:15（90 日），另有 18:37、18:41、19:06、19:15 各 1 日。国债期货日盘
  255 分钟，比商品多 30 分钟，判据与「盘后结算快照」的解释都需要按品种重新确定。
- **从 tick 反推时段表存在结构性盲区，且误差正好等于决策时点的位移。** sc 的 909 日实测：
  声明的竞价窗口 20:55-20:59 与 08:55-08:59 内没有任何 tick，反推只能得到 20:59 与 08:59，
  与真实开盘差 1 分钟、与竞价起点差 5 分钟；而决策时点定在开盘前 60 秒。因此**新品种的
  时段表一律不得由数据反推**，这条约束的代价在本票中就是第一条人工裁决。