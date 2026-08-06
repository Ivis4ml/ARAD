"""Atlas 渲染：把投影变成静态站点（M9 第二部分）。

**静态生成而非服务端。**决定 0003 允许 FastAPI 或静态站点，这里取静态：
不引入新依赖，且只读边界变成物理的 —— 一个 HTML 文件写不了账本。
同时没有服务端生命周期需要与 `ServiceState` 互相解释。

渲染层不认识统计学：它不 import 任何统计模块，所有数字来自投影里存好的 payload。
浮点数按 6 位有效数字显示，`title` 属性里保留原值；同一份数据的机器可读副本
写在 `atlas.json` 里，供审计比对。
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .project import AtlasProjection

#: verdict 的显示色。五个都是合法完整产出，配色不暗示优劣，只区分类别。
VERDICT_STYLE = {
    "candidate": "#1f6f43",
    "null": "#5a6270",
    "underpowered": "#8a6d1f",
    "blocked": "#3f5d8a",
    "error": "#8a2f2f",
}

CSS = """
:root { color-scheme: light dark; --fg:#1b1d20; --bg:#fbfbfa; --line:#d8d6d1;
        --muted:#5f6672; --card:#ffffff; }
@media (prefers-color-scheme: dark) {
  :root { --fg:#e6e6e3; --bg:#16181b; --line:#33373d; --muted:#9aa1ad; --card:#1d2024; }
}
* { box-sizing: border-box; }
body { margin:0; padding:0 1.5rem 4rem; background:var(--bg); color:var(--fg);
       font: 15px/1.65 -apple-system, "Helvetica Neue", "Songti SC", serif;
       max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin: 2rem 0 .3rem; }
h2 { font-size: 1.2rem; margin: 2.4rem 0 .6rem; border-bottom:1px solid var(--line);
     padding-bottom:.3rem; }
h3 { font-size: 1rem; margin: 1.4rem 0 .4rem; }
p, li { margin: .35rem 0; }
.sub { color: var(--muted); }
.badges { display:flex; flex-wrap:wrap; gap:.5rem; margin:.8rem 0 1.4rem; }
.badge { border:1px solid var(--line); border-radius:3px; padding:.2rem .6rem;
         background:var(--card); font-size:.85rem; }
.badge.bad { border-color:#8a2f2f; color:#8a2f2f; }
.badge.ok { border-color:#1f6f43; color:#1f6f43; }
table { border-collapse: collapse; width:100%; margin:.6rem 0; font-size:.9rem;
        display:block; overflow-x:auto; }
th, td { border:1px solid var(--line); padding:.35rem .55rem; text-align:left;
         vertical-align:top; }
th { background:var(--card); font-weight:600; }
code, .mono { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size:.85em; }
.verdict { display:inline-block; padding:.05rem .45rem; border-radius:3px;
           color:#fff; font-size:.8rem; }
details { border:1px solid var(--line); border-radius:4px; margin:.6rem 0;
          background:var(--card); }
details > summary { cursor:pointer; padding:.5rem .8rem; font-weight:600; }
details > div { padding:0 .8rem .8rem; }
ol.timeline { list-style:none; padding-left:0; margin:.4rem 0; }
ol.timeline li { border-left:2px solid var(--line); padding:.15rem 0 .15rem .8rem; }
ul.tree { list-style:none; padding-left:1rem; margin:.2rem 0; }
ul.tree > li > span.k { color:var(--muted); }
.notice { border-left:3px solid #8a6d1f; padding:.4rem .8rem; margin:.6rem 0;
          background:var(--card); }
footer { margin-top:3rem; color:var(--muted); font-size:.85rem;
         border-top:1px solid var(--line); padding-top:.8rem; }
"""


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _num(value: float) -> str:
    text = f"{value:.6g}"
    return f'<span class="mono" title="{_e(repr(value))}">{_e(text)}</span>'


def _value(node: Any) -> str:
    """把任意 payload 片段渲染成嵌套列表。渲染不改变数值，只改变显示位数。"""
    if isinstance(node, bool):
        return f'<span class="mono">{"true" if node else "false"}</span>'
    if isinstance(node, float):
        return _num(node)
    if isinstance(node, int):
        return f'<span class="mono">{node}</span>'
    if isinstance(node, dict):
        items = "".join(
            f'<li><span class="k">{_e(k)}：</span>{_value(v)}</li>' for k, v in node.items()
        )
        return f'<ul class="tree">{items}</ul>'
    if isinstance(node, (list, tuple)):
        if not node:
            return '<span class="sub">（空）</span>'
        return '<ul class="tree">' + "".join(f"<li>{_value(v)}</li>" for v in node) + "</ul>"
    text = _e(node)
    return f'<span class="mono">{text}</span>' if len(text) == 64 else text


def _verdict_chip(verdict: str) -> str:
    if not verdict:
        return '<span class="sub">未判决</span>'
    colour = VERDICT_STYLE.get(verdict, "#5a6270")
    return f'<span class="verdict" style="background:{colour}">{_e(verdict)}</span>'


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{_e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _overview(p: AtlasProjection, freshness: list[dict]) -> str:
    d = p.denominators
    totals = p.totals
    parts = [
        "<h2>一、总览</h2>",
        _table(
            ["计数", "值", "含义"],
            [
                [
                    "proposal denominator",
                    f'<span class="mono">{d["proposal_denominator"]}</span>',
                    f'全部提案，含被预检挡下的 {d["proposals_screened_out"]} 个',
                ],
                [
                    "statistical denominator",
                    f'<span class="mono">{d["statistical_denominator"]}</span>',
                    "真正读过 outcome 的检验次数，只增不减",
                ],
                ["Study", f'<span class="mono">{totals["studies"]}</span>', "建立并留下判决的研究单元"],
                [
                    "中止轮次",
                    f'<span class="mono">{totals["aborted_rounds"]}</span>',
                    "有事件但未建立 Study 的轮次（如输出无法解析）",
                ],
                [
                    "原语缺口声明",
                    f'<span class="mono">{totals["primitive_gaps"]}</span>',
                    "现有原语无法表达某机制的声明，属有价值产出",
                ],
            ],
        ),
        "<h3>Verdict 分布</h3>",
        _table(
            ["verdict", "Study 数"],
            [
                [_verdict_chip(k), f'<span class="mono">{v}</span>']
                for k, v in p.verdicts.items()
            ],
        ),
        ('<p class="sub">五种 verdict 都是合法完整产出；underpowered 与 blocked 同样是'
         "结论，不是失败。调度动作与 verdict 分开记录，见各 Study 的 next_action。</p>"),
        "<h3>库存覆盖（机制族 × 数据源 × 时域）</h3>",
    ]
    if p.coverage:
        parts.append(
            _table(
                ["机制族", "数据源", "时域", "Study 数", "verdict 构成"],
                [
                    [
                        _e(c["family"]),
                        _e(c["source"]),
                        _e(c["horizon"]),
                        f'<span class="mono">{c["studies"]}</span>',
                        " ".join(
                            f"{_verdict_chip(k)} {v}" for k, v in sorted(c["verdicts"].items())
                        ),
                    ]
                    for c in p.coverage
                ],
            )
        )
    else:
        parts.append('<p class="sub">尚无已判决的 Study。</p>')

    parts.append("<h3>三源数据新鲜度</h3>")
    parts.append(
        _table(
            ["数据源", "状态", "覆盖末日", "manifest 指纹", "扫描时间", "findings"],
            [
                [
                    _e(s["source_id"]),
                    _e(s["status"]),
                    _e(s.get("coverage_end", "")),
                    f'<span class="mono">{_e(s.get("fingerprint", "")[:16])}</span>',
                    _e(s.get("scanned_at", "")),
                    _e(s.get("findings", "")),
                ]
                for s in freshness
            ],
        )
    )
    parts.append(
        '<p class="sub">新鲜度来自 M1 manifest 自身记录的指纹与覆盖末日；'
        "Atlas 不扫描源数据目录，也不触发采集。</p>"
    )
    if p.service:
        parts.append("<h3>Research Service 状态</h3>")
        parts.append(_value(p.service))
        parts.append(
            '<p class="sub">Service 只有 running / paused / shutdown 三态，没有 completed：'
            "研究服务不会「完成」，只会被人停下。</p>"
        )
    return "\n".join(parts)


def _episodes(p: AtlasProjection) -> str:
    parts = ["<h2>二、过程</h2>", "<h3>Search Episode</h3>"]
    if not p.episodes:
        parts.append('<p class="sub">账本中尚无 Episode 记录。</p>')
    for ep in p.episodes:
        summary = ep["summary"] or {}
        ended = ep["ended_at"] or "（未结束）"
        parts.append("<details open><summary>Episode "
                     f'{_e(ep["episode_id"])}　{_e(ep["started_at"])} → {_e(ended)}'
                     "</summary><div>")
        if summary:
            parts.append(
                _table(
                    ["轮数", "结束原因", "各类结局", "预算"],
                    [[
                        f'<span class="mono">{summary.get("rounds", "")}</span>',
                        _e(summary.get("ended_because", "")),
                        _value(summary.get("outcomes", {})),
                        _value(summary.get("budget", {})),
                    ]],
                )
            )
            parts.append(
                '<p class="sub">预算耗尽只结束 Episode 并交回剩余预算，'
                "Research Service 不因此停止。</p>"
            )
        if ep["studies"]:
            links = "、".join(
                f'<a href="#study-{_e(s)}"><code>{_e(s)}</code></a>' for s in ep["studies"]
            )
            parts.append(f"<p>本 Episode 触及的 Study：{links}</p>")
        if ep["events"]:
            parts.append("<h4>不属于任何 Study 的事件</h4>")
            parts.append(
                '<p class="sub">原语缺口声明与 provider 故障本来就没有 Study 归属。'
                "按 Study 分组会让它们整批消失，而它们恰恰是第一版最有信息量的产出。</p>"
            )
            for record in ep["events"]:
                parts.append(
                    f'<p><span class="mono">#{record["seq"]}</span>　{_e(record["at"])}　'
                    f'<strong>{_e(record["label"])}</strong></p>{_value(record["payload"])}'
                )
        parts.append("</div></details>")

    if p.aborted_rounds:
        parts.append("<h3>中止轮次（未建立 Study）</h3>")
        parts.append(
            '<p class="sub">这些轮次带着 study_id 入账，但没有 study_created，'
            "因而不是 Study。它们是预期状态，不是账本缺口。</p>"
        )
        parts.append(
            _table(
                ["标识", "中止于", "时间"],
                [
                    [f'<code>{_e(a["study_id"])}</code>', _e(a["reason"]), _e(a["at"])]
                    for a in p.aborted_rounds
                ],
            )
        )
    return "\n".join(parts)


def _timeline_html(timeline: list[dict]) -> str:
    items = "".join(
        f'<li><span class="mono">#{t["seq"]}</span>　<span class="sub">{_e(t["at"])}</span>'
        f'　{_e(t["label"])}</li>'
        for t in timeline
    )
    return f'<ol class="timeline">{items}</ol>'


def _snapshot_html(study: dict) -> str:
    snap = study["snapshot"]
    parts = [
        _table(
            ["verdict", "next_action", "判决时间", "理由"],
            [[
                _verdict_chip(study["verdict"]),
                f'<code>{_e(study["next_action"])}</code>',
                _e(study["decided_at"]),
                _e(study["rationale"]),
            ]],
        )
    ]
    if study["forward_reserved"]:
        parts.append(
            '<p class="notice">forward 段：<strong>预约待裁决</strong>。'
            "forward 区间的数据与标签在 Atlas 中不可见，此处只显示预约状态，"
            "不显示任何尚未到期的结果。</p>"
        )
    parts.append("<h4>判决当时可见的数据范围</h4>")
    parts.append(_value(snap["visible_data_range"]))
    parts.append("<h4>冻结的假设</h4>")
    parts.append("<p>提案（Hypothesis Lock 之前）</p>")
    parts.append(_value(snap["proposal"]))
    parts.append("<p>Hypothesis Lock（读取任何 outcome 之前）</p>")
    parts.append(_value(snap["hypothesis_lock"]))
    parts.append("<p>Confirmatory Lock（validation 开始之前）</p>")
    parts.append(_value(snap["confirmatory_lock"]))
    if snap.get("feature_spec"):
        parts.append("<h4>特征规格与工件哈希</h4>")
        parts.append(_value(snap["feature_spec"]))
    parts.append(f'<h4>读过 outcome 的检验（{len(snap["outcome_reads"])} 次）</h4>')
    parts.append(_value(snap["outcome_reads"]))
    evaluation = snap.get("evaluation")
    if evaluation:
        parts.append("<h4>评价机结果</h4>")
        parts.append("<p>覆盖</p>")
        parts.append(_value(evaluation.get("coverage", {})))
        if evaluation.get("effects"):
            parts.append("<p>估计量</p>")
            parts.append(_value(evaluation["effects"]))
        parts.append("<p>未通过的预注册闸门</p>")
        parts.append(_value(evaluation.get("blocked_reasons", [])))
        parts.append("<p>诊断与独立性</p>")
        parts.append(_value(evaluation.get("diagnostics", {})))
        parts.append(
            _table(
                ["evaluator 版本", "request 摘要", "result 摘要"],
                [[
                    _e(evaluation.get("evaluator_version", "")),
                    f'<span class="mono">{_e(evaluation.get("request_digest", "")[:16])}</span>',
                    f'<span class="mono">{_e(evaluation.get("result_digest", "")[:16])}</span>',
                ]],
            )
        )
        parts.append(
            '<p class="sub">以上全部数字由评价机出具并存入账本，Atlas 原样读出，'
            "不实现任何统计量。</p>"
        )
    else:
        parts.append(
            '<p class="sub">本 Study 没有评价结果：它在取数或功效预检阶段就已判决。</p>'
        )
    parts.append("<h4>分母（判决当时）</h4>")
    parts.append(_value(snap["denominators"]))
    return "\n".join(parts)


def _studies(p: AtlasProjection) -> str:
    parts = ["<h2>三、判决快照</h2>"]
    if not p.studies:
        parts.append('<p class="sub">尚无 Study。</p>')
    for study in p.studies:
        parts.append(
            f'<details id="study-{_e(study["study_id"])}"><summary>'
            f'{_verdict_chip(study["verdict"])}　<code>{_e(study["study_id"])}</code>'
            f'　{_e(study["mechanism"][:80])}</summary><div>'
        )
        parts.append("<h4>时间线</h4>")
        parts.append(_timeline_html(study["timeline"]))
        parts.append(_snapshot_html(study))
        parts.append("</div></details>")
    return "\n".join(parts)


def render_html(
    projection: AtlasProjection,
    *,
    title: str = "ARAD Research Atlas",
    freshness: list[dict] | None = None,
) -> str:
    chain = projection.chain
    chain_badge = (
        f'<span class="badge ok">哈希链完整：{chain["events"]} 个事件</span>'
        if chain["intact"]
        else f'<span class="badge bad">哈希链断裂于 seq {chain["broken_at"]}</span>'
    )
    service_badge = ""
    if projection.service:
        state = projection.service.get("state", "")
        service_badge = f'<span class="badge">Service：{_e(state)}</span>'
    body = "\n".join(
        [
            f"<h1>{_e(title)}</h1>",
            '<p class="sub">研究过程的只读投影。Atlas 读账本，不写账本，不重算任何统计量。</p>',
            (f'<div class="badges">{chain_badge}{service_badge}'
             f'<span class="badge">Study {projection.totals["studies"]}</span>'
             f'<span class="badge">Episode {projection.totals["episodes"]}</span>'
             f'<span class="badge">Atlas {projection.atlas_version}</span></div>'),
            _overview(projection, freshness or []),
            _episodes(projection),
            _studies(projection),
            ("<footer>"
             "每次渲染都重算整条哈希链：Atlas 因此也是账本完整性的持续检验。"
             "浮点数按 6 位有效数字显示，鼠标悬停可见原值；"
             "机器可读副本见同目录的 <code>atlas.json</code>。"
             "</footer>"),
        ]
    )
    return (
        "<!doctype html>\n"
        '<html lang="zh"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_e(title)}</title><style>{CSS}</style></head>"
        f"<body>{body}</body></html>\n"
    )


def render_site(
    projection: AtlasProjection,
    out_dir: str | Path,
    *,
    title: str = "ARAD Research Atlas",
    freshness: list[dict] | None = None,
) -> dict[str, str]:
    """写出静态站点。返回产物路径。"""
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.html"
    data = root / "atlas.json"
    index.write_text(
        render_html(projection, title=title, freshness=freshness), encoding="utf-8"
    )
    payload = projection.to_dict()
    payload["data_freshness"] = freshness or []
    data.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return {"index": str(index), "data": str(data)}
