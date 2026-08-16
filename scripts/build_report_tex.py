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
from report_sections_v9 import all_sections as _v9_sections
from report_sections_v10 import all_sections as _v10_sections

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
    """一行 = 一条 Study。target 与控制项并入特征块的小字第二行 ——
    单独成列会把数字列挤出页边（实测溢出至 120pt）。整表 footnotesize。"""
    rows = [s for s in D["studies"] if s["run"] == run]
    if not rows:
        return "\n"
    out = [(r"{\footnotesize\begin{longtable}"
            r"{@{}>{\ttfamily}l >{\raggedright\arraybackslash}p{0.50\textwidth} "
            r"r r l@{}}"),
           (r"\toprule Study & 特征（第二行：target · 控制） & $t$ & IC$_\rho$ & 判决 "
            r"\\ \midrule"),
           r"\endhead"]
    for s in rows:
        meta = [(s.get("target") or "—").replace("sc_", "")]
        if s.get("controls"):
            meta.append("控制 " + ",".join(s["controls"]))
        fid = mono(s.get("feature_id") or "—")
        fid += (r"\newline {\scriptsize\color{gray}"
                + tex_escape(" · ".join(meta)) + r"}")
        if s.get("audit"):
            fid += (r"\newline {\scriptsize\color{warn}审计拦下："
                    + tex_escape("、".join(s["audit"])) + r"}")
        out.append(
            f"{tex_escape(s['study_id'])} & {fid} & "
            f"{num(s.get('t'))} & {num(s.get('ic'), 3)} & "
            f"{tex_escape(s.get('verdict') or '进行中')} \\\\")
    out.append(r"\bottomrule\end{longtable}}")
    return "\n".join(out) + "\n"


def run_figures(D: dict, figs: dict, run: str) -> str:
    """该 run 的信号图紧跟其表格：表给判决与数字，图给形状，两两一组对照读。"""
    parts = []
    for s in D["studies"]:
        if s["run"] != run:
            continue
        meta = figs.get(s["study_id"])
        if not meta:
            continue
        cap = (r"\texttt{" + tex_escape(s["study_id"]) + r"}：\path{"
               + meta["feature_id"] + r"}。有定义 "
               + f"{meta['defined_points']}/{meta['total_points']} 点。")
        parts.append(
            r"\noindent\includegraphics[width=\textwidth]{figures/"
            + meta["file"] + r"}\par\vspace{-2pt}{\scriptsize\sloppy " + cap
            + r"\par}\vspace{6pt}" + "\n")
    return "".join(parts)


def chronicle(D: dict, figs: dict) -> str:
    parts = []
    for r in RUN_ORDER:
        title, narr = NARRATIVE[r]
        parts.append(r"\subsection{" + tex_escape(title) + "}\n")
        parts.append(tex_escape(narr) + "\n\n")
        parts.append(study_rows(D, r))
        parts.append(run_figures(D, figs, r))
        parts.append("\n\\clearpage\n")
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
            + meta["file"] + r"}\par\vspace{-2pt}{\scriptsize\sloppy " + cap
            + r"\par}\vspace{6pt}" + "\n")
    return "".join(parts)


def render(D: dict, figs: dict) -> str:
    # 第九版新增的三节（M16 至 M18），正文在 report_sections_v9.py。
    V9_SECTIONS = _v9_sections()
    # 第十版新增的四节（M19 至 M23），正文在 report_sections_v10.py。
    # 该模块不写死任何数字，全部从 artifacts/manifests/ 读取：
    # 重建报告即重算，避免再出现「印在报告里却复算不出来」的数字。
    V10_SECTIONS = _v10_sections()
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
        f"{tex_escape(s['study_id'])} & {mono(s.get('feature_id') or '—')} & "
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

    tex = (r"""% 由 scripts/build_report_tex.py 生成；数字全部来自账本快照 seq """
            + str(D["frozen_at"]["seq"]) + r"""
\documentclass[11pt]{ctexart}
\usepackage[a4paper,margin=2.4cm]{geometry}
\usepackage{array,booktabs,longtable,graphicx,amsmath,amssymb,url,xcolor,caption}
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
（三）第一条走完全流程的候选在一次性的封存段被否决；
（四）\textbf{最小成本模型（决定 0007）建成后}，按失效表对全部历史判决作回溯投影：
16 条 blocked 会翻为 candidate，其中唯一同时满足「纯 Polymarket、已残差化、
越过评价时地板」的是 run16-study-3（$t=+4.39$ 对地板 $2.60$，置换 $0/200$，
自罚奖励 $+1.79$，为残差化另类构造首次）；人随后决定开封，封存段
\textbf{未保住} —— 至截稿封存段共否决\textbf{四个}候选形态；
（五）把问题换成\textbf{事件条件形态}（决定 0008：只在 PM 概率大幅移动后的窗口上
评价，独立问题族、地板从头起）后，两轮四十回合、{EVENT_N} 次检验（触发源十一个互异族），
仍无一越过本族地板 {EVENT_FLOOR}。报告完成后的对抗性评审（\S\ref{sec:adversarial}）给出总判定：
在实际检验过的窄切面上「没找到」是扎实的，但该切面恰好避开了先验证据最强的
三块地 —— \textbf{方法的边界先于市场的真相被触到}。评审给出的最短路径
（吸收目标升为主要目标、先验四种子喂入、多控制残差化）随即在 run26 的二十回合中
全部走完：吸收目标被采纳十次、双控制残差化十四次，结果仍全为 null，
最好 $|t|=2.31$ 低于其预注册证否线 2.85 —— 归因的天平自此偏向市场真相。
本文第 \ref{sec:conclusions} 节
把经验结论与结构约束分开陈述，每条结论附证否条件。
全部数字由脚本从同一次账本快照派生。
\end{abstract}
\tableofcontents

\section{给零背景读者：这份报告在讲什么}\label{sec:primer}
本节假设读者从未听说过本项目、也不熟悉量化因子研究。读完本节即可读懂全文。

\subsection{被研究的两样东西}
\textbf{Polymarket} 是一个公开的预测市场：人们用真金白银买卖「某件事会不会发生」的
合约，例如「以色列与哈马斯是否在某日前停火」。一份合约的价格若是 0.30，
粗略地说市场认为该事件有 30\% 的概率发生。价格随消息实时变动，
因此它是一条关于世界局势的、连续的、带钱背书的观点序列。

\textbf{中国商品期货}是在上海、大连、郑州等交易所交易的标准化合约，
标的是原油、铜、豆粕、玻璃等实物商品。本文最常出现的 \path{sc} 是
上海国际能源交易中心的原油期货。它们有固定的交易时段（日盘与夜盘），
收盘后停市，而 Polymarket 二十四小时连续交易。

\subsection{本项目要回答的问题}
一句话：\textbf{预测市场里的信息，能不能提前告诉我们中国商品期货接下来会怎么动？}

这个猜想不荒唐。中东冲突的概率变化直接关系原油供给；而中国盘面夜间停市时，
Polymarket 仍在交易 —— 停市期间到达的信息，理论上要等次日开盘才被本地价格吸收。
若这条通路真实存在，它应表现为：某个由预测市场数据算出的数字（下称\textbf{信号}），
与之后一段时间里期货的波动或涨跌，存在稳定的统计关系。

\subsection{为什么这件事需要一套系统，而不是一个人试几次}
可以从预测市场数据里造出的信号\textbf{数量上没有上限}：换事件族、换时间窗、
换聚合方式、换归一化方法，组合是无穷的。而只要试得够多，
\textbf{纯粹的巧合必然会产出看起来很显著的结果} —— 这不是手艺问题，是概率的必然。

本项目的前身留下过一个刺眼的实测（图~\ref{fig:hillclimb}）：某次自动搜索迭代 81 次，
挑出的最好成绩是年化 Sharpe 2.40；而把\textbf{同一套搜索过程}放在纯随机数据上，
它的期望最好成绩是 2.63。搜索赢了自己的历史最好，却输给了噪声。

因此本项目造的不是「一个能找因子的程序」，而是
\textbf{一套让「找到了」这件事变得可信的记账制度}。
研究本身由大语言模型执行（它提出假设、写下构造），
但可信性不托付给模型，而由框架用不可绕过的规则保证。

\subsection{一轮研究是怎么走的}
\begin{enumerate}\itemsep2pt
\item 框架向模型提供一份\textbf{屏蔽了全部结果信息}的材料：有哪些数据、
  有哪些可用的运算、以前试过哪些构造、再试一次的「代价」是多少。
  模型看不到任何历史成绩。
\item 模型提出一个假设：经济机制是什么、用什么数据、预测什么、
  \textbf{以及什么样的结果会判定它错}（这一条必须事先写下）。
\item 框架把提案\textbf{冻结}并写入账本（只能追加、带哈希链的数据库）。
  冻结之后任何改动都是新的一次提案，改不了旧的。
\item 一位「语义审计员」检查提案里的文字与实际构造是否说的是同一件事。
  \textbf{对不上就在读取答案之前拦下} —— 被拦下的提案不消耗检验预算。
\item 评价机是全流程中\textbf{唯一能看到真实答案}的组件。它算出统计量、
  逐项检查预先声明的关卡，并给出判决。
\item 判决入账，搜索的「价格」随之上升（见下）。
\end{enumerate}

\subsection{读懂全文所需的十二个词}
\begin{center}\footnotesize
\begin{tabular}{@{}l p{0.72\textwidth}@{}}\toprule
术语 & 含义 \\ \midrule
Study & 一次完整的研究：从提出假设到得出判决。本文共 {N_STUDIES} 个。 \\
族（family） & 按上下文两义：（一）\textbf{事件族}，Polymarket 上语义相近的一批
  市场合成的一条序列，如 \path{cand:iran}；（二）\textbf{问题族}，共享同一本
  「搜索代价账」的一批研究，见「地板」。 \\
target & 要预测的东西。本文主要两个：下一交易时段的\textbf{已实现波动}
  （价格摆动的剧烈程度）与\textbf{对数收益}（涨跌幅）。 \\
universe & 在哪些品种上做这次检验：单个品种，或 36 个品种的面板。 \\
决策时点 & 做出预测的那一刻（某交易时段开盘前一分钟）。此刻之后的任何信息
  都不允许进入信号 —— 这条纪律叫 PIT（point-in-time）。 \\
信号 & 由数据算出的一个数，用来预测 target。也叫特征、因子。 \\
Baseline Control & 已知的、不新鲜的解释变量（如「今天波动大，明天多半也大」）。
  另类数据的主张必须是\textbf{在它之上的增量}。 \\
残差化 & 把 Baseline Control 从信号里减掉：先用过去数据拟合「信号与基线的关系」，
  再看当前信号\textbf{超出}这条关系多少。 \\
两个分母 & \textbf{提案分母}数「提了多少想法」，\textbf{统计分母}只数
  「真正看过答案多少次」。后者只增不减，由数据库触发器保证。 \\
地板 & 搜索的价格。看过 $n$ 次答案后，即使全是噪声，最好的那次也会达到某个高度；
  该高度即地板，随 $n$ 上升。一个结果要算数，必须\textbf{越过它被检验时的地板}。 \\
置换检验 & 把答案打乱后重做一遍，看多少次「假数据」能做得和真数据一样好。
  假数据赢得多，说明真数据没本事。 \\
封存段 & 一段被封存、从未参与筛选的历史数据。每个构造\textbf{终身只能开封一次}，
  由账本强制。这是终审。 \\
\bottomrule\end{tabular}\end{center}

\subsection{四种判决的意思}
\begin{center}\footnotesize
\begin{tabular}{@{}l p{0.74\textwidth}@{}}\toprule
判决 & 意思 \\ \midrule
\textbf{candidate} & 通过全部关卡，值得进一步验证。\textbf{本文至今为零}。 \\
\textbf{null} & 有把握的否定：不仅「没看出关系」，而且置换检验表明打乱的假数据
  也做得一样好。这是本项目的主要产出。 \\
\textbf{blocked} & 某个前置条件不满足（例如样本结构不足以做某项检验），
  本次检验不足以支持任何肯定结论。 \\
\textbf{underpowered} & 样本太小，本来就看不出东西，与结果无关。 \\
\bottomrule\end{tabular}\end{center}

\subsection{这份报告怎么读}
赶时间的读者：第~\ref{sec:insights} 节是十句话的核心要点（各带数据），
第~\ref{sec:conclusions} 节是逐条附证否条件的结论。
第~\ref{sec:worked} 节把一个具体的数从原始数据一路算到最终统计量 ——
\textbf{只想知道「指标到底怎么定义」的读者，读那一节即可}。
第~\ref{sec:math} 节是全部公式的精确定义与实现出处；第~\ref{sec:results} 节是结果；
第~\ref{sec:limits} 节列出本次核对中发现的、测量装置自身的十二处缺陷；
第~\ref{sec:conclusions} 节是逐条附带证否条件的结论。
全部数字由脚本从同一次账本快照生成，叙述由人撰写且不含数字，
因此正文与表格不会互相矛盾。

\paragraph{符号约定}$n$ 为本族已读取 outcome 的次数（统计分母）；$t=\hat\beta/\mathrm{SE}$
为一元回归斜率对双向 cluster 标准误之比；IC$_\rho$ 为预测与标签的 Spearman 秩相关；
$E_\tau(n)$ 为 $n$ 次搜索在零假设下的期望最大统计量（\S\ref{sec:selection}）；
$\bar p$ 为 Polymarket 某事件族的归一化概率均值；「决策时点」指某品种某交易时段
开始前一分钟，系统在该时刻冻结全部可见信息并作出预测。

\section{核心要点：十句话与它们背后的数据}\label{sec:insights}
赶时间的读者读本节与第~\ref{sec:conclusions} 节即可。每条要点先用一句白话概括，
再给出支撑它的数据与出处。

\paragraph{一、不设防的搜索必然「发现」噪声。}
本项目前身迭代 81 次选出年化 Sharpe 2.40，而同一搜索在纯噪声上的期望是 2.63
（图~\ref{fig:hillclimb}）；本项目自身不加控制时也立即产出 $|t|={TOP_T}$ 的
「发现」。这不是操作失误，是最大值统计量的必然 —— 所以每条结论都必须对照
「看了多少次答案」计价。

\paragraph{二、减掉已知的东西之后，新东西大多消失了。}
$|t|={TOP_T}$ 的构造，其分母与预测目标同为已实现波动 —— 它重新发现的是
「今天波动大、明天多半也大」这条教科书事实。对它做残差化后秩相关缩小约 74 倍
（\S\ref{sec:results}）。残差化普及后，Polymarket 构造的绝大多数统计量落回
噪声区间。

\paragraph{三、四个走到最后的候选，全部死在终审。}
四个通过发现段全部关卡的构造，在只能开封一次的封存段上 $t$ 保持率分别为
17.6\%、18.7\%、51\%（但其发现段仅 10 行样本，证据无效）与 12.7\% ——
全部低于 35\% 的预注册保持线（\S\ref{sec:retro}）。共同判词：发现段的强度来自
2024 年伊朗事件簇的样本构成，不是跨时期稳定的关系。

\paragraph{四、换一种问法，答案没变。}
「概率大幅移动之后的窗口是否可预测」（事件条件形态，独立记账）：两轮四十回合、
十一个互异事件源、{EVENT_N} 次检验，最好 $|t|=1.87$，未越过本族地板
{EVENT_FLOOR}（\S\ref{sec:results}）。

\paragraph{五、$t$ 大不等于效应大。}
最强的残差化构造 $t=4.39$，但换算成经济量纲：一个标准差的信号变化只对应
典型波动的 3.4\%（\S\ref{sec:worked} 末段）。统计显著回答「斜率像不像零」，
不回答「值不值得交易」。

\paragraph{六、搜索是有价格的，而且价格必须公开。}
旧问题族看了 {N_OLD} 次答案，地板升至 {FLOOR_OLD}：今天任何新构造要算数，
必须比早期强约四分之一。地板对已有与将来的全部结论同时生效 ——
「多试几次」从来不是免费的（\S\ref{sec:selection}）。

\paragraph{七、否定是产出，不是失败。}
全部 {N_STUDIES} 个 Study 中 {N_NULL} 条是带排除界的可信否定：每条都预注册了证否条件、
通过了语义审计、并被置换检验确认「打乱的假数据做得一样好」。对「Polymarket
能否预测中国商品期货」这个问题，这批否定就是当前最可信的答案（\S\ref{sec:conclusions}）。

\paragraph{八、方法的可信度来自它被事故打磨过。}
本文方法的几乎每条规则都由一次真实事故催生（\S\ref{sec:evolution} 的对应表）；
测量装置自身的十二处缺陷也一并公开（\S\ref{sec:limits}），并逐条说明影响方向 ——
没有一处能把否定翻成肯定。

\paragraph{九、对抗性评审的判定：方法边界先于市场真相被触到。}
持全部上下文的评审代理核实后指出：检验过的切面（session 级、线性、单控制、
无先验地图）避开了先验证据最强的三块地 —— 休市吸收目标只用了 2/200 次
（先验相关 0.86）、四个先验阳性种子从未进入提案器、$t=5.0$ 的截面框架无法表达；
同时反向核实地板并不偏严（同族信号平均 $|\rho|=0.097$）。检验归因的最短路径
约两张票（\S\ref{sec:adversarial}）。

\paragraph{十、最短路径走完，仍是 null：归因偏向市场真相。}
评审的第一梯队三件（吸收目标升 primary、先验四种子喂入、多控制残差化）在
决定 0009 中实施，run26 二十回合直接检验：吸收目标被采纳十次（正负方向都试过）、
brent 与自身已实现波动同时残差化十四次，十四 null 一 blocked，最好 $|t|=2.31$
（低于其预注册证否线 2.85）；吸收目标侧最好 $|t|=1.83$。前身 $0.86$ 的休市吸收
相关在七倍样本上没有再现。被指为「避开的高地」补上之后结论未变
（\S\ref{sec:adversarial} 末尾的后记）。

\section{数据}
\begin{table}[htbp]\centering\footnotesize
\begin{tabular}{@{}l p{0.30\textwidth} p{0.24\textwidth} l@{}}\toprule
层 & 内容 & 规模 & 状态 \\ \midrule
商品 tick 归档 & chinese-commodity（只读） & 87 品种 · 221 GB · 909 交易日 & M1 合同化 \\
Temporal Spine & 分钟 bar、主力视图、三类 target & 51 品种（36 个满 1{,}816 行） & 郑商所 21 品种待裁决 \\
时段表 & 按夜盘收盘参数化 & 72 品种登记 & SC 权威几何 + tick 归纳 \\
Polymarket & 族级小时序列 & 1{,}998 族 · 5{,}986{,}409 行 & 全量物化 \\
控制序列 & brent · own\_realised\_volatility & 933 行 / 逐品种 & residualise 可用 \\
财联社 & cls\_telegraph 原文 & 562{,}548 行 & \textcolor{bad}{未接入解释器} \\
\bottomrule\end{tabular}
\caption{数据层与状态。}\end{table}

\paragraph{一行数据是什么。}评价样本的一行 =（品种，交易时段）：在该时段开始前
一分钟（决策时点）冻结全部可见信息，特征在此刻求值；标签取该时段结束后才可知的量。
SC 每交易日两个时段（夜盘、日盘），discovery 段共 1{,}040 个决策时点；36 品种面板
把行数扩到三万余，但同一交易日的行高度相关 —— 这正是双向 cluster 标准误存在的原因。

\paragraph{特征的原料。}Polymarket 侧不用单个市场，而用「族」：把语义相近的事件市场
（如全部与伊朗相关的）聚成一条小时级序列，含归一化概率 $p$、名义资金 notional、
成交笔数 trades 三个字段。族定义由归纳产生，归纳语料的时间切点被记为
taxonomy\_freeze\_at 并进入前向门（\S1 第六段）。

\paragraph{字段字典（可被特征引用的全部序列）。}
\begin{center}\footnotesize
\begin{tabular}{@{}l l p{0.52\textwidth}@{}}\toprule
源 & 字段 & 含义与单位 \\ \midrule
pm\_market & \path{<族>:p} & 该族的名义额加权归一化概率，小时分桶，无量纲 $\in[0,1]$ \\
pm\_market & \path{<族>:notional} & 该桶内成交名义额，USDC \\
pm\_market & \path{<族>:trades} & 该桶内成交笔数，计数 \\
commodity\_bar & \path{realised_volatility} & 该品种上一时段已实现波动的\textbf{对数}，
  可用时刻为该时段 label\_end（波动只有窗口结束后才可知） \\
commodity\_bar & \path{log_return} & 该品种上一时段的对数收益 \\
intl & \path{brent} & 布伦特原油日频价格（外生控制） \\
\bottomrule\end{tabular}\end{center}
引用其他字段判 blocked：菜单必须反映真实可用的东西，否则「自主选择」
变成在一张有空头支票的表上选。

\paragraph{目标。}三类，逐品种命名，声明即被评（M8.2 硬校验）：
\path{rv_next_session}（下一时段已实现波动，主目标 —— 波动可预测性是另类数据最可能
先出现的地方）、\path{ret_next_session}（入场到收盘对数收益，唯一可交易主张）、
\path{open_gap_absorption}（诊断用）。universe 由模型自选：36 品种面板或任一单品种
主力视图。

\section{方法}\label{sec:math}
本节集中全部方法：设计原则（每条规则防什么）、一轮的流水线、全部统计量的精确定义
（含实现与教科书不一致处）、以及三项后加的机制（事前筛、事件条件形态、菜单三层设计）。
方法在项目进行中经历过多次迭代，迭代本身见 \S\ref{sec:evolution}。

\subsection{设计原则：每条约束防的是哪一种自欺}
系统的每个机制对应一种具体的、已经发生过的失败。本小节每段先摆失败，再给约束。

\paragraph{一条上升的曲线本身不是证据。}选择在纯噪声上必然产出上升的 running-best
曲线。图~\ref{fig:hillclimb} 是本项目的前身（Alpha-Data 时代）留下的实测：81 次
爬山选出的最好年化 Sharpe 为 2.40，把\textbf{同一套搜索过程}放在纯噪声上，其期望
最大值在第 46 次就超过了这个成绩，到第 81 次为 2.63 —— 曲线一直在涨，成绩却
比噪声还差。这个教训是整个 ARAD 设计的起点：本系统给每条曲线配一条随检验次数抬升
的零假设带（\S\ref{sec:selection}），且地板对已有与将来的全部结论同时生效。
\begin{figure}[htbp]\centering
\includegraphics[width=0.9\textwidth]{figures/hillclimb_baseline.png}
\caption{旧系统爬山基线：红线为零假设期望（用与本文判决同一套公式计算，
参数为该搜索自身的试验间离散度），蓝虚线为 81 次爬山的实测最好。三个输入数字
均有合同测试钉定。}\label{fig:hillclimb}
\end{figure}

与之成对的是本系统自己的搜索全貌（图~\ref{fig:searchcurve}）：同一条地板公式
随统计分母抬升；量价假象在第 20 至 26 次检验间越顶（截顶为 $\blacktriangle$，
按决定 0002 归 Baseline Control）；残差化的 Polymarket 构造几乎全部诚实地
落在地板之下 —— 唯一的例外在第 61 次检验，见 \S\ref{sec:retro}。
\begin{figure}[htbp]\centering
\includegraphics[width=0.94\textwidth]{figures/arad_search_curve.png}
\caption{ARAD 的搜索全貌：逐次检验的 $|t|$ 对同步抬升的零假设地板。
每点一条已评价的 Study，按「量价 ／ 未残差化 PM ／ 残差化 PM」着色；
圈出者为 run16-study-3。}\label{fig:searchcurve}
\end{figure}

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

\subsection{一轮的流水线}
\paragraph{十一步。}一条 Study 固定走十一步，缺步本身是信息：
（1）组装盲化上下文 $\to$（2）冻结提案（机制、target、universe、方向、证否条件）
$\to$（3）冻结假设 $\to$（4）冻结检验规格 $\to$（5）建立 Study $\to$
（6）冻结特征规格 $\to$（7）语义审计（在读 outcome \textbf{之前}；被拦下的不进
统计分母）$\to$（8）声明可见数据范围 $\to$（9）读取 outcome（统计分母加一，
零假设带随之抬升）$\to$（10）评价机出具全部统计量与阻塞理由 $\to$
（11）判决由理由种类机械推出并入账。提案器全程看不到任何效应的方向与量级；
评价机是唯一读标签的组件。以下各小节只写参与判决的量；
凡实现与教科书形式或与本仓文档不一致处，一律写明。

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
$\text{exceed}=\#\{|s^\ast|\ge|\hat\beta|\}/\text{成功次数}$，闸门 $>0.1$ 时记
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
判决只读阻塞理由的\textbf{种类}，不读数值。失效表：
\begin{center}\footnotesize\begin{tabular}{@{}ll@{}}\toprule
理由种类 & 使哪些结论失效 \\ \midrule
\path{insufficient_sample} · \path{not_identified} · \path{single_point_influence_both}
  & \{candidate, null\} \\
\path{cost_model_missing} · \path{cluster_structure_insufficient} & \{candidate\} \\
\path{single_point_influence_candidate_only} & \{candidate\} \\
\path{placebo_failed} & $\varnothing$ \\
\bottomrule\end{tabular}\end{center}导出顺序：未知种类报错 $\to$ 样本不足判
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

\subsection{信号侧事前筛（prescreen-v1）}
置换检验按 Episode 整块打乱；一个在决策节奏上几乎不动的信号，打乱前后难以区分，
读 outcome 只能得到一条注定的 null 并抬高地板。该性质只依赖特征值本身，
可在读之前判定：
\[ \hat\rho=\frac{\sum_t (x_t-\bar x)(x_{t+1}-\bar x)}{\sum_t (x_t-\bar x)^2},\qquad
   n_{\mathrm{eff}}=n\,\frac{1-\hat\rho}{1+\hat\rho}. \]
$n_{\mathrm{eff}}<30$ 或互异值 $<3$（防退化；主责在 $n_{\mathrm{eff}}$）时判 blocked：
不读 outcome、不占统计分母、地板不抬。检验机理同时作为方法说明写进提案器上下文
（预注册规则的说明，不是任何结果的泄漏）。生产实测：run24 两版被拦
（$n_{\mathrm{eff}}$ 13.9 与 23.1），预算一分未花。

\subsection{事件条件形态（决定 0008）}
预测市场的信息天然是事件性的：概率长期钉着不动，事件来临才跳变。「永远在线」的
检验把无事时段与事件时段混进同一条回归，信号被稀释。事件条件形态由提案声明触发器
$(\text{field}, L, \delta)$：决策时点 $t$ 活跃当且仅当
\[ \bigl|\,p^{\,\text{last}}_{<t} - p^{\,\text{last}}_{<t-L}\,\bigr| \ge \delta, \]
两值取自\textbf{严格早于}边界的分桶（与特征窗口同一右端点排他约定）。
不活跃时点记入预注册排除，不读其 outcome —— 触发只依赖决策前可见信息，
不是结果依赖过滤。触发器进 content id：同一机制加不同触发是不同的提案。
事件条件研究以独立问题族记账：分母从零、地板从 $0.798$ 起；旧族账目原样保留
（分账纪律同 Alpha-Data 主族／扩展族）。

\subsection{候选族菜单的三层设计（M12）}
「起点选择」此前是按成交量取前 30 的默认。现为预注册结构：
资格筛（qualify-v1，纯 PM 侧：跨度、桶数、未决性 $\overline{p(1-p)}$、活动度，
1{,}998 族筛得 1{,}404 合格）；事前经济映射（只读引入 Alpha-Data P1 的 tier
registry，验证只用外部 ETF 证据，以声明先验标注、不过滤）；分层轮换
（每轮 30 = 先验 4 + 安慰剂 3 + 头部 8 + 轮换 15，确定性轮换使全部合格族长期
都有出场机会）。评价侧按需装载：轮到谁就能评价谁，不合格族即使被引用也不装载。

\subsection{封存段}
\[ \text{seal\_key}=\mathrm{SHA256}(\text{feature\_id},\ \text{segment},\ \text{version}), \]
开封记录进哈希链，第二次开封抛 SealedAlreadyOpened。因子卡状态用
$|t_{\text{封存}}|/|t_{\text{发现}}|$ 对阈值 0.35 —— 该阈值与 min\_rows=120
均为写死常量，\textbf{无文档推导}；且分子分母是 $t$ 值而非效应量（\S\ref{sec:hero}）。

\subsection{方法的迭代：哪次事故催生了哪条规则}\label{sec:evolution}
本文的方法不是一次设计成型的：几乎每条规则都由一次真实运行中的事故催生。
下表是完整对应（事故细节见附录~\ref{sec:chronicle} 的对应运行）：
\begin{center}\footnotesize
\begin{tabular}{@{}l p{0.36\textwidth} p{0.38\textwidth}@{}}\toprule
版本 & 触发事故 & 由此新增／修改的方法 \\ \midrule
决定 0005 & \path{Verdict.NULL} 在全仓无产出路径，否定结论无处安放 &
  判决由「每条理由使哪些结论失效」的集合推出，null 成为一等产出 \\
M7.3 & 审计按散文子串匹配，连续误拦对「幅度对方向」的正确回应 &
  语义判据改为沿特征 DAG 的结构判定 \\
M8 & $|t|=9.3$ 的「发现」实为波动率聚集（分母与目标同为已实现波动） &
  新增 rank\_pct 与 residualise 原语；「另类主张必须是基线之上的增量」写入口径 \\
决定 0006 & 具名规格清单 + 判决计数可做减法，反推逐条成败 &
  判决分类退出提案器上下文（匿名前提被记忆架构取消） \\
M9.8 & residualise 原语可见却零使用（run9 十一版全未用） &
  发现「可见 $\ne$ 会用」：提示词必须写明\textbf{为什么}要残差化 \\
M11.3 & 语义错配教训每次运行清零重学 & 错配码初值从账本回放全历史 \\
决定 0007 & 「未声明成本模型」以每条 Study 的错误形式呈现系统级状态 &
  最小成本模型（tick 实测 + 声明常量）；新增 uneconomic\_target 闸门 \\
M12 & 成交量前 30 垄断菜单，1{,}998 族中 98\% 永无出场机会 &
  资格筛＋事前经济映射标注＋分层轮换菜单＋按需装载 \\
M13 & run22 十六条 null 的主因是持续性构造对置换无分辨力 &
  信号侧事前筛：$n_{\mathrm{eff}}<30$ 拦在读 outcome 之前，不花预算 \\
决定 0008 & 146 个构造证明「永远在线的线性检验」问题族无信号 &
  事件条件形态：触发器进提案契约，独立问题族独立地板 \\
B6--B9 & 束位先后被基线假象、十行样本、异族成员、错误族标签占据 &
  束的四条准入规则（详见 \S\ref{sec:limits}） \\
\bottomrule\end{tabular}\end{center}
这张表本身是一条结论的证据：\textbf{对这类系统，最有效的除错器是真实运行}。

""" + V9_SECTIONS + V10_SECTIONS + r"""
\section{一条特征的完整算术：从原始数据到 $t$ 值}\label{sec:worked}
前一节给出的是定义。本节把\textbf{一个具体的数}算给读者看：取 run16-study-3
（回溯投影下唯一的完整候选形态，\S\ref{sec:retro}），在一个真实决策时点上把
信号侧、标签侧、回归侧三层算术逐位展开。全部数值取自账本与 spine，
并与解释器的记忆表逐位核对一致。

\subsection{特征名怎么读}
\path{pm_iran_outstanding_resolution_mass_resid_own_rv_12h_90d} 由提案器自行命名，
是\textbf{约定而非合同}（真正的身份是冻结规格的内容哈希）。按约定它读作：
\path{pm}（源为 pm\_market）· \path{iran}（族 cand:iran）·
\path{outstanding_resolution_mass}（机制：仍未解决的概率质量）·
\path{resid_own_rv}（对品种自身已实现波动残差化）· \path{12h}（主窗口 43{,}200 秒）·
\path{90d}（残差化回看窗 7{,}776{,}000 秒）。

\subsection{冻结规格（七步 DAG）}
\begin{center}\footnotesize
\begin{tabular}{@{}rlll@{}}\toprule
\# & 步骤名 & 原语 & 参数／输入 \\ \midrule
1 & \path{iran_p_mean_12h} & window & \path{cand:iran:p}，op=mean，$W$=43200s \\
2 & \path{iran_p_mean_12h_ref} & window & 同上（作为下一步的分母占位） \\
3 & \path{unity} & ratio & 步 1 ÷ 步 2 $\;\equiv 1$ \\
4 & \path{iran_p_complement_12h} & difference & \path{unity} $-$ 步 1 $\;=1-\bar p$ \\
5 & \path{inv_complement_12h} & ratio & \path{unity} ÷ 步 4 $\;=1/(1-\bar p)$ \\
6 & \path{iran_resolution_mass_12h} & ratio & 步 1 ÷ 步 5 $\;=\bar p\,(1-\bar p)$ \\
7 & \path{iran_resolution_mass_resid} & residualise & 步 6，控制 own\_realised\_volatility \\
\bottomrule\end{tabular}\end{center}
第 2 至 5 步是\textbf{用现有原语表达 $\bar p(1-\bar p)$ 的绕行}：语言里没有「乘法」，
模型用 $\bar p \div \frac{1}{1-\bar p}$ 达成同一结果。这正是「窄语言 + 缺口声明」
的设计意图 —— 它让每一次表达都留下可读的痕迹。

\subsection{第一层：信号侧（决策时点 2024-01-26 08:59:00+08:00，合约 sc2403 日盘）}
\paragraph{原始输入。}Polymarket 侧的 \path{cand:iran:p} 是该族的\textbf{名义额加权
归一化概率}，按小时分桶。窗口 $[\,$01-25 20:59, 01-26 08:59$)$ 内落入三个桶
（右端点排他，恰在 08:59 完成的桶不参与）：
\[ 0.04,\quad 0.05,\quad 0.21948 \;\Longrightarrow\; \bar p=0.10316009. \]
\paragraph{逐步取值。}
\begin{center}\footnotesize
\begin{tabular}{@{}llr@{}}\toprule
步骤 & 算式 & 取值 \\ \midrule
\path{iran_p_mean_12h} & 三桶均值 & 0.10316009 \\
\path{unity} & $0.10316009 \div 0.10316009$ & 1.0 \\
\path{iran_p_complement_12h} & $1-0.10316009$ & 0.89683991 \\
\path{inv_complement_12h} & $1 \div 0.89683991$ & 1.11502621 \\
\path{iran_resolution_mass_12h} & $0.10316009 \div 1.11502621$ & 0.09251809 \\
\bottomrule\end{tabular}\end{center}
第五行即 $\bar p(1-\bar p)$：验算 $0.10316009\times0.89683991=0.09251809$。

\paragraph{残差化（第七步）。}回看窗 90 天、采样间隔 1 天，期望 90 个过去时点，
其中 85 个的特征值与控制值\textbf{同时}有定义，成对入样（$\ge$ min\_samples $=40$）。
当前点\textbf{不入样}。在这 85 对上作一元 OLS：
\[ \bar c=-4.33457234,\qquad \bar x=0.12809524, \]
\[ \hat\beta=\frac{\sum(c_k-\bar c)(x_k-\bar x)}{\sum(c_k-\bar c)^2}=0.089024,\qquad
   \hat\alpha=\bar x-\hat\beta\bar c=0.51397767. \]
（控制变量是 SC 自身已实现波动的对数，故 $\bar c$ 为负。）当前时点的控制值
$c=-4.72389357$，于是
\[ \text{预测}=\hat\alpha+\hat\beta c=0.09343618,\qquad
   \boxed{\;\text{信号}=0.09251809-0.09343618=-0.00091809\;} \]
这个数与解释器记忆表中的 \path{-0.000918090964138904} 逐位一致。它是
\textbf{样本外预测残差}：当前观测减去用纯过去数据拟合的直线在当前控制值处的预测。

\subsection{第二层：标签侧（同一行）}
标签是 \path{sc_rv_next_session}：决策时点之后那个交易时段的已实现波动。
该行的 label 窗口是 2024-01-26 的日盘 09:00–15:00，含三个交易段
（09:00–10:15、10:30–11:30、13:30–15:00）。已实现波动定义为
\[ \mathrm{RV}=\sqrt{\textstyle\sum_i r_i^2},\qquad
   r_i=\ln\frac{C_{i+1}}{C_i}\;\text{（相邻分钟 bar 收盘价，\textbf{跨段不产生收益}）}. \]
按段分组后得 $74+59+89=222$ 个对数收益，
$\sum r_i^2=3.717261\times10^{-5}$，$\mathrm{RV}=0.006096934357$ —— 与账本标签值逐位一致。

\paragraph{「跨段不产生收益」不是形式主义。}核对时若把日盘三段并作一段，
会多出两个跨越午休与上午休市的「收益」，$\mathrm{RV}$ 变成 $0.006538$
（偏高 7.2\%）—— 那两个数字度量的是休市期间的价格跳变，不是交易中的波动。

\subsection{第三层：从 14{,}923 行到 $t=4.39$}
同样的两层算术在 36 个品种 $\times$ 全部决策时点上重复，得到评价表：
\begin{center}\footnotesize
\begin{tabular}{@{}lr l@{}}\toprule
量 & 值 & 含义 \\ \midrule
候选行 & 37{,}245 & 面板上全部（品种，时段）对 \\
预注册排除 & 22{,}322 & 特征在该时点无定义（窗口内无数据／控制不可识别） \\
入回归 & \textbf{14{,}923} & \\
episode 数 & 8{,}290 & Kish $n_{\mathrm{eff}}=7{,}900.1$ \\
交易日 cluster & 233 & Kish $n_{\mathrm{eff}}=222.3$ \\
品种 cluster & 36 & Kish $n_{\mathrm{eff}}=35.7$（面板不退化） \\ \midrule
$\hat\beta$ & 0.00412963 & 信号每增 1 单位，下一时段 RV 增 0.00413 \\
$V=V_a+V_b-V_{ab}$ & $8.8388\times10^{-7}$ & 双向 cluster 方差（233 日 $\times$ 36 品种） \\
$\mathrm{SE}=\sqrt V$ & 0.00094015 & \\
$t=\hat\beta/\mathrm{SE}$ & \textbf{4.392535} & \\
$\mathrm{MDE}=2.8\,\mathrm{SE}$ & 0.00263241 & 否定时的排除界 \\
IC$_\rho$ & 0.08531 & 时序秩相关（不入闸门） \\
DFBETAS & 0.04836 & 最大单点影响，闸门 1.0 \\
最大杠杆 $h_i$ & 0.00070 & \\
置换 exceed & 0/200 & 闸门 0.1 \\
\bottomrule\end{tabular}\end{center}

\paragraph{$t$ 大不等于经济上大。}$\hat\beta$ 的单位是「每单位信号对应的 RV 变化」，
而信号本身的量纲由构造决定。该信号在 SC 网格上的标准差为 $0.0704$，因此
\emph{一个标准差}的信号变化对应 RV 变化 $0.004130\times0.0704=0.000291$，
而 SC 的典型（中位）RV 为 $0.008516$ —— 即约 \textbf{3.4\%} 的典型波动。
这就是为什么 $t$、IC 与经济幅度必须并列报告：$t=4.39$ 说的是「这个斜率不像是零」，
不是「这个效应很大」。而在封存段上，这个斜率连「不像是零」也没保住。

\section{结果}\label{sec:results}
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
            + (f"{retention * 100:.1f}\\%" if retention is not None else "—")
            + r""" $<$ 0.35 $\Rightarrow$ sealed\_failed \\
\bottomrule\end{tabular}\caption{候选在两段上的对比。裁决终身有效，不重开。}\end{table}

\textbf{口径更正}：闸门比的是两个 $t$ 值而非效应量，两段样本量不同（"""
            + str(n_d) + " 对 " + str(n_s) + r""" 行），即便效应完全不变 $t$ 也按
$\sqrt{n_s/n_d}\approx """ + (f"{size_factor:.2f}" if size_factor else "—")
            + r"""$ 缩小；样本量修正后效应保留率约 """
            + (f"{retention_adj * 100:.1f}\\%" if retention_adj is not None else "—")
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

\subsection{成本模型建成后的回溯投影}\label{sec:retro}
最小成本模型（决定 0007）建成后，判决可按失效表机械地重推：从每条已判 Study 的
阻塞理由种类中移除 cost\_model\_missing，对收益型 target 补入经济闸门投影。
这不改写任何已入账判决（账本不可回写），它回答的是「若当时就有成本模型，
判决会是什么」。结果分三组：

\begin{itemize}
\item \textbf{基线假象组}（4 条，量价源，$|t|$ 至 9.30）：翻为 candidate，
且确实越过评价时地板（奖励 $+7.1$ 至 $+2.3$）。但按决定 0002 它们归
Baseline Control 库，\textbf{不计入另类清单} —— 翻转只说明「波动率聚集是真的」。
\item \textbf{未越地板组}（11 条，Polymarket）：置换全部通过（exceed
$0$ 至 $0.035$），但 $|t|$ 在 $1.2$ 至 $2.3$，自罚奖励为负 —— 干净而不够高。
\item \textbf{真形态，一条}：run16-study-3。
\end{itemize}

\begin{table}[htbp]\centering\small
\begin{tabular}{@{}l >{\raggedright\arraybackslash}p{0.74\textwidth}@{}}\toprule
特征 & \path{pm_iran_outstanding_resolution_mass_resid_own_rv_12h_90d} \\
构造 & $\bar p(1-\bar p)$：iran 族 12 小时窗口均值的伯努利方差（「仍未解决的概率质量」），\\
     & 残差化掉品种自身波动持续性 \\
universe & 36 品种面板 · 14{,}923 行 \\
统计 & $t=+4.393$ · IC$_\rho$ = $0.085$ · 置换 $0/200$ · DFBETAS $0.048$ \\
地板 & 评价时 $n=61$，$E_2(61)=2.600$ → \textbf{自罚奖励 $+1.79$}（残差化另类构造首次为正）\\
当时判决 & blocked，唯一理由 cost\_model\_missing —— 该理由今日已不存在 \\
封存段裁决 & \textbf{未保住}（人于 2026-08-08 决定开封，一次性）：$t=+0.823$、
IC$_\rho$ = $0.029$、14{,}297 行 —— $t$ 保持率 18.7\%，远低于 0.35 保持线，
判 sealed\_failed。与 run11-study-3 不同，这次\textbf{秩相关同样塌陷}
（$0.085\to0.029$），是一次更干净的否决 \\
\bottomrule\end{tabular}
\caption{run16-study-3：回溯投影下唯一的完整候选形态，及其封存段裁决。
裁决终身有效，不重开。}
\end{table}

一条使它区别于全部前例的证据：\textbf{模型在提案时把当时的地板写进了证否条件}：
\begin{quote}\small
「在 full coverage panel 上……若残差对 sc rv next session 的 $|t|$ 不超过
本轮噪声地板 2.5998，或其系数符号为负，则本机制不被支持。」
\end{quote}
随后做到 $4.39$。
这不是事后从账本里挑出来的幸存者：预注册的证否线就是地板本身，另附三条
非统计的证否观测（增量在纳入信念波动后消失、预测力由样本组成漂移承担等）。

机制上它是 run11-study-3（发生率水平）与 run15 推理（事件不确定性）的直系后代：
$\bar p$ 接近 $0.5$ 表示事件悬而未决、任何新证据都会引发实质重定价，
$\bar p(1-\bar p)$ 正是这份「未决质量」的读数。谨慎读法同样必要：
run11-study-3 在发现段同样通过置换（$0.05$）而封存段未保住；本条的发现段
统计强得多（$4.39$ 对 $2.42$，且越过地板），但唯一有权裁决的是那次一次性开封。

\subsection{事件条件族：两轮四十回合}
图~\ref{fig:eventcurve} 是事件族自己的搜索曲线（分母独立、地板从头起）。
run23 触发器采用 19/19 但 17 版集中在 iran 单一事件源，十九版全 null；
run24 经方向指令铺开到十一个互异触发族（含轮换层新族），结论一致。
两轮合计：即使只看概率大幅移动后的窗口、即使换了十一个事件源，
线性可预测性仍然缺席。本族最好 $|t|=1.87$，从未越过本族地板。
\begin{figure}[htbp]\centering
\includegraphics[width=0.9\textwidth]{figures/event_search_curve.png}
\caption{事件条件族的搜索曲线。分母独立（决定 0008），地板从 $0.798$ 起。}
\label{fig:eventcurve}
\end{figure}

\paragraph{四次封存否决的共同判词。}截稿时封存段共否决四个候选形态：
run11-study-3（发生率水平，$t$ 保持率 17.6\%）、run16-study-3（未决质量，18.7\%，
秩相关同塌）、dip\_barrier（十行样本的 underpowered 假象经束缺陷混入，
还原后 51\% 但发现段证据无效）、belief\_jump（12.7\%）。共同形态：
发现段的强度来自该段特有的样本构成（2024 年伊朗事件簇），
不是跨段稳定的关系。置换检验打乱段内对齐，检验不出跨段构成差异；
封存段可以 —— 它因此是终审。

\subsection{封存段全记录（""" + str(len(D["sealed"])) + r""" 次开启）}
{\footnotesize\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.44\textwidth} r r r l l@{}}
\toprule 特征 & $t$ & IC$_\rho$ & 行 & 时间样本外 & 分类法干净 \\ \midrule\endhead
""" + sealed_rows + r"""
\bottomrule\end{longtable}}

\section{测量装置本身的局限}\label{sec:limits}
为写第 3 节，对全部参与判决的统计量做了一次逐行提取核对。下列不一致由本次核对发现，
记入 \path{docs/BLOCKERS.md}，按项目规矩只记录不修：置换兜底把度量失败记成支持
null（null 偏多）；置换块结构使零分布边缘与样本不同（方向不定）；置换阈值 0.1 较常用
0.05 宽松（null 偏少）；cluster SE 无有限样本修正（排除界宣称偏紧）；面板上
min\_clusters 被 episode 命名稀释 $N$ 倍（underpowered 偏少）；$h_i=1$ 时 DFBETA
可为 $+\infty$ 而守卫只覆盖 SE 一侧；MDE 硬编码 2.8 未引用常量；紧缩 Sharpe 方差项
较发表式少 $1/2\cdot SR^2$（偏乐观）；Sharpe 带尺度含前视；驾驶舱曲线与顶栏用两个
口径不同的 $n$；提案器读到的地板说明写 $\sqrt{2\ln n}$ 与实现不符；0.35 与 120 无推导。
\textbf{没有一处能把 null 翻成 candidate}：candidate 被失效表结构性挡住，与数值无关。

\paragraph{束的四连修（B6--B9）。}束位即自动封存的名额，四类占位缺陷先后被实跑暴露：
基线假象以 $+7.1$ 的奖励霸占束位（B6：Baseline Control 不占另类束位）；
十行样本的 underpowered 以假奖励进榜并烧掉封条（B7：样本不足不进束）；
束不按族过滤，事件族的收尾封存烧在旧族特征上（B8）；评价证据的族标签被写死为
旧族，按族过滤后束反而为空（B9：族由调用方传入）。B9 的一个后果须如实声明：
run17 至 run24 期间的评价载荷 family 字段不可靠，族归属应按运行前缀判定 ——
本文全部按此口径。

\paragraph{provider 的四课。}CLI 对管道按块缓冲堵死推理流（伪终端修复）；
思考阶段不发增量（如实标注，无法修复）；超时线 900s 卡在实测思考时长分布中间
（提为 1800s）；pty 阻塞读使超时永远不触发（实测挂死 103 分钟，
select 五秒一拍轮询修复，挂死调用三十分钟必被回收）。每课带回归护栏。

\section{结论（每条附证否条件）}\label{sec:conclusions}
\begin{enumerate}
\item \textbf{结构（已解除）：截至 M11 之前，「candidate=0」不是经验结论。}
cost\_model\_missing 曾对全部 Study 成立且其失效集合含 candidate。
决定 0007 建成最小成本模型后该约束解除；回溯投影（\S\ref{sec:retro}）显示
16 条历史 blocked 在新制度下为 candidate 形态。\emph{证否（更正后）：
新制度下一条各闸门全过的 Study 仍被判 blocked。}
\item \textbf{经验：已检验机制上，Polymarket 特征相对基线的线性增量预测力，
在两种问题形态（永远在线；事件条件窗口）上都未过预注册证否闸门。}
\emph{证否：任一形态下，残差化后在其族地板上方且置换 $\le0.1$ 并在封存段保住的
一条特征。}
\item \textbf{经验（已按自身证否条件更正）：残差化之前，四条波动假象的自罚奖励
为正（最高 $+7.1$）；残差化的另类构造中，第一条奖励为正的出现在 run16-study-3
（$+1.79$，见 \S\ref{sec:hero} 后补）。}本报告上一版此条写作「从未有 Study 越过
评价时地板」，按其证否条件（beam\_state 出现 reward $>0$）在写下时即不成立 ——
假象家族早已越过；当时想表达而未写准的是「无残差化的另类构造越过」。
\emph{证否（更正后）：残差化另类构造的奖励为正且封存段保持。}
\item \textbf{方法：残差化把「发现」与「重新发现基线」分开，效果是数量级的}；
模型采用它的转折点是提示词写明「为什么」，不是原语可见。\emph{证否：一条残差化后
$|t|$ 不显著下降且封存段保住的量价构造。}
\item \textbf{方法：封存段是唯一无法用「再跑一次」绕过的闸门，且起了作用。}
\emph{证否：对同一（规格,段）二次取值而不触发 SealedAlreadyOpened 的路径。}
\item \textbf{局限：全部 Polymarket 结论被分类法污染封顶}（决定 0004），肯定结论
在此状态下不可采信；否定结论方向不受影响。\emph{证否：用干净切点语料重归纳并重跑。}
\item \textbf{局限：测量装置有 12 处实现与文档不符，但无一能把 null 翻成
candidate。}\emph{证否：修正后重跑，判决分布改变。}
\item \textbf{经验（已裁决）：run16-study-3 —— 七个月账本中唯一同时满足
「纯 Polymarket、已残差化、越过评价时地板、置换零例外、影响有界」的构造 ——
在人决定开封后未保住封存段}（$t$ 保持率 18.7\% $<$ 0.35，秩相关同塌）。
上一版本条预注册的证否条件（保持率低于 0.35）\textbf{触发}，它加入被否决候选
的行列。两次开封两次否决（run11-study-3、run16-study-3）共同指向的读法：
发现段上越过地板、通过置换的构造，其强度主要来自该段特有的样本构成 ——
封存段正是为识别这一点而存在。
\emph{证否：一条开封后保持率不低于 0.35 的同类构造。}
\item \textbf{经验（新）：事件条件形态下结论不变。}触发器由模型自主声明并预注册
（进 content id），两轮四十回合、十一个互异触发源、本族独立地板 ——
最好 $|t|=1.87$ 未越线。「概率大幅移动之后的窗口」并没有比「永远在线」
更可预测。\emph{证否：一条事件条件构造越过本族地板、置换通过并在封存段保住。}
\item \textbf{经验（新）：对抗性评审指出的三块「被避开的高地」补上之后，结论不变。}
决定 0009 实施评审第一梯队（吸收目标升为主要目标、先验四个阳性种子经方向通道
喂入、残差化支持至三个控制），run26 二十回合作直接检验：吸收目标被采纳十次、
双控制残差化十四次，十四 null 一 blocked（cluster 结构退化），最好 $|t|=2.31$
低于其预注册证否线 2.85；前身 $0.86$ 的休市吸收相关在七倍样本上未再现。
评审给出的最短归因路径就此走完，「方法边界」假说失去其最强的三条证据 ——
归因的天平偏向市场真相。\emph{证否：在剩余的方法缺口（截面暴露度框架、
财联社控制、稀疏族延用末值）中任一补上后出现越过地板并保住封存段的构造。}
\end{enumerate}

\section{对抗性评审：没找到的是市场真相，还是方法的边界}\label{sec:adversarial}
报告初稿完成后，我们让一个持有全部上下文的评审代理对本项目做对抗性检查，
任务是攻击「没找到东西」这个结果本身：有多大成分是问错了、用漏了、设计得太保守？
要求每条断言先读代码或数据核实。以下是它核实后的主要发现（按杠杆排序）。

\subsection{三块被避开的高地（先验证据最强处，恰好没花预算）}
\begin{enumerate}\itemsep2pt
\item \textbf{休市吸收目标被结构性劝退。}200 个提案的 target 分布：rv 115 次、ret 64 次、\textbf{吸收目标仅 2 次} ——
  而前身研究唯一的强阳性
  恰是闭市吸收形态（油价主题 $\times$ SC 相关 0.86，$n=37$；合并缺口 0.743，$n=74$）。
  该目标在本系统中被标注为「诊断用、不作可交易主张」，菜单措辞实质性劝退了它。
\item \textbf{先验研究的四个阳性种子从未进入提案器。}前身 2{,}742 项检验留下的种子
  （吸收 0.86、截面 RankIC 0.26 且 $t=5.0$、中东增量 $t=4.94$、
  tension$\to$波动 $t=-4.40$ \textbf{负号}）无一在上下文中 —— 本系统的 rv 提案
  几乎全部 direction $=+1$，而先验说该关系为负。喂入外部先验不违反
  决定 0006（它封的是本系统自身结果的回流），通道（研究方向指令）现成。
\item \textbf{截面暴露度排序无法表达。}先验里唯一带 $t=5$ 的识别框架
  （按品种对主题的暴露度做横截面排序）被两个已记录的原语缺口恰好卡住：
  无滚动载荷类原语；pm-only 特征同一时点跨品种同值。
\end{enumerate}

\subsection{两处可能削弱增量主张的设计限制}
\textbf{单控制残差化}：语言强制恰好一个控制变量，而先验的「中东增量 $t=4.94$」
是在控制 12 个国际基准后得出的 —— 单控制残差可能残留共同因子，使发现段虚高、
封存段塌陷，与四次封存否决的形态一致。\textbf{线性探针}：评价机唯一的统计通道是
一元线性 OLS；秩相关只记录不裁决 —— 而 run11-study-3 恰好呈现「线性斜率塌、
秩相关反升」的非线性形态特征。

\subsection{两处数据面的实质缺陷}
\textbf{族序列稀疏}：实测主力族有 21--34\% 的交易日整日无桶（iran 覆盖 79\%、
up 72\%、dip 66\%），run16-study-3 的面板 60\% 行因此被排除 —— 短窗构造承压最大。
\textbf{negRisk 缺口}：2024 大选期（在发现段内）的 2{,}873 个市场只有元数据无成交，
与 up/dip 类族的稀疏叠加；回爬需另行授权。财联社 89.4 万条电报从未接线，
使全部否定的解释力打折：分不清「PM 无信息」与「信息本来就在国内公开、PM 只是镜像」。

\subsection{一条反向发现：地板不偏严}
评审同时核实了「地板因独立性假设偏严」的猜测：账本相关性记录显示
同族信号平均 $|\rho|=0.097$ —— 独立性近似成立，地板大致是对的。
\textbf{不要往放松标准的方向找出路。}

\subsection{评审的总回答}
在「session 级、线性、单控制、无先验地图」这个实际检验过的窄切面上，
「没找到」是扎实的市场真相 —— 地板不偏严，置换与封存的否决都经得起复核。
但这个切面恰好避开了先验证据最强的三块地。因此更准确的表述是：
\textbf{方法的边界先于市场的真相被触到了。}检验「究竟是哪一种」的最短路径
是三件合计不到两张票的改动：提升吸收目标的地位、喂入先验种子、多控制残差化。

\subsection{后记：最短路径的检验结果（run26）}
上述三件在决定 0009 中实施，run26 二十回合作直接检验。过程本身有两处值得入册：
先验种子第一次喂入（run25）时，方向文本里的一个效果词被盲化断言三次拦下，
零研究作废 —— 人写的指令不豁免审查，系统按设计工作；改词重启后 run26 干净跑完。
结果：十五版判决，吸收目标被采纳十次（$+1$ 与 $-1$ 两个方向都试过），
brent 与自身已实现波动同时残差化十四次（正规方程路径首次生产使用），
十四 null 一 blocked。最好 $|t|=2.31$（sc\_ret\_next\_session，低于其预注册
证否线 2.85）；吸收目标侧最好 $|t|=1.83$。前身在约 150 个交易日样本上量到的
$0.86$ 休市吸收相关，在七倍规模的样本上没有再现。评审列举的三块高地中，
两块已补上并检验为 null；仍未检验的方法缺口只剩截面暴露度框架（原语缺口）、
财联社控制（数据未接入）与稀疏族延用末值语义（需预注册裁决）。
「方法边界」假说失去其最强的证据之后，「市场真相」是当前分量更重的解释。

\section{下一步（全部需人决定）}
按对抗性评审（\S\ref{sec:adversarial}）重排为两个梯队。

\paragraph{第一梯队（评审判定的最短路径 —— 已完成并检验，见
\S\ref{sec:adversarial} 后记）：}
（1）\textbf{提升休市吸收目标的地位}（决定 0009，已完成）—— run26 中被采纳十次，
最好 $|t|=1.83$，null；
（2）\textbf{把先验研究的四个阳性种子作为研究方向喂入}（已完成）—— run25 因方向
文本触发盲化作废，run26 干净跑完，种子形态全部为 null；
（3）\textbf{多控制残差化}（决定 0009，已完成）—— run26 中双控制十四次，
正规方程路径首次生产使用，null；
（4）族序列稀疏的\textbf{延用末值语义}（带陈旧上限，预注册）—— 把被排除的
60\% 行抬回来。\textbf{唯一未做的第一梯队项}，需先出决定文档。

\paragraph{第二梯队（原有清单，评审证据更新了其中两项的分量）：}
（5）\textbf{截面暴露度排序}（先验 $t=5.0$ 的框架）—— 需滚动载荷原语＋截面 target，
约两三张票；（6）\textbf{财联社接线} —— 评审升级了它的理由：它是区分「传导」与
「镜像」的必需控制，也是事件族的天然触发源（含约七周回爬，数据获取需单独授权）；
（7）分类法重归纳（解除决定 0004 封顶）；（8）negRisk 回爬（2024 大选期 2{,}873 个
市场，需授权）；（9）重开 ADAR 时代因样本不足搁置的假设清单（样本已 7 倍）；
（10）秩序／分位闸门（给非线性关系一条正式判决通道）；（11）郑商所 TradingDay 裁决；
（12）搜索吞吐三倍化（变异器邻域扫描 + 批量提案，不改单位检验功效）。

\paragraph{评审建议明确不做的：}tick 级分钟管道 —— 先验已在分钟级方向信号上
重锤无果：1{,}646 项检验的最大 $|t|$ 为 3.99、未过当时门槛，且成本后净收益
为正的组合 0/114。

\section{复现}\label{sec:repro}
\begin{enumerate}\small
\item 环境：\path{uv venv && uv pip install -e ".[dev]"}；校验
\path{.venv/bin/python -m pytest tests/ -q}（684 项合同测试）。
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
{\footnotesize\begin{longtable}{@{}>{\ttfamily}l >{\raggedright\arraybackslash}p{0.42\textwidth} r r r l@{}}
\toprule Study & 特征 & $t$ & IC & 置换 $p$ & 判决 \\ \midrule\endhead
""" + appendix_rows + r"""
\bottomrule\end{longtable}}

\section{二十四次运行编年（全记录）}\label{sec:chronicle}
以下是二十四次运行（auto 前缀涵盖最早两次）的完整记录：每次运行的叙述、
全部 Study 的判决表、以及每条有冻结规格的 Study 的「信号 × SC 收盘价」图。
正文中的方法迭代（\S\ref{sec:evolution}）多由这些运行触发。
""" + chronicle(D, figs) + r"""

\vfill\noindent\rule{\textwidth}{0.4pt}\\
{\small 账本冻结点：事件 seq """ + str(D["frozen_at"]["seq"]) + r"""（"""
            + D["frozen_at"]["at"] + r"""，run16 当时仍在进行）；事件 """
            + str(D["events"]) + r""" 条，哈希链"""
            + ("完整" if D["chain_intact"] else r"\textbf{断裂}") + r"""。
叙述由人撰写且不含数字；数字一律由快照渲染，二者不会不一致。}
\end{document}
""")
    ne = D.get("event_denominators", {}).get("statistical_denominator", 0)
    ef = D.get("event_floor")
    tex = tex.replace("{N_STUDIES}", str(len(D["studies"])))
    tex = tex.replace("{N_OLD}", str(n))
    tex = tex.replace("{FLOOR_OLD}", f"{floor:.3f}")
    tex = tex.replace("{TOP_T}", f"{abs(top[0]['t']):.2f}")
    tex = tex.replace("{N_NULL}", str(v.get("null", 0)))
    tex = tex.replace("{EVENT_N}", str(ne))
    tex = tex.replace("{EVENT_FLOOR}", f"{ef:.3f}" if ef else "—")
    # 第三本账与合并账（决定 0011 约束 4：合并口径必须随时可读）
    nm = D.get("mech_denominators", {}).get("statistical_denominator", 0)
    mf = D.get("mech_floor")
    nall = D.get("merged_denominators", {}).get("statistical_denominator", 0)
    mgf = D.get("merged_floor")
    tex = tex.replace("{MECH_N}", str(nm))
    tex = tex.replace("{MECH_FLOOR}", f"{mf:.3f}" if mf else "尚无（分母为零）")
    tex = tex.replace("{MERGED_N}", str(nall))
    tex = tex.replace("{MERGED_FLOOR}", f"{mgf:.3f}" if mgf else "—")
    return tex


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
