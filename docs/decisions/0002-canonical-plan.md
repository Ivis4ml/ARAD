# 决定 0002：确认 Merge-Plan-2 为 canonical plan

日期：2026-08-05。状态：已由人类确认。

## 决定内容

1. `Merge-Plan-2.md` 是后续实施的唯一入口。与其他文档冲突时以它为准；
   数据事实以 M1 生成的机器 manifest 为最终权威。
2. **新闻族因子计入主库存目标**（人类裁决）：Alternative Factor Inventory 的
   计数口径为"新增信息来自另类数据源（Polymarket 或财联社新闻）或其与期货状态的
   事前声明交互"。纯量价因子仍归 Baseline Control Library，不计入主目标。
   库存按源标签（polymarket / news / mixed）分别记账，正交性检验同时约束跨源重复。
3. 财联社内容完整性争议的裁决：72.5% 至 88.6% 的抽查结论经二次复核不成立
   （方法错误：多日滚动快照当单日基准），99% 至 100% 维持，附 `in_roll=1`
   母体限定；复现脚本 `scripts/verify_cls_coverage.py`。
4. `docs/decisions/0001-two-docsets-merge.md` 的权威划分被本决定取代，保留为历史。

## 随本决定执行的文档归一化

- `Merge-Plan-2.md` §0/§3.1：新闻计入主目标的口径修订；
- `docs/01-goal.md`：里程碑改为库存覆盖目标表述、双库存分账、per-Study forward 准入；
- `docs/00-material-analysis.md`：verified/provisional 区分、弱化"保证存在因子"表述；
- `docs/02-plan.md`：降级为 ETL 与评价机规格出处，修正 Title 保留、来源数据只读、
  样本治理与状态存储口径；
- `program.md`：按 Merge-Plan-2 §13 十项修订；
- `README.md`：Merge-Plan-2 设为唯一实施入口。
