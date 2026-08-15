"""报告第九版新增的三节（M16 至 M18）。

拆成独立模块只为篇幅：build_report_tex.py 的 render() 已经很长，
再塞三节会让任何一处改动都要在上千行里定位。

三节的内容经过一轮起草与两轮核实（逐数字复算 + 对抗审稿），
审稿指出并已在此改正的实质问题：
1. 参照带写反：五族与前身的序数一致「不可区分于无关序列」这一表述不成立 ——
   其中三族落在参照带内（确实不可区分），另两族低于参照带下界（差异比无关序列还大）。
2. 同一指纹指认两个不同对象（规则集与花名册），审计照此复核必然失败。
3. 「盲化挡住事后择优」写成了无条件现在时，与前一节刚划出的前向边界冲突。
4. 未转义的百分号会使 LaTeX 吞掉半句。
"""

from __future__ import annotations


def mechanism_families_section() -> str:
    return r"""
\section{检验的单位：从词汇聚类到机制聚类}\label{sec:mechfam}
检验一个假说之前，必须先确定\textbf{检验的单位}。ARAD 的信号侧序列由「族」聚合而成：
一个族是一组 Polymarket 市场，其概率按成交额加权合成一条时间序列，特征再由该序列构造。
成员规则因此决定了序列在度量什么。现行规则见
\path{src/arad/data_catalog/pm_series.py} 的 \path{conditions_by_family} 函数：
把市场的 slug（网址中由连字符分开的英文标识）分词，与族词表有交集即判入族。
这是词汇聚类，不是机制聚类。

本节多次出现两个时间概念，先给定义：\textbf{discovery 段}指用于搜索假设的历史数据段
（截至 2024-12-31），与预留作最终检验、每个特征只允许评价一次的\textbf{封存段}相对；
\textbf{小时桶}指把时间按小时切成的格子，一格内的成交聚合为该族的一个概率取值。

\subsection{词汇族实际混入了什么}
\begin{center}\footnotesize
\begin{tabular}{@{}l r p{0.22\textwidth} p{0.34\textwidth}@{}}\toprule
族 & 成员数 & 族词表 & 混入实例 \\ \midrule
\path{cand:iran} & 1{,}444 & attack, iran, response, shipping, successfully, targets &
  「土耳其空袭伊朗」「美伊核谈重启」「特朗普会晤时会不会提到伊朗」同处一池 \\
\path{cand:hormuz} & 237 & hormuz, send, ships, strait, transit, warships &
  send 拉进「是否向底特律派国民警卫队」与电竞市场；transit 拉进
  「乌克兰是否恢复俄气过境」与纽约地铁 \\
\path{cand:blockade} & 78 & been, blockade, has, that &
  四词中三个是虚词；该族在 discovery 段的 4{,}272 个小时桶完全由「外星人是否存在」
  与「OpenAI 是否达成 AGI」的概率构成，零封锁内容 \\
\path{cand:oil} & 829 & cl, crude, oil, per, production &
  per 是通用介词；该族含电影《Sarah's Oil》的烂番茄评分市场 \\
\bottomrule
\end{tabular}\par\vspace{2pt}
{\footnotesize\parbox{0.9\textwidth}{成员计数为\textbf{全历史口径}的族词表扫描，
与 \path{artifacts/manifests/pm_candidate_families.json} 的 markets 字段逐族相等；
下一小节的诊断数字则一律限于 discovery 段，两者口径不同，不可直接相减。}}
\end{center}

\subsection{诊断：不是正反抵消，而是构成与桶占有}
一个直觉的解释是同族内正反机制相互抵消。discovery 段实测否定了它：
\path{cand:iran} 的反极性成员只有一个市场，\path{cand:hormuz} 在该段只有一个成员。
起作用的是另外两条途径。其一，\textbf{构成切换主导方差}：族概率的日度变化主要来自
当日哪些市场在成交、权重如何，而非同一批成员自身的重定价；纯正向子集自身的构成方差
也在七成以上，混入只是放大了本已存在的性质。其二，\textbf{噪声经桶占有而非经成交额
进入构造}：window 算子对小时桶等权，一个桶只要有成交就贡献一份权重，与额度无关，
于是按成交额只占一成六的噪声，按桶占到近三成。

\begin{center}\footnotesize
\begin{tabular}{@{}p{0.16\textwidth} p{0.26\textwidth} p{0.44\textwidth}@{}}\toprule
诊断 & 口径 & discovery 段实测 \\ \midrule
（已否定）正反机制抵消 & 反极性成员的规模 &
  \path{cand:iran} 反极性成员为 1 个市场，占族名义额 0.8\%，覆盖 423 个小时桶
  （正向成员 4{,}425 桶）；\path{cand:hormuz} 的「27 封锁加 12 恢复」是 2025 至 2026 年
  的现象，该族 discovery 段只有 1 个成员 \\
构成切换主导方差 & 日度 $\Delta p$ 方差分解为构成移动与成员重定价 &
  构成移动 91.3\%，成员重定价 7.0\%；纯正向子集自身的构成方差仍占 74.3\% \\
噪声经桶占有进入 & 族桶计数与名义额两种口径对照 &
  噪声独占 \path{cand:iran} 全部 6{,}098 个族桶中的 1{,}673 个（27.4\%）；按名义额
  噪声只占 16.1\%、正向子集 83.1\%；2024-03 正向名义额占比实测 0.000、2024-05 为 0.002，
  这两个月族概率整月由噪声定价 \\
既有结论受影响的量级 & 同一构造在混合族与纯正向子集上的日度相关 &
  run11-study-3 的形态（30 日均值）相关 0.176（$n=387$）；run16-study-3 的形态
  （12 小时均值的 $p(1-p)$）相关 0.700 \\
\bottomrule\end{tabular}\end{center}

\subsection{机制族层的实现}
机制族成员由冻结的谓词规则集定义，只作用于 slug，不枚举市场清单：先过实体门，
再按序判定排除段、路由段与成员段，每个成员带 $\pm 1$ 极性，同一机制的否定式提问
折成同号（$q=p$ 或 $q=1-p$）。落在实体门内、既不入成员段也不入排除段的市场
（即规则的盲区）在 discovery 段为 0 个，这是构建时的硬性检查，不取默认值。

序列口径与词汇族逐字相同（成交额加权、按 \path{outcome_seq==1} 归一、分桶取右端），
使「成员资格」成为唯一变化的变量；另产出构成受控的分桶变化 \path{dp}
（只对相邻两桶共有的成员求加权重定价，权重取前一桶成交额，新入族成员不贡献电平跳变）
与当桶活跃成员数 \path{conditions}。编译得成员 1{,}410 行、排除 2{,}606 行，
八族 discovery 成员数与人工分诊的锚点逐一相符，规则集内容指纹前 16 位为
\path{e90addfe4641482a}。

分类模式取自一项外部研究（Rev-PLM 的价格形成驱动分类与 Polymarket 可测族清单，
35 族、431 个结果代币、706 个「族 $\times$ 品种」配对；该研究与本项目同属一人所有，
其产物路径记于 \S\ref{sec:repro}）。其清单不可照搬：只有 132 个代币见于 ARAD 档案；
它在 discovery 段仅覆盖 490 个「资产-日」，其中 316 个属同一族；
\path{HORMUZ_CLOSE} 的 21 个代币有 20 个是「封锁被解除」式提问，而该族 25 个配对品种
一律标为正向，照搬清单连同其方向先验会使 95\% 的代币方向相反。
故只借其分类法作标注模式，在 ARAD 自家的 PIT 市场索引（point-in-time，
即只含当时已可得信息的索引）上重建成员，成员资格由首笔公开成交定义。

\subsection{重合度闸门与它的裁断}
闸门判断机制族是否只是其词汇前身的改写。\textbf{裁断所依据的量}是决策网格上的窗口
取值（21600 秒窗口、offset 0 的族概率水平），因为那才是特征真正看到的量；
同一份 manifest 并列报告小时级的 \path{dp} 与小时级水平两个口径，但裁断不取它们。
统计量为序数一致比例：随机取两个时点，看两条序列是否给出同向排序，0.5 表示无关联。
阈值取自参照分布而非本次结果：无关机制族两两比较共 24 对，中位 0.502、
区间 0.463 至 0.582；上界 0.582 定为 \path{distinct_upper}，
它与 1.0 的中点 0.791 定为 \path{replay_lower}。

\begin{center}\footnotesize
\begin{tabular}{@{}p{0.25\textwidth} p{0.19\textwidth} r r p{0.13\textwidth}@{}}\toprule
机制族 & 词汇前身 & 前身引用 & 序数一致 & 裁断 \\ \midrule
\path{mech:FED_HIKE} & \path{cand:cut} & 0 & 0.135 & 不同（反号）\\
\path{mech:RU_UA_CEASEFIRE} & \path{cand:ukraine} & 76 & 0.442 & 不同 \\
\path{mech:HURRICANE_LANDFALL} & \path{cand:a} & 32 & 0.530 & 不同 \\
\path{mech:FED_DECISION} & \path{cand:interest} & 0 & 0.544 & 不同 \\
\path{mech:US_INFLATION_MONTHLY} & \path{cand:inflation} & 0 & 0.561 & 不同 \\
\path{mech:HOUTHI_ATTACKS} & \path{cand:military} & 0 & 0.703 & 部分重合 \\
\path{mech:ISR_IRAN} & \path{cand:iran} & 474 & 0.816 & 重放 \\
\path{mech:US_SHUTDOWN} & \path{cand:government} & 0 & 0.883 & 重放 \\
\bottomrule
\end{tabular}\par\vspace{2pt}
{\footnotesize\parbox{0.9\textwidth}{判定分三带：低于 0.582 判「不同」，
0.582 至 0.791 判「部分重合」，高于 0.791 判「重放」。「前身引用」指该词汇族
在 ARAD 全部历史规格中被引用的次数。五个判「不同」的族里，
\textbf{三族（0.530、0.544、0.561）落在无关族参照区间 0.463 至 0.582 之内}，
即与前身的关系已与两条无关序列之间的关系不可区分；
\textbf{另两族（0.135、0.442）低于该区间下界}，与前身的差异比无关序列之间还大。}}
\end{center}

\subsection{一条与直觉相反的结论}
ARAD 的历史搜索共有 474 条规格引用 \path{cand:iran}，居全部词汇族之首，而
\path{mech:ISR_IRAN} 与它重合 0.816 判为重放。\textbf{在闸门所测的量上}
（决策网格的窗口取值），这条轴上的词汇族本来就已经近似是机制族，
机制重建不构成增量；\path{dp} 与 \path{conditions} 两个派生量未经此判据检验，
其增量另行评估。

但「重放」与「无价值」不是一回事。重放说的是机制族与其词汇前身近似等价，
等价是否构成损失，取决于\textbf{前身是否被检验过}。\path{mech:ISR_IRAN} 重放且前身
引用 474 次，增量为零；\path{mech:US_SHUTDOWN} 同判重放（0.883），但前身引用为 0，
与一条从未被检验的族等价并不付出代价，该轴仍是没问过的问题。
本报告付印前的排除规则曾把这两种情形一并排除，即因为「像一条同样没被检验过的序列」
而永久放弃一条未测轴；更正后的规则要求排除同时满足两个条件：
重合度裁断不在准入集合内，\textbf{且}其词汇前身确曾被检验过（\S\ref{sec:accounts}）。

增量在别处：八族中五族的词汇前身从未被任何历史规格引用过，
即美联储加息路径、议息幅度、月度通胀、政府停摆、红海袭击这五条机制轴一次都没测过。
此外还有一处具体缺陷：\path{mech:FED_HIKE} 与 \path{cand:cut} 的序数一致仅 0.135，
近乎反号 —— 词汇族的族信念是「降息发生」，而机制族问的是「加息发生」；
该族历史引用为 0，故无既有结论因此失效。
"""


def researcher_boundary_section() -> str:
    return r"""
\section{研究员进程的边界：闸门此前拦不住的两条通道}\label{sec:hermetic}
\subsection{闸门原本在哪，它真实拦下过什么}
盲化（blinding）在本项目指：提出假设的角色不得看见任何已知结果。实现是调用前的
一道检查 \path{assert_blinded}，在提示词组装完成、发出之前扫描整段文本，一旦命中
效果字段名（\path{beta}、\path{t_stat}、\path{p_value}、\path{ic}、\path{sharpe}、
\path{return}、\path{alpha}、\path{slope}，以及 \path{se_}、\path{mde_}、
\path{beta_} 等前缀）即拒绝调用。它确实拦下过：run25 把先验研究的方向文本交给研究员，
人写的那段文字里出现一个效果词，闸门三次拒绝组装，整轮作废、零研究
（\S\ref{sec:chronicle}）。人写的指令不豁免审查。

\subsection{它扫不到的两条通道}
闸门扫的是提示词文本，管不到模型自己取回的东西。2026-08-15 实测本机默认的
\path{claude -p} 调用：CLI 在会话开始时发出的 init 事件回报显示，研究员可用的工具
包括 \path{Bash}、\path{Read}、\path{Write}、\path{Edit}、\path{Task}、
\path{WebSearch}，外加全部已连接的 MCP 服务器（MCP 是把外部服务接进模型的协议，
此处有 Gmail、Notion、Slack、Figma 等），工作目录就是仓库根目录。
也就是说，盲化角色在原理上可以自己去读 \path{data/ledger/service.db}，
把全部判决、$t$ 值与封存结果取回来；闸门所在的位置拦不住这条路。
第二条通道同形：用户级 \path{CLAUDE.md} 会被读进研究员上下文。
人工核对该文件不含效果字段词，但它从未经过 \path{assert_blinded}，也从未进过账本。

过去的调用是否真的用过这些工具，\textbf{无法追认}：当时的 provider 既不记录
\path{num_turns}，也不记录 \path{tool_use}。只能如实陈述：能力一直在，且未被记录。
因此下文的断言是\textbf{前向的}：它覆盖本次改造之后的调用，不能追溯认证此前的
196 条提案与两族分母。变化在于这两个字段此后进入证据，这个问题从此可回答，
此前不可回答。

\subsection{处置：以运行时回报为断言基础}
\begin{center}\footnotesize
\begin{tabular}{@{}p{0.27\textwidth} p{0.31\textwidth} p{0.30\textwidth}@{}}\toprule
参数 & 它关掉什么 & init 事件的回报 \\ \midrule
\path{--disallowed-tools} & 拒绝全部工具，清单 37 项 & \path{tools} 为空 \\
\path{--strict-mcp-config} & 不加载任何 MCP 服务器 & \path{mcp_servers} 为空 \\
\path{--disable-slash-commands} & 不加载任何 skill & \path{skills} 与
  \path{slash_commands} 均为空 \\
\path{--setting-sources} 置空 & 不读用户级与项目级设置 & 用户级 \path{CLAUDE.md}
  不再进入上下文 \\
\bottomrule\end{tabular}\par\vspace{2pt}
{\footnotesize\parbox{0.88\textwidth}{全规模复核：claude-opus-5 跑完整的提案器提示词
（246{,}890 字符）加 4{,}188 字符方法说明，耗时 164 秒，\path{num_turns=1}，
工具清单为空，无任何工具调用。}}
\end{center}

拒绝清单会过期：实测拒掉一批之后，\path{Glob} 与 \path{Grep} 才出现在清单里。
因此更强的断言基础是\textbf{运行时回报}而非静态清单：init 事件只要报出任何工具、
MCP 服务器或 skill，即中止调用（\path{require_hermetic}，默认开启）。
该断言依赖 init 事件如实枚举其能力，这一前提本身未经独立验证，应如实记下。

同一原则要求上线前单独做一次探针：被静默忽略的参数与生效的参数，在冒烟测试里
不可区分。探针问「声明原语缺口时三个必填字段叫什么」，标准输入里不含这三个名字，
回答正确，才证明参数生效。

\subsection{方法说明这一层与它的更新规则}
研究员此前只收到一段提示词，没有任何方法说明。本版新增一份版本化的方法说明，
但不走 CLI 的 skill 机制（从目录自动发现并注入的指令文件，即上表关掉的那一类）：
那是环境通道，任何人放一个文件进目录就改变了研究员的上下文，而账本看不见、
闸门扫不到。装载方式因此是显式的：读成字符串，过 \path{assert_blinded}，
算内容指纹，作为 \path{ProviderRequest} 的 \path{system_prompt} 字段发出，
指纹进账本。该字段并入 \path{request_id} 的内容寻址：同一段提示词配不同版本的
方法说明，不是同一次调用。

更新规则写在文件自身，装载时核对：\textbf{只能承载机械失败的教训}，即解析失败、
schema 不合、事前功效筛拦下、语义审计判不一致，它们全部发生在读取结果之前。
来自判决的教训一律不得写入，否则它自身成为结果回流通道，而那正是决定 0006
（禁止本系统的判决结果回流进提案器上下文）关闭的东西。\path{update_rule} 一栏
不是 \path{mechanical_failures_only}，装载即被拒绝。第一版内容取自实测的失败模式：
\path{direction} 写成词而非 $\pm 1$、声明原语缺口（原语指特征构造的基本算子）时
漏掉 \path{mechanism}、自创契约之外的键、给派生步骤加 \path{offset_seconds}、
把 JSON 包进 markdown 代码块。run26 的二十回合里约四分之一耗在这类机械失败上。

\subsection{搜索为什么收窄到一条轴}
\begin{center}\footnotesize
\begin{tabular}{@{}p{0.16\textwidth} p{0.38\textwidth} p{0.36\textwidth}@{}}\toprule
维度 & 实测 & 可选空间 \\ \midrule
universe & 196 条提案里 119 条落在 \path{sc_dominant_t1} & 51 个品种有目标表，
  用过的不到十个 \\
target & 只用过 3 个（\path{rv} 116 条、\path{ret} 68 条、开盘跳空吸收 12 条） &
  目标族本身只有这三个 \\
族 & 1{,}998 个候选族只有 23 个被引用过，\path{cand:iran} 独占 96 条 Study；
  单个组合 \path{cand:iran} $\times$ \path{sc} $\times$ \path{rv} 就有 34 条提案 &
  合格族数以百计 \\
\bottomrule\end{tabular}\par\vspace{2pt}
{\footnotesize\parbox{0.9\textwidth}{\path{sc_dominant_t1} 指原油期货主力连一的
单品种视图；\path{rv} 为下一时段已实现波动率，\path{ret} 为下一时段收益率，
开盘跳空吸收指开盘跳空在当日被回补的比例。}}
\end{center}

原因不在于模型的选择偏好，而在于提示词中不含各组合的历史提案计数。处置是
\textbf{搜索覆盖表}：按（族, universe, target）统计\textbf{提案}次数并进上下文。
它不违反决定 0006：只数 \path{proposal_locked}，不读 \path{evaluation_result} 与
\path{verdict_recorded}，也不按「有没有通过事前筛」过滤；提案计数在读取任何结果
之前就已确定，判决计数才是 0006 关闭的通道。合同测试钉住覆盖表的任何字段里
不得出现判决词。

\subsection{另一处实测：提示词的九成三是旧提案}
组装出的提案器提示词 633{,}755 字符，其中记忆一节 491{,}641 字符，占 93\%：
195 条历史规格，每条都带完整的机制叙述段落。处置：只有最近 12 条带全文，
更早的只留特征名与步骤形状。提示词降至 246{,}890 字符。
"""


def accounts_section() -> str:
    return r"""
\section{三本账：分族的统计理由与它必须付的代价}\label{sec:accounts}
\subsection{前提：地板是什么，为什么只增不减}
「地板」是判定一个结果是否算数的门槛。对同一目标检验 $n$ 个互不相同的构造，
即使全部与目标无关，其中绝对值最大的统计量也会因抽样达到一定高度，该高度的期望值
即地板 $E_2(n)$：只试一次时不足 $0.8$，试过三位数次后升至 $2.8$ 以上。

两条性质决定本节的争议。\textbf{只增不减}：账本只追加，已读取结果的检验不可撤回，
族内分母单调上升。\textbf{追溯生效}：地板按族的当前分母计算，分母增长后，
族内既有记录重印时对照的是更高的线，「距门槛还差多少」的陈述随之改写。
故一次新检验记进哪本账不是记账细节，而是决定由谁支付搜索代价。

\begin{table}[htbp]\centering\footnotesize
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.24\textwidth} p{0.09\textwidth}
p{0.09\textwidth} >{\raggedright\arraybackslash}p{0.40\textwidth}@{}}\toprule
选项 & 分母 & 适用地板 & 追溯代价 \\ \midrule
甲：新开族 \path{sc_mechanism_prior_v1} & 20（预算） & 2.1895 &
  无。旧族与事件条件族的账目原样不动 \\
乙：并入事件条件族 & $33\to53$ & 2.5510 &
  事件条件族 33 条既有否定的对照门槛抬高 0.1702 \\
丙：留在旧族 & $135\to155$ & 2.9058 &
  旧族 135 条既有否定的对照门槛抬高 0.0436 \\
\bottomrule\end{tabular}
\caption{机制族提案的三种记账方式。三者检验的内容相同，差别只在越过哪条线、
谁的既有记录被抬高。地板值由 \texttt{expected\_max\_abs\_z} 实算。}
\label{tab:threeopts}
\end{table}

\subsection{裁定：选甲，三条理由}
\paragraph{（一）家族的统计定义。}多重检验的家族应当是\textbf{实际取过极大值的
那个集合}。五个入选机制族的词汇前身在全部历史规格中的引用次数为
$0$、$0$、$0$、$76$、$32$；重合度闸门在决策网格上判定它们与前身的序数一致
全部低于 \path{distinct_upper}（$0.135$ 至 $0.561$），其中三族落在无关族参照区间
$0.463$ 至 $0.582$ 之内、两族低于该区间下界（\S\ref{sec:mechfam}）。
让它们去越一条由 135 次完全不同构造堆出的门槛，是把无关的搜索历史算作本次负担。

\paragraph{（二）乙的家族不融贯。}事件条件族由触发器的问题形态定义；并入机制族
宇宙上的常在线性检验后，族的定义退化为「某个日期之后测的东西」，那是时间区间，
不是问题族。

\paragraph{（三）通过分族降低门槛的主通道已被规则挡住。}重合度闸门判为重放且
\textbf{前身确曾被检验过}的族不进菜单、不重测；该规则由菜单生成代码执行，
并有合同测试钉住。两个条件缺一不可：付印前的版本只查前一个条件，
于是 \path{mech:US_SHUTDOWN}（前身零引用）被误判为应当放弃，
那等于因为「像一条同样没被检验过的序列」而永久弃掉一条未测轴。

\subsection{买下这项正当性的五条约束}
五条缺一即拒，任一条不成立则裁定作废、退回丙。
\begin{enumerate}\small
\item 序列重合度先行证明族确实不同：裁断取决策网格上的窗口取值，
阈值取自参照分布而非本次结果。
\item 花名册在读取任何结果之前以内容哈希闭合：五个机制族、三个目标族后缀、
现有七种原语。花名册引用的成员规则集，其内容指纹前 16 位为
\path{e90addfe4641482a}；花名册自身的哈希另记于决定文档，两者是不同的对象，
不共用同一指纹。运行期内不得增补。
\item 检验预算预注册为 20 回合，\textbf{全轮证否线统一取预算末地板}
$E_2(20)=2.1895$，不使用轮内更低的早期地板。
\item 每条评价记录与每张因子卡同时印族地板与合并地板：分族站得住的前提是
未分族的那个数字随时可读。
\item 同一机制与目标在旧族读过结果后再测，双计两族分母，禁止迁族降低门槛。
\end{enumerate}
外观风险如实记录：这是第二次分族，由此产生第三本账（表~\ref{tab:ledgers}），
抵消手段即约束 4 的双印。据此声明：\textbf{将来第四本账的请求默认拒绝}。

\begin{table}[htbp]\centering\footnotesize
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.26\textwidth} p{0.09\textwidth}
p{0.09\textwidth} >{\raggedright\arraybackslash}p{0.38\textwidth}@{}}\toprule
账本 & 分母 & 适用地板 & 说明 \\ \midrule
\path{demo_sc_price_volume} & {N_OLD} & {FLOOR_OLD} & 常在线性检验 \\
\path{sc_event_conditional_v1} & {EVENT_N} & {EVENT_FLOOR} & 由触发器的问题形态定义 \\
\path{sc_mechanism_prior_v1} & {MECH_N} & {MECH_FLOOR} &
  机制族；预算 20 回合，全轮以预算末地板 2.1895 为证否线 \\
合并口径（不分族） & {MERGED_N} & {MERGED_FLOOR} & 约束 4 要求随时可读 \\
\bottomrule\end{tabular}
\caption{三本账的现状。「适用地板」指该族按当前分母算出的线；
新族另按约束 3 以预算末地板为证否线。candidate 指通过全部预注册闸门、
可进入封存段检验的判决档，全部账本至今累计为 0。}
\label{tab:ledgers}
\end{table}

\subsection{广度：面板与逐品种是两个问题}
面板与逐品种不是二选一。面板（36 个品种）上的一次评价是\textbf{一次}检验：
单一汇总斜率，按日期簇做推断，回答「该机制对整个面板有无系统性定价」；
预测市场特征在同一时点跨品种同值，斜率由时间变异识别。结构性限制是：
机制若对不同品种方向相反，合并斜率自我抵消，真实的逐品种信号在面板上读作零，
此类机制必须拆成品种假设。逐品种是每条一次检验，品种选择须由传导通道论证给出，
不是穷举扫描。

此前反对逐品种的理由是分母大致翻倍会把旧族地板推过 $E_2(270)=3.0756$ 并追溯抬高
全部既有否定；新开族后该代价消失，新族自付、预算封顶、旧账不动。
「先跑面板再挑最好的品种」这类事后择优被盲化挡住：在本次改造之后的封闭调用条件下
（\path{require_hermetic} 开启，\S\ref{sec:hermetic}），提案器读不到任何判决，
品种选择只能条件于机制文本与仅含提案计数的覆盖表。

\paragraph{一条限定：单品种取不到 candidate。}双向 cluster 的品种维在单品种样本上
只有一组，评价机因此发出 \path{cluster_structure_insufficient}，而按失效表
（决定 0005）该理由使 candidate 失效。它不使 null 失效，故单品种检验仍能产出
可信的否定；但一条在单品种上置换检验通过、$|t|$ 很高的构造，最好的结局是
blocked，不可能是 candidate。全史实测：122 条单品种 Study 中 118 条带该阻断，
47 条面板 Study 中只有 1 条。这也解释了为何回溯投影里唯一的完整候选形态
run16-study-3 是\textbf{面板}研究，而同期的 run11-study-3 在单品种上同时带
成本模型缺失与 cluster 两条阻断，即使成本模型建成也翻不成 candidate。
逐品种买到的是机制证据与排除界，买不到 candidate。

\subsection{连带修复：封条的地板门}
先给三个词的定义。\textbf{束}指通过评价、待封存检验的特征集合；\textbf{封存}
指在预留的封存段数据上做一次性最终评价；\textbf{封条}是该一次性机会的记号，
每个特征只允许开封一次，烧掉即永久占用。

束按自罚奖励收录成员，奖励等于 $|t|$ 减去同样次数搜索在纯噪声上的期望。
新族早期分母极小，$E_2(1)=0.7979$，$|t|=1.5$ 的弱构造也会带正奖励进束，
运行结束时的自动封存会把封条烧在远低于任何可信线的特征上。此形态与此前记录的
一次事故同构（封条曾烧在只有 10 行观测、$|t|=3.17$ 的假象上），区别仅在于
经由低分母而非低行数。修复：封存只对越过本族当前地板的束成员开封，
被挡下的成员记入账本。该门对旧族是无损收紧，既有束成员 $|t|$ 在 $3.2$ 至 $4.9$
之间，全部在旧族地板之上。
"""


def all_sections() -> str:
    return (mechanism_families_section()
            + researcher_boundary_section()
            + accounts_section())
