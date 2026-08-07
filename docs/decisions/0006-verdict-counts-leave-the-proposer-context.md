# 决定 0006：判决分类退出提案器上下文

- 日期：2026-08-07
- 状态：已采纳
- 触发：M9 第 0 层记忆的对抗性审查（五个独立视角），经实测证否
- 影响：取代决定 0005「泄漏边界」一节；`assemble_proposer_context` 的 facts

## 被证否的是什么

决定 0005 把「判决词对提案器可见」定价为安全，论证是：它只泄漏**存在性**，
不泄漏方向（置换检验对 |slope| 双侧）也不泄漏量级（推导只依赖分类闸门的越界与否），
且披露的是**聚合计数**而非逐 Study 的判决。

那个定价有一个未被写出的前提：**计数指向的是一个匿名总体。**提案器每轮由独立子进程
承载（`claude_cli.py` 的 `DEFAULT_ARGS` 不含任何会话延续参数），跨轮不携带上下文，
`RoundOutcome.feedback` 全仓没有消费者。因此「9 个 null」指的是哪 9 条，它无从知道。

**M9 的具名清单取消了匿名。**它把总体的成员与基数交给了提案器，而定价没有被重新审视。

## 推断链，以及它在真实账本上的实测

提案器在同一份 facts 里读到：具名规格清单（M9）、`tests_spent`（M9）、
判决计数（M7）。三条结构事实使它们可以做减法：

1. `feature_spec_locked` 之后每条路径恰好产出一个 `verdict_recorded`，规格与判决一一对应；
2. `null` 当且仅当 `placebo_failed` 在理由种类里且 `null` 未被作废，而 `placebo_failed`
   的语义是**实际斜率未超出其置换分布** —— 那是一条关于量级的陈述；
3. `null` 与 `candidate` 只可能在读过 outcome 之后产生，因此 `#null + #candidate <= tests_spent`。

**实测（run4）**：规格 11 条，`outcome_read` 9 条，判决 `{null: 9, underpowered: 1, blocked: 1}`。
`#null = tests_spent = 9`，等式成立，因此提案器可**确定地**推出
「全部被度量过的具名规格都是 null」—— 逐条的量级上界，与族内规格条数无关。

新族、新账本、系统冷启动都恰好落在这个区间，而它们正是常态运行的开端。

## 裁决

**判决分类（`verdict_taxonomy` 与 `studies_seen`）不再进提案器上下文。**
`blinded_history` 本身保留：Atlas 与人工复核要用它。

保留在提案器上下文里的是：具名清单、`tests_spent`、地板、两本分母。
「这些规格里哪些被度量过」由语义审计与解释器可求值性决定，两者都是**读 outcome
之前的纯函数**，因此不构成结果信息。

## 一处必须收回的表述

M9 写着第 0 层「泄漏为零，按构造成立」。**逐条记录成立，逐视图不成立。**
由「每一条都不含结果」推出「视图不含结果」是组合谬误，上面的推断链即反例。

同时收回 M9 里另一句：「唯一的泄漏是族内只有一条规格且只有一条判决时的平凡配对，
本模块不加重它」。确定性配对不需要 K = 1，只需已度量者的判决呈现单一词；
而配对能力的另一半（具名总体）在 M9 之前根本不存在，因此不是「本来就存在而未被加重」，
是由 M9 首次提供。

**这条之所以要单独写下来，是因为它是泄漏得以通过全部检查而发布的原因**：
一句「已评估过」会让后续审查者跳过这条路径。模型会读到的两处 `note` 字符串
（「不含任何效应的方向与量级」「效果方向与量级对提案器不可见」）也一并改掉 ——
只改 docstring 而把错误的保证留在提示词里，等于让模型继续读到一句假话。

## 顺带关掉的两处结构问题

**一、记忆的投影表与 `read_events` 的投影表分开。**`PROPOSER_VISIBLE_FIELDS`
同时是两者的投影表，而 `read_events` 的信封对任何角色都原样返回 `study_id`。
把 `feature_spec_locked` 加进那张表，等于让 `read_events(role=PROPOSER, study_id=X)`
一次返回规格**与**该 Study 的判决，由同一个 study_id 串起 ——
而 `proposer_memory` 丢弃 study_id 正是为了挡这个。当前没有代码路径把该配对送进
提示词，因此不是活的泄漏；但强制边界的已经不是账本而是装配器里的一行 if。
新增 `PROPOSER_MEMORY_FIELDS`，`feature_spec_locked` 移回。

**二、记忆补上第二道递归遮蔽。**`read_events` 做两道（白名单 + `_redact`），
`proposer_memory` 只做一道。`steps` 是嵌套结构且逐字保留，将来若步骤定义里出现
`slope`/`ic` 一类子键，一道白名单会原样送出。有负向测试把 `slope`/`t_stat`
塞进 `steps` 里验证它们被丢掉。

## 实测

- `.venv/bin/ruff check .` 通过；`pytest tests/ -q`：**658 通过**（M9 后 655 + 3）；
- 既有测试 `test_only_aggregate_verdict_counts_reach_the_proposer` 改写为
  `test_the_verdict_classification_no_longer_reaches_the_proposer`：断言
  `blinded_history` 仍给出分类（Atlas 用），而 `assemble_proposer_context` 的 facts
  里不含任何判决词。

## 未修，记为阻塞

- **记忆不按族过滤。**`proposer_memory` 的 SQL 只按 `event_type` 过滤，
  而 `events` 表没有 `family` 列；`search_price` 却按族取分母。多族共存时
  族 A 的提案器会读到族 B 的全部具名规格。当前 `service.db` 只有一个族，未触发。
  需在 payload 补记 `family` 或给表加列，且过滤必须在丢弃 `study_id` **之前**完成；
- **M5 之后本条的严重度会上升。**当前 `cost_model_declared=False` 使 `candidate`
  结构上不可达（四本账本实测 candidate 计数均为 0）。成本模型接入后，
  同一条推断链给出的将不只是量级上界：`tried_features` 保留机制全文，
  而机制陈述通常已蕴含方向，一条 `candidate: 1` 配合结构筛收缩即成为方向陈述。
