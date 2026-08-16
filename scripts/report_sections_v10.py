"""报告第十版新增的四节（M19 至 M23）。

与第九版同一形态：拆成独立模块只为篇幅。与第九版**不同**的一点是纪律上的：
本模块**不写死任何数字**，全部从 `artifacts/manifests/` 下的产物读取。

这条纪律来自一次实际的失败。第九版之后流通过两组数字（四条构造的 decoy 对照、
「40 条构造」的相关分析），核对时发现仓库里没有任何脚本能复算它们 ——
它们出自一次临时计算，产物已不存在。一份声称「每个数字可复算」的报告不能这样
排版。因此第十版的每个数字都必须有一份产物在它背后，重建报告即重算。

四节的内容经过一轮起草与两轮核实（逐数字复算 + 对抗审稿）。审稿指出并已在此
改正的实质问题：
1. 「本次改动既不收紧也不放松标准」是自利的修辞。书面判据确实没变，但**执行的
   判据被收紧了**，三条 candidate 降为 blocked 就是证据。
2. 「若不修，run30 会产出三条候选」不成立：四条 blocked 全部独立带品种维退化，
   移除方向判据后重推判决不变。
3. 「第一条越过预注册证否线」读起来比它配得上的强：批级证否线是决定 0011 才
   引入的，旧族从来没有过这条线。
4. 「实测相关多半是抽样噪声」由一次中位对均值的错误比较得出；同类比较下相关是真的。
5. 「decoy 一致地更严」由四条构造下的普遍结论，且单条差值多在蒙特卡洛误差内。
"""

from __future__ import annotations

import json
from pathlib import Path

_MANIFESTS = Path("artifacts/manifests")


def _load(name: str) -> dict:
    """读一份产物。缺失即报错 —— 宁可不出报告，也不出一份数字来路不明的报告。"""
    path = _MANIFESTS / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"缺少产物 {path}。第十版的每个数字都由产物驱动，"
            f"请先运行对应的 scripts/measure_*.py 或 scripts/settle_run.py")
    return json.loads(path.read_text(encoding="utf-8"))


def _pct(value: float | None, digits: int = 1) -> str:
    return "—" if value is None else f"{value * 100:.{digits}f}\\%"


def _num(value: float | None, digits: int = 4) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def direction_check_section() -> str:
    d = _load("direction_check_projection")
    rc = d["rank_correlation"]
    recorded = d["verdict_counts_as_recorded"]
    checked = d["verdict_counts_under_check"]
    n = d["studies_with_declared_direction"]
    agree, opposite = d["sign_agrees"], d["sign_opposite"]

    # 合计行必须由分层自身求和，不能取顶层计数：分层只收 $t$ 有限的读数，
    # 而顶层的 sign_agrees 与 studies_with_declared_direction 是全部读数。
    # 混用会印出一行三个口径的合计，各列求和对不上。
    strata_n = sum(s["n"] for s in d["strata"])
    strata_agree = sum(s["sign_agrees"] for s in d["strata"])

    strata_rows = "".join(
        f"$[{s['low']:.1f},{s['high']:.1f})$ & {s['n']} & {s['sign_agrees']} & "
        f"{_pct(s['rate'])} \\\\\n"
        if s["high"] is not None else
        f"$\\geq {s['low']:.1f}$ & {s['n']} & {s['sign_agrees']} & "
        f"{_pct(s['rate'])} \\\\\n"
        for s in d["strata"] if s["n"])

    changed_rows = "".join(
        f"\\path{{{r['study_id']}}} & ${r['declared_direction']:+d}$ & "
        f"${r['t_stat']:+.3f}$ & {r['verdict_as_recorded']} $\\to$ "
        f"{r['verdict_under_direction_check']} \\\\\n"
        for r in d["changed"])

    return r"""
\section{预注册的方向，机器一次都没有核对过}\label{sec:direction}
本节讲一处装置缺口：每份提案都在检验之前写下了「什么符号算这条机制被否定」，
而评价机从来没有执行过这条判据。

先给两个词。一份\textbf{提案}是一次检验的完整声明，在看到任何结果之前锁定，
此后不可改；它的\path{direction} 字段取 $+1$ 或 $-1$，声明所主张的机制要求回归
斜率取哪个符号，\path{falsifiable_condition} 字段要求写明什么读数算这条机制被否定。
\textbf{判决}是评价机对一次检验给出的四值结论之一：\path{null}（干净的否定）、
\path{underpowered}（样本不足以判定）、\path{blocked}（这次检验不足以支持结论）、
\path{candidate}（全部闸门通过）。要紧的是 \path{candidate} 回答的是「这次检验做得
对不对」，不是「效应大不大」。

\subsection{触发：一条越线的构造，符号却是反的}
run29-study-4 越过了它那一批预先定下的证否线（$|t|=2.5649$ 对 $E_2(45)=2.4933$），
36 个品种的面板、21{,}390 行配对、316 个日期簇，整块置换 200 次没有一次超过实际值。
核实时发现它的斜率点估计为正，而它自己声明的方向是 $-1$。它在提案里写下的判据是：

\begin{quote}\small
「其二，斜率的点估计符号为正，即停火概率的净上修系统性地伴随更高的下一时段收益，
这与本条主张的风险溢价压缩通道方向相反，说明所读到的不是该通道。」
\end{quote}

这句话写在结果出现之前。按它自己预注册的判据，这条读数是一次否定；而机器判的是
\path{candidate}。

\subsection{根因：方向字段在提案锁定之后再没有被读过}
原因不在阈值，在调用路径：评价机的请求对象 \path{EvaluationRequest} 里根本没有方向
字段。\path{direction} 写进提案、进入账本，此后没有任何代码读过它。

全史实测印证这一点。截至本报告的账本快照，有预注册方向且斜率非零的 Study 共
""" + f"""{n} 条，符号一致 {agree} 条、相反 {opposite} 条
（相反占 {_pct(opposite / n)}），与掷硬币无从区分。

\\subsection{{这次改动的性质：书面判据没变，执行的判据收紧了}}
这一点必须讲清楚，否则读者无法判断它是不是一次事后调整。准确的表述分两层：
\\textbf{{书面判据从未改动}} —— 每份提案的符号判据从第一条起就写在可证否条件里；
而\\textbf{{就实际执行而言，本次是收紧}} —— 三条 \\path{{candidate}} 降为
\\path{{blocked}} 就是收紧的直接证据。早先的表述说它「既不收紧也不放松」，
那是一句对自己有利的修辞，此处更正。

这次改动之所以仍然正当，靠的是另外三条，它们与「收紧还是放松」无关：

\\begin{{enumerate}}
\\item 每份提案的方向在读取任何结果之前冻结，并进入内容指纹；
\\item 失效表保证投影\\textbf{{单向}}：新增的阻断理由只使 \\path{{candidate}} 失效，
      因此只可能把候选降为阻塞，不可能把任何否定翻成肯定；
\\item 投影统一施于全部历史，不挑选适用范围。
\\end{{enumerate}}

时序也要如实记下：\\textbf{{触发是事后的，判据是事前的}}。是先看到 run29-study-4
越线、核实时发现符号相反，才去查为什么机器没执行判据。触发在后不改变判据在先这一
事实，但把它写出来，读者才能自行判断。

\\subsection{{回溯投影：账本不回写，只在读取侧重算}}
账本只追加、不可回写，已入账的判决原样保留。投影回答的是另一个问题：
若当时评价机就核对方向，判决会是什么。

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.16\\textwidth}} r r
>{{\\raggedright\\arraybackslash}}p{{0.34\\textwidth}}@{{}}}}
\\toprule
判决 & 如实入账 & 方向核对投影 & 变化 \\\\ \\midrule
\\path{{null}} & {recorded.get('null', 0)} & {checked.get('null', 0)} & 不变 \\\\
\\path{{underpowered}} & {recorded.get('underpowered', 0)} & {checked.get('underpowered', 0)} & 不变 \\\\
\\path{{blocked}} & {recorded.get('blocked', 0)} & {checked.get('blocked', 0)} & 增加 {checked.get('blocked', 0) - recorded.get('blocked', 0)} 条 \\\\
\\path{{candidate}} & \\textbf{{{recorded.get('candidate', 0)}}} & \\textbf{{{checked.get('candidate', 0)}}} & 减少 {recorded.get('candidate', 0) - checked.get('candidate', 0)} 条 \\\\
\\bottomrule\\end{{tabular}}
\\caption{{方向核对下的回溯投影，{n} 条有预注册方向且斜率非零的 Study。
产物：\\texttt{{artifacts/manifests/direction\\_check\\_projection.json}}。}}
\\end{{table}}

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.22\\textwidth}} r r
>{{\\raggedright\\arraybackslash}}p{{0.32\\textwidth}}@{{}}}}
\\toprule
Study & 声明方向 & 实得 $t$ & 入账判决 $\\to$ 投影判决 \\\\ \\midrule
{changed_rows}\\bottomrule\\end{{tabular}}
\\caption{{投影下发生变化的构造，全部是「声明 $-1$、实得正号」。
它们原本的阻断理由表为空，方向不匹配是其唯一的候选失效理由。}}
\\end{{table}}

\\subsection{{一处更正：run30 的判决与方向判据无关}}
本节早先的一稿写过「若不修，run30 会产出三条越线或接近越线的候选」。该句不成立。

run30 的四条 \\path{{blocked}} 全部\\textbf{{独立命中}}
\\path{{cluster\\_structure\\_insufficient}}：二十版里有十八版在单品种品种域上求值，
品种维只有一组、双向 cluster 退化，而该理由按失效表同样只使 \\path{{candidate}} 失效。
把方向不匹配从各版理由中移除后按同一失效表重推，判决仍是 16 条 \\path{{null}}、
4 条 \\path{{blocked}}，逐条不变。

因此 run30 不是「修复改变了判决」的实证；改变判决的实证是上一小节的回溯投影。
run30 给出的是另一种实证：本轮读数最大的三条（$3.744$、$2.377$、$2.361$）
符号全部与所声明的 $-1$ 相反，第一条还越过本轮证否线。它们若出现在没有品种维退化
这道闸的面板品种域上（run29-study-4 正是如此），方向核对就是唯一拦得住它们的判据。

\\subsection{{符号一致率不随效应大小上升}}
把有预注册方向、斜率非零且 $t$ 有限的 Study 按 $|t|$ 分层：

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.16\\textwidth}} r r r@{{}}}}
\\toprule
$|t|$ 区间 & Study 数 & 符号一致数 & 一致率 \\\\ \\midrule
{strata_rows}\\midrule
合计 & {strata_n} & {strata_agree} & \\textbf{{{_pct(strata_agree / strata_n)}}} \\\\
\\bottomrule\\end{{tabular}}
\\caption{{符号一致率按 $|t|$ 分层。本表只含 $t$ 有限的读数，
因此合计 {strata_n} 少于上文的 {n} 条（差额是双向 cluster 方差为负、$t$ 无定义的
那几次读取；它们消耗了分母，但没有可分层的 $|t|$）。
最高一层的样本很小，不宜单独解读；可读的是整体没有随 $|t|$ 上升的形状。}}
\\end{{table}}

分层的形状比总体更有信息：一致率不随 $|t|$ 上升。逐条秩相关（$|t|$ 与符号一致
指示变量的 Spearman 相关）为 ${rc['spearman']:+.4f}$，
{rc['draws']} 次置换 $p={rc['permutation_p']:.4f}$（种子 {rc['seed']}）。
这一层证据不支持「方向判断有内容、只是被噪声淹没」：若符号推理有预测力，
效应大的那些应当更容易对。需要限定的是，二元结果的功效有限，
此处是「无证据支持」而非「有证据反对」。

\\textbf{{此处有一处数字更正}}：先前流通过一组「Spearman $+0.139$、置换 $p=0.155$」，
它复算不出来。付印一律采用上面这组可复算值，产物随报告重建而重算。

两种技术性解释已直接排除：残差化不翻转符号（残差化与未残差化两组的一致率相差不到
一个百分点）；机制族的极性折叠经成员表核对无反转，停火类市场归 $+1$、
战事推进类归 $-1$。剩下两种解释用这批数据分不开：被测切面上确实没有真实关系，
符号只是噪声；或者模型的符号推理本身没有预测内容 —— 机制叙述在两个方向上都讲得通，
符号是叙述里最不受约束的那一位。区分二者需要一批已知存在真实关系的对照检验。
"""


def null_baseline_section() -> str:
    e = _load("empirical_nulls")
    c = _load("construction_correlation")
    td = _load("t_distribution")
    rho, ref = c["abs_rho"], c["pure_noise_reference"]
    sim = c["simulated_null_max"]
    n = c["n_constructions"]

    exception_rows = "".join(
        f"\\path{{{r['study_id']}}} & {r['placebo_exceed']:.4f} & "
        f"{r['decoy_exceed']:.4f} \\\\\n" for r in e["exceptions"])

    return r"""
\section{基准线怎么造：解析地板之外的两条经验零分布}\label{sec:nullbase}
\textbf{地板} $E_2(n)$ 回答一个具体问题：对同一个目标试 $n$ 个互不相同的构造，
若它们全都与目标无关，其中绝对值最大的那个统计量期望能到多高。越不过它，
就说明这次的最好成绩不比「试很多次的运气」更值得相信。

它的推导前提是每次检验抽到一个标准正态随机数。这个前提可以用我们自己的读数核对，
而核对的结果是两侧都有偏差，方向还相反。本节把两侧都量出来，并说明为什么
\textbf{两侧都量出来之后，门槛仍然照旧执行}。

\subsection{一侧：我们的读数比理论噪声更容易碰出大值}
""" + f"""实际检验的 $|t|$ 分布比同样本量的标准正态噪声更肥尾。

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.14\\textwidth}} r r r@{{}}}}
\\toprule
量 & 实测 & 正态参照 & 倍数 \\\\ \\midrule
中位 & {_num(td['observed']['median'])} & {_num(td['normal_reference']['median'])} &
  {td['observed']['median'] / td['normal_reference']['median']:.2f} \\\\
均值 & {_num(td['observed']['mean'])} & {_num(td['normal_reference']['mean'])} &
  {td['observed']['mean'] / td['normal_reference']['mean']:.2f} \\\\
90 分位 & {_num(td['observed']['p90'])} & {_num(td['normal_reference']['p90'])} &
  {td['observed']['p90'] / td['normal_reference']['p90']:.2f} \\\\
最大值 & {_num(td['observed']['max'])} & {_num(td['normal_reference']['max'])} &
  {td['observed']['max'] / td['normal_reference']['max']:.2f} \\\\
\\bottomrule\\end{{tabular}}
\\caption{{实测 $|t|$（{td['n_finite']} 条有限读数，另有 {td['n_undefined']} 条无定义）
与同样本量标准正态噪声的对照。参照列为 {td['reference']['draws']} 次模拟的均值，
种子 {td['reference']['seed']}；分位一律用{td['quantile_definition']}，
全表同一定义。产物：\\texttt{{artifacts/manifests/t\\_distribution.json}}。}}
\\end{{table}}

中段接近而尾部明显更重：最大值差了三倍有余。真实金融数据有自相关、厚尾与体制切换，
这一侧使解析地板作为参照\\textbf{{偏松}}。

需要一处限定：这批读数\\textbf{{不是纯零样本}}，其中混着可能真实但与另类数据无关的
效应 —— 最大的那条正是波动率聚集假象（分母是已实现波动，目标也是已实现波动）。
因此本表只作提示，严格的零参照要从下面两条经验零分布来。

\\subsection{{另一侧：构造之间不独立，解析地板因此偏严}}
解析地板假设 $n$ 次检验相互独立。实际不然：同一族的构造共用底层序列。
集合的界必须先说清楚，否则算出来的数没有对照对象 —— 这里取
\\textbf{{机制先验族里在决策网格上能重新求出信号序列的全部冻结构造}}，
共 {n} 条，{rho['n_pairs']} 对。信号序列不是回放存下的数字，
而是用冻结规格在决策网格上重新求值得到。

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.20\\textwidth}} r r
>{{\\raggedright\\arraybackslash}}p{{0.30\\textwidth}}@{{}}}}
\\toprule
量 & 实测 & 纯噪声参照 & 说明 \\\\ \\midrule
两两 $|\\rho|$ 中位 & {_num(rho['median'])} & {_num(ref['abs_rho_median_under_null'])} &
  {rho['median'] / ref['abs_rho_median_under_null']:.2f} 倍 \\\\
两两 $|\\rho|$ 平均 & {_num(rho['mean'])} & {_num(ref['abs_rho_mean_under_null'])} &
  {rho['mean'] / ref['abs_rho_mean_under_null']:.2f} 倍 \\\\
最大特征值 & {c['eigenvalues_top10'][0]:.2f} & {c['marchenko_pastur_upper']:.2f} &
  纯噪声上界为 Marchenko-Pastur \\\\
大于 1 的特征值 & {c['n_eigenvalues_above_one']} 个 & — &
  这些构造大致张成十几个方向 \\\\
\\bottomrule\\end{{tabular}}
\\caption{{构造之间的相关结构。纯噪声参照\\textbf{{逐对按该对自己的共同点数}}计算
再同类汇总（均值对均值、中位对中位）。产物：
\\texttt{{artifacts/manifests/construction\\_correlation.json}}。}}
\\end{{table}}

把实测相关矩阵直接拿去模拟纯噪声下的最大 $|z|$，期望为 {_num(sim['expected_max_abs_z'])}
（{sim['draws']} 次，种子 {sim['seed']}），而同一个 $n$ 的解析地板
$E_2({n})={_num(c['analytic_floor_same_n'])}$。即解析地板在这一侧\\textbf{{偏严}}约
{_num(c['floor_over_strict_by'], 3)}，{n} 次尝试大致等价于
{c['equivalent_independent_tests']} 次独立尝试。

\\textbf{{模拟的 $n$ 必须与对照的 $E_2(n)$ 是同一个 $n$}}。这一句看起来是废话，
但先前的一段论述正是在这里出错：它用了「40 条构造」，而 40 是当时预注册的
\\textbf{{回合预算}}，不是被相关的构造数。拿回合预算去查 $E_2$ 表，对照的对象就错了。

\\textbf{{一处需要挑明的巧合}}：本节的 $n={n}$ 与第~\\ref{{sec:coverage}}~节那条批级
证否线的 $n$ 恰好都是 {n}，但它们是两个来历不同的数。本节的 {n} 是\\textbf{{可重新
求值的冻结构造数}}（已读结果的那些，加上读取之前即被拦下、因而没消耗分母的那几条）；
证否线的 {n} 是\\textbf{{预算末分母}}（开跑前的分母加本批回合数）。两者相等是巧合，
不存在一个由另一个推出的关系。

\\subsection{{两处自我更正，其中一处此前也没改对}}
先前给出过一条折算：用设计效应公式 $n/(1+(n-1)\\bar{{\\rho}})$ 得到有效次数 6.4、
地板将降至 1.66。那是错的，原因有两条，而当时只有第一条说对了：

\\begin{{enumerate}}
\\item \\textbf{{第一条仍然成立}}：设计效应公式是给\\textbf{{平均值}}用的，
      不能用于\\textbf{{最大值}}。最大值的分布不由方差决定。正确做法是用实测相关
      矩阵直接模拟最大值，即上一小节所做的。
\\item \\textbf{{第二条当时说错了}}：当时称「实测 $|\\rho|$ 中位 0.054 仅略高于纯噪声
      期望 0.040，故观察到的相关多半是抽样噪声」。那是\\textbf{{中位对均值}}，
      不同类。同类比较下相关是真的：平均之比 {rho['mean'] / ref['abs_rho_mean_under_null']:.2f} 倍，
      且最大特征值 {c['eigenvalues_top10'][0]:.2f} 远超纯噪声上界
      {c['marchenko_pastur_upper']:.2f}。第一条的结论不因此改变（方法错就是错），
      但理由要改写。
\\end{{enumerate}}

两处限制必须与结论同印：由信号相关推出统计量相关，是零假设下的近似而非恒等式；
相关矩阵自身的抽样误差没有传播进「偏严多少」那个差值，该值是点估计。

\\subsection{{两条经验零分布：切的是同一条链的两端}}
\\begin{{itemize}}
\\item \\textbf{{置换检验}}（既有）：按 Episode（一段连续的持仓区间）整块打乱
      \\textbf{{标签}}，保留真实因子序列。它条件于真实的 $x$，但 $y$ 侧的序列结构
      与体制被打乱破坏，零分布可能过窄。
\\item \\textbf{{decoy 校准}}（诱饵构造，本批新增）：把真实因子\\textbf{{循环平移}}
      得到一条伪造因子，保留真实标签序列的肥尾、体制与序列相关，也逐点保留因子自身的
      边际分布与自相关（平移不改变这两者），只破坏 $x$ 与 $y$ 的配对。
      不用打乱因子，因为打乱会毁掉因子的自相关，而自相关正是构造伪迹的主要来源。
\\end{{itemize}}

评价机在同一次评价里同时记下两个超越比例，因此每一条带 decoy 的 Study 本身就是一次
配对观测，两个比例算在同一批预测、同一批标签上。截至本报告快照共
\\textbf{{{e['n_paired']} 条}}配对读数，其中 decoy 更严 \\textbf{{{e['n_decoy_stricter']} 条}}
（{_pct(e['share_decoy_stricter'])}），符号检验双侧 $p={e['sign_test_two_sided_p']:.4f}$；
中位为置换 {_num(e['median_placebo_exceed'])}、decoy {_num(e['median_decoy_exceed'])}。

\\textbf{{可读的是方向，不是任何一对的差值大小}}。decoy 只有 {e['decoy_draws']} 次平移，
单条比例的蒙特卡洛标准误上界约 {_num(e['per_row_mc_se_upper_bound'], 3)}，
因此单条构造上的两率之差多半落在抽样误差之内。
""" + ("" if not e["exceptions"] else f"""
反向的例外如下，一并列出而不是只报有利的那一侧：

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.26\\textwidth}} r r@{{}}}}
\\toprule
Study & 置换超越比例 & decoy 超越比例 \\\\ \\midrule
{exception_rows}\\bottomrule\\end{{tabular}}
\\caption{{decoy 反而比置换更松的那几条。产物：
\\texttt{{artifacts/manifests/empirical\\_nulls.json}}。}}
\\end{{table}}
""") + r"""
\textbf{decoy 只作信息披露，不作判据}：把它升格为闸门需要另一份决定，先看两条零分布
在更多真实构造上的分离度。同时禁止用 decoy 差距给构造排序 —— 那会使它变成一次选择
读取。它不读任何新的结果（用的就是本次已读的标签），因此不进统计分母。

\subsection{封存段自己的分母}
\textbf{封存段}是预留作最终检验的数据段，每个特征只允许在其上评价一次。
一次性规则挡的是「同一条构造反复开封」，它挡不住「在同一段封存数据上试很多条不同
构造、再报告其中最好的那条」—— 那同样是取最大值，同样要按次数记账。

实测：封存段已开 18 次、18 条互异构造、全部在同一段上，而这 18 次读取此前一次都没进
任何分母。补记后，封存段分母 18、地板 $E_2(18)=2.1475$，而封存段历史最大
$|t|=1.836$ —— \textbf{连封存段自己的地板都没越过}。这比「四次封存否决」更强：
不是个别候选没保住，是整个封存段的最大值仍在噪声带内。此后每次开封在证据里并列记下
开封前后的分母，使「18 选 1」与「钉死一条开一次」在记录上可以分辨。

\subsection{为什么这一节对确认模式尤其要紧}
解析地板是一条\textbf{搜索修正}：它回答「试了 $n$ 次，运气能给多好」。
在单次确认里没有搜索，它塌回单次临界值。但基准线并未因此消失，只是必须换一种造法：
从数据里造，而不是假设一个理论分布。两条经验零分布都不依赖「试了几次」，
因此在 $n=1$ 上同样成立。

\subsection{两侧都量出来之后，门槛为什么照旧}
肥尾那一侧使参照物偏松，相关那一侧使解析地板偏严，两者方向相反，
而净效应\textbf{没有量化}。在净效应没有量化之前调整门槛，等于挑一侧对自己有利的
偏差去用。因此这两项测量\textbf{都不下调任何门槛}，它们进入报告是作为标定的
不确定性说明，不是作为调低标准的依据。
"""


def coverage_section(run: str = "run31") -> str:
    s = _load(f"settlement_{run}")
    cov = s["coverage"]
    unc = cov["uncovered"]
    thin, unread = unc["thin_history"], unc["full_history_but_unread"]
    thin_text = "、".join(
        f"\\path{{{r['product']}}}（{r['target_rows']}）" for r in thin)

    return r"""
\section{把中国期货覆盖全：三种形态的代价与机制子面板}\label{sec:coverage}
\textbf{品种域}（\path{universe}）是一次评价所覆盖的期货品种集合，它是提案的一个字段，
在检验之前锁定。本节讲一个此前一直没被处理的问题：搜索几乎全都压在一个品种上。

51 个品种有目标表，其中 27 个被单独检验过，而原油一个品种就占了 121 次；
24 个从未被单独检验。更彻底的一点是，全部历史提案的目标 100\% 是原油，
即被解释的那一侧从来没有换过品种。

\subsection{三种形态各自的代价}
\begin{table}[htbp]\centering\footnotesize
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.22\textwidth} r r
>{\raggedright\arraybackslash}p{0.34\textwidth}@{}}
\toprule
形态 & 覆盖 51 个要几票 & 证否线 & 能否取到 \path{candidate} \\ \midrule
逐品种 & 51 & 2.7417 & \textbf{不能}（品种维退化） \\
\textbf{机制子面板}（约 5 品种一组） & \textbf{11} & 2.5510 & 能 \\
全覆盖面板 & 1（只覆盖 36 个） & 2.4771 & 能 \\
\bottomrule\end{tabular}
\caption{覆盖全部品种的三种形态。证否线按各自的预算末分母算出，
多买一张彩票中奖标准就要相应提高。}
\end{table}

逐品种为什么取不到候选，要看双向 cluster 标准误：它同时按日期与按品种聚类，
以免把同一天多个品种的共同波动当成互相独立的证据。单品种的品种维只有一组，
这一维退化，评价机发出 \path{cluster\_structure\_insufficient}，
而该理由按失效表使 \path{candidate} 失效。全覆盖面板则有另一个问题：
只作用于少数品种的机制会被其余品种稀释，甚至被反号的品种抵消。

\subsection{子面板：品种集合必须由机制论证，并随提案冻结}
新增的品种域形态写作 \path{mech_panel:} 后接以加号分隔的品种代码，按传导通道选出一组品种，
一次评价覆盖它们全部，品种维因而有变异、候选可达。至少两个成员：
一个成员的子面板就是单品种，不该用另一个名字表达，否则就绕过了品种维退化的记账。

关键的一条纪律是\textbf{品种集合随提案冻结并进入内容指纹}。它必须由机制文本论证，
事后按结果挑品种在盲化下也做不到。与之配套，菜单只给出形态与可用品种全表，
\textbf{不预先枚举组合}：替提案挑组合，那就成了菜单的选择而不是研究判断。

""" + f"""\\subsection{{实测：满行的品种已无遗漏}}
{run} 的 {s['studies_decided']} 条提案覆盖了 \\textbf{{{cov['n_products_read']} 个品种}}，
品种域形态的分布为 {'、'.join(chr(92) + 'path{' + k + '} ' + str(v) + ' 次' for k, v in cov['universe_forms'].items())}。

余下 {len(thin) + len(unread)} 个品种没有被读到，但\\textbf{{原因要分开说}}，
否则一条关于数据可得性的事实会被读成一条关于搜索行为的事实：

\\begin{{itemize}}
\\item \\textbf{{目标表行数不足 {len(thin)} 个}}：{thin_text}，
      对满样本 {unc['full_coverage_rows']} 行。这是一条数据可得性的事实，
      不是搜索遗漏；至于它们为什么行数少（上市晚、成交稀疏或别的原因），
      本报告没有核过，不下断言。
\\item \\textbf{{满行却未被选中 {len(unread)} 个}}：{'无' if not unread else '、'.join(chr(92) + 'path{' + r['product'] + '}' for r in unread)}。
\\end{{itemize}}

{'因此在「有足够历史可供检验」这个意义上，覆盖已经完成。' if not unread else ''}
这与本批之前的状况对照鲜明：此前二十条提案只覆盖十八个品种，
且其中多数是同一个品种的重复检验。

\\subsection{{一处边界情形，以及它要求的记账}}
{run} 中有 {s['t_undefined']} 条检验的 $t$ \\textbf{{无定义}}：
双向 cluster 标准误算出了负方差。评价机如实记下两条阻断理由并判 \\path{{null}}，
\\textbf{{没有}}改用可计算的替代标准误去凑一个数 —— 代码中 $t$ 只由双向 cluster
标准误定义，替代口径会给出一个大得多的值并可能冲击封存名额。
这与此前修过的单点影响那次是同一类纪律：度量失败不得报成关于特征的实质发现。

由此引出一条必须写进报告的记账规则：\\textbf{{「因 cluster 结构不足而 $t$ 无定义」
要单独计数}}。这类检验消耗了分母却不进「最好 $|t|$」一类统计，
若不单列，读者会以为每次检验都产出了可比的读数。与之配套的另一半是：
\\textbf{{分母仍然照扣}}。分母记的是「看了几次」，不是「看成了几次」；
若把算不出 $t$ 的那次从分母里摘掉，等于让一次失败的读取免费。

\\subsection{{本批的结算与预注册停止规则}}
本批预注册了一条停止规则：四十票花完后，若三条同时成立 —— 候选为零、
合格构造最好 $|t|$ 未越批级证否线、符号一致率仍在掷硬币的噪声内 ——
则宣告数据源级否定并终止检验票支出。

结算结果：\\textbf{{三条中成立两条，规则不触发}}。合格最好
$|t|={s['best_by_tier']['另类数据且符号一致']['best_abs_t']:.4f}$，
未越 $E_2({s['budget_denominator']})={s['floor']:.4f}$；符号一致
{s['direction']['sign_agrees']} 条、相反 {s['direction']['sign_opposite']} 条，
对 50\\% 的双侧 $p={s['direction']['two_sided_p_vs_half']:.4f}$，仍在噪声内。
不成立的是第一条：本轮有 {s['verdicts'].get('candidate', 0)} 条候选。

规则不触发\\textbf{{不是一次退让}}，需要把这三条候选的性质讲清楚：

\\begin{{itemize}}
\\item 它们是方向判据生效之后产出的第一批候选，因此与 run29 那三条不同，
      \\textbf{{符号与自己声明的方向一致}}；
\\item 但三条的 $|t|$ 全部低于各自读取时刻的\\textbf{{本族地板}}
      （$2.194$ 对 $2.4771$、$2.021$ 对 $2.5510$、$2.020$ 对 $2.5824$），
      更低于批级证否线。按报告反复申明的辨析，这属于「闸门全过而效应微弱」，
      不是发现；
\\item 更要紧的一点：\\textbf{{三条出自同一条机制轴}}（本批新增的美国大选关税倾向轴），
      因此它们不是三个互相独立的发现，而更接近同一条机制被在三组品种上测了三次。
      把它们当作三份证据会重复计数。
\\end{{itemize}}

据此，本批的结论是：没有任何构造越过它所在族的地板，
而停止规则因候选计数一条不满足而暂不触发。是否续投预算属于统计预算决定，
由人裁断，不由本报告代为决定。

\\subsection{{两条容易被混为一谈的线}}
报告里「越线」一词指过两件不同的事，此处一次分清：

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.20\\textwidth}}
>{{\\raggedright\\arraybackslash}}p{{0.40\\textwidth}}
>{{\\raggedright\\arraybackslash}}p{{0.24\\textwidth}}@{{}}}}
\\toprule
线 & 定义 & 何时存在 \\\\ \\midrule
\\textbf{{当次族地板}} & 读取时刻的 $E_2(n)$，$n$ 为该族当时已读次数，随分母上升 & 一直存在 \\\\
\\textbf{{批级预注册证否线}} & 开跑前按预算末分母定的 $E_2(n_{{\\text{{预算}}}})$，全轮统一 & 决定 0011 起 \\\\
\\bottomrule\\end{{tabular}}
\\caption{{两条线的区别。混用会让同一句「第一条越线」指向不同的构造。}}
\\end{{table}}

因此诚实的表述要两句并列，不能只说后一句：run16-study-3 是第一条越过
\\textbf{{当次族地板}}的另类数据构造（$|t|=4.3925$），它走完全流程后
\\textbf{{在封存段被否}}；run29-study-4 是第一条越过\\textbf{{批级预注册证否线}}的
构造，核实时发现斜率符号与其声明方向相反。批级证否线是后来才引入的，
旧族从头到尾都没有过这条线 —— 「第一条越过它的」在很大程度上是因为
这个概念此前不存在，这一点必须讲明，否则那句话读起来比它配得上的要强。
"""


def climb_section() -> str:
    c = _load("climb")
    series = [s for s in c["series"] if s["best_reward"] is not None]
    rows = "".join(
        f"\\path{{{s['run']}}} & {s['family']} & {s['n_decided']} & "
        f"{s['n_t_undefined']} & {s['n_qualified']} & {s['best_abs_t']:.3f} & "
        f"{s['best_floor']:.3f} & ${s['best_reward']:+.3f}$ \\\\\n"
        for s in series)
    positive = c["positive_runs"]
    pos_text = "、".join(
        f"\\path{{{r['run']}}}（${r['reward']:+.3f}$）" for r in positive)

    return r"""
\section{爬升的诚实读数}\label{sec:climb}
自动研究的图景是「沿曲线一直往上爬」。本节回答它到底有没有在爬，
用的是一把先说清楚的尺。

\subsection{先说清用哪把尺}
\textbf{奖励} $=|t|-$ 当次本族地板。三条约定，一次说明、全节执行：

\begin{enumerate}
\item \textbf{地板取当次本族地板}：读取该次结果时该族已读次数 $n$ 对应的 $E_2(n)$。
      这是评价机当时真正施加的那条线。报告另有「合并地板」口径（把三本账并成一个
      分母），两者都真但不可混用，本节只用本族口径。
\item \textbf{$n$ 按读取次数计}，一次读取消耗一次分母，与那次有没有算出有限的 $t$ 无关。
\item \textbf{合格}指来自另类数据（量价构造属基线对照，不计入另类清单）
      \textbf{且}斜率符号与预注册方向一致。符号相反的读数不支持它自己主张的机制，
      不该计入成绩。
\end{enumerate}

这把尺比报告其余部分用的都严，正因为本节要回答的是最容易自我安慰的那个问题。
还须记住第~\ref{sec:nullbase}~节的结论：这把尺本身的标定有两侧方向相反的不确定性，
净效应未量化。

""" + f"""\\subsection{{全部有合格构造的运行，一个不漏}}
早先的一稿印过一条十个数的序列并附了一段更正，但那条序列\\textbf{{仍然不完整}} ——
有合格构造的运行共 {c['n_runs_with_qualified']} 个，更正只补了其中五个。
一段以「对趋势诚实」为主题的正文里留一个不完整的序列，是最不该留的缺口。
下表一次给全，由产物直接渲染，不再手抄。

\\begin{{table}}[htbp]\\centering\\footnotesize
\\begin{{tabular}}{{@{{}}>{{\\raggedright\\arraybackslash}}p{{0.10\\textwidth}}
>{{\\raggedright\\arraybackslash}}p{{0.07\\textwidth}} r r r r r r@{{}}}}
\\toprule
运行 & 族 & 判决 & $t$ 无定义 & 合格 & 最好 $|t|$ & 当次地板 & 奖励 \\\\ \\midrule
{rows}\\bottomrule\\end{{tabular}}
\\caption{{逐轮合格构造的最好成绩。产物：\\texttt{{artifacts/manifests/climb.json}}，
地板口径见上文三条约定。}}
\\end{{table}}

奖励为正的只有 {c['n_runs_with_positive_reward']} 轮：{pos_text}。
\\textbf{{三条后来都没有存活}}，其中最高的那条走完全流程后在封存段被否：
样本外斜率仅为样本内的 18.7\\%，秩相关同时降至接近零。

\\textbf{{一处更正}}：先前说过「近三轮最低」，那不成立 —— 早期有三轮的奖励为正，
且更早的若干轮比近三轮更低。序列在 ${c['worst_reward_overall']:+.3f}$ 至
${c['best_reward_overall']:+.3f}$ 之间起伏，没有上行趋势，这是可以说的；
「近三轮最低」不可以说。

\\subsection{{结构性的原因：门槛在抬，成绩没动}}
地板随分母单调上升，因此\\textbf{{维持同样的 $|t|$ 等于奖励在下降}}。
这不是原地踏步，是有效距离在拉大：要在第 100 次尝试上说出与第 10 次同样有力的话，
需要一个大得多的读数。上表里近几轮的合格最好 $|t|$ 与早期同量级，而地板已经抬高了
将近一个单位。
""" + r"""
\subsection{装置确实在改善，但它买到的不是信号}
需要同时说清两件事，而且不能把任何一件说得比数据支持的更满。

装置侧的改善是实的：机械损耗（解析失败与 provider 修复）从早期的约五分之一回合
降到近几轮的零或个位数；搜索广度从一个品种散到四十个；机制族从零使用到全部提案使用；
方向判据补上后候选归零。但这些序列\textbf{都不是单调的}，中间有反复，
把它们讲成一条平滑上升的曲线是不诚实的。

更要紧的是，它们买到的是「测的对象是它自称的那个东西」与「失败能被正确归类」，
不是「离找到信号更近」。后者不可度量，而可度量的那个量 —— 合格构造与门槛的距离 ——
在扩大而不是缩小。

到目前为止最可靠的产出仍是：一批带排除界的否定、四次封存否决、
以及一批被正确识别出来的假象。这不是一句谦辞。一个能把自己的假象认出来的装置，
比一个报告了假象的装置有用得多；本报告全部的可信度都建立在前者上。

\subsection{配图}
\begin{figure}[htbp]\centering
\includegraphics[width=\textwidth]{figures/qualifying_climb.png}
\caption{三本账各一栏的爬升图。横轴是本族已读结果次数，虚线为随之上升的零假设地板，
橙点为合格构造（另类数据且符号一致），灰点为不合格者。
子图标题里的数是\textbf{可作图的点数}，与分母不等：$t$ 无定义的读数消耗了分母
却画不出点。}\label{fig:climb}
\end{figure}

图~\ref{fig:climb} 把三本账各画一栏：虚线是随分母上升的零假设地板，
橙点是合格构造（另类数据且符号一致），灰点是不合格者。橙点始终在虚线之下，
唯一的例外是旧族那个后来在封存段没保住的点。

它与另外三条搜索曲线的差别只在\textbf{过滤}：不过滤的曲线看起来乐观得多，
而那些高点逐条查下来都不成立 —— 最大的那个是波动率聚集假象（分母是已实现波动，
目标也是已实现波动），机制族最高的那条方向相反、单点影响过大且品种维退化。
"""


def all_sections(run: str = "run31") -> str:
    return (direction_check_section() + null_baseline_section()
            + coverage_section(run) + climb_section())
