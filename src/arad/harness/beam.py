"""Beam search 与组合选择（M7）。

**加强优化器之前必须先改 reward，否则加强的是错误的东西。**

若 reward 取评估段上的 |t| 或 IC，那么搜索越强，观测到的最好值越高 —— 即使底下
什么都没有。这不是某个算法的缺陷，这就是「N 次抽样的最大值期望」的定义。
本仓库参考的 ADAR hillclimb 就是实例：81 次迭代选出的最好 Sharpe 是 2.40，
而同一套搜索在零假设下的期望是 2.63，优化器输给了噪声。

因此这里的 reward 是**越过噪声地板多少**：`|t| − E[max|z| at n]`，n 取该族已读
outcome 的次数。每多试一次，地板自己抬高一格，于是「多看几次」本身不再有回报 ——
搜索对自身的代价自惩罚。

组合选择用贪心前向：每步纳入**边际增量最大且与已选低相关**的那一个。相关性必须进
判据，否则组合会收敛成同一个想法的若干写法（实测过：11 个特征只相当于 2.28 个
独立信号）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..evaluation import stats
from ..evaluation.selection import expected_max_abs_z

BEAM_VERSION = "0.1.0"


@dataclass(frozen=True)
class Candidate:
    """一次尝试的可比较结果。`value` 是原始统计量，`reward` 才是搜索的目标。"""

    feature_id: str
    study_id: str
    value: float | None
    tests_at_evaluation: int
    source: str = ""

    @property
    def reward(self) -> float:
        """越过噪声地板多少。地板随该族已读 outcome 的次数抬高。"""
        if self.value is None or not math.isfinite(self.value):
            return float("-inf")
        floor = expected_max_abs_z(max(1, self.tests_at_evaluation))
        return abs(self.value) - floor


@dataclass
class Beam:
    """保留前 k 个**按 reward 排**的候选。

    按原始 |t| 排会让束的头部被「试得更多」这件事推高，而那正是要防的东西。
    """

    width: int = 4
    members: list[Candidate] = field(default_factory=list)

    def offer(self, candidate: Candidate) -> bool:
        """返回是否进入了束。"""
        if candidate.reward == float("-inf"):
            return False
        self.members.append(candidate)
        self.members.sort(key=lambda c: -c.reward)
        del self.members[self.width:]
        return candidate in self.members

    def summary(self) -> dict:
        return {
            "beam_version": BEAM_VERSION,
            "width": self.width,
            "members": [
                {"feature_id": c.feature_id, "study_id": c.study_id,
                 "value": c.value, "tests_at_evaluation": c.tests_at_evaluation,
                 "reward": c.reward, "source": c.source}
                for c in self.members
            ],
            "note": (
                "reward = |t| 减去同样次数搜索在纯噪声上的期望。"
                "按原始 |t| 排会让束的头部被「试得更多」推高"
            ),
        }


def greedy_ensemble(
    signals: dict[str, list[float]],
    labels: list[float],
    *,
    max_size: int = 4,
    max_correlation: float = 0.7,
) -> dict:
    """贪心前向组合：每步纳入边际增量最大、且与已选相关性不超上限的那一个。

    相关性必须进判据。否则组合会收敛成同一个想法的若干写法，看起来分散、
    实际是一条腿 —— 实测本族 11 个特征只相当于 2.28 个独立信号。

    评价用的是**传入的这一段**。谁来调用、用哪一段，由调用方负责：
    在发现段上调它是选择，在封闭段上调它就把封条揭了。
    """
    names = sorted(signals)
    chosen: list[str] = []
    trajectory: list[dict] = []
    rejected: list[dict] = []

    def combined(members: list[str]) -> list[float]:
        rows = len(labels)
        out = []
        for i in range(rows):
            vals = [signals[m][i] for m in members]
            good = [v for v in vals if v is not None and math.isfinite(v)]
            out.append(sum(good) / len(good) if len(good) == len(members) else float("nan"))
        return out

    def score(series: list[float]) -> float:
        pairs = [(v, y) for v, y in zip(series, labels, strict=True) if math.isfinite(v)]
        if len(pairs) < 20:
            return float("-inf")
        return abs(stats.spearman([p[0] for p in pairs], [p[1] for p in pairs]))

    best = float("-inf")
    while len(chosen) < max_size:
        gains: list[tuple[float, str]] = []
        for name in names:
            if name in chosen:
                continue
            rho = max(
                (abs(stats.spearman(signals[name], signals[m])) for m in chosen),
                default=0.0,
            )
            if math.isfinite(rho) and rho > max_correlation:
                rejected.append({"feature_id": name, "max_correlation": rho,
                                 "reason": "与已选相关性超过上限"})
                continue
            gain = score(combined([*chosen, name]))
            if math.isfinite(gain):
                gains.append((gain, name))
        if not gains:
            break
        gain, name = max(gains)
        if gain <= best:
            break
        best = gain
        chosen.append(name)
        trajectory.append({"added": name, "size": len(chosen), "score": gain})

    return {
        "method": "greedy_forward_low_correlation",
        "max_correlation": max_correlation,
        "constituents": chosen,
        "trajectory": trajectory,
        "rejected_for_correlation": rejected[:12],
        "score": best if math.isfinite(best) else None,
        "note": (
            "分数是组合信号与标签的秩相关绝对值，评价段由调用方决定；"
            "在封闭段上调用它就等于把封条揭了"
        ),
    }
