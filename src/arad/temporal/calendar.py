"""交易日历。

日历只从归档实测的交易日集合构造，不从自然日推断。夜盘归属完全依赖
"前一交易日"，因此日历一旦缺一天，其后所有夜盘的自然日都会静默错位；
本模块用显式边界异常和缺口检查替代静默猜测。
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import zipfile
from bisect import bisect_left
from datetime import date, timedelta

from ..data_catalog.schema import QualityFinding, Severity
from .errors import CalendarBoundaryError

_DAY_RE = re.compile(r"(20\d{6})")


def _decode_name(info: zipfile.ZipInfo) -> str:
    if info.flag_bits & 0x800:
        return info.filename
    try:
        return info.filename.encode("cp437").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return info.filename


class TradingCalendar:
    """有序、去重的交易日序列。"""

    def __init__(self, days: list[date], *, source: str):
        self._days = sorted(set(days))
        self.source = source

    # ------------------------------------------------------------ 构造

    @classmethod
    def from_archive(cls, root: str, layouts: list[str]) -> TradingCalendar:
        """只读 zip 中央目录，提取归档中出现过的全部交易日。不解压任何数据。"""
        zip_paths: list[str] = []
        for pat in layouts:
            zip_paths.extend(glob.glob(os.path.join(root, pat)))
        days: set[date] = set()
        for zp in sorted(set(zip_paths)):
            try:
                with zipfile.ZipFile(zp) as zf:
                    infos = zf.infolist()
            except zipfile.BadZipFile:
                continue
            for info in infos:
                if info.is_dir():
                    continue
                name = _decode_name(info)
                for cand in _DAY_RE.findall(name):
                    if len(cand) == 8:
                        days.add(date(int(cand[:4]), int(cand[4:6]), int(cand[6:])))
                        break
        return cls(sorted(days), source=f"archive:{root}")

    @classmethod
    def from_yyyymmdd(cls, days: list[int | str], *, source: str) -> TradingCalendar:
        out = []
        for d in days:
            s = str(d)
            out.append(date(int(s[:4]), int(s[4:6]), int(s[6:])))
        return cls(out, source=source)

    # ------------------------------------------------------------ 查询

    @property
    def days(self) -> list[date]:
        return list(self._days)

    def __len__(self) -> int:
        return len(self._days)

    def __contains__(self, day: date) -> bool:
        i = bisect_left(self._days, day)
        return i < len(self._days) and self._days[i] == day

    def _index(self, day: date) -> int:
        i = bisect_left(self._days, day)
        if i >= len(self._days) or self._days[i] != day:
            raise CalendarBoundaryError(f"{day.isoformat()} 不在交易日历中（来源 {self.source}）")
        return i

    def prev(self, day: date) -> date:
        i = self._index(day)
        if i == 0:
            raise CalendarBoundaryError(
                f"{day.isoformat()} 是日历的首个交易日，没有前一交易日可用；"
                "夜盘归属需要前一交易日，拒绝以自然日猜测"
            )
        return self._days[i - 1]

    def prev_or_none(self, day: date) -> date | None:
        try:
            return self.prev(day)
        except CalendarBoundaryError:
            return None

    def next(self, day: date) -> date:
        i = self._index(day)
        if i + 1 >= len(self._days):
            raise CalendarBoundaryError(f"{day.isoformat()} 是日历的最后一个交易日")
        return self._days[i + 1]

    # ------------------------------------------------------------ 质量检查

    def night_gap_findings(self, days_with_night: set[date]) -> list[QualityFinding]:
        """夜盘存在，意味着前一交易日晚间开市。

        若前一交易日与当日之间跨越了非周末的长间隔（通常是长假，交易所会停夜盘），
        很可能是归档缺日导致夜盘被错误归到了更早的自然日；一律报告，不静默通过。
        """
        findings: list[QualityFinding] = []
        for day in sorted(days_with_night):
            prev = self.prev_or_none(day)
            if prev is None:
                continue
            gap = (day - prev).days
            if gap == 1 or (gap == 3 and prev.weekday() == 4):
                continue
            findings.append(
                QualityFinding(
                    severity=Severity.WARNING,
                    code="calendar.night_session_across_unexplained_gap",
                    message=(
                        "该交易日存在夜盘，但与前一交易日的间隔既非相邻日也非周末；"
                        "需确认归档是否缺日或该日确有夜盘"
                    ),
                    evidence={
                        "trading_day": day.isoformat(),
                        "prev_trading_day": prev.isoformat(),
                        "gap_days": gap,
                    },
                )
            )
        return findings

    def natural_gaps(self) -> list[tuple[date, date, int]]:
        """相邻交易日之间的自然日间隔（用于人工审计长假与停市）。"""
        out = []
        for a, b in zip(self._days, self._days[1:]):
            gap = (b - a).days
            if gap > 1:
                out.append((a, b, gap))
        return out

    def weekday_span(self, start: date, end: date) -> int:
        """区间内的工作日数量，用于估计缺失交易日规模。"""
        n, cur = 0, start
        while cur <= end:
            if cur.weekday() < 5:
                n += 1
            cur += timedelta(days=1)
        return n

    @property
    def fingerprint(self) -> str:
        blob = ",".join(d.isoformat() for d in self._days)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def facts(self) -> dict:
        return {
            "source": self.source,
            "trading_days": len(self._days),
            "first_day": self._days[0].strftime("%Y%m%d") if self._days else None,
            "last_day": self._days[-1].strftime("%Y%m%d") if self._days else None,
            "fingerprint": self.fingerprint,
        }
