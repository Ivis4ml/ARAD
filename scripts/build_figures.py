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


if __name__ == "__main__":
    main()
