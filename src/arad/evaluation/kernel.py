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

from ..registry.specs import Verdict, content_id
from . import stats

EVALUATOR_VERSION = "0.1.0"

#: 准入所需的最小证据。缺任一项，Study 不得取 candidate。
ADMISSION_REQUIREMENTS = (
    "cost_model_declared",
    "min_returns",
    "min_clusters",
    "placebo_passed",
    "influence_bounded",
)


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
    preregistered_exclusions: dict[str, str] = field(default_factory=dict)
    cost_model_declared: bool = False
    placebo_draws: int = 200
    placebo_seed: int = 20260805
    hac_lag: int = 5
    min_returns: int = 30
    min_clusters: int = 10
    max_abs_dfbeta_share: float = 0.5

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
                "periods_per_year": self.periods_per_year,
                "authoritative_keys": sorted(self.authoritative_keys),
                "preregistered_exclusions": dict(sorted(self.preregistered_exclusions.items())),
                "params": {
                    "placebo_draws": self.placebo_draws,
                    "placebo_seed": self.placebo_seed,
                    "hac_lag": self.hac_lag,
                    "min_returns": self.min_returns,
                    "min_clusters": self.min_clusters,
                    "max_abs_dfbeta_share": self.max_abs_dfbeta_share,
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

    blocked: list[str] = []
    coverage = {
        "rows_submitted": len(rows),
        "rows_authoritative": len(request.authoritative_keys),
        "rows_excluded_preregistered": len(request.preregistered_exclusions),
        "episodes": len(set(episodes)),
        "date_clusters": len(set(dates)),
        "product_clusters": len(set(products)),
    }
    if len(rows) < request.min_returns:
        blocked.append(f"观测数 {len(rows)} 低于预注册下限 {request.min_returns}")
    if len(set(episodes)) < request.min_clusters:
        blocked.append(
            f"Episode 数 {len(set(episodes))} 低于预注册下限 {request.min_clusters}"
        )

    try:
        intercept, slope, resid = stats.ols(y, x)
    except ValueError as exc:
        return _result(request, coverage, None, [*blocked, f"回归不可识别：{exc}"], {})

    two_way = stats.two_way_cluster_se(x, resid, dates, products)
    hac = stats.newey_west_se(x, resid, request.hac_lag)
    influence = stats.influence_on_slope(x, resid)
    placebo = stats.placebo_slope_distribution(
        y, x, episodes, draws=request.placebo_draws, seed=request.placebo_seed
    )
    se = two_way["se"]
    t_stat = slope / se if se and not math.isnan(se) and se > 0 else float("nan")
    mde = 2.8 * se if se and not math.isnan(se) else float("nan")
    dfbeta_share = (
        abs(influence["max_abs_dfbeta"]) / abs(slope) if slope else float("inf")
    )

    if not request.cost_model_declared:
        blocked.append("未声明成本模型：不得取 candidate")
    if placebo["placebo_exceed_rate"] > 0.1:
        blocked.append(
            f"置换检验未通过：{placebo['placebo_exceed_rate']:.3f} 的置换斜率不小于实际值"
        )
    if dfbeta_share > request.max_abs_dfbeta_share:
        blocked.append(
            f"单点影响过大：最大 DFBETA 占斜率 {dfbeta_share:.2f}，"
            f"超过预注册上限 {request.max_abs_dfbeta_share}"
        )
    if two_way["variance_negative"]:
        blocked.append("cluster 方差非正：cluster 结构不足以支撑推断")
    if two_way.get("degenerate_dimension"):
        blocked.append(
            f"{two_way['degenerate_dimension']} 维只有一组，双向 cluster 退化，"
            f"已降级为{two_way['fell_back_to']}单向；单品种样本的横截面相关结构无法识别"
        )

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
        "cost_model_declared": request.cost_model_declared,
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
    blocked: list[str],
    diagnostics: dict,
) -> dict:
    verdict = Verdict.BLOCKED.value if blocked else Verdict.CANDIDATE.value
    if blocked and any("低于预注册下限" in b for b in blocked):
        verdict = Verdict.UNDERPOWERED.value
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
        "blocked_reasons": blocked,
        "suggested_verdict": verdict,
    }
    result["result_digest"] = content_id(
        {k: v for k, v in result.items() if k != "result_digest"}
    )
    return result
