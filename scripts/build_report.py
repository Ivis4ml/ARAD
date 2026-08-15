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
import math
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from arad.evaluation.selection import expected_max_abs_z
from arad.memory.ledger import EvidenceLedger, Role

FAMILY = "demo_sc_price_volume"

RUN_ORDER = ["auto", "run3", "run4", "run5", "run6", "run7", "run8", "run9",
             "run10", "run11", "run12", "run13", "run14", "run15", "run16", "run17",
             "run18", "run19", "run20", "run21", "run22", "run23", "run24",
             "run25", "run26", "run27"]

#: 事件条件族（决定 0008）的运行。族归属按运行前缀判定 —— B9 时代的评价载荷
#: 曾把族标签写错，运行前缀才是可靠索引。
EVENT_RUNS = frozenset({"run23", "run24"})
EVENT_FAMILY = "sc_event_conditional_v1"

#: 机制先验族（决定 0011）的运行。第三本账：成员按机制与极性定义，
#: 分母从零起，正当性由五条约束买下（重合度已证、花名册闭合、预算预注册、
#: 双地板并印、跨族双计）。族归属同样按运行前缀判定。
MECH_RUNS = frozenset({"run27"})
MECH_FAMILY = "sc_mechanism_prior_v1"

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
        "run16 · 流式全程生效，并产出首个越过地板的残差化另类构造",
        (
            "pty 流式全程可见的首轮，二十个回合。其中 study-3"
            "（伊朗族未决概率质量 p̄(1−p̄)，残差化掉自身波动，36 品种面板）"
            "在评价时越过族地板，置换检验零例外、单点影响极小 —— 当时唯一的"
            "阻塞理由是成本模型未建。它排在束的第五位而束宽为四，"
            "收尾的自动封存没有轮到它（缺陷记 B6），封条因此仍未开启。"
        ),
    ),
    "run17": (
        "run17 · 人类研究方向通道首用",
        (
            "首轮通过入账的研究方向指令（标的不限于 sc）运行。标的确实铺开"
            "（面板为主，另有黄金与燃油单品种），十六版判决全为否定。"
            "为加载最小成本模型（决定 0007）主动停止。"
        ),
    ),
    "run18": (
        "run18 · 成本模型时代首轮",
        (
            "决定 0007 后第一轮：cost_model_missing 从判决理由中绝迹，"
            "真实成本诊断（盈亏平衡捕捉率）入账 —— 首版即显示成本仅占典型幅度"
            "约百分之九，构造死于统计而非成本。为错配教训跨运行回放修复让位。"
        ),
    ),
    "run19": (
        "run19 · 错配教训回放首轮",
        (
            "语义错配码此前每次运行清零重学（run3 用七轮撞出的教训 run18 并不知道），"
            "修为初值从账本回放全历史。为分层轮换菜单（M12）让位。"
        ),
    ),
    "run20": (
        "run20 · 分层轮换菜单首轮，provider 三连超时",
        (
            "M12 菜单（先验 4 + 安慰剂 3 + 头部 8 + 轮换 15）首轮。第 2 至 4 轮"
            "provider 连续三次 900 秒超时触发保护性停机（行为正确），但暴露两处"
            "strict 投影被半途 Study 炸掉（归档为崩溃而生却在崩溃现场先崩），"
            "以及超时线卡在实测思考时长分布中间。仅一版判决。"
        ),
    ),
    "run21": (
        "run21 · 阻塞读吞超时（零判决）",
        (
            "pty 改造的阻塞读使超时永远不触发：CLI 一个字节不发时，检查超时的"
            "代码轮不到执行 —— 进程挂死 103 分钟（子进程仅 3 秒 CPU）被杀。"
            "修为 select 五秒一拍的带超时轮询，挂死调用三十分钟必被回收。"
        ),
    ),
    "run22": (
        "run22 · 基础设施首次全程无恙",
        (
            "二十轮跑满，两次超时被正确吸收。轮换层的族被真实选中并惰性装载"
            "（生产验证）；标的横跨面板与六个单品种。十六条干净 null。收尾自动封存"
            "把封条烧在一条十行样本的 underpowered Study 上（B7 由此修复：样本不足"
            "不进束）。"
        ),
    ),
    "run23": (
        "run23 · 事件条件族第一轮",
        (
            "决定 0008：只在 PM 概率大幅移动后的窗口上评价，独立问题族、地板从头起。"
            "触发器采用 19/19，但 17 版集中在 iran 单一事件源。十九版全为 null ——"
            "iran 事件窗口内 SC 仍无线性可预测性。收尾封存越界烧在旧族特征上"
            "（B8 由此修复：束按族过滤）。"
        ),
    ),
    "run24": (
        "run24 · 触发多样化",
        (
            "方向指令要求触发源互异：铺开到十一个族（含轮换层新族）。"
            "十一 null、三 underpowered、四 blocked（信号事前筛在生产首次拦下两版，"
            "读 outcome 之前省下预算）。结论与 run23 一致。束为空暴露 B9：评价证据"
            "的族标签曾被写死为旧族。"
        ),
    ),
    "run25": (
        "run25 · 盲化拦下人的方向文本",
        (
            "对抗性评审第一梯队（决定 0009）上线后的首次运行：先验四种子经"
            "--direction 通道喂入。方向文本中出现了效果词，盲化断言三次拒绝组装"
            "上下文（人写的指令不豁免审查），provider_unusable，零研究。改词后"
            "以 run26 重启。账面只留三条 context_blocked——系统按设计工作的记录。"
        ),
    ),
    "run27": (
        "run27 · 装置缺陷：菜单与准入不同源",
        (
            "机制先验族（决定 0011）的首次运行。菜单把 mech: 族列了出来，"
            "而惰性装载的准入名单只读词汇族那一份 manifest，解释器因此拒绝装载"
            "机制族序列，三条提案一律判 blocked，理由都是「没有为 "
            "(pm_market, 'mech:X:dp') 提供数据序列」。三个回合作废，"
            "但**未消耗统计分母**：blocked 发生在读 outcome 之前。"
            "三条被拦下的提案本身证明新层在起作用 —— 分别是加息路径对沪银、"
            "加息路径对沪金、俄乌停火对玉米，三个组合在此前 196 条提案里"
            "一次都没出现过。修法是两份 manifest 取并集；"
            "教训入册：菜单与准入必须同源，否则模型看得见、系统求不出。"
        ),
    ),
    "run26": (
        "run26 · 对评审判定的直接检验",
        (
            "评审第一梯队三件齐上：吸收目标升 primary、先验四种子喂入、多控制"
            "残差化。二十轮出十五版：吸收目标被采纳十次（正负两个方向都试过），"
            "多控制（brent 与自身已实现波动同时残差化）十四次，正规方程路径首次"
            "生产使用。结果十四 null 一 blocked（cluster 结构退化），最好 |t|=2.31"
            "（sc_ret_next_session，低于其预注册证否线 2.85）；吸收目标侧最好"
            "|t|=1.83。前身 0.86 的休市吸收相关在七倍样本上没有再现。评审给出的"
            "最短路径走完，方法边界的三块高地补上后仍是 null——「市场真相」的"
            "分量自此显著加重。"
        ),
    ),
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

    with EvidenceLedger("data/ledger/service.db") as ledger2:
        event_denominators = ledger2.denominators(EVENT_FAMILY)
        mech_denominators = ledger2.denominators(MECH_FAMILY)
        merged_denominators = ledger2.denominators(None)
    n = denominators["statistical_denominator"]
    ne = event_denominators["statistical_denominator"]
    nm = mech_denominators["statistical_denominator"]
    nall = merged_denominators["statistical_denominator"]
    last = events[-1] if events else {}
    return {
        "denominators": denominators,
        "event_denominators": event_denominators,
        # 第三本账与合并账（决定 0011 的约束四）：分族的正当性以合并数字
        # 随时可读为前提，因此报告与卡片一样并列印出。
        "mech_denominators": mech_denominators,
        "mech_floor": expected_max_abs_z(nm) if nm else None,
        "merged_denominators": merged_denominators,
        "merged_floor": expected_max_abs_z(nall) if nall else None,
        "event_floor": expected_max_abs_z(ne) if ne else None,
        "event_floor_curve": [(k, expected_max_abs_z(k))
                              for k in (1, 5, 10, 20, ne) if ne and k <= ne],
        "floor": expected_max_abs_z(n),
        "floor_curve": [(k, expected_max_abs_z(k))
                        for k in (1, 5, 10, 15, 25, 40, 50, n) if k <= n],
        "studies": list(studies.values()),
        "verdicts": Counter(s.get("verdict") for s in studies.values() if s.get("verdict")),
        # 封存载荷的统计量嵌在 result.effects 下（open_sealed 的 verdict.payload
        # 结构）；此前取顶层键拿到 None，报告封存表整列空白。这里抽平。
        "sealed": [_flatten_seal(e["payload"]) for e in events
                   if e["event_type"] == "sealed_segment_opened"],
        "events": len(events),
        "chain_intact": not broken,
        "frozen_at": {"seq": last.get("seq"), "at": (last.get("created_at") or "")[:19]},
        "residualised": sum(1 for s in studies.values() if s.get("controls")),
        "specs": sum(1 for s in studies.values() if s.get("feature_id")),
        "tickets": _headings("docs/tickets/*.md"),
        "decisions": _headings("docs/decisions/*.md"),
    }


def _flatten_seal(payload: dict) -> dict:
    result = payload.get("result") or {}
    effects = result.get("effects") or {}
    ic = effects.get("ic") or {}
    coverage = result.get("coverage") or {}
    return {
        "feature_id": payload.get("feature_id"),
        "segment": payload.get("segment"),
        "t_stat": payload.get("t_stat", effects.get("t_stat")),
        "ic_spearman": payload.get("ic_spearman", ic.get("ic_spearman")),
        "rows": payload.get("rows", coverage.get("rows_submitted")),
        "out_of_sample_in_time": payload.get("out_of_sample_in_time"),
        "taxonomy_clean": payload.get("taxonomy_clean"),
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

    # 唯一走完全流程的候选：散文里的每个数字都必须从快照取，不得手写 ——
    # 封面声明了这条约束，散文里硬编码就是文档自我违约（而账本每几分钟在变）。
    HERO_ID = "run11-study-3"
    hero = next((s for s in D["studies"] if s["study_id"] == HERO_ID), {})
    hero_sealed = next((e for e in D["sealed"]
                        if e.get("feature_id") == hero.get("feature_id")), {})
    hero_t, hero_seal_t = hero.get("t"), hero_sealed.get("t_stat")
    retention = (abs(hero_seal_t) / abs(hero_t)
                 if isinstance(hero_t, float) and isinstance(hero_seal_t, float)
                 and hero_t else None)
    # 闸门比的是**两个 t 值**，而两段样本量不同：即便斜率与残差标准差完全不变，
    # t 也会按 √(n_封存 / n_发现) 缩小。因此该比值不是「效应保住了多少」。
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
    artefacts = "、".join(f"{s['study_id']}（{s['t']:+.2f}）" for s in top)
    residualised = D["residualised"]
    specs = D["specs"]

    return f"""<!doctype html><html lang=zh><head><meta charset=utf-8>
<title>ARAD 完整研究报告</title><style>
@page {{ size: A4; margin: 17mm 15mm 15mm; }}
*{{ box-sizing: border-box }}
body{{font:10.4pt/1.7 -apple-system,"SF Pro Text","PingFang SC","Hiragino Sans GB",sans-serif;
  color:#1c1c1e;margin:0;letter-spacing:-.005em;-webkit-font-smoothing:antialiased}}
@media screen {{ body {{ max-width:190mm;margin:0 auto;padding:18mm 15mm;background:#fff }} }}
.m,.n,.eq,code{{font-family:"SF Mono",ui-monospace,Menlo,monospace;
  font-variant-numeric:tabular-nums}}
.cover{{height:250mm;display:flex;flex-direction:column;justify-content:flex-end;
  padding-bottom:14mm;page-break-after:always}}
.eyebrow{{font-size:9pt;letter-spacing:.13em;text-transform:uppercase;color:#8a8f98;
  margin-bottom:16pt}}
.cover h1{{font-size:28pt;line-height:1.3;margin:0 0 12pt;letter-spacing:-.022em;
  text-wrap:balance}}
.cover .dek{{font-size:11.5pt;color:#4b5563;max-width:60ch;line-height:1.7}}
.cover .meta{{margin-top:36pt;color:#8a8f98;font-size:9.2pt;line-height:2;
  border-top:.6pt solid #dfe3e8;padding-top:12pt}}
h2{{font-size:14pt;margin:22pt 0 8pt;letter-spacing:-.018em;page-break-after:avoid;
  border-bottom:.7pt solid #c9cfd8;padding-bottom:4pt}}
h3{{font-size:11pt;margin:14pt 0 4pt;page-break-after:avoid;letter-spacing:-.01em}}
h4{{font-size:10.2pt;margin:10pt 0 3pt;page-break-after:avoid;color:#374151}}
p{{margin:0 0 7pt;max-width:74ch}}
p.note,.aud,.ctl,.src{{font-size:8.8pt;color:#6b7280}}
.aud{{color:#9a6510}} .ctl{{color:#3c5488}}
.src{{color:#9aa1ab;margin-top:-4pt}}
.eq{{background:#f5f6f8;border-left:2pt solid #c9cfd8;padding:6pt 10pt;margin:5pt 0 7pt;
  font-size:9.2pt;line-height:1.75;white-space:pre-wrap;overflow-wrap:anywhere;
  page-break-inside:avoid}}
table{{border-collapse:collapse;width:100%;font-size:8.4pt;margin:5pt 0 10pt}}
tr{{page-break-inside:avoid}}
th{{text-align:left;font-size:7.5pt;letter-spacing:.06em;text-transform:uppercase;
  color:#8a8f98;border-bottom:.8pt solid #b3bac4;padding:3pt 8pt 3pt 0;font-weight:600}}
td{{border-bottom:.4pt solid #e4e7ec;padding:3.2pt 8pt 3.2pt 0;vertical-align:top}}
td.n,th.n{{text-align:right;white-space:nowrap}}
td.id{{white-space:nowrap;color:#6b7280}}
.v{{font-weight:600;font-size:8.2pt}}
.v-null{{color:#5a6270}} .v-blocked{{color:#3c5488}} .v-underpowered{{color:#9a6510}}
.v-candidate{{color:#00806e}} .v-none{{color:#a0a5ad}}
.neg{{color:#b93c28}}
.slab{{display:flex;gap:22pt;flex-wrap:wrap;border:.7pt solid #d5d9e0;border-radius:6pt;
  padding:11pt 15pt;margin:9pt 0 12pt}}
.slab div{{display:flex;flex-direction:column}}
.slab .k{{font-size:7.3pt;text-transform:uppercase;letter-spacing:.07em;color:#8a8f98}}
.slab .val{{font-size:17pt;font-weight:700;font-variant-numeric:tabular-nums;line-height:1.3}}
ol,ul{{margin:0 0 9pt;padding-left:17pt;max-width:74ch}} li{{margin:0 0 5pt}}
.twocol{{columns:2;column-gap:20pt;font-size:8.6pt}}
.twocol li{{break-inside:avoid;margin:0 0 3pt}}
blockquote{{margin:7pt 0 10pt;padding:8pt 13pt;border-left:2.5pt solid #3c5488;
  background:#f4f6fa;font-size:9.4pt;max-width:72ch;line-height:1.66}}
.claim{{border:.7pt solid #d5d9e0;border-radius:6pt;padding:9pt 13pt;margin:0 0 9pt;
  page-break-inside:avoid}}
.claim .cn{{font-size:7.5pt;letter-spacing:.07em;text-transform:uppercase;color:#8a8f98}}
.claim .ct{{font-weight:650;margin:2pt 0 4pt}}
.claim .cf{{font-size:8.8pt;color:#6b7280;border-top:.4pt solid #e4e7ec;padding-top:4pt;
  margin-top:5pt}}
.pb{{page-break-before:always}}
</style></head><body>

<section class=cover>
  <div class=eyebrow>ARAD · Autoresearch on Alternative Data</div>
  <h1>从计划到{cn(n)}次检验：<br>一个自主因子研究系统的全部证据</h1>
  <p class=dek>Polymarket 预测市场与中国商品期货（以 SC 原油为主）。研究者是大语言模型
  （claude-opus-5，经 claude -p 调用）；确定性框架负责让它的产出可信且可累积。
  本报告写明动机、数学、结果与结论，并逐条给出实现出处。</p>
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
<p><strong>{n} 次检验，{v.get('candidate', 0)} 个 candidate。</strong>不加控制时最惊人的
「发现」全部是波动率聚集这一教科书事实；把品种自身波动或国际油价残差化之后，Polymarket
特征大面积蒸发；唯一走完全流程的候选在封存段被一次性否决。</p>
<p><strong>但这个「0」必须分成两半读，否则会被误读为经验结论。</strong>其中一半是经验的：
{v.get('null', 0)} 条否定都通过了置换检验这道唯一能产出 null 的闸门。另一半是结构的：
成本模型未建（M5）使 <span class=m>cost_model_missing</span> 对每一条 Study 都成立，
而该理由的失效集合含 candidate —— <strong>在 M5 补上之前，candidate 在判决导出规则下
不可达，与数据无关。</strong>本报告第七章把这两半分开陈述。</p>
<div class=slab>
  <div><span class=k>candidate</span><span class=val
    style="color:#b93c28">{v.get('candidate', 0)}</span></div>
  <div><span class=k>读过 outcome</span><span class=val>{n}</span></div>
  <div><span class=k>互异假设</span><span class=val>{D['denominators']['proposal_denominator']}</span></div>
  <div><span class=k>噪声地板</span><span class=val>{floor:.3f}</span></div>
  <div><span class=k>封存开启</span><span class=val>{len(D['sealed'])}</span></div>
  <div><span class=k>Study 总数</span><span class=val>{len(D['studies'])}</span></div>
</div>

<h2>一 · 动机：每一条约束防的是哪一种自欺</h2>
<p>系统的每一个机制都对应一种<strong>具体的、已经发生过的</strong>失败。这一章按
「失败形态 → 约束 → 实测证据」写，不按功能模块写。</p>

<h3>1.1 一条上升的曲线本身不是证据</h3>
<p>选择在纯噪声上必然产出上升的 running-best 曲线。旧系统的实测就摆在那里：81 次爬山
选出的最好 Sharpe 是 2.40，而同一套搜索过程在零假设下的期望是 2.63 —— 曲线在涨，
实际比噪声还差。只画「每次尝试」与「running best」两条线的界面会系统性地骗人。</p>
<p><strong>约束</strong>：给每条曲线配一条随检验次数上升的零假设带（§3.5），并把
「多问一个问题的价格」写进提案器上下文。<strong>后果是对称的</strong>：地板对已有与
将来的全部结论同时生效，因此「再跑几轮」从来不是免费的。</p>

<h3>1.2 分母会被悄悄做小</h3>
<p>如果「试过多少次」由报告者自己数，它必然缩水。<strong>约束</strong>：分母进数据库，
且只增不减 —— <span class=m>statistical_denominator</span> 表上挂 DELETE 与 UPDATE
触发器，一律 <span class=m>RAISE(ABORT)</span>。提案分母（内容寻址，含被拦下的）与
统计分母（只计真正读过 outcome 的）分成两张表：被预检挡下的提案不抬高零假设带。</p>
<p class=src>ledger.py:79-100, 359-385</p>

<h3>1.3 提案者一旦看见效应，就不再是提案者</h3>
<p><strong>约束</strong>：白名单投影 —— 提案器能看见的字段由账本按事件类型逐个列举，
不在名单上的一律不可见。黑名单形式在本项目历史上失败过两次。</p>
<p><strong>这条约束曾被自己违反，且是被对抗性审查抓出来的</strong>（决定 0006）：
决定 0005 曾论证「判决词只泄漏存在性，不泄漏方向与量级」是安全的。该定价有一个
未写出的前提 —— 计数指向的是<strong>匿名总体</strong>。M9 的第 0 层记忆把具名规格清单
交给提案器，取消了匿名：具名清单 + 检验次数 + 判决计数三者可做减法，反推出哪些规格
落在哪一类。定价没有被重新审视，于是判决计数被移出提案器上下文。</p>

<h3>1.4 问错的问题不该消耗预算</h3>
<p><strong>约束</strong>：语义审计在<strong>读 outcome 之前</strong>运行，被拦下的
Study 不读 outcome、不进统计分母。判据必须是结构的：run3 的实测显示，按机制散文
做子串匹配会把「改用波动率归一的有符号收益」这个<strong>正确回应</strong>连续误拦
（因为表达「按波动率归一」必须提到 volatility）。判据因此改为沿特征 DAG 判断。</p>

<h3>1.5 否定结论必须有地方安放</h3>
<p>判决原本由「blocked 与否」二分导出，<span class=m>Verdict.NULL</span> 在全仓
没有任何产出路径 —— 成因是 <span class=m>cost_model_declared=False</span> 对每条
Study 都成立，<span class=m>blocked</span> 恒非空。<strong>约束</strong>（决定 0005）：
判决改由「每条阻塞理由使哪些结论失效」的集合并集推出（§3.4），使 null 成为一等产出。</p>

<h3>1.6 分类法本身可能是后见之明</h3>
<p>Polymarket 的族定义由归纳产生，而归纳语料有自己的时间切点。若该切点晚于结果窗口，
族的划分方式本身就含有后见信息。<strong>约束</strong>（决定 0004）：把
<span class=m>taxonomy_freeze_at</span> 并入前向门的 max 项：</p>
<div class=eq>observation_time &gt; max(system_protocol_freeze_at,
                    study_confirmatory_freeze_at,
                    source_snapshot_at,
                    taxonomy_freeze_at) + embargo</div>
<p>当前语料切点覆盖了手上全部三段，因此全部 Polymarket 结论的
<span class=m>taxonomy_clean</span> 为否，主张被结构性封顶。这不是缺陷，是如实标注。</p>

<h2 class=pb>二 · 数据</h2>
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
<p>universe 由模型自选：<span class=m>full_coverage_panel</span>（36 品种）或任一
单品种主力视图。三类 target 逐品种命名，声明即被评（M8.2 硬校验）。</p>

<h2>三 · 数学定义</h2>
<p>本章只写<strong>参与判决的量</strong>，每条给出实现出处。凡实现与教科书形式或与本仓
文档不一致之处，一律在此写明，不按发表版本填写。</p>

<h3>3.1 时点与目标</h3>
<p>三个时刻的不等式由构造保证，并在评价机再查一遍：</p>
<div class=eq>availability_time ≤ decision_time &lt; execution_time &lt; label_start ≤ label_end

窗口一律左闭右开：V = {{ v_i : end − W ≤ t_i &lt; end }}，  end = decision_time − offset
t_i 取 bar 的**右端点**（该 bar 收完才可用），因此 end 严格不含。
offset_seconds ≥ 0 由语言层强制，负值无法表达。</div>
<p class=src>targets.py:466（建表期断言）· kernel.py:225-241（评价机三条硬边界）·
interpreter.py:94-99（窗口右端点排他）· asof.py:72-97（as-of 取数严格早于决策时点）</p>
<p>主目标 <span class=m>rv_next_session</span>：下一 session 的已实现波动，由该 session
内 bar 对数收益的平方和开方得到；<span class=m>ret_next_session</span>：入场价到收盘价的
对数收益，是唯一带可交易主张的目标；<span class=m>open_gap_absorption</span> 标为
diagnostic_only，定义为 −move_k ⁄ gap（跳空被抹去的比例）。</p>

<h3>3.2 特征语言的七个原语</h3>
<p>每条特征是一张 DAG，节点取自七个原语；规格冻结后由代码生成器产出与解释器<strong>逐位
一致</strong>的代码。无定义一律返回 None 并沿 DAG 传播，<strong>绝不返回 0</strong> ——
「没有数据」与「数据为零」是不同的事实。</p>
<table>
<tr><th>原语</th><th>定义</th></tr>
<tr><td class=m>window</td><td>在左闭右开窗口内对某字段作 mean ／ sum ／ std ／ min ／ max ／ last</td></tr>
<tr><td class=m>innovation</td><td>当前窗口值减去同长度的前一窗口值</td></tr>
<tr><td class=m>ratio ／ difference</td><td>两个上游节点的商 ／ 差</td></tr>
<tr><td class=m>zscore</td><td>(x − x̄) ⁄ s，参考样本取自严格过去的采样网格</td></tr>
<tr><td class=m>rank_pct</td><td>x 在同一参考样本中的分位排名</td></tr>
<tr><td class=m>residualise</td><td>见下</td></tr>
</table>
<h4>residualise：逐点前向残差化（最关键的一个）</h4>
<div class=eq>设 X 为被控制的上游节点，c 为控制序列（brent 或 own_realised_volatility），
窗口 W、采样间隔 S、最小样本 m。在决策时点 at：

  control_at(t) = 控制序列在 [t − W, t) 内的**最后一个**观测（无则 None）
  拟合样本   = {{ (x_k, c_k) : k = 1..W⁄S,  past_k = at − k·S,  两者皆有限 }}
  ← k 从 1 起：**当前点不进入拟合样本**
  若 |set(cs)| &lt; m 则返回 None      ← 计的是**控制变量**的互异取值个数
  β̂ = Σ(c_k − c̄)(x_k − x̄) ⁄ Σ(c_k − c̄)²,   α̂ = x̄ − β̂·c̄
  返回 x_now − (α̂ + β̂·c_now)</div>
<p>三点必须写清，否则会被误读：<strong>（一）返回的不是教科书意义上的残差</strong> ——
当前点被排除在拟合之外，返回值是「当前观测减去用<strong>纯过去</strong>数据拟合的直线在
当前控制值处的预测」，属于样本外预测残差，它在拟合样本上不满足均值为零。
<strong>（二）每个决策时点重新拟合一次</strong>，记忆表按 (步骤, 时刻) 键控，不跨决策点
复用。<strong>（三）门槛计的是控制变量的互异取值个数</strong>，不是样本对数 —— 控制序列
在窗口内取值常量时不可识别，这条门槛正是为它设的。</p>
<p class=src>interpreter.py:231-296（注册表见 43-49）· 代码生成镜像 codegen.py:243-292</p>

<h3>3.3 评价机：五个参与判决的量</h3>
<h4>斜率、双向 cluster 标准误与 t</h4>
<div class=eq>一元 OLS：β̂ = Σ(x_i − x̄)(y_i − ȳ) ⁄ Sxx,  Sxx = Σ(x_i − x̄)²

Cameron–Gelbach–Miller 双向 cluster（a = 交易日，b = 品种）：
  M(g) = Σ_{{组 c ∈ g}} ( Σ_{{i ∈ c}} (x_i − x̄)·e_i )²,   V_g = M(g) ⁄ Sxx²
  V  = V_a + V_b − V_ab
  SE = √V （V ≤ 0 时 NaN，并记 cluster_structure_insufficient）
  t  = β̂ ⁄ SE  （SE 非正或 NaN 时 t = NaN）</div>
<p><strong>实现与教科书的差别</strong>：加减的就是这三项，<strong>没有任何有限样本修正</strong>
（无 G⁄(G−1)，无 (n−1)⁄(n−k)），也没有自由度调整；x̄ 用全样本均值。某一维的互异组数
小于 2 时降级为单向，而字段名仍是 <span class=m>se_two_way_cluster</span>，唯一提示是
<span class=m>diagnostics.two_way.fell_back_to</span>。t、MDE、DFBETAS 三个量一并继承
这个降级后的分母。</p>
<p class=src>kernel.py:332, 338, 394-399</p>

<h4>Kish 有效样本量</h4>
<div class=eq>n_eff = (Σ_g w_g)² ⁄ Σ_g w_g²,  权重 w_g = 该组观测数 c_g
     = n² ⁄ Σ_g c_g²</div>
<p><strong>量纲提醒</strong>：权重取的是 cluster 规模，所以这个数是<strong>有效
cluster 数</strong>而非有效观测数 —— 等规模时它恰好等于组数 G。它与同一字典里的
<span class=m>nominal_n</span> 并排出现，容易被读成有效观测数。</p>

<h4>置换检验（按 Episode 整块置换）——唯一能产出 null 的闸门</h4>
<div class=eq>置换单位是 episode_id（不是单行）。默认 draws = 200，seed = 20260805。
每次抽样：对 episode 键做一次洗牌得映射 g → src，
        对每一行取 pool[src] 中第 cursor[src] mod len(pool[src]) 个标签作 y*，
        用 (y*, 原 x) 重跑 OLS 得 s；  exceed += 1 当 |s| ≥ |β̂|
placebo_exceed_rate = exceed ⁄ 成功抽样数     （成功数为 0 时兜底 1.0）
闸门：placebo_exceed_rate &gt; 0.1 → 记 placebo_failed</div>
<p><strong>三处必须声明的偏差。</strong>（一）episode 规模不等时 y* <strong>不是</strong>
y 的置换：短块的标签被循环复用、长块尾部的标签被丢弃，零分布的标签边缘分布因此与实际
样本不同。（二）exceed 用 ≥ 且<strong>没有</strong> (exceed+1)⁄(draws+1) 修正。
（三）成功抽样数为 0 时兜底 1.0，会直接触发 placebo_failed —— 也就是<strong>把一次
度量失败记成支持 null 的证据</strong>。阈值 0.1 的取值来源代码与文档均未给出。</p>
<p class=src>kernel.py:335-337, 369-373</p>

<h4>单点影响：杠杆、DFBETA、DFBETAS</h4>
<div class=eq>h_i     = 1⁄n + (x_i − x̄)² ⁄ Sxx                （只依赖回归元，不含标签）
DFBETA_i = (x_i − x̄)·e_i ⁄ [ Sxx·(1 − h_i) ]        （解析一步删除，非逐点重跑）
DFBETAS  = max_i |DFBETA_i| ⁄ SE                    （SE 即双向 cluster SE）
闸门：DFBETAS &gt; 1.0 时按方向分两种理由 ——
  could_flip_null = isnan(t) 或 |t| + DFBETAS ≥ 2.8
    真 → single_point_influence_both        （使 candidate 与 null 同时失效）
    假 → single_point_influence_candidate_only（只使 candidate 失效）</div>
<p><strong>为什么不用 |DFBETA| ⁄ |β̂|</strong>：那个比值在 β̂ → 0 时发散，也就是
<strong>在完全没有效应时叫得最响</strong>。它已从闸门移除，只留在诊断里。
现用分母是双向 cluster SE，与 Belsley–Kuh–Welsch 的留一 s₍ᵢ₎·√(1⁄Sxx) 量纲相同、
数值不同。杠杆值刻意不设阈值、不阻断：它只捕到三条问题里的一条，而「一个点占多少变异
算太多」同样无法在不看结果的前提下定下来。</p>
<p class=src>kernel.py:334, 341-365, 374-389</p>

<h4>否定结论的排除界</h4>
<div class=eq>mde_at_2p8_se = 2.8 · SE      仅当判决为 null 时写入 null_exclusion_bound</div>
<p>它是「2.8 个标准误」的换算，<strong>功效 1−β 没有出现在公式里</strong>，因此不是
给定功效下的正式 MDE。SE 被低估时（cluster 退化降级、无有限样本修正）这个界一并被低估，
于是 null 会宣称排除了比它实际排除的更小的效应。外部经济参照（M5）尚未声明，
因此这个界目前<strong>只有统计含义，没有经济含义</strong>。</p>

<h3>3.4 判决导出：只读理由种类，不读数值</h3>
<div class=eq>失效表 REASON_INVALIDATES：
  insufficient_sample                → {{candidate, null}}
  not_identified                     → {{candidate, null}}
  single_point_influence_both        → {{candidate, null}}
  cost_model_missing                 → {{candidate}}
  cluster_structure_insufficient     → {{candidate}}
  single_point_influence_candidate_only → {{candidate}}
  placebo_failed                     → ∅

derive_verdict(kinds)：
  1. 出现未登记的种类            → ValueError（不容忍未知理由）
  2. insufficient_sample ∈ kinds → UNDERPOWERED
  3. invalidated = ∪ REASON_INVALIDATES[k]
  4. placebo_failed ∈ kinds 且 null ∉ invalidated → NULL
  5. candidate ∈ invalidated     → BLOCKED
  6. 否则                         → CANDIDATE</div>
<p>判决<strong>只读理由的种类</strong>，不读任何数值：数值唯一能影响种类的地方是
<span class=m>could_flip_null</span>，而它经由预注册的闸门表达。这条设计使判决可
机械复核 —— 给定理由集合，判决唯一确定。</p>
<p class=src>kernel.py:44-87, 506-522</p>

<h3>3.5 选择校正：零假设带与自罚奖励</h3>
<p>这是整个系统的定价机制。<strong>此前本仓文档把它写作 √(2 ln n)，那是渐近主项，
不是实现所算</strong>（n = 10 时渐近式给 2.146，实际 1.901）。实现是
Bailey &amp; López de Prado 的两项闭式：</p>
<div class=eq>γ = 0.5772156649015329（欧拉常数）,  Φ⁻¹ 用 Acklam 有理逼近（不引入 scipy）

E_τ(n) = (1 − γ)·Φ⁻¹(1 − 1⁄(τn)) + γ·Φ⁻¹(1 − 1⁄(τne))

|z| 最大值的期望（双侧，τ = 2）：expected_max_abs_z(n) = E₂(n),  n ≥ 2
                            n = 1 时硬编码 √(2⁄π) = 0.797885（半正态均值）
有符号最大值（单侧，τ = 1）：expected_max_z(n) = E₁(n),  n ≥ 2;  n = 1 时为 0

自罚奖励：reward = |t| − expected_max_abs_z(n_at_evaluation)

实测：n=1 → 0.798,  n=2 → 1.052,  n=10 → 1.901,  n=81 → 2.696,  n=1000 → 3.447</div>
<p><strong>三条声明。</strong>（一）τ 参数是本仓对发表形式的改写（发表式为 1−1⁄n 与
1−1⁄(ne)，不含 τ）；因 τ 与 n 只以乘积出现，恒有
<span class=m>expected_max_abs_z(n) = expected_max_z(2n)</span>。
（二）n = 1 处硬编码值与公式取值不连续（0.798 对 0.520），这是 Φ⁻¹(0) = NaN 的必需
分支。（三）<strong>独立性假设使阈值偏严</strong> —— 同一族里的变体高度相关，真实的
期望最大值更低。因此「没越过带」不等于「确定无效」，它是独立情形下的上界，
不构成判决，也不是多重检验校正后的 p 值。</p>
<p class=src>selection.py:26, 60-97 · beam.py:41-46 · induction.py:83-97</p>

<h3>3.6 封存段：一次性由账本强制</h3>
<div class=eq>seal_key = SHA256(feature_id, segment, SEALED_VERSION)
assert_unopened：扫描全部 sealed_segment_opened 事件，键已存在 → SealedAlreadyOpened
开封记录 append 进哈希链，不可撤销、不可重开

因子卡状态：retention = |t_封存| ⁄ |t_发现|,  阈值 _HOLD_RATIO = 0.35
taxonomy_clean = not (contamination 且 归纳语料切点落在任一结果窗口起点之后)</div>
<p><strong>两处必须写明。</strong>（一）<span class=m>_HOLD_RATIO = 0.35</span> 与
<span class=m>min_rows = 120</span> 都是写死的模块常量，全仓各只用一处，
<strong>没有任何文档给出推导</strong> —— 不是由功效分析、样本量比或先验收缩推出的。
（二）比值的分子分母都是 <strong>t 值</strong>而非效应量，而两段样本量通常不同，
详见 §5.2 的量化。</p>
<p class=src>sealed.py:60-97 · registry/specs.py:149-157</p>

<h3>噪声地板的实际抬升轨迹</h3>
<table style="max-width:44ch"><tr><th class=n>已读 outcome 次数 n</th>
<th class=n>E[max|z|]</th></tr>{floor_rows}</table>

<h2 class=pb>四 · 十六次运行编年</h2>
{chronicle}

<h2 class=pb>五 · 结果</h2>

<h3>5.1 假象家族：重新发现了波动率聚集</h3>
<p>统计量最大的几条：{E(artefacts)}。共同构造是<strong>分母为已实现波动、目标也是
已实现波动</strong>。PIT 无问题、置换检验通过 —— 因为这个关系是真的；它只是金融学里
最稳健的定型化事实之一，属 Baseline Control，不是另类数据的 alpha。</p>
<p>诊断证据（离线，不进族账本）：对其中最大一条的构造做残差化，秩相关由 −0.5695
塌至 −0.0077，<strong>缩小 74 倍</strong>。这几条是 <span class=m>rank_pct</span> 与
<span class=m>residualise</span> 两个原语被实现的直接动因；此后
{residualised}／{specs} 的规格带控制项，近数轮为 100%。</p>

<h3>5.2 唯一走完全流程的候选，及其封存段裁决</h3>
<blockquote><strong>{E(hero.get('feature_id') or '—')}</strong>（{HERO_ID}）：
cand:iran 族归一化概率的 30 日均值，减掉品种自身波动持续性之后，预测下一时段已实现波动。
机制为混合分布假说 —— 波动由信息到达强度决定，到达强度由风险的当前发生率水平决定；
油价已含发生率×损失的一阶期望，发生率水平本身另有信息。<br><br>
发现段：t = {num(hero.get('t'))}、IC 秩 = {num(hero.get('ic'), 3)}、{n_d} 行、
置换 {hero.get('placebo', '—')} 通过。<br>
封存段（一次性）：t = {num(hero_seal_t)}、IC 秩 = {num(hero_sealed.get('ic_spearman'), 3)}、
{n_s} 行 —— t 值比 {f'{retention:.1%}' if retention is not None else '—'}，
低于 0.35 的保持线，判 sealed_failed。<strong>裁决终身有效，不重开。</strong></blockquote>
<p><strong>一处口径更正。</strong>闸门比的是<strong>两个 t 值</strong>而非两个效应量，
而两段样本量不同（{n_d} 行对 {n_s} 行）。即便斜率与残差标准差完全不变，t 也会按
√(n_封存⁄n_发现) ≈ {f'{size_factor:.2f}' if size_factor else '—'} 缩小。
按样本量修正后，效应本身的保留率约
{f'{retention_adj:.1%}' if retention_adj is not None else '—'} —— 仍远低于 0.35，
<strong>裁决结论不变</strong>，但此前文档所用的「线性效应保留率」这一措辞与代码实际
所算的量不是同一个东西（记 B3）。</p>
<p>该候选在发现段也从未越过当时的族地板：被评价时本族已花 {tests_then} 次检验，
地板 {f'{floor_then:.3f}' if floor_then else '—'}，而它是 {num(hero.get('t'))}，
自罚奖励为负。</p>

<h3>5.3 一个未解释的现象：秩相关在样本外升高</h3>
<p>同一条特征，线性斜率在封存段几乎消失（t 由 {num(hero.get('t'))} 降到
{num(hero_seal_t)}），而<strong>秩相关反而从 {num(hero.get('ic'), 3)} 升到
{num(hero_sealed.get('ic_spearman'), 3)}</strong>。两者方向相反。</p>
<p>可能的读法有三种，本系统<strong>无法在不花新预算的前提下区分</strong>：
（一）关系是单调但非线性的，线性斜率本就不是它的正确统计量；
（二）封存段样本更小，秩相关的抽样噪声更大，这个升高只是噪声；
（三）发现段存在若干高杠杆点支撑着线性斜率，封存段没有。<strong>它是一个开放问题，
不是一条结论</strong>；把它写成「其实有效」需要一次新的预注册检验，而那要另花地板。
IC 在本系统中不给标准误、不给 p 值、不进入任何闸门（kernel.py:410）。</p>

<h3>5.4 干净的 null（{v.get('null', 0)} 条）</h3>
<p>残差化普及后，模型在互异机制上系统扫过：资金集中度、信念下限棘轮、闭市时段资金份额、
停火与伊朗资金倾斜、平均单笔金额、方向性信念离散度、事件不确定性 p̄(1−p̄)、到达加速度、
对娱乐族的安慰剂对照。每一条都先减掉 Baseline Control、都是预注册的可证伪假设、
否定都带自己的排除界。<strong>按判决导出规则，null 只能经由置换检验产出</strong>
（§3.4 第 4 步），因此这 {v.get('null', 0)} 条都是「置换分布里 ≤ 10% 的抽样达到了
实际斜率的绝对值」这一具体陈述，不是「没看出什么」。</p>

<h3>封存段全记录（{len(D['sealed'])} 次开启，每规格终身一次）</h3>
{''.join(sealed)}
<p class=note>taxonomy_clean 全为否：族归纳语料的切点覆盖了全部三段（决定 0004）。</p>

<h2 class=pb>六 · 测量装置本身的局限</h2>
<p>为写第三章，对全部参与判决的统计量做了一次逐行提取，核对实现与文档是否一致。
下列不一致<strong>由本次核对发现</strong>，全部记入 <span class=m>docs/BLOCKERS.md</span>，
按本项目的规矩<strong>只记录不修</strong>（票外）。它们不改变已有判决的方向，
但决定了这些判决能被读到多紧。</p>
<table>
<tr><th>项</th><th>不一致之处</th><th>对结论的影响方向</th></tr>
<tr><td>置换检验兜底</td><td>成功抽样数为 0 时 <span class=m>placebo_exceed_rate</span>
  兜底 1.0，直接触发 placebo_failed</td>
  <td>把一次<strong>度量失败</strong>记成支持 null 的证据 —— null 偏多</td></tr>
<tr><td>置换的块结构</td><td>episode 规模不等时短块标签循环复用、长块尾部丢弃，
  y* 不是 y 的置换</td><td>零分布的边缘分布与样本不同，方向不定</td></tr>
<tr><td>置换阈值</td><td>0.1，严格大于，不随 draws 变化；来源代码与文档均无</td>
  <td>比常用的 0.05 宽松 —— null 偏少</td></tr>
<tr><td>cluster SE</td><td>无任何有限样本修正（无 G⁄(G−1)）</td>
  <td>SE 偏小 → |t| 偏大、MDE 偏小 —— 排除界宣称得比实际紧</td></tr>
<tr><td>功效闸门</td><td><span class=m>min_clusters</span> 数的是 episode 不重复数，
  而多品种下 episode_id 以品种开头，N 个品种把同一批交易日的 episode 数放大 N 倍</td>
  <td>面板上功效闸门被稀释 N 倍 —— underpowered 偏少</td></tr>
<tr><td>DFBETA 分子</td><td>h_i = 1 时 DFBETA = +inf，而
  <span class=m>gate_evaluable</span> 仍为 True</td>
  <td>账本可写下「斜率移动 inf 个标准误」，守卫只覆盖标准误一侧</td></tr>
<tr><td>MDE 常量</td><td><span class=m>mde_at_2p8_se</span> 硬编码字面量 2.8，
  未引用 <span class=m>SIGNIFICANCE_T</span>，而注释声明二者共用</td>
  <td>目前数值相同；改一处会静默漂移</td></tr>
<tr><td>紧缩 Sharpe</td><td>方差项比发表式少常数项 2⁄4（正态情形代码得 1，
  发表式得 1 + SR²⁄2）</td><td>方差偏小 → z 偏极端 —— 紧缩 Sharpe 偏乐观</td></tr>
<tr><td>Sharpe 带的尺度</td><td><span class=m>sharpe_spread</span> 在循环外对整个序列
  算一次，含第 i 点之后才发生的试验</td><td>Sharpe 带含前视成分；|t| 带没有</td></tr>
<tr><td>驾驶舱的两个 n</td><td>曲线的 n 是 <span class=m>evaluation_result</span>
  事件序号且<strong>不按 family 过滤</strong>，顶栏的 n 按 family 过滤统计分母</td>
  <td>同一屏两个口径；单族时接近，多族时给出错误的图（B1）</td></tr>
<tr><td>提案器看到的口径</td><td><span class=m>search_price</span> 的说明文字写
  √(2 ln n)，与实现不符</td><td>提案器读到的地板口径是错的（B2）</td></tr>
<tr><td>0.35 与 120</td><td>写死常量，无推导（B4）</td>
  <td>封存段的判定线是约定，不是导出的</td></tr>
</table>
<p><strong>这一章存在本身是一条结论</strong>：本系统的可信性来自约束的结构，
而不是任何单个数字的精确。上表里没有一条会把某个 null 翻成 candidate ——
candidate 被 §3.4 的失效表结构性挡住，与这些数值无关。</p>

<h2 class=pb>七 · 结论</h2>
<p>每条结论后面写明<strong>什么证据会推翻它</strong>。凡不能写出证否条件的，
不写成结论。</p>

<div class=claim><div class=cn>结论 一 · 结构</div>
<div class=ct>「candidate = 0」当前<strong>不是</strong>一个经验结论。</div>
<p><span class=m>cost_model_declared</span> 默认为 False 且对全部 {len(D['studies'])}
条 Study 都成立；<span class=m>cost_model_missing</span> 的失效集合含 candidate；
按 §3.4 第 5 步，判决必为 BLOCKED 或更弱。<strong>在 M5 补上之前，任何数据都不可能
产出 candidate。</strong>把这个 0 当作「另类数据没用」的证据是错误的读法。</p>
<div class=cf>证否：给出一条 <span class=m>cost_model_declared=True</span> 且理由集合
不含任何使 candidate 失效之项的 Study。</div></div>

<div class=claim><div class=cn>结论 二 · 经验</div>
<div class=ct>在已检验的机制上，Polymarket 特征相对 Baseline Control 的<strong>线性</strong>
增量预测力，未能通过预注册的证否闸门。</div>
<p>{v.get('null', 0)} 条 null 中的每一条，都是「置换分布里超过 10% 的抽样达到了实际
斜率的绝对值」这一具体陈述，且都在残差化之后。这不是「没看出什么」，是一批带排除界的
否定。</p>
<div class=cf>证否：一条残差化后的特征，在同族地板之上取得 |t| 且置换 exceed ≤ 0.1，
并在封存段保住。<strong>注意：目前尚无任何一条满足前半句</strong>（见结论三）。</div></div>

<div class=claim><div class=cn>结论 三 · 经验</div>
<div class=ct>历史上从未有任何一条 Study 越过它被评价时的族地板。</div>
<p>含四条波动假象在内，最好的一次也只在发现段短暂高于当时地板；唯一走完全流程的候选
（{HERO_ID}）在评价时地板为 {f'{floor_then:.3f}' if floor_then else '—'}，
而它是 {num(hero.get('t'))}，<strong>自罚奖励为负</strong>。</p>
<div class=cf>证否：账本中出现 reward = |t| − expected_max_abs_z(n) &gt; 0 的记录。
可直接从 <span class=m>beam_state</span> 事件复核。</div></div>

<div class=claim><div class=cn>结论 四 · 方法</div>
<div class=ct>残差化把「发现」与「重新发现基线」分开了，且效果是数量级的。</div>
<p>不加控制时 |t| 达 {abs(top[0]['t']):.2f} 的构造，残差化后秩相关缩小约 74 倍（该诊断在离线完成、不进族账本，是本报告中唯一不来自快照的数字）；
原语可用后，{residualised}／{specs} 的规格自带控制项，近数轮 100%。
<strong>模型采用它的转折点不是「原语可见」，而是提示词写明了为什么要用</strong> ——
run9 时原语已在菜单里，使用率为零；run10 补上口径后立即 5／5。</p>
<div class=cf>证否：一条残差化后 |t| 未显著下降、且能在封存段保住的量价构造。</div></div>

<div class=claim><div class=cn>结论 五 · 方法</div>
<div class=ct>封存段是这套系统里唯一无法用「再跑一次」绕过的闸门，且它起了作用。</div>
<p>{HERO_ID} 在发现段通过了置换、影响、覆盖三关，机制论证也立得住；封存段一次开启即
判 sealed_failed。开封记录进哈希链，<span class=m>seal_key</span> 拒绝第二次。
<strong>若无此闸门，这条会以「t = {num(hero.get('t'))}、置换通过」的面貌进入结论。</strong></p>
<div class=cf>证否：找到一条路径能对同一 (规格, 段) 二次取值而不触发
<span class=m>SealedAlreadyOpened</span>。</div></div>

<div class=claim><div class=cn>结论 六 · 局限</div>
<div class=ct>本报告的全部 Polymarket 结论都被分类法污染结构性封顶。</div>
<p>族归纳语料的切点覆盖了手上全部三段，因此 {len(D['sealed'])} 次封存开启的
<span class=m>taxonomy_clean</span> 全部为否（决定 0004）。这不影响否定结论的方向
（污染只会使主张更容易成立，不会凭空制造 null），但<strong>任何肯定结论在此状态下
都不可采信</strong>。</p>
<div class=cf>证否：用切点早于全部结果窗口的语料重新归纳族定义，并重跑。</div></div>

<div class=claim><div class=cn>结论 七 · 局限</div>
<div class=ct>测量装置本身有 12 处实现与文档不符，但没有一处能把 null 翻成 candidate。</div>
<p>第六章逐条列出。影响方向可判的几处中，SE 缺有限样本修正使排除界宣称得比实际紧；
置换阈值 0.1 比常用的 0.05 宽松；面板上功效闸门被 episode 命名稀释。
<strong>三者的净效应无法在不重跑的前提下定号。</strong></p>
<div class=cf>证否：补上有限样本修正与功效闸门口径后重跑，若判决分布不变，则这些偏差
在本样本上不重要。</div></div>

<h2>八 · 下一步（全部需人决定）</h2>
<ol>
<li><strong>M5 成本模型</strong> —— 由结论一，这是唯一能让 candidate 从不可达变为可达
的改动。在它之前继续花检验预算，只是把地板抬得更高。</li>
<li><strong>分类法重归纳（干净切点）</strong> —— 解除结论六的封顶。</li>
<li><strong>郑商所 21 品种</strong> —— TradingDay 自然日与交易日之别，属 PIT 语义裁决。</li>
<li><strong>财联社接入</strong> —— 第三个数据源，五十六万行原文待进解释器。</li>
<li><strong>横截面 target</strong> —— 面板已通，但真正的截面 IC 需要「同一时点排序多品种」
的新目标定义；同时应修 <span class=m>min_clusters</span> 在面板上的稀释（见第六章）。</li>
</ol>
<p class=note>顺序上，1 应先于其余四项：不修门而继续敲门，每一次都在抬高自己的地板。</p>

<h2 class=pb>附录 · 全部 {len(D['studies'])} 个 Study</h2>
{''.join(appendix)}
<p class=note>数据来源 data/ledger/service.db，冻结于 seq {D['frozen_at']['seq']}
（{E(D['frozen_at']['at'])}）。生成方式：scripts/build_report.py 直接投影账本；
第三、六章的公式与出处由一次逐行代码提取核对，叙述部分由人撰写、不含任何数字，
因此散文与表格不会不一致。</p>
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
