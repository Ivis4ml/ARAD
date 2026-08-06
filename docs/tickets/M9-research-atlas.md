# 工程票 M9：Research Atlas 最小版本

2026-08-05 立。前置：决定 0003（新增可视化交付层）、M3 账本、M4 闭环。

决定 0003 把技术选型留给本票定稿，本票定稿如下。

## 技术选型：静态生成，不做服务端

决定 0003 允许 FastAPI 或静态站点，取静态。三条理由：

1. **不引入新依赖。**当前依赖只有 pyarrow / pydantic / PyYAML / pytest / ruff，
   静态渲染用标准库即可；
2. **只读边界从承诺变成物理事实。**一个 HTML 文件写不了账本。这与 events 表上
   UPDATE/DELETE 触发器是同一种论证：边界要由结构保证，不由约定保证；
3. **没有服务生命周期需要解释。**Research Service 只有 running / paused / shutdown
   三态，再叠一个 web 服务的启停会造成"Atlas 停了是不是研究停了"的歧义。

产物：`artifacts/atlas/index.html`（人读）与 `artifacts/atlas/atlas.json`（机读，
供审计比对渲染是否篡改了数字）。入口：`arad atlas render --ledger <db> [--queue <db>]`。

## 三层内容（决定 0003）

- **总览**：两本分母、verdict 分布、库存覆盖（机制族 × 数据源 × 时域）、
  三源数据新鲜度（读 M1 manifest 自身记录的指纹与覆盖末日，**不扫描源数据**）、
  Research Service 状态、哈希链完整性；
- **过程**：Search Episode 的展开与收束、每个 Episode 触及的 Study、
  **不属于任何 Study 的事件**（原语缺口声明、provider 故障）、中止轮次；
- **快照**：任一 Study 展开为判决时刻的完整证据 —— 时间线、两把锁、特征规格与
  工件哈希、读过 outcome 的检验、评价机的覆盖与估计量与未通过闸门与诊断、
  当时可见的数据范围、verdict 与理由。

## 三条不可妥协的边界（决定 0003），以及它们在代码里的位置

1. **只读投影**：`atlas/project.py` 只有 SELECT，渲染产物是文件。
   回归测试 `test_rendering_never_writes_to_the_ledger` 在渲染前后比对事件数与哈希链；
2. **尊重能力隔离**：`next_action == queue_forward` 的 Study 只显示"预约待裁决"，
   forward 区间的数据与标签不出现在页面上；
3. **不重算**：`atlas/render.py` 不 import 任何统计模块，数字全部来自账本 payload。
   浮点数按 6 位有效数字显示，原值保留在 `title` 属性与 `atlas.json` 中。

## 三个映射陷阱（本票的主要工程内容）

- **没有 study_id 的事件不能被丢掉。**原语缺口声明与 Episode 起讫本就不属于任何
  Study，按 study_id 分组会让它们整批消失 —— 而第一版恰恰以缺口声明为主要产出。
  它们进 Episode 层单独成节；无 Episode 归属的进 orphan 段；
- **有 study_id 不等于存在 Study。**解析失败的轮次带着 study_id 入账，却没有
  `study_created`、没有提案、没有判决。用 `study_created` 判别，否则这些预期状态
  会被误报成账本缺口；
- **以 human 角色读账本。**proposer 视图递归遮蔽效果字段，而快照层的存在意义正是
  呈现逐项结果。Atlas 要守的边界是 forward 不可见，不是效果字段遮蔽。

## 附带价值兑现

- Atlas 每次渲染都重算整条哈希链，因此它同时是账本完整性的持续检验；
- 真实 Study 拼不出完整快照时抛 `SnapshotIncomplete` 而不是渲染半页 ——
  按决定 0003，那是账本缺口，按 bug 处理。

## 出口条件

- `arad episode demo` 在真实 SC 数据上跑完一次 Episode 后，`arad atlas render`
  能把这次 Episode 讲清楚（四种结局各自可见）；
- 负向测试：缺口事件被渲染、中止轮次不被误判为账本缺口、真实缺口刺眼、
  渲染不写账本、forward 只显示预约、payload 文本无法注入标记；
- 全仓 ruff 与 pytest 通过。

## 本版不做

- Study 谱系 DAG（承继、重开、家族分母累计）：需要 M6 的版本关系，届时补；
- 衰减曲线与分位单调性图表：需要评价机产出对应结构，属 M5/M6；
- 增量渲染与大账本分页：当前账本量级不需要。
