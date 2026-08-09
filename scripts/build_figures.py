"""为每一条有冻结规格的 Study 画「信号 × 标的价格」双轴图。

设计约束与报告脚本相同：图上的一切都从账本与 spine 派生。信号序列不是回放
存下的数字，而是**用冻结规格在 SC 的 discovery 决策网格上重新求值**得到 ——
这本身就是一次可复现性检验：规格是完备的，不需要当时的进程状态。

面板 universe 的 Study 也画在 SC 网格上（以 SC 为代表），图题注明。
输出：docs/reports/figures/<study_id>.png 与 figures/index.json。
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from arad.harness import demo
from arad.memory.ledger import EvidenceLedger, Role

OUT = Path("docs/reports/figures")

#: 中文字体：报告与 app 同一字体家族
for name in ("PingFang SC", "Hiragino Sans GB", "Arial Unicode MS"):
    if any(name in f.name for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = [name]
        break
plt.rcParams["axes.unicode_minus"] = False

SIGNAL = "#3c5488"   # 参照报告的正文蓝
PRICE = "#b93c28"    # 砖红：与判决色域不冲突


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with EvidenceLedger("data/ledger/service.db") as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))

        studies: dict[str, dict] = {}
        for e in events:
            sid = e.get("study_id")
            if not sid:
                continue
            st = studies.setdefault(sid, {"study_id": sid})
            p = e["payload"]
            if e["event_type"] == "feature_spec_locked":
                st["feature_id"] = p.get("feature_id")
            elif e["event_type"] == "proposal_locked":
                st["universe"] = p.get("universe")
                st["target"] = p.get("target")
            elif e["event_type"] == "evaluation_result":
                eff = p.get("effects") or {}
                st["t"] = eff.get("t_stat")
            elif e["event_type"] == "verdict_recorded":
                st["verdict"] = p.get("verdict")

        rows, sc, _visible = demo._load_sc(
            demo._product_target_path("sc", "sc_rv_next_session"), "discovery")
        # 价格：ret 目标表的 exit_price（该时段收盘）。_read_target 做了列投影，
        # 不含价格列，因此这里用 pyarrow 直读并按 (contract, trading_day, session) 对齐。
        import pyarrow.parquet as pq
        rt = pq.read_table(
            demo._product_target_path("sc", "sc_ret_next_session"),
            columns=["contract", "trading_day", "session_name",
                     "sample_segment", "exit_price"])
        price_by_key = {
            (c, d, sn): x
            for c, d, sn, seg, x in zip(
                rt.column("contract").to_pylist(),
                rt.column("trading_day").to_pylist(),
                rt.column("session_name").to_pylist(),
                rt.column("sample_segment").to_pylist(),
                rt.column("exit_price").to_pylist())
            if seg == "discovery" and x is not None
        }
        times = [r["decision_time"] for r in rows]
        prices = [price_by_key.get(
            (r["contract"], r["trading_day"], r["session_name"])) for r in rows]
        hit = sum(1 for x in prices if x is not None)
        assert hit > len(rows) * 0.8, f"价格对齐率过低：{hit}/{len(rows)}"

        wanted = {st["feature_id"]: sid for sid, st in studies.items()
                  if st.get("feature_id")}
        signals = demo._signal_values(ledger, sc, rows, list(wanted))

    index: dict[str, dict] = {}
    for fid, values in signals.items():
        sid = wanted[fid]
        st = studies[sid]
        fig, ax = plt.subplots(figsize=(6.4, 2.5), dpi=200)
        ax2 = ax.twinx()
        ax2.plot(times, prices, color=PRICE, lw=0.9, alpha=0.85, label="SC 收盘价")
        ax.plot(times, values, color=SIGNAL, lw=0.9, label="信号")
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
        t = st.get("t")
        ttxt = f"t={t:+.2f}" if isinstance(t, (int, float)) else "未评价"
        ax.set_title(f"{sid} · {ttxt} · {st.get('verdict') or '—'}",
                     fontsize=8.5, loc="left")
        ax.tick_params(labelsize=6.5)
        ax2.tick_params(labelsize=6.5, colors=PRICE)
        ax.tick_params(colors=SIGNAL)
        for spine in ("top",):
            ax.spines[spine].set_visible(False)
            ax2.spines[spine].set_visible(False)
        ax.margins(x=0.01)
        # x 轴太密：只留 5 个刻度
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
        fig.autofmt_xdate(rotation=0, ha="center")
        fig.tight_layout(pad=0.4)
        out = OUT / f"{sid}.png"
        fig.savefig(out)
        plt.close(fig)
        defined = sum(1 for v in values if not math.isnan(v))
        index[sid] = {"file": out.name, "feature_id": fid,
                      "defined_points": defined, "total_points": len(values)}
        print(f"{sid}: {defined}/{len(values)} 点有定义", flush=True)

    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"共 {len(index)} 张图 → {OUT}")




def hillclimb_baseline() -> None:
    """旧系统（Alpha-Data 时代）的爬山基线：为什么上升的曲线不是证据。

    三个数字的出处都有合同测试钉着（tests/contracts/test_selection.py:28-37）：
    81 次爬山、试验间 Sharpe 标准差 0.06758419676972037、
    实测最好年化 Sharpe 2.40；零假设下同样搜索的期望是
    expected_max_sharpe(81, sd) * sqrt(252) = 2.6345。
    曲线用与判决同一套公式画出 —— 不是示意，是可复现的计算。
    """
    from arad.evaluation.selection import expected_max_sharpe

    SD = 0.06758419676972037
    ANN = 252 ** 0.5
    ns = list(range(2, 82))
    null_curve = [expected_max_sharpe(k, SD) * ANN for k in ns]
    best = 2.40

    fig, ax = plt.subplots(figsize=(6.4, 2.9), dpi=200)
    ax.plot(ns, null_curve, color=PRICE, lw=1.4,
            label="零假设期望 E[max Sharpe]（同一搜索过程、纯噪声）")
    ax.axhline(best, color=SIGNAL, lw=1.4, ls="--",
               label="实测最好（81 次爬山选出）= 2.40")
    cross = next((k for k, v in zip(ns, null_curve) if v > best), None)
    if cross:
        ax.axvline(cross, color="#8a8f98", lw=0.8, ls=":")
        ax.annotate(f"n={cross} 起，噪声期望即超过实测最好",
                    xy=(cross, best), xytext=(cross + 3, best - 0.55),
                    fontsize=7.5, color="#374151",
                    arrowprops={"arrowstyle": "->", "lw": 0.7, "color": "#8a8f98"})
    ax.set_xlabel("搜索次数 n", fontsize=8)
    ax.set_ylabel("年化 Sharpe", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "hillclimb_baseline.png")
    plt.close(fig)
    print("hillclimb_baseline.png 完成")




def arad_search_curve() -> None:
    """ARAD 自己的爬山曲线：逐次检验的 |t| 对同步抬升的零假设地板。

    与 hillclimb_baseline（旧系统的教训）成对：旧图说明为什么要有地板，
    本图展示带着地板搜索七个月账本的全貌 —— 基线假象越过地板（按决定 0002
    归 Baseline Control，不计入另类清单）；残差化的另类构造中，第一条越过
    地板的是 run16-study-3（成本模型建成后按失效表即为 candidate 形态）。
    """
    import sys as _sys

    _sys.path.insert(0, "src")
    from arad.evaluation.selection import expected_max_abs_z
    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger("data/ledger/service.db") as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))
    specs: dict[str, dict] = {}
    pts = []          # (n_at, abs_t, group, study_id)
    n_reads = 0
    for e in events:
        sid = e.get("study_id")
        if e["event_type"] == "outcome_read":
            n_reads += 1
        if not sid:
            continue
        if e["event_type"] == "feature_spec_locked":
            st = e["payload"]
            specs[sid] = {
                "srcs": {x.get("source") for x in st.get("steps", []) if x.get("source")},
                "resid": any(x.get("controls") for x in st.get("steps", [])),
            }
        elif e["event_type"] == "evaluation_result":
            t = (e["payload"].get("effects") or {}).get("t_stat")
            if not isinstance(t, (int, float)) or math.isnan(t):
                continue
            # 族归属按运行前缀：B9 时代评价载荷的族标签写死为旧族，不可靠
            if sid.split("-study-")[0] in ("run23", "run24"):
                continue          # 事件族另有一张图，n 计数也各自独立
            sp = specs.get(sid, {})
            if "commodity_bar" in sp.get("srcs", set()) and "pm_market" not in sp.get("srcs", set()):
                grp = "baseline"
            elif sp.get("resid"):
                grp = "pm_resid"
            else:
                grp = "pm_plain"
            pts.append((n_reads, abs(t), grp, sid))

    n_max = max(n for n, *_ in pts)
    xs = list(range(1, n_max + 1))
    floor = [expected_max_abs_z(k) for k in xs]

    fig, ax = plt.subplots(figsize=(6.6, 3.2), dpi=200)
    ax.plot(xs, floor, color=PRICE, lw=1.5, ls="--",
            label="零假设地板 E[max|z|]（随已读 outcome 次数抬升）")
    STYLE = {
        "baseline": ("#8a8f98", "量价构造（Baseline Control，不计入另类清单）"),
        "pm_plain": ("#b7c3d6", "Polymarket 构造（未残差化）"),
        "pm_resid": (SIGNAL, "Polymarket 构造（已残差化）"),
    }
    seen = set()
    for n, t, grp, sid in pts:
        c, lbl = STYLE[grp]
        ax.scatter([n], [min(t, 6.0)], s=16 if grp != "pm_resid" else 24,
                   color=c, zorder=3,
                   marker="^" if t > 6.0 else "o",
                   label=lbl if grp not in seen else None)
        seen.add(grp)
    hero = next((x for x in pts if x[3] == "run16-study-3"), None)
    if hero:
        n, t, *_ = hero
        ax.annotate("run16-study-3\n|t|=4.39，地板 2.60\n首个越过地板的残差化另类构造",
                    xy=(n, t), xytext=(n - 26, t + 0.7), fontsize=7,
                    color="#1c1c1e",
                    arrowprops={"arrowstyle": "->", "lw": 0.8, "color": SIGNAL})
        ax.scatter([n], [t], s=70, facecolors="none", edgecolors=SIGNAL,
                   linewidths=1.6, zorder=4)
    ax.set_xlabel("已读 outcome 次数 n（统计分母）", fontsize=8)
    ax.set_ylabel("|t|（超过 6 截顶为 ▲）", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.4, frameon=False, loc="upper left")
    for spx in ("top", "right"):
        ax.spines[spx].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "arad_search_curve.png")
    plt.close(fig)
    print("arad_search_curve.png 完成")




def event_search_curve() -> None:
    """事件条件族（决定 0008）自己的搜索曲线：分母独立、地板从头起。"""
    import sys as _sys

    _sys.path.insert(0, "src")
    from arad.evaluation.selection import expected_max_abs_z
    from arad.memory.ledger import EvidenceLedger, Role

    with EvidenceLedger("data/ledger/service.db") as ledger:
        events = list(ledger.read_events(role=Role.HUMAN))
    pts = []
    n = 0
    for e in events:
        sid = e.get("study_id") or ""
        if sid.split("-study-")[0] not in ("run23", "run24"):
            continue
        if e["event_type"] == "outcome_read":
            n += 1
        elif e["event_type"] == "evaluation_result":
            t = (e["payload"].get("effects") or {}).get("t_stat")
            if isinstance(t, (int, float)) and not math.isnan(t):
                pts.append((n, abs(t), sid))
    if not pts:
        return
    n_max = max(x for x, *_ in pts)
    xs = list(range(1, n_max + 1))
    fig, ax = plt.subplots(figsize=(6.4, 2.8), dpi=200)
    ax.plot(xs, [expected_max_abs_z(k) for k in xs], color=PRICE, lw=1.5, ls="--",
            label="零假设地板（本族独立分母）")
    ax.scatter([x for x, *_ in pts], [t for _, t, _ in pts], s=22, color=SIGNAL,
               zorder=3, label="事件条件构造（每点一条 Study）")
    ax.set_xlabel("本族已读 outcome 次数 n", fontsize=8)
    ax.set_ylabel("|t|", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.6, frameon=False, loc="upper left")
    for spx in ("top", "right"):
        ax.spines[spx].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "event_search_curve.png")
    plt.close(fig)
    print("event_search_curve.png 完成")


if __name__ == "__main__":
    main()
    hillclimb_baseline()
    arad_search_curve()
    event_search_curve()
