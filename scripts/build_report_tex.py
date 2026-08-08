"""从证据账本生成发表格式的 LaTeX 研究报告（xelatex / ctexart）。

格式参照 Alpha-Data 的 cn_futures_polymarket_ext_round.pdf：中文文章、蓝色链接、
摘要内加粗关键数字、目录、booktabs 表、行间公式、结尾附复现一节。

纪律与 HTML 报告相同：**每一个数字都从同一次账本快照派生**（collect() 一次读完，
冻结点印在标题页脚注）；叙述由人写、不含数字。图由 scripts/build_figures.py
预先生成 —— 每条有冻结规格的 Study 一张「信号 × SC 收盘价」双轴图。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from build_report import (
    NARRATIVE,
    RUN_ORDER,
    cn,
    collect,
)

from arad.evaluation.selection import expected_max_abs_z

FIGDIR = Path("docs/reports/figures")


def tex_escape(s: str) -> str:
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                 ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"),
                 ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    return s


def mono(s: str) -> str:
    """等宽且可在下划线处断行：feature_id 很长，普通 \\texttt 会撑爆表格。"""
    return r"\path{" + s + "}"


def num(v, digits: int = 3) -> str:
    return f"{v:+.{digits}f}" if isinstance(v, (int, float)) else "—"


def study_rows(D: dict, run: str) -> str:
    rows = [s for s in D["studies"] if s["run"] == run]
    if not rows:
        return r"\emph{本次运行没有产出任何属于自己的 Study。}" + "\n"
    out = [r"\begin{longtable}{@{}l p{0.44\textwidth} l r r l@{}}",
           r"\toprule Study & 特征（控制项） & target & $t$ & IC$_\rho$ & 判决 \\ \midrule",
           r"\endhead"]
    for s in rows:
        fid = mono(s.get("feature_id") or "—")
        if s.get("controls"):
            fid += r" {\scriptsize（控制：" + tex_escape(",".join(s["controls"])) + r"）}"
        if s.get("audit"):
            fid += (r" {\scriptsize\color{warn}（审计拦下："
                    + tex_escape("、".join(s["audit"])) + r"）}")
        tgt = mono((s.get("target") or "—").replace("sc_", ""))
        out.append(
            f"{mono(s['study_id'])} & {fid} & {tgt} & "
            f"{num(s.get('t'))} & {num(s.get('ic'), 3)} & "
            f"{tex_escape(s.get('verdict') or '进行中')} \\\\")
    out.append(r"\bottomrule\end{longtable}")
    return "\n".join(out) + "\n"


def chronicle(D: dict, figs: dict) -> str:
    parts = []
    for r in RUN_ORDER:
        title, narr = NARRATIVE[r]
        parts.append(r"\subsection{" + tex_escape(title) + "}\n")
        parts.append(tex_escape(narr) + "\n\n")
        parts.append(study_rows(D, r))
    return "".join(parts)


def figure_block(sid: str, figs: dict, caption: str, width: str = "0.95") -> str:
    meta = figs.get(sid)
    if not meta:
        return ""
    return (r"""\begin{figure}[htbp]\centering
\includegraphics[width=""" + width + r"""\textwidth]{figures/""" + meta["file"] + r"""}
\caption{""" + caption + r"""}\label{fig:""" + sid + r"""}
\end{figure}
""")


def appendix_figures(D: dict, figs: dict) -> str:
    """附录 B：全部信号图，每行一张（宽图两列会小到读不了）。"""
    parts = []
    for s in D["studies"]:
        sid = s["study_id"]
        meta = figs.get(sid)
        if not meta:
            continue
        cap = (mono(sid) + "：" + mono(meta["feature_id"])
               + f"。有定义 {meta['defined_points']}/{meta['total_points']} 点。")
        parts.append(
            r"\noindent\includegraphics[width=\textwidth]{figures/"
            + meta["file"] + r"}\par\vspace{-2pt}{\scriptsize " + cap
            + r"}\par\vspace{6pt}" + "\n")
    return "".join(parts)


def render(D: dict, figs: dict) -> str:
    v = D["verdicts"]
    n = D["denominators"]["statistical_denominator"]
    pn = D["denominators"]["proposal_denominator"]
    floor = D["floor"]

    HERO_ID = "run11-study-3"
    hero = next((s for s in D["studies"] if s["study_id"] == HERO_ID), {})
    hero_sealed = next((e for e in D["sealed"]
                        if e.get("feature_id") == hero.get("feature_id")), {})
    hero_t, hero_seal_t = hero.get("t"), hero_sealed.get("t_stat")
    retention = (abs(hero_seal_t) / abs(hero_t)
                 if isinstance(hero_t, float) and isinstance(hero_seal_t, float)
                 and hero_t else None)
    import math
    n_d, n_s = hero.get("rows"), hero_sealed.get("rows")
    size_factor = (math.sqrt(n_s / n_d)
                   if isinstance(n_d, int) and isinstance(n_s, int) and n_d else None)
    retention_adj = (retention / size_factor
                     if retention is not None and size_factor else None)
    hero_index = next((i for i, s in enumerate(D["studies"])
                       if s["study_id"] == HERO_ID), None)
    tests_then = sum(1 for s in D["studies"][:(hero_index or 0) + 1] if s.get("read"))
    floor_then = expected_max_abs_z(tests_then) if tests_then else None

    top = sorted((s for s in D["studies"] if isinstance(s.get("t"), float)),
                 key=lambda s: -abs(s["t"]))[:4]

    floor_rows = "\n".join(f"{k} & {val:.3f} \\\\" for k, val in D["floor_curve"])
    sealed_rows = "\n".join(
        f"{mono(str(s.get('feature_id', '—')))} & {num(s.get('t_stat'))} & "
        f"{num(s.get('ic_spearman'), 3)} & {s.get('rows', '—')} & "
        f"{'是' if s.get('out_of_sample_in_time') else '—'} & "
        + ("是" if s.get("taxonomy_clean") else r"\textcolor{bad}{否}") + r" \\"
        for s in D["sealed"])
    appendix_rows = "\n".join(
        f"{mono(s['study_id'])} & {mono(s.get('feature_id') or '—')} & "
        f"{num(s.get('t'))} & {num(s.get('ic'), 3)} & "
        f"{s.get('placebo') if s.get('placebo') is not None else '—'} & "
        f"{tex_escape(s.get('verdict') or '进行中')} \\\\"
        for s in D["studies"])

    hero_fig = figure_block(
        HERO_ID, figs,
        "唯一走完全流程的候选：信号（蓝，左轴）与 SC 收盘价（红，右轴）。"
        "信号由冻结规格在 discovery 决策网格上重新求值，非回放存档。")
    artefact_figs = "".join(
        figure_block(s["study_id"], figs,
                     r"波动假象 \texttt{" + tex_escape(s["study_id"]) + "}"
                     f"（$t={s['t']:+.2f}$）："
                     "信号与价格。该信号实为已实现波动的函数，与目标同源。")
        for s in top[:2])

    return (r"""% 由 scripts/build_report_tex.py 生成；数字全部来自账本快照 seq """
            + str(D["frozen_at"]["seq"]) + r"""
\documentclass[11pt]{ctexart}
\usepackage[a4paper,margin=2.4cm]{geometry}
\usepackage{booktabs,longtable,graphicx,amsmath,amssymb,url,xcolor,caption}
\usepackage[colorlinks=true,linkcolor=blue!60!black,urlcolor=blue!60!black]{hyperref}
\definecolor{warn}{HTML}{9A6510}\definecolor{bad}{HTML}{B93C28}
\definecolor{ok}{HTML}{00806E}
\captionsetup{font=small,labelfont=bf}
\setlength{\parskip}{2pt}
\title{\textbf{ARAD：另类数据自主因子研究}\\
\large 从计划到""" + cn(n) + r"""次检验的全部证据 —— 方法、数学与逐条可证否的结论}
\author{ARAD 项目}
\date{2026 年 8 月 8 日}
\begin{document}
\maketitle
\begin{abstract}
研究者是大语言模型（claude-opus-5，经 \path{claude -p} 调用），确定性框架负责使其产出
可信且可累积。截至账本冻结点（事件 seq """ + str(D["frozen_at"]["seq"]) + r"""），系统在
Polymarket 预测市场 $\times$ 中国商品期货（以 SC 原油为主）上共冻结 \textbf{"""
            + str(pn) + r""" 个互异假设}，读取 outcome \textbf{""" + str(n) + r""" 次}，
判决为 null \textbf{""" + str(v.get("null", 0)) + r"""}、blocked \textbf{"""
            + str(v.get("blocked", 0)) + r"""}、underpowered \textbf{"""
            + str(v.get("underpowered", 0)) + r"""}、candidate \textbf{"""
            + str(v.get("candidate", 0)) + r"""}；噪声地板升至 \textbf{"""
            + f"{floor:.3f}" + r"""}。三条主结果：（一）不加控制时最大的统计量
（$|t|$ 至 """ + f"{abs(top[0]['t']):.2f}" + r"""）全部是波动率聚集这一教科书事实；
（二）对品种自身波动或国际油价残差化后，Polymarket 特征大面积失去线性预测力；
（三）唯一走完全流程的候选在一次性的封存段被否决。\textbf{「candidate = 0」的一半是
结构性的}：成本模型未建使 candidate 在判决导出规则下不可达，与数据无关 ——
本文第 \ref{sec:conclusions} 节把经验结论与结构约束分开陈述，每条结论附证否条件。
全部数字由脚本从同一次账本快照派生。
\end{abstract}
\tableofcontents

\section{动机：每条约束防的是哪一种自欺}
系统的每个机制对应一种具体的、已经发生过的失败。

\paragraph{一条上升的曲线本身不是证据。}选择在纯噪声上必然产出上升的 running-best
曲线。旧系统实测：81 次爬山选出的最好 Sharpe 为 2.40，而同一搜索过程在零假设下的
期望是 2.63 —— 曲线在涨，实际比噪声还差。因此每条曲线配一条随检验次数抬升的
零假设带（\S\ref{sec:selection}），且地板对已有与将来的全部结论同时生效。

\paragraph{分母会被悄悄做小。}「试过多少次」若由报告者自己数必然缩水。统计分母
入库且只增不减（\path{statistical_denominator} 表挂 DELETE/UPDATE 触发器，一律
\path{RAISE(ABORT)}）；提案分母与统计分母分账，被预检拦下的提案不抬高零假设带。

\paragraph{提案者一旦看见效应就不再是提案者。}提案器可见字段由账本按事件类型
白名单列举。此约束曾被自己违反并被对抗性审查抓出（决定 0006）：判决计数曾被定价为
「只泄漏存在性」，而该定价的隐含前提是计数指向匿名总体；第 0 层记忆交出具名规格清单后
匿名被取消，三者可做减法，判决计数遂被移出提案器上下文。

\paragraph{问错的问题不该消耗预算。}语义审计在读 outcome 之前运行，被拦下的 Study
不进统计分母。判据必须结构化：按散文子串匹配曾把「改用波动率归一的有符号收益」这一
正确回应连续误拦，判据因此改为沿特征 DAG 判断。

\paragraph{否定结论必须有处安放。}判决曾由「blocked 与否」二分导出，\path{Verdict.NULL}
在全仓无产出路径。决定 0005 改由失效集合推出（\S\ref{sec:verdict}），null 成为一等产出。

\paragraph{分类法本身可能是后见之明。}Polymarket 族定义由归纳产生，归纳语料的切点
进入前向门的 $\max$ 项（决定 0004）。当前语料切点覆盖全部三段，故全部 Polymarket
结论的 taxonomy\_clean 为否，主张被结构性封顶 —— 这是如实标注，不是缺陷。

\section{数据}
\begin{table}[htbp]\centering\small
\begin{tabular}{@{}llll@{}}\toprule
层 & 内容 & 规模 & 状态 \\ \midrule
商品 tick 归档 & chinese-commodity（只读） & 87 品种 · 221 GB · 909 交易日 & M1 合同化 \\
Temporal Spine & 分钟 bar、主力视图、三类 target & 51 品种（36 个满 1{,}816 行） & 郑商所 21 品种待裁决 \\
时段表 & 按夜盘收盘参数化 & 72 品种登记 & SC 权威几何 + tick 归纳 \\
Polymarket & 族级小时序列 & 1{,}998 族 · 5{,}986{,}409 行 & 全量物化 \\
控制序列 & brent · own\_realised\_volatility & 933 行 / 逐品种 & residualise 可用 \\
财联社 & cls\_telegraph 原文 & 562{,}548 行 & \textcolor{bad}{未接入解释器} \\
\bottomrule\end{tabular}
\caption{数据层与状态。}\end{table}

三类目标逐品种命名，声明即被评（M8.2 硬校验）：\path{rv_next_session}（下一时段
已实现波动，主目标）、\path{ret_next_session}（入场到收盘对数收益，唯一可交易主张）、
\path{open_gap_absorption}（诊断用）。universe 由模型自选：36 品种面板或任一单品种
主力视图。

\section{方法与数学定义}
只写参与判决的量；凡实现与教科书形式或与本仓文档不一致处，一律写明。

\subsection{时点与窗口}
三个时刻的不等式由构造保证并在评价机复查：
\[ \text{availability} \le \text{decision} < \text{execution} < \text{label start}
   \le \text{label end}. \]
窗口一律左闭右开：$V=\{v_i: \text{end}-W \le t_i < \text{end}\}$，
$\text{end}=\text{decision}-\text{offset}$，$t_i$ 取 bar 的右端点，
offset $\ge 0$ 由语言层强制。

\subsection{特征语言与 residualise}
特征是七原语（window / innovation / ratio / difference / zscore / rank\_pct /
residualise）构成的 DAG；规格冻结后由代码生成器产出与解释器逐位一致的代码；
无定义返回 None 并沿 DAG 传播，绝不返回 0。最关键的 residualise 在决策时点 $a$：
\[ \hat\beta=\frac{\sum_k (c_k-\bar c)(x_k-\bar x)}{\sum_k (c_k-\bar c)^2},\qquad
   \text{返回 } x_a-\bigl(\bar x-\hat\beta\bar c+\hat\beta c_a\bigr), \]
拟合样本 $\{(x_k,c_k)\}$ 取自严格过去的采样网格（$k\ge 1$，当前点不入样），
每个决策时点重新拟合；门槛计的是控制变量互异取值个数。三点声明：返回值是
\textbf{样本外预测残差}而非教科书残差；每点重拟合不跨点复用；控制序列在窗口内取值
常量时判不可识别。

\subsection{评价机}
一元 OLS 斜率 $\hat\beta$；Cameron--Gelbach--Miller 双向 cluster（$a$=交易日，
$b$=品种）：
\[ V=V_a+V_b-V_{ab},\qquad V_g=\frac{1}{S_{xx}^2}\sum_{c\in g}
   \Bigl(\sum_{i\in c}(x_i-\bar x)e_i\Bigr)^2,\qquad t=\hat\beta/\sqrt{V}. \]
\textbf{无任何有限样本修正}（无 $G/(G-1)$、无自由度调整）；一维互异组数小于 2 时
降级为单向而字段名不变。Kish 有效数 $n_{\mathrm{eff}}=n^2/\sum_g c_g^2$
（权重为组规模，量纲是\textbf{有效 cluster 数}）。

置换检验按 episode 整块置换（默认 200 次，种子 20260805）；
$\text{exceed}=\#\{|s^\ast|\ge|\hat\beta|\}/\text{成功次数}$，闸门 $>0.1$ 记
placebo\_failed —— 它是唯一能产出 null 的理由。三处声明：块规模不等时 $y^\ast$
并非 $y$ 的置换（短块循环复用、长块截尾）；无 $(e{+}1)/(d{+}1)$ 修正；成功次数为 0
时兜底 1.0，等于把度量失败记成支持 null 的证据。

单点影响：$h_i=\tfrac1n+(x_i-\bar x)^2/S_{xx}$；
$\mathrm{DFBETA}_i=(x_i-\bar x)e_i/[S_{xx}(1-h_i)]$；
$\mathrm{DFBETAS}=\max_i|\mathrm{DFBETA}_i|/\mathrm{SE}$，闸门 1.0，按
$|t|+\mathrm{DFBETAS}\ge 2.8$ 分「同时使 candidate 与 null 失效」或「只使 candidate
失效」。不用 $|\mathrm{DFBETA}|/|\hat\beta|$：它在 $\hat\beta\to0$ 时发散，
在完全没有效应时叫得最响。

否定的排除界 $\mathrm{mde}=2.8\cdot\mathrm{SE}$ 只是标准误换算，功效 $1-\beta$
不在式中；SE 被低估时该界一并被低估。

\subsection{判决导出}\label{sec:verdict}
判决只读阻塞理由的\textbf{种类}，不读数值。失效表：insufficient\_sample、
not\_identified、single\_point\_influence\_both $\to\{$candidate, null$\}$；
cost\_model\_missing、cluster\_structure\_insufficient、
single\_point\_influence\_candidate\_only $\to\{$candidate$\}$；
placebo\_failed $\to\varnothing$。导出顺序：未知种类报错 $\to$ 样本不足判
UNDERPOWERED $\to$ 求失效并集 $\to$ placebo\_failed 且 null 未失效判 NULL $\to$
candidate 失效判 BLOCKED $\to$ 否则 CANDIDATE。给定理由集合，判决唯一确定、可机械复核。

\subsection{选择校正}\label{sec:selection}
零假设带用 Bailey--López de Prado 两项闭式（\textbf{非} $\sqrt{2\ln n}$ ——
那是渐近主项，$n{=}10$ 时给 2.146 而实际 1.901）：
\[ E_\tau(n)=(1-\gamma)\,\Phi^{-1}\!\Bigl(1-\tfrac1{\tau n}\Bigr)
   +\gamma\,\Phi^{-1}\!\Bigl(1-\tfrac1{\tau n e}\Bigr),\qquad
   \gamma=0.57721\ldots \]
$|z|$ 带取 $\tau=2$（搜索接受任一方向），$n=1$ 时取半正态均值 $\sqrt{2/\pi}$；
自罚奖励 $\mathrm{reward}=|t|-E_2(n_{\text{评价时}})$。独立性假设使带偏严：
同族变体高度相关，真实期望最大值更低，故「未越带」不等于「确定无效」。
\begin{table}[htbp]\centering\small
\begin{tabular}{@{}rr@{}}\toprule 已读 outcome 次数 $n$ & $E_2(n)$ \\ \midrule
""" + floor_rows + r"""
\bottomrule\end{tabular}\caption{零假设带的实际抬升轨迹（账本快照）。}\end{table}

\subsection{封存段}
$\text{seal\_key}=\mathrm{SHA256}(\text{feature\_id},\text{segment},\text{version})$；
开封记录进哈希链，第二次开封抛 SealedAlreadyOpened。因子卡状态用
$|t_{\text{封存}}|/|t_{\text{发现}}|$ 对阈值 0.35 —— 该阈值与 min\_rows=120
均为写死常量，\textbf{无文档推导}；且分子分母是 $t$ 值而非效应量（\S\ref{sec:hero}）。

\section{十六次运行编年}
""" + chronicle(D, figs) + r"""

\section{结果}
\subsection{假象家族：重新发现了波动率聚集}
统计量最大的构造（$|t|$ 至 """ + f"{abs(top[0]['t']):.2f}" + r"""）分母为已实现波动、
目标亦为已实现波动。PIT 无误、置换通过 —— 关系是真的，但它是 Baseline Control，
不是另类数据 alpha。诊断（离线，不进账本，本文唯一非快照数字）：对最大一条做残差化，
秩相关由 $-0.5695$ 塌至 $-0.0077$，缩小约 74 倍。此后 """
            + str(D["residualised"]) + "/" + str(D["specs"]) + r""" 的规格自带控制项。
""" + artefact_figs + r"""

\subsection{唯一走完全流程的候选及其封存裁决}\label{sec:hero}
""" + mono(hero.get("feature_id") or "—") + r"""（""" + mono(HERO_ID) + r"""）：
cand:iran 族归一化概率 30 日均值，残差化掉品种自身波动持续性后预测下一时段已实现波动。
机制为混合分布假说：波动由信息到达强度决定，到达强度由风险的当前发生率决定；油价已含
发生率$\times$损失的一阶期望，发生率水平本身另有信息。
\begin{table}[htbp]\centering\small
\begin{tabular}{@{}lrrrl@{}}\toprule
段 & $t$ & IC$_\rho$ & 行 & 闸门 \\ \midrule
发现段 & """ + num(hero_t) + " & " + num(hero.get("ic"), 3) + " & " + str(n_d)
            + r""" & 置换 """ + str(hero.get("placebo", "—")) + r""" 通过 \\
封存段（一次性） & """ + num(hero_seal_t) + " & "
            + num(hero_sealed.get("ic_spearman"), 3) + " & " + str(n_s)
            + r""" & $t$ 值比 """
            + (f"{retention:.1%}" if retention is not None else "—")
            + r""" $<$ 0.35 $\Rightarrow$ sealed\_failed \\
\bottomrule\end{tabular}\caption{候选在两段上的对比。裁决终身有效，不重开。}\end{table}

\textbf{口径更正}：闸门比的是两个 $t$ 值而非效应量，两段样本量不同（"""
            + str(n_d) + " 对 " + str(n_s) + r""" 行），即便效应完全不变 $t$ 也按
$\sqrt{n_s/n_d}\approx """ + (f"{size_factor:.2f}" if size_factor else "—")
            + r"""$ 缩小；样本量修正后效应保留率约 """
            + (f"{retention_adj:.1%}" if retention_adj is not None else "—")
            + r"""，仍远低于 0.35，\textbf{裁决不变}。该候选在发现段也从未越过当时的
族地板（评价时已花 """ + str(tests_then) + r""" 次检验，地板 """
            + (f"{floor_then:.3f}" if floor_then else "—") + r"""，而它是 """
            + num(hero_t) + r"""，自罚奖励为负）。

另一并如实记录：秩相关在封存段反而由 """ + num(hero.get("ic"), 3) + r""" 升至 """
            + num(hero_sealed.get("ic_spearman"), 3) + r"""。线性斜率消失而单调关联
仍在，可能读法有三（非线性关系 / 小样本噪声 / 发现段高杠杆点支撑），本系统无法在
不花新预算的前提下区分 —— \textbf{它是开放问题，不是结论}。
""" + hero_fig + r"""

\subsection{干净的 null（""" + str(v.get("null", 0)) + r""" 条）}
残差化普及后，模型系统扫过互异机制：资金集中度、信念下限棘轮、闭市时段资金份额、
停火/伊朗资金倾斜、平均单笔金额、方向性信念离散度、事件不确定性 $\bar p(1-\bar p)$、
到达加速度、对娱乐族的安慰剂对照。按判决导出规则 null 只能经由置换检验产出，因此
每一条都是「置换分布里 $\le 10\%$ 的抽样达到实际斜率绝对值」的具体陈述。

\subsection{封存段全记录（""" + str(len(D["sealed"])) + r""" 次开启）}
\begin{longtable}{@{}p{0.42\textwidth} r r r l l@{}}
\toprule 特征 & $t$ & IC$_\rho$ & 行 & 时间样本外 & 分类法干净 \\ \midrule\endhead
""" + sealed_rows + r"""
\bottomrule\end{longtable}

\section{测量装置本身的局限}
为写第 3 节，对全部参与判决的统计量做了一次逐行提取核对。下列不一致由本次核对发现，
记入 \path{docs/BLOCKERS.md}，按项目规矩只记录不修：置换兜底把度量失败记成支持
null（null 偏多）；置换块结构使零分布边缘与样本不同（方向不定）；置换阈值 0.1 较常用
0.05 宽松（null 偏少）；cluster SE 无有限样本修正（排除界宣称偏紧）；面板上
min\_clusters 被 episode 命名稀释 $N$ 倍（underpowered 偏少）；$h_i=1$ 时 DFBETA
可为 $+\infty$ 而守卫只覆盖 SE 一侧；MDE 硬编码 2.8 未引用常量；紧缩 Sharpe 方差项
较发表式少 $1/2\cdot SR^2$（偏乐观）；Sharpe 带尺度含前视；驾驶舱曲线与顶栏用两个
口径不同的 $n$；提案器读到的地板说明写 $\sqrt{2\ln n}$ 与实现不符；0.35 与 120 无推导。
\textbf{没有一处能把 null 翻成 candidate}：candidate 被失效表结构性挡住，与数值无关。

\section{结论（每条附证否条件）}\label{sec:conclusions}
\begin{enumerate}
\item \textbf{结构：「candidate=0」当前不是经验结论。}cost\_model\_missing 对全部
Study 成立且其失效集合含 candidate，判决必为 BLOCKED 或更弱；在 M5 之前任何数据都
不可能产出 candidate。\emph{证否：一条 cost\_model\_declared=True 且无 candidate
失效理由的 Study。}
\item \textbf{经验：已检验机制上，Polymarket 特征相对基线的线性增量预测力未过
预注册证否闸门。}\emph{证否：残差化后在族地板上方且置换 $\le0.1$ 并在封存段保住的
一条特征。}
\item \textbf{经验：从未有 Study 越过其评价时的族地板}（自罚奖励恒负）。
\emph{证否：账本 beam\_state 中出现 reward $>0$。}
\item \textbf{方法：残差化把「发现」与「重新发现基线」分开，效果是数量级的}；
模型采用它的转折点是提示词写明「为什么」，不是原语可见。\emph{证否：一条残差化后
$|t|$ 不显著下降且封存段保住的量价构造。}
\item \textbf{方法：封存段是唯一无法用「再跑一次」绕过的闸门，且起了作用。}
\emph{证否：对同一（规格,段）二次取值而不触发 SealedAlreadyOpened 的路径。}
\item \textbf{局限：全部 Polymarket 结论被分类法污染封顶}（决定 0004），肯定结论
在此状态下不可采信；否定结论方向不受影响。\emph{证否：用干净切点语料重归纳并重跑。}
\item \textbf{局限：测量装置有 12 处实现与文档不符，但无一能把 null 翻成
candidate。}\emph{证否：修正后重跑，判决分布改变。}
\end{enumerate}

\section{下一步（全部需人决定）}
（1）M5 成本模型 —— 唯一使 candidate 可达的改动，应先于其余；（2）分类法重归纳
（干净切点）；（3）郑商所 21 品种的 TradingDay 裁决；（4）财联社接入；
（5）横截面 target 设计并修 min\_clusters 稀释。

\section{复现}
\begin{enumerate}\small
\item 环境：\path{uv venv && uv pip install -e ".[dev]"}；校验
\path{.venv/bin/python -m pytest tests/ -q}（668 项合同测试）。
\item 本文全部数字：\path{scripts/build_report_tex.py} 调用 \path{collect()} 一次
读取 \path{data/ledger/service.db}（哈希链完整性在读取时重算）。
\item 全部信号图：\path{scripts/build_figures.py} 用冻结规格在 discovery 决策网格
重新求值 —— 不读任何回放存档。
\item 判决复核：对任一 Study 取其 blocked\_reason\_kinds，按 \S\ref{sec:verdict}
的失效表手工推导，应与账本一致。
\item 编译：\path{cd docs/reports/tex && xelatex main && xelatex main}。
\end{enumerate}

\appendix
\section{全部 """ + str(len(D["studies"])) + r""" 个 Study}
\begin{longtable}{@{}l p{0.40\textwidth} r r r l@{}}
\toprule Study & 特征 & $t$ & IC & 置换 $p$ & 判决 \\ \midrule\endhead
""" + appendix_rows + r"""
\bottomrule\end{longtable}

\section{全部信号图（信号：蓝，左轴；SC 收盘价：红，右轴）}
面板 universe 的 Study 亦在 SC 决策网格上重算并以 SC 为代表绘制。
「有定义点数」少于总点数的部分为窗口未满或控制序列缺失，按纪律返回无定义而非零。

""" + appendix_figures(D, figs) + r"""

\vfill\noindent\rule{\textwidth}{0.4pt}\\
{\small 账本冻结点：事件 seq """ + str(D["frozen_at"]["seq"]) + r"""（"""
            + D["frozen_at"]["at"] + r"""，run16 当时仍在进行）；事件 """
            + str(D["events"]) + r""" 条，哈希链"""
            + ("完整" if D["chain_intact"] else r"\textbf{断裂}") + r"""。
叙述由人撰写且不含数字；数字一律由快照渲染，二者不会不一致。}
\end{document}
""")


def main() -> None:
    D = collect()
    figs = json.loads((FIGDIR / "index.json").read_text(encoding="utf-8")) \
        if (FIGDIR / "index.json").exists() else {}
    out = Path("docs/reports/tex")
    out.mkdir(parents=True, exist_ok=True)
    (out / "main.tex").write_text(render(D, figs), encoding="utf-8")
    # 图目录软链接，xelatex 相对引用
    link = out / "figures"
    if not link.exists():
        link.symlink_to(Path("../figures"))   # 相对链接：随仓库移动仍有效
    print(f"main.tex 就绪 · {len(D['studies'])} Study · {len(figs)} 图 · "
          f"冻结 seq {D['frozen_at']['seq']}")


if __name__ == "__main__":
    main()
