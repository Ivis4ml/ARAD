"""Atlas 的只读 API（M9.5）。

用标准库的 http.server，不引任何依赖 —— 这一层的职责只是把 `runs/` 里已经落好的
JSON 端出去，没有任何值得引框架的复杂度。

三条边界与投影层一致，并且在这里是**物理**的：

1. **只读。**没有任何写入路径。GET 以外的方法一律 405；
2. **只绑本机。**默认 127.0.0.1，不接受外部连接；
3. **不越出运行目录。**run_id 与产物名都过 `_safe`，路径穿越在读取层就被挡掉。

前端两种数据源都吃：文档里有注入的 `#atlas-data` 就用它（单文件自包含，不需要服务器），
没有就走这套 API。因此这一层是增量，不是替代。
"""

from __future__ import annotations

import json
import mimetypes
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .app import SHELL_PATH
from .runs import list_runs, read_artifact

SERVER_VERSION = "0.1.0"


class AtlasHandler(BaseHTTPRequestHandler):
    """只读处理器。`runs_root` 由 partial 绑定。"""

    server_version = f"arad-atlas/{SERVER_VERSION}"
    runs_root = "runs"
    #: 实时进度直接读账本 —— 运行目录要等服务结束才写。
    ledger_path = "data/ledger/service.db"
    family = "demo_sc_price_volume"

    def log_message(self, fmt: str, *args) -> None:
        return                                        # 不往 stderr 刷访问日志

    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _shell(self) -> None:
        if not SHELL_PATH.exists():
            self._json({"error": "缺少 React 外壳；在 atlas-app/ 运行 npm run build"}, 503)
            return
        body = SHELL_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if not parts or parts == ["index.html"]:
            self._shell()
            return
        if parts[0] != "api":
            self._json({"error": "未知路径"}, 404)
            return
        if parts[1:] == ["live"]:
            # 运行中的进度。运行目录只在服务结束后写一次，因此运行期间应用里
            # 什么都看不到；账本本来就是实时写的，这里只读它投影当前状态。
            from .live import live_state

            try:
                self._json(live_state(self.ledger_path, self.family))
            except Exception as exc:                       # noqa: BLE001
                # 读不到就如实说读不到。**不要返回一个空的进度** ——
                # 把「暂时读不到」显示成「什么都没有」，与本仓库一直在修的
                # 那类错误是同一种。
                self._json({"error": f"读取账本失败：{exc}"}, 503)
            return
        if parts[1:] == ["runs"]:
            self._json(list_runs(self.runs_root))
            return
        if len(parts) >= 4 and parts[1] == "runs":
            run_id, name = parts[2], parts[3]
            payload = read_artifact(self.runs_root, run_id, name)
            if payload is None:
                self._json({"error": f"没有产物 {name!r}"}, 404)
                return
            if name == "events":
                since = int((parse_qs(parsed.query).get("since") or ["0"])[0])
                payload = [e for e in payload if int(e.get("seq", 0)) > since]
            self._json(payload)
            return
        self._json({"error": "未知路径"}, 404)

    def do_POST(self) -> None:
        # 只读投影不接受任何写入：这不是没实现，是刻意不实现
        self._json({"error": "Atlas 是只读投影，不接受写入"}, 405)


def serve(runs_root: str, *, host: str = "127.0.0.1", port: int = 8770,
          ledger_path: str = "data/ledger/service.db",
          family: str = "demo_sc_price_volume") -> None:
    mimetypes.init()
    handler = partial(_bound_handler, runs_root, ledger_path, family)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Atlas API 在 http://{host}:{port}/  （只读，只绑本机）")
    print(f"运行目录：{Path(runs_root).resolve()}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def _bound_handler(runs_root: str, ledger_path: str, family: str, *args, **kwargs):
    cls = type("BoundAtlasHandler", (AtlasHandler,),
               {"runs_root": runs_root, "ledger_path": ledger_path, "family": family})
    return cls(*args, **kwargs)
