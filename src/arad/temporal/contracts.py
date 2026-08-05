"""合约代码解析。

四位年月码（`sc2608`）直接解析。郑商所的三位年码（`MA608`）缺少世纪与十位年，
必须结合交易日才能还原；没有交易日时拒绝解析，不按"最近的合理月份"猜测。
本票范围只涉及 SC，三位码路径保留但不在 SC 上使用。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

_FOUR = re.compile(r"^([A-Za-z]{1,2})(\d{4})$")
_THREE = re.compile(r"^([A-Za-z]{1,2})(\d{3})$")


@dataclass(frozen=True)
class ContractCode:
    raw: str
    product: str
    delivery_year: int
    delivery_month: int

    @property
    def delivery_key(self) -> int:
        return self.delivery_year * 100 + self.delivery_month

    @classmethod
    def parse(cls, code: str, *, trading_day: date | None = None) -> ContractCode:
        m = _FOUR.match(code)
        if m:
            product, digits = m.group(1), m.group(2)
            year = 2000 + int(digits[:2])
            month = int(digits[2:])
            if not 1 <= month <= 12:
                raise ValueError(f"合约 {code!r} 的交割月 {month} 非法")
            return cls(raw=code, product=product, delivery_year=year, delivery_month=month)
        m = _THREE.match(code)
        if m:
            if trading_day is None:
                raise ValueError(
                    f"合约 {code!r} 使用三位年码，缺少交易日无法还原世纪与十位年；拒绝猜测"
                )
            product, digits = m.group(1), m.group(2)
            month = int(digits[1:])
            if not 1 <= month <= 12:
                raise ValueError(f"合约 {code!r} 的交割月 {month} 非法")
            decade = trading_day.year // 10 * 10
            year = decade + int(digits[0])
            if year < trading_day.year:  # 三位码只向前滚动
                year += 10
            return cls(raw=code, product=product, delivery_year=year, delivery_month=month)
        raise ValueError(f"无法解析的合约代码 {code!r}")
