"""受保护的确定性评价机（M3 第二块）。

评价机是**唯一**读取标签的组件。research worker 只提交冻结 spec 与逐行预测，
拿不到标签，也无法自行裁剪样本。三类操作必须在这里失败，而不是被记为警告：

1. **故意泄漏**：任何一行的 feature availability_time 不早于决策时点，
   或决策时点不早于 label 窗口起点；
2. **单位错误**：控制变量在全样本上恒定 —— 旧系统的真实故障就是微秒时间戳被按
   纳秒解析，导致新闻控制恒为零而无人察觉，回归照常给出"显著"结果；
3. **结果依赖过滤**：提交的行集合是权威行集合的真子集，且没有预注册的排除规则。

评价机同时是唯一签发 evidence result 的地方：结果结构化返回，关键数字不经人手抄。

**范围限制（M3 第一版）**：回归是一元的，`controls` 只做完整性检查（缺失与恒定），
**不进入回归**。残差化是 worker 的职责：worker 提交的 `prediction` 必须已经对
其冻结 spec 里声明的控制变量残差化过。多元回归留待后续块。结果里以
`controls_are_integrity_checked_only` 显式声明这一点，避免下游误以为控制已被回归掉。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise

from ..registry.specs import Verdict, content_id
from . import stats

EVALUATOR_VERSION = "0.4.0"

#: 准入所需的最小证据。缺任一项，Study 不得取 candidate。
ADMISSION_REQUIREMENTS = (
    "cost_model_declared",
    "cost_model",
    "min_returns",
    "min_clusters",
    "placebo_passed",
    "influence_bounded",
)

#: 显著性门槛。`mde_at_2p8_se` 与「单点能否把 null 翻成显著」共用它，
#: 各写一份就会漂。
SIGNIFICANCE_T = 2.8

#: 每条阻塞理由**使哪些结论失效**（决定 0005）。
#:
#: 线性优先级表达不了这件事：同一条理由对 candidate 与对 null 的效力可以不同。
#: 未声明成本模型挡的是可交易主张，不妨碍断言「该机制与标的没有统计关系」；
#: cluster 退化使标准误被低估，那只会**高估**显著性，因此它只可能推翻 candidate ——
#: 真实标准误更大只会让 |t| 更小，null 反而更强，而置换检验根本不使用标准误。
#:
#: **判决只能是这张表的函数。**一旦推导条件化到任何未经预注册闸门表达的效应数值
#: （例如「|t| < 0.5 才算 null」），判决词就开始编码一次新的量级比较，那才是泄漏。
#: 有合同测试钉住这一条。
REASON_INVALIDATES: dict[str, frozenset[str]] = {
    # 样本不足：什么都断言不了，单独走 underpowered
    "insufficient_sample": frozenset({"candidate", "null"}),
    "not_identified": frozenset({"candidate", "null"}),
    "cost_model_missing": frozenset({"candidate"}),
    # 声明了成本模型之后才可能出现：典型一笔的往返成本吃掉了平均绝对标签的
    # 全部或更多 —— 即使每次都完美捕捉平均幅度也付不起成本。只废 candidate：
    # 「统计上有关系但不足以支付交易成本」仍是一条合法的否定/对照结论。
    "uneconomic_target": frozenset({"candidate"}),
    "cluster_structure_insufficient": frozenset({"candidate"}),
    # 单点影响是方向感知的：一个点能制造效应，也能遮蔽效应，但两者的判据不同
    "single_point_influence_candidate_only": frozenset({"candidate"}),
    "single_point_influence_both": frozenset({"candidate", "null"}),
    # 置换检验未通过**本身就是 null 的证据**，它不使任何结论失效
    "placebo_failed": frozenset(),
}



#: 信号侧事前筛（M13）的声明阈值。置换检验按 Episode 整块打乱：一个在决策节奏上
#: 几乎不动的信号（长窗水平类构造），打乱前后难以区分 —— 实测 exceed 0.9+ 的
#: 构造全部是这一形态。该性质**只依赖特征值本身**，可以在读 outcome 之前判定，
#: 拦下的构造不花统计预算。阈值与 min_returns 同源（30 个有效独立观测）。
SIGNAL_PRESCREEN = {
    "version": "prescreen-v1",
    "min_effective_obs": 30,
    # 互异值只防退化（近常量/二值以下回归无意义）；低功效的主责在 n_eff。
    # 定 10 会误伤十分位 rank 这类合法构造（恰好 10 个值，实测夹具即中招）。
    "min_distinct_values": 3,
}


def signal_power(predictions: list[float]) -> dict:
    """信号自身的有效功效统计。**不读任何标签**，盲化无涉。

    n_eff 按 AR(1) 折算：n·(1−ρ)/(1+ρ)，ρ 为决策节奏上的一阶自相关。
    一个 30 日均值在逐时段网格上 ρ 常在 0.99 以上 —— 六百个名义观测
    折算不足十个独立观测，置换检验对它没有分辨力。
    """
    vals = [v for v in predictions if v is not None and math.isfinite(v)]
    n = len(vals)
    if n < 3:
        return {"n": n, "distinct": len(set(vals)), "lag1_autocorr": None,
                "n_eff": float(n)}
    mean = math.fsum(vals) / n
    dev = [v - mean for v in vals]
    var = math.fsum(d * d for d in dev)
    if var <= 0:
        return {"n": n, "distinct": len(set(vals)), "lag1_autocorr": 1.0,
                "n_eff": 1.0}
    rho = math.fsum(a * b for a, b in pairwise(dev)) / var
    rho = max(-0.999, min(0.999, rho))
    n_eff = n * (1 - rho) / (1 + rho)
    return {"n": n, "distinct": len(set(vals)),
            "lag1_autocorr": round(rho, 4), "n_eff": round(n_eff, 1)}


def derive_verdict(kinds: list[str]) -> str:
    """由阻塞理由的**种类**推出判决。不读任何效应数值。

    `Verdict.NULL` 此前从未被产出过：原实现是 `BLOCKED if blocked else CANDIDATE`，
    而 `cost_model_declared=False` 对每一条 Study 都成立，于是一个干净的否定结论
    与一个真正无法判定的 Study 在账本里无从区分。整套系统存在的理由正是让否定结论可信。
    """
    unknown = [k for k in kinds if k not in REASON_INVALIDATES]
    if unknown:
        raise ValueError(f"未登记的阻塞理由种类 {unknown}；判决只能是封闭表的函数")
    if "insufficient_sample" in kinds:
        return Verdict.UNDERPOWERED.value
    invalidated: set[str] = set()
    for kind in kinds:
        invalidated |= REASON_INVALIDATES[kind]
    if "placebo_failed" in kinds and "null" not in invalidated:
        return Verdict.NULL.value
    if "candidate" in invalidated:
        return Verdict.BLOCKED.value
    return Verdict.CANDIDATE.value


class LeakageDetected(RuntimeError):
    """检出前视。评价机拒绝出具结果。"""


class DegenerateControl(RuntimeError):
    """控制变量恒定，很可能是单位或解析错误。"""


class OutcomeDependentFiltering(RuntimeError):
    """提交的行集合被结果依赖地裁剪过。"""


class LabelAccessDenied(RuntimeError):
    """非评价机角色试图读取标签。"""


class LabelIsNotAReturn(RuntimeError):
    """调用方声称 label 是收益，而该 target 的 label 规则并不产出收益。

    没有这道检查，`tradable_claim` 就只是装饰：把 `label_is_return=True` 配上一张
    已实现波动的表，评价机照样会出一个年化 Sharpe，而那个数没有任何含义。
    """


#: label 值本身即有符号收益的规则。**必须与 `temporal.targets.RETURN_LABEL_RULES`
#: 一致**（有合同测试钉住）。这里复述一份而不是 import，是为了不让评价机依赖
#: 数据层 —— 评价机要能在没有 spine 的环境里独立运行。
RETURN_LABEL_RULES = frozenset({"entry_to_close"})


@dataclass(frozen=True)
class EvaluationRow:
    """一行可评价观测。标签由评价机持有，worker 提交的只有 prediction。"""

    row_key: str
    episode_id: str
    date_cluster: str
    product_cluster: str
    decision_time: datetime
    label_start: datetime
    availability_times: dict[str, datetime]
    prediction: float
    controls: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationRequest:
    """一次评价请求。authoritative_keys 来自冻结 spec，不由 worker 决定。"""

    study_id: str
    confirmatory_id: str
    family: str
    rows: list[EvaluationRow]
    authoritative_keys: list[str]
    #: 算出这些 prediction 的解释器版本。由调用方填入（kernel 不依赖 features 层）。
    #: 进 digest：同一规格换一个解释器版本可能算出另一个数，证据必须能区分。
    interpreter_version: str = ""
    #: label 是否是一条**有符号的收益**。Sharpe 只有在这一项为真时才有定义 ——
    #: 已实现波动与吸收比例都不是收益，对它们算 Sharpe 会得到一个数，但那个数
    #: 不是 Sharpe。默认为假：要声明它，就要为它负责。
    label_is_return: bool = False
    #: 该 label 来自哪个 target 与哪条 label 规则。进 digest：同一批预测配不同的
    #: label 语义不是同一次评价。
    target_name: str = ""
    label_rule: str = ""
    #: 年化用的每年期数。SC 一天两个 session，但年化只是显示口径，不改变判决。
    periods_per_year: float = 252.0
    #: 仓位规则。sign_unit：按 prediction 的符号取单位多空。规则必须显式记录，
    #: 否则"这条收益序列是怎么来的"不可回放。
    position_rule: str = "sign_unit"
    #: 分位组合的两端。多空组合与超额收益按它计算 —— 这是因子研究里的常规口径，
    #: 与 sign_unit 度量的不是同一件事：前者问「最极端的两端是否真的不同」，
    #: 后者问「符号是否指对方向」。
    top_quantile: float = 0.05
    bottom_quantile: float = 0.05
    preregistered_exclusions: dict[str, str] = field(default_factory=dict)
    cost_model_declared: bool = False
    #: M5 成本模型（决定 0007）。形态：{"version": str, "round_trip_cost_ret": float}
    #: —— 该品种（或面板中位）一次往返的成本，以标签同量纲（对数收益）计。
    #: 提供即视为已声明；digest 纳入 version，换成本表就是另一次评价。
    cost_model: dict | None = None
    placebo_draws: int = 200
    placebo_seed: int = 20260805
    hac_lag: int = 5
    min_returns: int = 30
    min_clusters: int = 10
    #: 单点影响的预注册上限，按 **DFBETAS** 计：删掉这一个观测，斜率移动多少个标准误。
    #: 旧字段 `max_abs_dfbeta_share`（按 |DFBETA| / |β̂| 计）已废除，理由见 M6.2：
    #: 该比值在 β̂ → 0 时发散，因此在完全没有效应时必然触发，而那时并不存在
    #: 任何被单点主导的结论。取 1.0 是 Belsley-Kuh-Welsch 的尺度无关读法
    #: 「一个点把估计移动了整整一个标准误」；他们同时给出的 2/sqrt(n) 是用于
    #: **筛出待人工检视的点**的大样本阈值，不是用于阻断的。
    max_abs_dfbetas: float = 1.0

    def digest(self) -> str:
        """请求的内容身份：同样的输入必然得到同样的结果。"""
        return content_id(
            {
                "study_id": self.study_id,
                "confirmatory_id": self.confirmatory_id,
                "rows": [
                    {
                        "row_key": r.row_key,
                        "episode_id": r.episode_id,
                        "date_cluster": r.date_cluster,
                        "product_cluster": r.product_cluster,
                        "decision_time": r.decision_time.isoformat(),
                        "label_start": r.label_start.isoformat(),
                        "availability_times": {
                            k: v.isoformat() for k, v in sorted(r.availability_times.items())
                        },
                        "prediction": r.prediction,
                        "controls": dict(sorted(r.controls.items())),
                    }
                    for r in sorted(self.rows, key=lambda r: r.row_key)
                ],
                "interpreter_version": self.interpreter_version,
                "label_is_return": self.label_is_return,
                "target_name": self.target_name,
                "label_rule": self.label_rule,
                "position_rule": self.position_rule,
                "top_quantile": self.top_quantile,
                "bottom_quantile": self.bottom_quantile,
                "periods_per_year": self.periods_per_year,
                "authoritative_keys": sorted(self.authoritative_keys),
                "preregistered_exclusions": dict(sorted(self.preregistered_exclusions.items())),
                "params": {
                    "placebo_draws": self.placebo_draws,
                    "placebo_seed": self.placebo_seed,
                    "hac_lag": self.hac_lag,
                    "min_returns": self.min_returns,
                    "min_clusters": self.min_clusters,
                    "max_abs_dfbetas": self.max_abs_dfbetas,
                },
                "evaluator_version": EVALUATOR_VERSION,
            }
        )


def _check_leakage(rows: list[EvaluationRow]) -> None:
    for row in rows:
        if row.decision_time >= row.label_start:
            raise LeakageDetected(
                f"{row.row_key}：决策时点 {row.decision_time} 不早于 label 起点 {row.label_start}"
            )
        for name, available in sorted(row.availability_times.items()):
            if available >= row.decision_time:
                raise LeakageDetected(
                    f"{row.row_key}：feature {name!r} 的 availability_time {available} "
                    f"不早于决策时点 {row.decision_time}"
                )
            if available >= row.label_start:
                raise LeakageDetected(
                    f"{row.row_key}：feature {name!r} 的 availability_time {available} "
                    f"不早于 label 起点 {row.label_start}"
                )


def _check_controls(rows: list[EvaluationRow]) -> None:
    names = sorted({n for r in rows for n in r.controls})
    for name in names:
        values = [r.controls.get(name) for r in rows]
        present = [v for v in values if v is not None]
        if len(present) != len(rows):
            raise DegenerateControl(f"控制变量 {name!r} 在部分行缺失；缺失必须显式处理")
        if max(present) == min(present):
            raise DegenerateControl(
                f"控制变量 {name!r} 在全样本上恒为 {present[0]!r}。"
                "这是旧系统的真实故障形态：微秒时间戳被按纳秒解析，"
                "新闻控制恒为零而回归照常给出显著结果。评价机拒绝出具结果"
            )


def _check_filtering(request: EvaluationRequest) -> None:
    submitted = {r.row_key for r in request.rows}
    authoritative = set(request.authoritative_keys)
    unknown = submitted - authoritative
    if unknown:
        raise OutcomeDependentFiltering(
            f"提交了权威行集合之外的 {len(unknown)} 行：{sorted(unknown)[:5]}"
        )
    missing = authoritative - submitted
    undeclared = sorted(missing - set(request.preregistered_exclusions))
    if undeclared:
        raise OutcomeDependentFiltering(
            f"{len(undeclared)} 行被丢弃且没有预注册的排除规则："
            f"{undeclared[:5]}。看过结果之后再删行属于结果依赖过滤"
        )


def evaluate(request: EvaluationRequest, labels: dict[str, float], *, role: str) -> dict:
    """出具结构化 evidence result。只有 evaluator 角色可以调用。"""
    if role != "evaluator":
        raise LabelAccessDenied(
            f"角色 {role!r} 不得读取标签；research worker 只能提交冻结 spec 与预测"
        )
    if request.label_is_return and request.label_rule not in RETURN_LABEL_RULES:
        raise LabelIsNotAReturn(
            f"target {request.target_name!r} 的 label 规则 {request.label_rule!r} "
            f"不产出有符号收益（可选 {sorted(RETURN_LABEL_RULES)}）；"
            "对非收益 label 计算 Sharpe 会得到一个可被误读的数字"
        )
    _check_filtering(request)
    _check_leakage(request.rows)
    _check_controls(request.rows)

    rows = sorted(request.rows, key=lambda r: (r.decision_time, r.row_key))
    missing_labels = [r.row_key for r in rows if r.row_key not in labels]
    if missing_labels:
        raise ValueError(f"{len(missing_labels)} 行缺少标签：{missing_labels[:5]}")

    y = [labels[r.row_key] for r in rows]
    x = [r.prediction for r in rows]
    dates = [r.date_cluster for r in rows]
    products = [r.product_cluster for r in rows]
    episodes = [r.episode_id for r in rows]

    # 每条理由与它的种类成对记录：判决读种类，人读文本
    blocked: list[tuple[str, str]] = []
    coverage = {
        "rows_submitted": len(rows),
        "rows_authoritative": len(request.authoritative_keys),
        "rows_excluded_preregistered": len(request.preregistered_exclusions),
        "episodes": len(set(episodes)),
        "date_clusters": len(set(dates)),
        "product_clusters": len(set(products)),
    }
    if len(rows) < request.min_returns:
        blocked.append(
            ("insufficient_sample",
             f"观测数 {len(rows)} 低于预注册下限 {request.min_returns}")
        )
    if len(set(episodes)) < request.min_clusters:
        blocked.append(
            ("insufficient_sample",
             f"Episode 数 {len(set(episodes))} 低于预注册下限 {request.min_clusters}")
        )

    try:
        intercept, slope, resid = stats.ols(y, x)
    except ValueError as exc:
        return _result(
            request, coverage, None,
            [*blocked, ("not_identified", f"回归不可识别：{exc}")], {},
        )

    two_way = stats.two_way_cluster_se(x, resid, dates, products)
    hac = stats.newey_west_se(x, resid, request.hac_lag)
    influence = stats.influence_on_slope(x, resid)
    placebo = stats.placebo_slope_distribution(
        y, x, episodes, draws=request.placebo_draws, seed=request.placebo_seed
    )
    se = two_way["se"]
    t_stat = slope / se if se and not math.isnan(se) and se > 0 else float("nan")
    mde = 2.8 * se if se and not math.isnan(se) else float("nan")
    # 按标准误标准化，不按点估计。除以 β̂ 的旧写法在 β̂ → 0 时发散：实测一条
    # t = -0.03 的干净零结果被报成「最大 DFBETA 占斜率 9.72」，而它的最大杠杆
    # 只有 0.022，根本没有任何单点主导。分母用本次推断实际使用的 SE（双向 cluster），
    # 因此这句话读作「删掉这一个观测，估计移动多少个我们实际用来做推断的标准误」。
    # 标准误不可用时（cluster 方差非正、或退化维使其为 NaN）这个量**无定义**，
    # 不是"超限"。取 inf 会让账本写下「斜率移动 inf 个标准误」，把度量失败报成
    # 关于特征的实质发现 —— 与本票要修的正是同一类错误。
    dfbetas = (
        abs(influence["max_abs_dfbeta"]) / se
        if se and not math.isnan(se) and se > 0
        else float("nan")
    )
    # 旧口径仍然报出，但**不再阻断**：既保留与既有记录的可比性，
    # 也让「它为什么曾经触发」在账本里能被看见
    dfbeta_share = (
        abs(influence["max_abs_dfbeta"]) / abs(slope) if slope else float("inf")
    )
    influence = {
        **influence,
        "max_abs_dfbetas": dfbetas,
        "dfbeta_over_slope": dfbeta_share,
        # 闸门有没有被评估过，必须与"评估了而且通过了"区分开：
        # 后者是关于特征的结论，前者只是说这次量不出来
        "gate_evaluable": not math.isnan(dfbetas),
    }

    declared = request.cost_model_declared or request.cost_model is not None
    cost_effects = None
    if request.cost_model is not None:
        cost = float(request.cost_model.get("round_trip_cost_ret", float("nan")))
        mean_abs_label = (math.fsum(abs(v) for v in y) / len(y)
                          if y else float("nan"))
        breakeven = (cost / mean_abs_label
                     if mean_abs_label and math.isfinite(mean_abs_label)
                     and mean_abs_label > 0 and math.isfinite(cost) else float("nan"))
        cost_effects = {
            "version": request.cost_model.get("version", ""),
            "round_trip_cost_ret": cost,
            "mean_abs_label": mean_abs_label,
            # 盈亏平衡捕捉率：往返成本占平均绝对标签的比例。>= 1 意味着
            # 即使完美捕捉平均幅度也付不起成本（旧系统的盈亏平衡倍数同一量纲）。
            "breakeven_capture_share": breakeven,
        }
        if request.label_is_return and math.isfinite(breakeven) and breakeven >= 1.0:
            blocked.append((
                "uneconomic_target",
                f"往返成本为平均绝对收益的 {breakeven:.1f} 倍：完美捕捉也不够付",
            ))
    if not declared:
        blocked.append((
            "cost_model_missing",
            # 这是**系统级状态**（M5 未建），不是本条 Study 的缺陷。措辞必须说清，
            # 否则每条判决都像在责备提案 —— 实测引起过误读。
            "成本模型未建（系统级，M5）：候选封顶，不影响否定结论",
        ))
    if placebo["placebo_exceed_rate"] > 0.1:
        blocked.append((
            "placebo_failed",
            # 措辞按比例读：0.640 曾被读成一个斜率值。它是比例 —— 打乱标签的
            # 样本里有多大比例跑出了不小于实际值的 |斜率|（闸门 0.1）。
            (f"置换检验未通过：{placebo['placebo_exceed_rate']:.0%} 的打乱样本"
             f"跑出的 |斜率| 不小于实际值（阈值 10%）"),
        ))
    if not math.isnan(dfbetas) and dfbetas > request.max_abs_dfbetas:
        # 方向感知：删掉一个点最多把 |t| 移动约 dfbetas 个标准误（一阶近似 ——
        # 删点同时也会改变标准误本身）。若移动之后仍够不着显著性门槛，
        # 这一个点能制造效应，但不能把「没效应」翻成「有效应」，
        # 因此它只使 candidate 失效，不使 null 失效。
        could_flip_null = (
            math.isnan(t_stat) or abs(t_stat) + dfbetas >= SIGNIFICANCE_T
        )
        blocked.append((
            "single_point_influence_both" if could_flip_null
            else "single_point_influence_candidate_only",
            f"单点影响过大：删掉最有影响的一个观测，斜率移动 {dfbetas:.2f} 个标准误，"
            f"超过预注册上限 {request.max_abs_dfbetas}"
            + ("" if could_flip_null else
               f"；移动后 |t| 仍不足 {SIGNIFICANCE_T}，不足以推翻否定结论"),
        ))
    if two_way["variance_negative"]:
        blocked.append(
            ("cluster_structure_insufficient", "cluster 方差非正：cluster 结构不足以支撑推断")
        )
    if two_way.get("degenerate_dimension"):
        blocked.append((
            "cluster_structure_insufficient",
            (f"{two_way['degenerate_dimension']} 维只有一组，双向 cluster 退化，"
             f"已降级为{two_way['fell_back_to']}单向；单品种样本的横截面相关结构无法识别"),
        ))

    effects = {
        "intercept": intercept,
        "slope": slope,
        "t_stat": t_stat,
        "se_two_way_cluster": se,
        "se_newey_west": hac["se"],
        "mde_at_2p8_se": mde,
        # 嵌套而不是摊平：IC 与 Sharpe 各自都有 n 与 note，摊平会互相覆盖，
        # 而被覆盖掉的恰恰是说明这个数是什么的那一句
        "ic": stats.information_coefficient(x, y),
        "performance": _performance(request, x, y),
    }
    independence = {
        "nominal_n": len(rows),
        "episode": stats.cluster_n_eff(episodes),
        "date_cluster": stats.cluster_n_eff(dates),
        "product_cluster": stats.cluster_n_eff(products),
        "residual_autocorrelation_lag1": stats.autocorrelation(resid, 1),
        "suggested_block_length": stats.suggested_block_length(resid),
        "two_way_cluster": two_way,
        "hac": hac,
        "note": (
            "Kish n_eff 只描述权重集中度，不替代双向 cluster、HAC 或 block bootstrap；"
            "主要推断单位由 mechanism 与 target 事前确定"
        ),
    }
    diagnostics = {
        "controls_are_integrity_checked_only": True,
        "controls_note": (
            "本版回归为一元；controls 只检查缺失与恒定，不进入回归。"
            "残差化由 worker 在提交预测前完成，控制清单以 Confirmatory Lock 为准"
        ),
        "influence": influence,
        "placebo": placebo,
        "cost_model_declared": declared,
        "cost_model": cost_effects,
        "cost_note": "成本占位：真实成本与容量模型属 M5，未声明时不得取 candidate",
    }
    return _result(request, coverage, effects, blocked, {**independence, **diagnostics})


def _performance(request: EvaluationRequest, x: list[float], y: list[float]) -> dict:
    """pre-cost Sharpe。**只有 label 是收益时才有定义。**

    已实现波动是正的量级，吸收比例是无量纲比值：对它们做 sign(prediction) * label
    会得到一个数，而那个数不是任何策略的收益。与其给一个能被误读的数字，
    不如给一个明确的"未定义"与理由 —— 这与解释器拒绝伪造 zscore 是同一条原则。
    """
    if not request.label_is_return:
        return {
            "sharpe": None,
            "sharpe_undefined_reason": (
                "label 不是有符号收益（label_is_return 未声明）。"
                "对非收益 label 计算 Sharpe 会产生一个可被误读的数字"
            ),
        }
    if request.position_rule != "sign_unit":
        return {"sharpe": None,
                "sharpe_undefined_reason": f"未实现的仓位规则 {request.position_rule!r}"}
    returns = [(1.0 if p > 0 else -1.0 if p < 0 else 0.0) * label
               for p, label in zip(x, y, strict=True)]
    out = stats.sharpe(returns, periods_per_year=request.periods_per_year)
    out.update(stats.moments(returns))
    out["position_rule"] = request.position_rule
    # 分位组合与 sign_unit 一起**always 记录**，不是二选一：两者是同一次 outcome 读取
    # 的两种汇总，不构成两次检验。事后挑好看的那个才是选择偏差，因此两个都留在证据里。
    quantile = stats.quantile_portfolio(
        x, y, top=request.top_quantile, bottom=request.bottom_quantile,
    )
    if quantile.get("defined"):
        active = quantile.pop("active_returns")
        quantile["sharpe"] = stats.sharpe(
            active, periods_per_year=request.periods_per_year,
        )["sharpe"]
    else:
        quantile.pop("active_returns", None)
    out["quantile_portfolio"] = quantile
    out["periods_per_year_declared"] = request.periods_per_year
    out["periods_per_year_derived"] = _derive_periods_per_year(request)
    out["periods_note"] = (
        "declared 与 derived 不一致不阻断：只覆盖夜盘的 Study 本就该导出更小的值。"
        "年化只是显示口径，不改变判决"
    )
    return out


def _derive_periods_per_year(request: EvaluationRequest) -> float | None:
    """从本次评价实际用到的决策时点导出每年期数。

    年化系数不能沿用教科书的 252：SC 一天两个 session，实测每年约 485 个 session。
    用错会把年化 Sharpe 系统性地低估约三成。
    """
    times = sorted(r.decision_time for r in request.rows)
    if len(times) < 2:
        return None
    span_years = (times[-1] - times[0]).total_seconds() / (365.2425 * 86400)
    return len(times) / span_years if span_years > 0 else None


def _result(
    request: EvaluationRequest,
    coverage: dict,
    effects: dict | None,
    blocked: list[tuple[str, str]],
    diagnostics: dict,
) -> dict:
    kinds = [kind for kind, _ in blocked]
    verdict = derive_verdict(kinds)
    result = {
        "evaluator_version": EVALUATOR_VERSION,
        "study_id": request.study_id,
        "confirmatory_id": request.confirmatory_id,
        "family": request.family,
        "interpreter_version": request.interpreter_version,
        "request_digest": request.digest(),
        "coverage": coverage,
        "effects": effects,
        "diagnostics": diagnostics,
        "blocked_reasons": [text for _, text in blocked],
        #: 判决**只**读这一项。文本里的数字不进推导。
        "blocked_reason_kinds": kinds,
        "suggested_verdict": verdict,
    }
    if verdict == Verdict.NULL.value:
        # null 必须带着它的排除界，否则它只是「没找到」而不是「排除了什么」。
        # M5 的 economic_bound 将来会给 MDE 一个外部参照；在那之前，
        # 这是「相对于本次达到的 MDE 的 null」，强度逐 Study 不同，证据里要能读出来。
        mde = (effects or {}).get("mde_at_2p8_se")
        result["null_exclusion_bound"] = {
            "mde_at_2p8_se": mde,
            "note": (
                "在本次达到的最小可检出效应之下未检出任一方向的效应。"
                "这是相对于该 MDE 的 null，不是对任意小效应的排除；"
                "外部经济参照属 M5，尚未声明"
            ),
        }
    result["result_digest"] = content_id(
        {k: v for k, v in result.items() if k != "result_digest"}
    )
    return result
