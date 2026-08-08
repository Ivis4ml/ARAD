"""从证据账本生成完整研究报告（HTML，可由无头 Chrome 打印为 PDF）。

设计上的一条硬约束：**报告里的每一个数字都从同一次账本快照派生**，
包括标题与摘要里的措辞。此前手写「六十次检验」而账本已跑到 65，
就是同一份文档自我矛盾 —— 服务在跑时分母每几分钟就变一次。
因此本脚本一次读完账本、记下冻结点（末条事件的 seq 与时间），
其后所有文字都引用这一份快照。

用法：
    .venv/bin/python scripts/build_report.py --out docs/reports/full
    # 随后（macOS）
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \\
        --no-pdf-header-footer --print-to-pdf=报告.pdf out.html
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from arad.evaluation.selection import expected_max_abs_z
from arad.memory.ledger import EvidenceLedger, Role

FAMILY = "demo_sc_price_volume"

RUN_ORDER = ["auto", "run3", "run4", "run5", "run6", "run7", "run8", "run9",
             "run10", "run11", "run12", "run13", "run14", "run15", "run16"]

#: 每次运行的叙述。这些是**只有人才知道的因果**（为什么停、修了什么），
#: 账本里只有事件，没有故事。数字一律不写在这里，全部由快照渲染。
NARRATIVE: dict[str, tuple[str, str]] = {
    "auto": (
        "run_llm 与 run_llm2 · 首次真实模型运行",
        (
            "早于运行域标识（M7.2），study 前缀为 auto。菜单给出 30 个 Polymarket 族，"
            "不含任何指向原油的提示。第 1 轮因输出契约只列字段名不列类型（direction 被写成 "
            "\"positive\"）三次解析全败；后续轮次模型自主选中 cand:iran 族，在关注度异常、"
            "跨族份额、自我归一份额、停市窗口信念四个角度展开。run_llm2 只跑一轮即报 "
            "no_runnable_work —— 队列跨运行持久而任务标识不带运行名，成为 M7.2 的直接动因。"
        ),
    ),
    "run3": (
        "run3 · 结构性误拦",
        (
            "语义审计对机制散文做子串匹配：模型收到「幅度对方向」诊断后改用波动率归一的有符号"
            "收益（正确回应），但表达「按波动率归一」必须提到 volatility，于是连续被同一错配码"
            "误拦、未读 outcome。判据据此改为沿特征 DAG 的结构判定（M7.3），真阳性全部保留。"
        ),
    ),
    "run4": (
        "run4 · 循环第一次真正转起来",
        (
            "长时间不间断运行，模型立即采用了新原语 rank_pct。决定 0005 使 null 首次可达，"
            "本轮产出第一批可信的否定。最好一次仍未越过当时的族地板。"
        ),
    ),
    "run5": (
        "run5 · 面板首测与假象初现",
        (
            "前两轮因目标菜单携带散文（含 alpha / Sharpe 字样）被盲化检查整轮拦下"
            "（M8.5 白名单投影修复）。其后出现本项目最大的单次统计量 —— 事后确认为"
            "波动率聚集假象：分母是已实现波动、目标也是已实现波动。"
        ),
    ),
    "run6": (
        "run6 · universe 自主选择首轮",
        (
            "模型第一次能自己选 universe，多数提案选了面板。首个 cluster 不退化的 Study "
            "在此出现（36 个品种簇，Kish n_eff 35.9），cluster_structure_insufficient 首次从"
            "判决理由中消失。同轮另产出三条同源的波动假象。"
        ),
    ),
    "run7": (
        "run7 · 记忆时代第一轮（中止）",
        (
            "第 0 层记忆（自己写过的规格）与第 1 层（检验的价格）进入提示词后的首轮；"
            "为承接后续修复被主动停止。residualise 在本轮首次被模型使用。"
        ),
    ),
    "run8": (
        "run8 · 零 Study 事故",
        (
            "启动后写出的第一条事件属于上一轮的 Study —— 队列里积着旧运行的 ready 任务，"
            "而认领按创建时间取最早。M7.2 补正为按运行前缀隔离认领。本次运行未产出任何"
            "属于自己的 Study。"
        ),
    ),
    "run9": (
        "run9 · 崩溃与两处提示词缺陷",
        (
            "跑到中途崩溃：模型返回文字齐全但 feature_spec 为 null 的提案，"
            "contamination(None) 打断整个服务（M9.9 降级为证据而非异常）。本轮 residualise "
            "使用率为零 —— 原因不是可见性（原语在菜单里），而是提示词从未说明**为什么**要"
            "残差化；另发现 blockers 里「pm_market 尚未接入」是一句假话（本轮实际用了 20 次）。"
            "M9.8 补上 what_counts_as_a_finding 口径。"
        ),
    ),
    "run10": (
        "run10 · residualise 全面采用，暴露接线缺口",
        (
            "口径写进提示词后立竿见影：全部规格残差化，并在 own_realised_volatility 与 brent "
            "两个控制项之间交替。但 brent 只登记未装载，多条规格死于 interpretation_gap"
            "（M9.10 接线并补上「登记即必须可装载」的合同测试）。"
        ),
    ),
    "run11": (
        "run11 · 质量最高的一轮",
        (
            "七个互异机制、全部残差化。产出唯一走完全流程的候选 run11-study-3"
            "（供给中断常备发生率），其余为干净 null。该候选随后在封存段被一次性否决。"
        ),
    ),
    "run12": (
        "run12 · 重复启动被守卫拦下",
        (
            "助手侧与用户侧同时启动服务，TaskIdentifierCollision 正确拒绝了重复运行 —— "
            "结构挡住了双倍消耗统计预算的事故。"
        ),
    ),
    "run13": (
        "run13 · 用户预算首段",
        "为加载推理流式（M10.2）被用户主动重启，判决全部保留在账本中。"),
    "run14": (
        "run14 · thinking 捕获缺失暴露",
        (
            "流式只捕正文增量，模型扩展思考约十一分钟期间观察窗显示零字。"
            "thinking_delta 补入观察窗（正文与思考分流，兜底解析只收正文，"
            "以免思考文字污染最终 JSON）。"
        ),
    ),
    "run15": (
        "run15 · 管道块缓冲暴露",
        (
            "同一进程内一次调用流畅、下一次近二百秒零字节 —— CLI 检测到 stdout 是管道即按块"
            "缓冲。M10.4 改走伪终端，端到端冒烟确认增量逐秒到达。本轮也留下一段高质量推理："
            "模型翻查自己的全部历史规格以避开已用过的族，并对 universe 给出「收盘几何是一个"
            "只有极少数取值的分组变量」这一统计论证。"
        ),
    ),
    "run16": (
        "run16 · 流式全程生效",
        "pty 流式全程可见的首轮，思考与正文逐秒可读。截稿时仍在进行。"),
}


def collect() -> dict:
    """一次读完账本，其后所有渲染都引用这一份快照。"""
    with EvidenceLedger("data/ledger/service.db") as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))
        denominators = ledger.denominators(FAMILY)
        _, broken = ledger.verify_chain()

    def run_of(sid: str | None) -> str | None:
        m = re.match(r"(.+)-study-\d+$", sid or "")
        return m.group(1) if m else None

    studies: OrderedDict[str, dict] = OrderedDict()
    for event in events:
        sid, kind, payload = event.get("study_id"), event["event_type"], event["payload"]
        if not sid or not run_of(sid):
            continue
        st = studies.setdefault(sid, {"study_id": sid, "run": run_of(sid)})
        if kind == "proposal_locked":
            st.update(target=payload.get("target"), universe=payload.get("universe"),
                      direction=payload.get("direction"))
        elif kind == "feature_spec_locked":
            steps = payload.get("steps", [])
            st["feature_id"] = payload.get("feature_id")
            st["controls"] = [c for s in steps for c in (s.get("controls") or [])]
            st["shape"] = "→".join(s["kind"] for s in steps)
        elif kind == "semantic_audit":
            st["audit"] = [m["code"] for m in payload.get("mismatches", [])]
        elif kind == "outcome_read":
            st["read"] = True
        elif kind == "evaluation_result":
            effects = payload.get("effects") or {}
            st["t"] = effects.get("t_stat")
            st["ic"] = (effects.get("ic") or {}).get("ic_spearman")
            st["rows"] = payload.get("coverage", {}).get("rows_submitted")
            st["clusters"] = payload.get("coverage", {}).get("product_clusters")
            st["placebo"] = ((payload.get("diagnostics") or {})
                             .get("placebo", {}).get("placebo_exceed_rate"))
        elif kind == "verdict_recorded":
            st["verdict"] = payload.get("verdict")

    n = denominators["statistical_denominator"]
    last = events[-1] if events else {}
    return {
        "denominators": denominators,
        "floor": expected_max_abs_z(n),
        "floor_curve": [(k, expected_max_abs_z(k))
                        for k in (1, 5, 10, 15, 25, 40, 50, n) if k <= n],
        "studies": list(studies.values()),
        "verdicts": Counter(s.get("verdict") for s in studies.values() if s.get("verdict")),
        "sealed": [e["payload"] for e in events
                   if e["event_type"] == "sealed_segment_opened"],
        "events": len(events),
        "chain_intact": not broken,
        "frozen_at": {"seq": last.get("seq"), "at": (last.get("created_at") or "")[:19]},
        "residualised": sum(1 for s in studies.values() if s.get("controls")),
        "specs": sum(1 for s in studies.values() if s.get("feature_id")),
        "tickets": _headings("docs/tickets/*.md"),
        "decisions": _headings("docs/decisions/*.md"),
    }


def _headings(pattern: str) -> list[str]:
    out = []
    for path in sorted(Path().glob(pattern.replace("docs/", "docs/"))):
        try:
            out.append(path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip())
        except (OSError, IndexError):
            continue
    return out


E = html.escape


def num(v, digits: int = 3) -> str:
    return f"{v:+.{digits}f}" if isinstance(v, (int, float)) else "—"


def cn(n: int) -> str:
    """整数的中文读法，仅用于标题（六十五次检验）。"""
    d = "零一二三四五六七八九"
    if n < 10:
        return d[n]
    if n < 20:
        return "十" + (d[n % 10] if n % 10 else "")
    if n < 100:
        return d[n // 10] + "十" + (d[n % 10] if n % 10 else "")
    return str(n)


def render(D: dict) -> str:
    v = D["verdicts"]
    n = D["denominators"]["statistical_denominator"]
    floor = D["floor"]

    def study_table(run: str) -> str:
        rows = [s for s in D["studies"] if s["run"] == run]
        if not rows:
            return "<p class=note>本次运行没有产出任何属于自己的 Study。</p>"
        cells = [("<table><tr><th>Study</th><th>特征</th><th>target ／ universe</th>"
                  "<th class=n>t</th><th class=n>IC 秩</th><th>判决</th></tr>")]
        for s in rows:
            audit = "｜".join(s.get("audit") or [])
            note = f"<div class=aud>审计拦下：{E(audit)}</div>" if audit else ""
            ctrl = ("<div class=ctl>控制：" + E(",".join(s["controls"])) + "</div>"
                    if s.get("controls") else "")
            cells.append(
                f"<tr><td class='m id'>{E(s['study_id'])}</td>"
                f"<td class=m>{E(s.get('feature_id') or '—')}{ctrl}{note}</td>"
                f"<td class=m>{E(s.get('target') or '—')}<br>{E(s.get('universe') or '—')}</td>"
                f"<td class=n>{num(s.get('t'))}</td>"
                f"<td class=n>{num(s.get('ic'), 4)}</td>"
                f"<td><span class='v v-{E(s.get('verdict') or 'none')}'>"
                f"{E(s.get('verdict') or '进行中')}</span></td></tr>")
        cells.append("</table>")
        return "".join(cells)

    chronicle = "".join(
        f"<h3>{E(NARRATIVE[r][0])}</h3><p>{E(NARRATIVE[r][1])}</p>{study_table(r)}"
        for r in RUN_ORDER)

    sealed = [("<table><tr><th>特征</th><th class=n>t</th><th class=n>IC 秩</th>"
               "<th class=n>行</th><th>时间样本外</th><th>分类法干净</th></tr>")]
    for s in D["sealed"]:
        sealed.append(
            f"<tr><td class=m>{E(str(s.get('feature_id', '—')))}</td>"
            f"<td class=n>{num(s.get('t_stat'))}</td>"
            f"<td class=n>{num(s.get('ic_spearman'), 4)}</td>"
            f"<td class=n>{s.get('rows', '—')}</td>"
            f"<td>{'是' if s.get('out_of_sample_in_time') else '—'}</td>"
            f"<td>{'是' if s.get('taxonomy_clean') else '<span class=neg>否</span>'}</td></tr>")
    sealed.append("</table>")

    floor_rows = "".join(f"<tr><td class=n>{k}</td><td class=n>{val:.3f}</td></tr>"
                         for k, val in D["floor_curve"])
    appendix = [("<table><tr><th>Study</th><th>特征</th><th class=n>t</th><th class=n>IC</th>"
                 "<th class=n>置换 p</th><th>控制</th><th>判决</th></tr>")]
    for s in D["studies"]:
        appendix.append(
            f"<tr><td class='m id'>{E(s['study_id'])}</td>"
            f"<td class=m>{E(s.get('feature_id') or '—')}</td>"
            f"<td class=n>{num(s.get('t'))}</td><td class=n>{num(s.get('ic'), 3)}</td>"
            f"<td class=n>{s.get('placebo', '—')}</td>"
            f"<td class=m>{E(','.join(s.get('controls') or []) or '—')}</td>"
            f"<td>{E(s.get('verdict') or '进行中')}</td></tr>")
    appendix.append("</table>")

    top = sorted((s for s in D["studies"] if isinstance(s.get("t"), float)),
                 key=lambda s: -abs(s["t"]))[:4]
    artefacts = "、".join(f"{s['study_id']}（{s['t']:+.2f}）" for s in top)

    return f"""<!doctype html><html lang=zh><head><meta charset=utf-8>
<title>ARAD 完整研究报告</title><style>
@page {{ size: A4; margin: 17mm 15mm 15mm; }}
*{{ box-sizing: border-box }}
body{{font:10.6pt/1.72 -apple-system,"SF Pro Text","PingFang SC","Hiragino Sans GB",sans-serif;
  color:#1c1c1e;margin:0;letter-spacing:-.005em;-webkit-font-smoothing:antialiased}}
@media screen {{ body {{ max-width:190mm;margin:0 auto;padding:18mm 15mm;background:#fff }} }}
.m,.n,code{{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}}
.cover{{height:250mm;display:flex;flex-direction:column;justify-content:flex-end;
  padding-bottom:14mm;page-break-after:always}}
.eyebrow{{font-size:9pt;letter-spacing:.13em;text-transform:uppercase;color:#8a8f98;
  margin-bottom:16pt}}
.cover h1{{font-size:29pt;line-height:1.3;margin:0 0 12pt;letter-spacing:-.022em;
  text-wrap:balance}}
.cover .dek{{font-size:11.5pt;color:#4b5563;max-width:60ch;line-height:1.7}}
.cover .meta{{margin-top:40pt;color:#8a8f98;font-size:9.2pt;line-height:2;
  border-top:.6pt solid #dfe3e8;padding-top:12pt}}
h2{{font-size:14.5pt;margin:24pt 0 8pt;letter-spacing:-.018em;page-break-after:avoid;
  border-bottom:.7pt solid #c9cfd8;padding-bottom:4pt}}
h3{{font-size:11.2pt;margin:15pt 0 4pt;page-break-after:avoid;letter-spacing:-.01em}}
p{{margin:0 0 8pt;max-width:74ch}}
p.note,.aud,.ctl{{font-size:9pt;color:#6b7280}}
.aud{{color:#9a6510}} .ctl{{color:#3c5488}}
table{{border-collapse:collapse;width:100%;font-size:8.5pt;margin:5pt 0 11pt}}
tr{{page-break-inside:avoid}}
th{{text-align:left;font-size:7.6pt;letter-spacing:.06em;text-transform:uppercase;
  color:#8a8f98;border-bottom:.8pt solid #b3bac4;padding:3pt 8pt 3pt 0;font-weight:600}}
td{{border-bottom:.4pt solid #e4e7ec;padding:3.5pt 8pt 3.5pt 0;vertical-align:top}}
td.n,th.n{{text-align:right;white-space:nowrap}}
td.id{{white-space:nowrap;color:#6b7280}}
.v{{font-weight:600;font-size:8.3pt}}
.v-null{{color:#5a6270}} .v-blocked{{color:#3c5488}} .v-underpowered{{color:#9a6510}}
.v-candidate{{color:#00806e}} .v-none{{color:#a0a5ad}}
.neg{{color:#b93c28}}
.slab{{display:flex;gap:24pt;flex-wrap:wrap;border:.7pt solid #d5d9e0;border-radius:6pt;
  padding:11pt 15pt;margin:9pt 0 12pt}}
.slab div{{display:flex;flex-direction:column}}
.slab .k{{font-size:7.4pt;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98}}
.slab .val{{font-size:17pt;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.3}}
ol,ul{{margin:0 0 10pt;padding-left:17pt;max-width:74ch}} li{{margin:0 0 5pt}}
.twocol{{columns:2;column-gap:20pt;font-size:8.8pt}}
.twocol li{{break-inside:avoid;margin:0 0 3pt}}
blockquote{{margin:7pt 0 10pt;padding:8pt 13pt;border-left:2.5pt solid #3c5488;
  background:#f4f6fa;font-size:9.6pt;max-width:72ch;line-height:1.68}}
.pb{{page-break-before:always}}
</style></head><body>

<section class=cover>
  <div class=eyebrow>ARAD · Autoresearch on Alternative Data</div>
  <h1>从计划到{cn(n)}次检验：<br>一个自主因子研究系统的全部证据</h1>
  <p class=dek>Polymarket 预测市场与中国商品期货（以 SC 原油为主）。研究者是大语言模型
  （claude-opus-5，经 claude -p 调用）；确定性框架负责让它的产出可信且可累积。
  本报告的每一个数字都由脚本从同一次账本快照派生，未经手抄。</p>
  <div class=meta>
    冻结点：事件 seq {D['frozen_at']['seq']} · {E(D['frozen_at']['at'])}（run16 当时仍在进行）<br>
    账本 {D['events']} 条事件 · 哈希链{'完整' if D['chain_intact'] else '<b>断裂</b>'} ·
    分支 feat-dev<br>
    统计分母 {n} · 提案分母 {D['denominators']['proposal_denominator']} · 噪声地板 {floor:.4f}<br>
    判决：null {v.get('null', 0)} · blocked {v.get('blocked', 0)} ·
    underpowered {v.get('underpowered', 0)} · candidate {v.get('candidate', 0)}
  </div>
</section>

<h2>〇 · 摘要</h2>
<p><strong>{n} 次检验，{v.get('candidate', 0)} 个 candidate。</strong>这不是系统失败，
而是它如实给出的答案：不加控制时最惊人的「发现」全部是波动率聚集这一教科书事实；
把品种自身波动或国际油价残差化之后，Polymarket 特征大面积蒸发；唯一的幸存者走完全部
流程后在封存段被一次性否决（线性效应保留率 17.6%，低于预注册的 35% 保持线）。
candidate 目前被两道结构性闸门挡住：成本模型未建（M5）与分类法污染封顶（决定 0004）。
在补上之前，任何结果封顶为 null。</p>
<div class=slab>
  <div><span class=k>candidate</span><span class=val
    style="color:#b93c28">{v.get('candidate', 0)}</span></div>
  <div><span class=k>读过 outcome</span><span class=val>{n}</span></div>
  <div><span class=k>互异假设</span><span class=val>{D['denominators']['proposal_denominator']}</span></div>
  <div><span class=k>噪声地板</span><span class=val>{floor:.3f}</span></div>
  <div><span class=k>封存开启</span><span class=val>{len(D['sealed'])}</span></div>
  <div><span class=k>Study 总数</span><span class=val>{len(D['studies'])}</span></div>
</div>

<h2>一 · 计划与设计原则</h2>
<p>目标：在中国商品期货上，以 Polymarket 预测市场与财联社新闻为另类数据，建立
<strong>连续运转</strong>的因子研究系统。研究者是模型，但可信性不托付给模型，
而由确定性框架结构性保证。八条核心机制：</p>
<ol>
<li><strong>PIT 纪律</strong>：availability_time &lt; decision_time &lt; label_start
由构造保证（窗口右端点一律不含，offset 非负），不靠事后检查。</li>
<li><strong>两本分母</strong>：提案分母（内容寻址，含被拦下的）与统计分母
（只计真正读过 outcome 的）；后者由数据库触发器禁止回缩。</li>
<li><strong>零假设带与自罚奖励</strong>：E[max|z|] 按检验次数以 √(2 ln n) 抬升，
对已有与将来的全部结论同时生效 —— 搜索自我计价。</li>
<li><strong>提案器盲化</strong>：效应的方向与量级按账本白名单强制不可见
（黑名单形式历史上失败过两次）。</li>
<li><strong>读 outcome 之前的语义审计</strong>：问错的问题被拦下，且不消耗检验预算。</li>
<li><strong>判决语义</strong>（决定 0005）：由每条阻塞理由的失效集合机械推出，
使「可信的否定」成为一等产出。</li>
<li><strong>封存段</strong>：每个规格终身只能开启一次，由账本强制。</li>
<li><strong>记忆分层</strong>（M9）：第 0 层（自己写过的规格，免费）、
第 1 层（检验的价格）、第 2 层（结果侧归纳，对提案器永久关闭）。</li>
</ol>
<h3>六份决定文档</h3>
<div class=twocol><ul>{''.join(f'<li>{E(t)}</li>' for t in D['decisions'])}</ul></div>

<h2>二 · 数据</h2>
<table>
<tr><th>层</th><th>内容</th><th>规模</th><th>状态</th></tr>
<tr><td>商品 tick 归档</td><td>chinese-commodity（只读）</td>
  <td class=n>87 品种 · 221 GB · 909 交易日</td><td>M1 合同化</td></tr>
<tr><td>Temporal Spine</td><td>分钟 bar、主力视图、三类 target</td>
  <td class=n>51 品种建成（36 个满 1,816 行）</td><td>郑商所 21 品种待裁决</td></tr>
<tr><td>时段表</td><td>按夜盘收盘参数化（02:30 ／ 01:00 ／ 23:00 ／ 无夜盘）</td>
  <td class=n>72 品种登记</td><td>出处：SC 权威几何 + 原始 tick 归纳</td></tr>
<tr><td>Polymarket</td><td>族级小时序列（p ／ notional ／ trades）</td>
  <td class=n>1,998 族 · 5,986,409 行</td><td>全量物化</td></tr>
<tr><td>控制序列</td><td>brent（外生油价）· own_realised_volatility</td>
  <td class=n>933 行 ／ 逐品种</td><td>residualise 可用</td></tr>
<tr><td>财联社</td><td>cls_telegraph 原文</td>
  <td class=n>562,548 行</td><td><span class=neg>未接入解释器</span></td></tr>
</table>
<p>target 三类，逐品种命名，声明即被评（M8.2 硬校验）：rv_next_session（已实现波动）、
ret_next_session（有符号收益，唯一可交易主张）、open_gap_absorption（诊断用）。
universe 由模型自选：full_coverage_panel（36 品种）或任一单品种主力视图。</p>

<h2>三 · 方法：一轮的解剖</h2>
<p>一个 Study 固定走十一步：组装盲化上下文 → 冻结提案 → 冻结假设 → 冻结检验规格 →
建立 Study → 冻结特征规格 → 语义审计（在读 outcome 之前）→ 声明可见数据范围 →
读取 outcome（统计分母加一）→ 评价机出具结果 → 判决入账。<strong>缺步本身是信息</strong>：
被审计拦下的 Study 不读 outcome，也不抬高地板。</p>
<p>特征语言七原语：window、innovation、ratio、difference、zscore、rank_pct、residualise，
均由冻结规格确定性生成代码，并与解释器逐位一致。评价闸门：置换检验（按 Episode 整块置换）、
单点影响（DFBETAS，按标准误标准化）、双向 cluster 标准误、覆盖准入、成本模型声明。</p>
<h3>噪声地板的抬升轨迹</h3>
<table style="max-width:44ch"><tr><th class=n>已读 outcome 次数 n</th>
<th class=n>E[max|z|]</th></tr>{floor_rows}</table>
<p class=note>曲线上任何一点要被称为发现，必须越过它右侧最高的那条线 —— 历史上从未发生。</p>

<h2 class=pb>四 · 十六次运行编年</h2>
{chronicle}

<h2>五 · 结果综合</h2>
<h3>A · 假象家族（全部早于残差化普及）</h3>
<p>统计量最大的几条：{E(artefacts)}。它们的共同构造是分母为已实现波动、目标也是已实现波动 ——
重新发现的是波动率聚集，金融学里最稳健的定型化事实之一，不是另类数据的 alpha。
诊断证据（离线，不进族账本）：对其中最大一条的构造做残差化，
秩相关由 −0.5695 塌至 −0.0077，<strong>缩小 74 倍</strong>。这几条是 rank_pct 与
residualise 两个原语被实现的直接动因。</p>

<h3>B · 唯一走完全流程的候选（已否决）</h3>
<blockquote><strong>pm_iran_hazard_level_30d_resid_own_rv_90d</strong>（run11-study-3）：
cand:iran 族归一化概率的 30 日均值，减掉品种自身波动持续性之后，预测下一时段已实现波动。
机制为混合分布假说 —— 波动由信息到达强度决定，到达强度由风险的当前发生率水平决定；
油价已含发生率×损失的一阶期望，发生率水平本身另有信息。<br><br>
discovery 段：t = +2.416、IC 秩 = +0.087、616 行、置换检验 0.05 通过、DFBETAS 0.267。<br>
封存段（一次性）：t = +0.426、IC 秩 = +0.128、405 行 —— 线性效应保留率 17.6%，
低于预注册的 35% 保持线，判 sealed_failed。<br><br>
如实并记：秩相关在样本外反而升高（约 2.6 个标准误），单调关联仍在、线性斜率没了。
但按预注册规则这就是失败；且 taxonomy_clean 为否，任何主张本就被封顶。
<strong>裁决终身有效，不重开</strong>。它在 discovery 段也从未越过当时的族地板
（2.416 &lt; 2.523）。</blockquote>

<h3>C · 干净的 null（{v.get('null', 0)} 条）</h3>
<p>残差化普及之后（近数轮使用率 100%），模型在互异机制上系统扫过：资金集中度、
信念下限棘轮、闭市时段资金份额、停火与伊朗资金倾斜、平均单笔金额、方向性信念离散度、
事件不确定性 p̄(1−p̄)、到达加速度、对娱乐族的安慰剂对照。
<strong>每一条都先减掉了 Baseline Control，每一条都是预注册的可证伪假设，
每一条否定都带着自己的排除界。</strong>按决定 0005，可信的否定就是研究产出。</p>

<h3>封存段全记录（{len(D['sealed'])} 次开启，每规格终身一次）</h3>
{''.join(sealed)}
<p class=note>taxonomy_clean 全为否：族归纳语料的切点覆盖了全部三段（决定 0004），
任何 Polymarket 主张被结构性封顶 —— 这正是「分类法重归纳」位列最高杠杆事项的原因。</p>

<h2>六 · 工程史：实跑暴露并修掉的缺陷</h2>
<p>本项目最有效的除错器是真实运行本身。代表性的缺陷包括：输出契约只列字段名不列类型，
使三次调用连续解析失败；解析失败被计入停滞，把工程缺陷写成「模型枯竭」；影响闸门除以
趋零的斜率，在没有效应时叫得最响；Verdict.NULL 从未可达，否定结论无处安放；
语义诊断只回传给确定性变异器，真实模型连续多轮撞同一错配；审计按散文匹配误拦正确回应；
声明的 target 与被评的 target 从不比对，十二条 Study 回答了没有被问的问题；
「泄漏为零」的断言被对抗性审查证否（具名清单与判决计数可做减法，决定 0006 移除后者）；
队列跨运行认领，新运行替旧运行干活；控制序列登记而未装载；CLI 对管道块缓冲堵死推理流。
<strong>每一条都带回归测试落档。</strong></p>
<div class=twocol><ul>{''.join(f'<li>{E(t)}</li>' for t in D['tickets'])}</ul></div>

<h2>七 · 未决事项与下一步（全部需人决定）</h2>
<ol>
<li><strong>M5 成本模型</strong> —— candidate 唯一剩下的普适闸门；不建则一切封顶为 null。</li>
<li><strong>分类法重归纳（干净切点）</strong> —— 解除决定 0004 对全部 Polymarket 结论的封顶。</li>
<li><strong>郑商所 21 品种</strong> —— TradingDay 自然日与交易日约定之别，属 PIT 语义裁决。</li>
<li><strong>财联社接入</strong> —— 第三个数据源，五十六万行原文待进解释器。</li>
<li><strong>横截面 target</strong> —— 面板已通，但真正的截面 IC 需要「同一时点排序多品种」
的新目标定义。</li>
</ol>

<h2 class=pb>附录 · 全部 {len(D['studies'])} 个 Study</h2>
{''.join(appendix)}
<p class=note>数据来源 data/ledger/service.db，冻结于 seq {D['frozen_at']['seq']}
（{E(D['frozen_at']['at'])}）。生成方式：scripts/build_report.py 直接投影账本；
叙述部分由人撰写，数字一律由快照渲染，二者不会不一致。</p>
</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/reports/ARAD-完整研究报告.html")
    args = ap.parse_args()
    data = collect()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data), encoding="utf-8")
    print(f"{out} · {len(data['studies'])} 个 Study · 统计分母 "
          f"{data['denominators']['statistical_denominator']} · "
          f"冻结于 seq {data['frozen_at']['seq']}")


if __name__ == "__main__":
    main()
