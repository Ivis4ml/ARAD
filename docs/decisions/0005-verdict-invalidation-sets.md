# 决定 0005：判决由「每条理由使哪些结论失效」推出

- 日期：2026-08-07
- 状态：已采纳
- 触发：M6.2 实跑发现 `Verdict.NULL` 从未被任何代码路径产出过，经独立评审
- 影响：`kernel.py` 的判决导出；`Verdict` 词表的可达性；Atlas 判决分类图的口径

## 事实

判决原本这样导出：

```python
verdict = Verdict.BLOCKED.value if blocked else Verdict.CANDIDATE.value
if blocked and any("低于预注册下限" in b for b in blocked):
    verdict = Verdict.UNDERPOWERED.value
```

`Verdict` 的注释写着「五个值，全部是合法完整产出」，而 `null` 在全仓没有任何产出路径。
成因是 `cost_model_declared=False`（M5 未做）对每一条 Study 都成立，因此
`blocked` 恒非空，判决恒为 `blocked`。

实跑的四条 Study 全部记为 `blocked`，其中 auto-study-1 的 t = −0.030、
置换检验 exceed 0.980、506 行有效样本。这是一个干净的、有功效的否定结论，
而 `blocked` 在词表里的意思是「判不出来」。整套系统存在的理由正是让否定结论可信，
它却恰恰记不下否定结论。

## 裁决

判决不再由「有没有阻塞理由」推出，而由**每条理由使哪些结论失效**推出。
线性优先级表达不了这件事：同一条理由对 candidate 与对 null 的效力可以不同。

```python
REASON_INVALIDATES: dict[str, frozenset[str]] = {
    "insufficient_sample":                    {"candidate", "null"},
    "not_identified":                         {"candidate", "null"},
    "cost_model_missing":                     {"candidate"},
    "cluster_structure_insufficient":         {"candidate"},
    "single_point_influence_candidate_only":  {"candidate"},
    "single_point_influence_both":            {"candidate", "null"},
    "placebo_failed":                         frozenset(),
}
```

推导：样本不足则 underpowered；否则若有理由使 null 失效而同时存在 `placebo_failed`，
落到后续分支；若 `placebo_failed` 存在且 null 未被使失效则 null；
否则若 candidate 被使失效则 blocked；否则 candidate。

三条分类的理由：

**未声明成本模型只使 candidate 失效。**断言「该机制与标的没有统计关系」不需要
交易成本模型。若它同时挡住 null，则在 M5 完成之前 null 结构性不可达，
而 M6/M7 的出口判据要求 null 可覆盖。

**cluster 退化只使 candidate 失效。**标准误被低估只会**高估**显著性，
因此只可能推翻 candidate；真实标准误更大只会让 |t| 更小，null 反而更强。
且置换检验根本不使用标准误（它按 `abs(s) >= abs(actual)` 双侧比较量级）。

**单点影响是方向感知的。**一个高杠杆点既能制造效应，也能**遮蔽**效应，
因此「估计不可信时，没效应同样不可信」这个担忧是真实的。但两侧的判据不同：
守 candidate 问「这一点是否撑起了效应」，守 null 问「删掉它之后 |t| 能否够到显著性」。
后者取 `|t| + DFBETAS >= 2.8`（一阶近似，删点同时也会改变标准误本身）。
对称地把两者都判为「什么都断言不了」，会让每一个干净的 null 自己把自己作废 ——
这正是旧口径 `|DFBETA| / |β̂|` 造成的效果：它在 β̂ → 0 时发散，
于是每个真 null 都会自动给自己贴上「单点影响过大」。M6.2 已修掉那个分母。

## null 必须携带它的排除界

否则 null 只是「没找到」而不是「排除了什么」。结果里新增 `null_exclusion_bound`，
记录本次达到的 `mde_at_2p8_se` 与一句限定：这是**相对于该 MDE 的 null**，
不是对任意小效应的排除。M5 的 `economic_bound`（`ConfirmatoryLock` 中现为空）
将来会给 MDE 一个外部参照；在那之前，null 的强度逐 Study 不同，证据里要能读出来。

## 泄漏边界：披露的是聚合计数，不是逐 Study 的判决

判决词对提案器可见是设计已声明的披露（`blinded_history` 的注释写着
「只给判决分类与分母」，且 `verdict` 在 `PROPOSER_VISIBLE_FIELDS` 白名单上，
既有合同测试断言提案器应看到 `null` 分类）。让 `null` 可达，使这个此前近乎常量的
计数变得有信息：它告诉提案器「这些机制被证否了」，不含方向（置换检验对 |slope| 双侧），
不含量级（推导只依赖分类闸门的越界与否）。

**要害在披露的边界。**`blinded_history` 只把按判决词的**计数**放进提示词，
不放逐 Study 的判决。一旦逐 Study 的判决也进了提示词，提案器就能把机制与结果
一一对上，那才是在检验统计量上爬山。新增合同测试钉住这条边界。

必须钉死的第二条不变量：**判决只能是理由种类的函数**。一旦推导条件化到任何
未经预注册闸门表达的效应数值（例如「|t| < 0.5 才算 null」，或把 null 分成强弱两档），
判决词就开始编码一次新的量级比较，那才是泄漏。因此 auto-study-3
（exceed 0.305 的弱非检出）与 auto-study-1（exceed 0.980 的强排除）
必须共用同一个词，强度差异只留在证据里给评价机与人看。这是盲化的代价，明码接受。
`derive_verdict()` 因此只接受种类列表，遇到未登记的种类直接报错。

## 两本分母的计数语义不变

已逐处确认：`record_outcome_read` 在调用 `evaluate` **之前**执行，与判决无关；
`ledger.py` 的触发器（`statistical_denominator_no_delete/no_update`）禁止回缩；
提案分母在提案时刻记录；`atlas/project.py` 的 `counts_toward_denominator` 取自
快照中的 `outcome_read` 事件是否非空，`selection.py` 的 `selection_band` 只消费
该字段与 `tests_so_far`，判决词只被显示、从不被计数。把某些 blocked 重新标为 null，
不会让任何 Study 跨越「读过 / 没读过 outcome」这条计数边界。

一个二阶效应记录在案但不构成偏差：若将来 null 触发与 blocked 不同的调度
（例如被证否的机制不再排新版本），搜索过程的走向会改变，但统计分母如实记录
每一次 outcome 读取，自适应搜索的代价仍被完整计入。

## 账本只增不改

已记录的四条 `blocked` 判决按旧语义永久成立，新语义只适用于新 Study。
按新规则重算，四条**全部**会是 `null`（t 分别为 −0.030 / −0.258 / −1.093 / +0.515，
`|t| + DFBETAS` 分别为 0.32 / 1.51 / 1.87 / 1.08，均够不到 2.8，
因此单点影响都只使 candidate 失效）。Atlas 的判决分类图会混排两种语义的记录，
口径以 `evaluator_version` 区分：0.2.0 及以前为旧语义，0.3.0 起为本决定。
