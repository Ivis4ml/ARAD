"""把投影注入 React 应用外壳（M9.1）。

外壳由 `atlas-app/` 用 Vite 构建成**单文件** HTML（JS 与 CSS 全部内联），
构建产物复制到 `src/arad/atlas/app_shell.html` 随包分发。因此：

- 渲染时不需要 node，`arad atlas render` 在任何机器上都能跑；
- 页面不发任何网络请求，只读边界仍是物理的 —— 一个 HTML 文件写不了账本；
- 数据以 `<script type="application/json">` 注入 `<head>`，在应用脚本之前解析完成。

外壳缺失时回退到服务端渲染的静态页（`render.py`）。回退是**显式**的：
它写进产物清单，而不是悄悄给出一个看起来正常但少了演化曲线的页面。
"""

from __future__ import annotations

import json
from pathlib import Path

from .project import AtlasProjection

SHELL_PATH = Path(__file__).with_name("app_shell.html")

DATA_ELEMENT_ID = "atlas-data"


class AppShellMissing(RuntimeError):
    """React 外壳未构建。请在 `atlas-app/` 运行 `npm run build`。"""


def _escape(payload: str) -> str:
    """避免数据里的 `</script>` 提前结束脚本块。JSON 里的 `<` 转义后语义不变。"""
    return payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace(
        "\u2029", "\\u2029"
    )


def inject(shell: str, payload: dict) -> str:
    data = _escape(json.dumps(payload, ensure_ascii=False, default=str))
    tag = f'<script id="{DATA_ELEMENT_ID}" type="application/json">{data}</script>'
    if "</head>" not in shell:
        raise AppShellMissing("外壳 HTML 里没有 </head>，无法注入投影")
    return shell.replace("</head>", f"{tag}</head>", 1)


def render_app(
    projection: AtlasProjection,
    out_dir: str | Path,
    *,
    freshness: list[dict] | None = None,
    shell_path: str | Path | None = None,
) -> dict[str, str]:
    """写出注入了数据的单页应用与机器可读副本。"""
    shell_file = Path(shell_path or SHELL_PATH)
    if not shell_file.exists():
        raise AppShellMissing(
            f"找不到 React 外壳 {shell_file}；在 atlas-app/ 运行 `npm run build`，"
            "或用 `--renderer static` 退回服务端渲染"
        )
    payload = projection.to_dict()
    payload["data_freshness"] = freshness or []

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    index = root / "index.html"
    data = root / "atlas.json"
    index.write_text(inject(shell_file.read_text(encoding="utf-8"), payload), encoding="utf-8")
    data.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return {"index": str(index), "data": str(data), "renderer": "react"}
