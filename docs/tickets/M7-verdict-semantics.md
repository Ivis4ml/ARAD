# 工程票 M7：让否定结论能被记下来

2026-08-07 立。前置：M6.2。配决定 0005。

## 为什么

`Verdict` 词表注释写着「五个值，全部是合法完整产出」，而 `Verdict.NULL`
**从未被任何代码路径产出过**。判决原本是
`BLOCKED if blocked else CANDIDATE`，而 `cost_model_declared=False`（M5 未做）
对每一条 Study 都成立，因此 `blocked` 恒非空。

第一次真实模型自主运行的四条判决全部记为 `blocked`，其中 auto-study-1 的
t = −0.030、置换检验 exceed 0.980、506 行有效样本。这是干净的、有功效的否定结论，
而 `blocked` 在词表里的意思是「判不出来」。整套系统存在的理由正是让否定结论可信，
它却恰恰记不下否定结论。

## 改法

见决定 0005。判决由**每条理由使哪些结论失效**推出，不再由「有没有阻塞理由」推出。
线性优先级表达不了「同一条理由对 candidate 与对 null 的效力不同」，
而三条真实记录恰好需要这个表达力。

`derive_verdict(kinds)` 只接受种类列表，遇到未登记的种类直接报错。
结果里新增 `blocked_reason_kinds`，判决只读它；文本里的数字不进推导。

## 实测

按新规则重算四条已记录判决：

| study | t | DFBETAS | \|t\|+DFBETAS | 旧 | 新 |
|---|---|---|---|---|---|
| auto-study-1 | −0.030 | 0.29 | 0.32 | blocked | **null** |
| auto-study-2 | −0.258 | 1.25 | 1.51 | blocked | **null** |
| auto-study-3 | −1.093 | 0.78 | 1.87 | blocked | **null** |
| auto-study-4 | +0.515 | 0.57 | 1.08 | blocked | **null** |

四条的 `|t| + DFBETAS` 都够不到 2.8，因此单点影响都只使 candidate 失效。
这四条本来就是四个干净的否定结论，各自带着自己的排除界。
账本只增不改：已记录的判决按旧语义永久成立，口径以 `evaluator_version` 区分
（0.2.0 及以前旧语义，0.3.0 起本决定）。

## 顺带查证的三处集成点

- **快照的完整性豁免范围本来就是对的**：只有 `blocked` 与 `underpowered`
  可以一次 outcome 都没读，`null` 不豁免 —— 没读 outcome 不可能得出 null。
  决定 0005 让 null 可达，这条边界才真正被走到，因此补了回归测试；
- **Atlas 两侧的判决配色早已覆盖五个值**（`render.py` 的 `VERDICT_STYLE` 与
  `Chart.tsx`），显示侧不需要改；
- **两本分母的计数语义不变**：`record_outcome_read` 在 `evaluate` 之前执行，
  数据库触发器禁止回缩，`selection_band` 只消费 `outcome_read` 是否非空与
  `tests_so_far`，判决词只被显示、从不被计数。

## 一次撤回

第一版把提案器可见视图里的 `null` 折叠成 `blocked`，理由是「这给了提案器
今天没有的逐 Study 证据信号」。撤回：既有合同测试
`test_proposer_sees_verdict_categories_but_not_effects` **早于本次会话**，
明确断言提案器应当看到 `null` 分类，且 `verdict` 本就在 `PROPOSER_VISIBLE_FIELDS`
白名单上。这是项目自己记录的设计意图，不是我可以顺手改的。

真正需要钉住的是披露的**边界**：`blinded_history` 只把按判决词的**计数**
放进提示词，不放逐 Study 的判决。新增测试断言 `s0`/`s1`/`s2` 这类 study_id
不出现在渲染后的提示词里 —— 一旦逐 Study 的判决进了提示词，
提案器就能把机制与结果一一对上，那才是在检验统计量上爬山。

## 实测命令

- `.venv/bin/ruff check .` 通过；
- `.venv/bin/python -m pytest tests/ -q`：**631 通过**（M6.2 后 624 + 7）；
- `EVALUATOR_VERSION` 由 0.2.0 升至 0.3.0。

## 本票不做

- 让 null 触发与 blocked 不同的调度（例如被证否的机制不再排新版本）。
  它会改变搜索过程的走向；统计分母如实记录每一次 outcome 读取，
  自适应搜索的代价仍被完整计入，但这是一次调度语义变更，另立一票；
- M5 的成本与容量模型。在它完成之前，`candidate` 仍然不可达。
