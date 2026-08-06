# 工程票 M3：最小 Research Kernel

对应 Decision Map #6 与 #7；canonical 依据 `Merge-Plan-2.md` §10 的 M3，
以及决定 0003 的快照渲染合同。

## 为什么先做账本

#12 的下一步（机制族命名、金标、跨模型一致性）需要把整批实体提案计入
proposal denominator；`size_entity_proposal()` 已经是评价侧那半，缺的是记账那半。
在账本存在之前，任何"挑一批候选"的动作都无处留痕，会退化成人工先验。
因此 M3 的第一块是账本与冻结规格，不是评价机。

## 范围（分块交付）

### 第一块：不可变规格与 Evidence Ledger（本次交付）

- `ProposalSpec` / `HypothesisLock` / `ConfirmatoryLock` / `StudySpec` /
  `Verdict` / `NextAction` 的最小机器合同，内容寻址、不可原地覆盖；
- SQLite WAL append-only hash-chain Evidence Ledger：
  - 事件只能追加，UPDATE 与 DELETE 由数据库层拒绝（不是靠提示词）；
  - 每个事件链接前一事件的哈希，任何篡改可检出；
- **两本分母**：proposal denominator（含被预检挡下的提案）与
  statistical denominator（所有读过 outcome 的检验），后者只增不减；
- **能力边界**：proposer 角色读不到 β/t/p/IC/Sharpe 等效果字段，
  由查询层强制，不由约定；
- **快照渲染合同**（决定 0003）：任意 Study 的事件流必须足以渲染为
  判决时刻的自包含快照。

### 后续块（不在本次）

- 最小 evaluator：coverage、Episode、MDE、n_eff、cluster/HAC、影响点、
  placebo、成本占位与 artifact hashing；
- durable queue、租约、heartbeat、checkpoint；
- 最小 Baseline Control：SC 自身收益/波动、国际油价、CLS 公开新闻强度。

## 不做

- 不做因子、不做回测、不碰 forward 数据；
- 不把 SHIP/ITERATE/KILL 当 Verdict；Verdict 只有五个值，调度动作另存；
- 不允许任何路径删除或修改已写入的证据。

## 出口条件

- 一个合成 Study 可从账本完整回放，并机械地渲染为自包含快照；
- 负向测试全部通过：修改事件失败、删除事件失败、篡改后链校验失败、
  统计分母缩小失败、Verdict 取五值之外失败、proposer 读效果字段失败；
- 全仓 ruff 与 pytest 通过；Decision Map 更新。
