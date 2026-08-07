"""因子卡：一个被确认的因子该带着走的全部东西（M8）。

人类的要求是每个被 autoresearch 确认的因子都要有「一段解释 final 意义」与「对应的
代码」。卡片把两者与证据绑在一起，并且**代码由规格确定性生成**，因此不存在
「说明写的是一回事、代码算的是另一回事」。

状态词表刻意不叫 accepted / rejected：本项目的 Verdict 只描述证据状态。
卡片状态描述的是**这个因子走到了哪一步**，与 Verdict 分开：

- `discovery_only`：只在发现段上有证据，封闭段还没开过；
- `sealed_survived`：封闭段上符号一致且未塌陷；
- `sealed_failed`：封闭段上符号翻转或塌陷 —— 这是完整结论，不是失败；
- `sealed_underpowered`：封闭段上定义点太少，判不了。

`taxonomy_clean=False` 时，即便 `sealed_survived` 也**不构成已验证** ——
机制的选择看过该段发生了什么，样本外救不了它（决定 0004）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..features.codegen import CODEGEN_VERSION, to_formula, to_python
from ..features.spec import FeatureSpec

CARD_VERSION = "0.1.0"

#: 封闭段上被判为「未塌陷」的门槛：符号一致，且幅度不低于发现段的这个比例。
_HOLD_RATIO = 0.35


def _status(discovery_t: float | None, sealed_t: float | None,
            sealed_rows: int | None, min_rows: int = 120) -> str:
    if sealed_t is None or sealed_rows is None:
        return "discovery_only"
    if sealed_rows < min_rows:
        return "sealed_underpowered"
    if discovery_t is None or not math.isfinite(discovery_t):
        return "discovery_only"
    if discovery_t * sealed_t <= 0:
        return "sealed_failed"
    return ("sealed_survived"
            if abs(sealed_t) >= _HOLD_RATIO * abs(discovery_t) else "sealed_failed")


@dataclass(frozen=True)
class AlphaCard:
    spec: FeatureSpec
    mechanism: str
    discovery: dict
    sealed: dict | None
    taxonomy_clean: bool
    family: str

    @property
    def status(self) -> str:
        return _status(
            self.discovery.get("t_stat"),
            (self.sealed or {}).get("t_stat"),
            (self.sealed or {}).get("rows"),
        )

    def meaning(self) -> str:
        """一段话说清楚这个因子最终意味着什么。由证据拼装，不写任何未测的东西。

        **正文里不得出现 markdown 标记。**这段话同时进 `.md` 文件与 app 的纯文本
        段落，后者会把 `**粗体**` 原样显示给人看 —— 这个错已经犯过四次，
        因此有一条测试钉住它。强调一律用「」。
        """
        d, s = self.discovery, self.sealed
        parts = [f"机制：{self.mechanism}"]
        dt = d.get("t_stat")
        if dt is not None:
            parts.append(
                f"发现段上斜率的 t 值为 {dt:+.3f}，"
                f"IC（时序秩相关）{d.get('ic_spearman', float('nan')):+.4f}，"
                f"提交观测 {d.get('rows')} 行。"
            )
        if s and s.get("t_stat") is not None:
            st = s["t_stat"]
            same = "同号" if dt is not None and dt * st > 0 else "反号"
            parts.append(
                f"封闭段（只开一次）上 t 值 {st:+.3f}，与发现段{same}，"
                f"提交观测 {s.get('rows')} 行。"
            )
        else:
            parts.append("封闭段尚未开启，因此没有任何样本外证据。")
        if self.status == "sealed_failed":
            parts.append(
                "结论：「在样本外没有保住」。这是一个完整的否定结论，不是运行失败 ——"
                "发现段上的强度来自搜索本身。"
            )
        elif self.status == "sealed_survived":
            parts.append("结论：在时间上的样本外保住了符号与量级。")
        elif self.status == "sealed_underpowered":
            parts.append("结论：封闭段上定义点太少，判不了，不得据此下任何结论。")
        if not self.taxonomy_clean:
            parts.append(
                "注意，分类法不干净：候选机制族的归纳语料覆盖了本段，"
                "机制的选择并不独立于结果，样本外也救不了这一点（决定 0004）。"
                "真正干净的检验只能在归纳切点之后的数据上做。"
            )
        parts.append(
            "成本与容量模型尚未建立（属 M5），因此本因子在任何情况下都不得取 candidate；"
            "以上全部为 pre-cost。"
        )
        return " ".join(parts)

    def payload(self) -> dict:
        return {
            "card_version": CARD_VERSION,
            "codegen_version": CODEGEN_VERSION,
            "feature_id": self.spec.feature_id,
            "content_id": self.spec.content_id,
            "family": self.family,
            "status": self.status,
            "taxonomy_clean": self.taxonomy_clean,
            "mechanism": self.mechanism,
            "failure_condition": self.spec.failure_condition,
            "formula": to_formula(self.spec),
            "code": to_python(self.spec),
            "required_lookback_seconds": self.spec.required_lookback_seconds,
            "sources": sorted(s.value for s in self.spec.sources),
            "discovery": self.discovery,
            "sealed": self.sealed,
            "meaning": self.meaning(),
        }
