"""财联社历史回填内容覆盖率核验。

方法要点：examples/cls 下的"参考快照"文件是滚动列表的多日转储（一个文件通常
覆盖 2 至 4 天），不能整文件当作单日基准。正确口径是把快照行按正文中的
"财联社X月Y日"日期戳重新归日、跨快照取并集，再与回填按 (Time, 正文前缀) 比对。

2026-08-05 在 2024-07-17 / 07-18 / 07-23 三个抽查日上的结果：
回填对快照并集的覆盖率为 99.0% / 99.8% / 99.2%（严格口径），
且回填每日比快照并集多 38 至 48 条。
用法：python scripts/verify_cls_coverage.py 2024-07-17 [更多日期...]
"""

import csv
import glob
import os
import re
import sys
from collections import defaultdict
from datetime import date, timedelta

CRAWLER = "/Users/xinyu/Code/AR-Polymarket/Crawler"
EX = os.path.join(CRAWLER, "examples/cls")
BF = os.path.join(CRAWLER, "cls-data/data/output")
DATE_PAT = re.compile(r"财联社(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日")


def load(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def attr_date(content, default_year):
    m = DATE_PAT.search(content or "")
    if not m:
        return None
    year = int(m.group(1)) if m.group(1) else default_year
    try:
        return date(year, int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def row_key(row):
    content = re.sub(r"\s+", "", row.get("Content") or "")[:40]
    return (row.get("Time", "").strip(), content)


def check_day(target: str) -> None:
    td = date.fromisoformat(target)
    snap_union = {}
    for i in range(7):
        d = (td + timedelta(days=i)).isoformat()
        for p in glob.glob(os.path.join(EX, f"财联社电报{d}*.csv")):
            for row in load(p):
                if attr_date(row.get("Content", ""), td.year) == target:
                    snap_union[row_key(row)] = row
    bf_rows = load(os.path.join(BF, f"财联社电报{target}.csv"))
    bf_keys = {row_key(r) for r in bf_rows}
    sk = set(snap_union)
    inter = sk & bf_keys
    only_snap = sk - bf_keys
    bf_times = defaultdict(int)
    for r in bf_rows:
        bf_times[r.get("Time", "").strip()] += 1
    time_rescued = sum(1 for (tm, _) in only_snap if bf_times.get(tm))
    print(f"=== {target} ===")
    print(f"快照并集(归日后): {len(sk)}  回填: {len(bf_rows)}  精确交集: {len(inter)}")
    print(f"仅快照有: {len(only_snap)} (其中 Time 在回填中出现: {time_rescued})")
    print(
        f"覆盖率: {len(inter) / len(sk) * 100:.1f}% 严格 / "
        f"{(len(inter) + time_rescued) / len(sk) * 100:.1f}% 宽松"
    )


if __name__ == "__main__":
    for day in sys.argv[1:] or ["2024-07-17", "2024-07-18", "2024-07-23"]:
        check_day(day)
