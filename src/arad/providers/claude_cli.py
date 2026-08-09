"""`claude -p` 适配器：把 Claude Code 的非交互模式接成 provider。

每次调用起一个独立进程，因此**上下文天然不跨角色携带** —— 角色隔离在这里
不是靠约定，而是操作系统的进程边界。

命令行参数做成可配置模板而不是写死：不同版本的 CLI 参数可能不同，
把它固化进代码等于把一个未经本机验证的假设写成事实。默认模板给出常见形态，
实际部署前应以 `--dry-run` 核对一次。
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

from .base import ProviderError, ProviderRequest, ProviderResponse

#: 默认命令模板。`{model}` 由 `model_id` 填充；prompt 走 stdin，不进命令行，
#: 避免超长 prompt 触发参数长度限制，也避免 prompt 出现在进程列表里。
#: stream-json 让输出**逐段到达**：单次调用 3 至 8 分钟，等待期间一个字都看不到
#: 是实测里最难受的一段 —— 现在把在途文本落到 INFLIGHT_PATH，app 实时展示。
DEFAULT_ARGS: tuple[str, ...] = (
    "-p", "--model", "{model}",
    "--output-format", "stream-json", "--include-partial-messages", "--verbose",
)

#: 在途输出文件。**给人看的观察窗**，不是数据通道：最终解析仍以进程完整输出为准，
#: 这个文件只被 Atlas 的 /api/live 读去展示。每次调用开始时清空，结束时删除。
INFLIGHT_PATH = "data/ledger/inflight_proposer.txt"


@dataclass
class ClaudeCliProvider:
    """通过子进程调用 `claude -p`。prompt 从 stdin 送入。"""

    model_id: str = "claude-opus-5"
    executable: str = "claude"
    extra_args: tuple[str, ...] = DEFAULT_ARGS
    timeout_seconds: int = 900
    env: dict[str, str] | None = None
    dry_run: bool = False
    calls: list[ProviderRequest] = field(default_factory=list)

    def command(self) -> list[str]:
        return [self.executable, *(a.format(model=self.model_id) for a in self.extra_args)]

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        if self.dry_run:
            return ProviderResponse(
                request_id=request.request_id,
                role=request.role,
                raw_text="",
                model_id=self.model_id,
                meta={"dry_run": True, "command": self.command(),
                      "prompt_chars": len(request.prompt)},
            )
        if not self.available():
            raise ProviderError(f"找不到可执行文件 {self.executable!r}")
        raw_text, meta = self._run_streaming(request.prompt)
        return ProviderResponse(
            request_id=request.request_id,
            role=request.role,
            raw_text=raw_text,
            model_id=self.model_id,
            output_tokens=len(raw_text) // 4,
            meta={"command": self.command(), **meta},
        )


    def _run_streaming(self, prompt: str) -> tuple[str, dict]:
        """跑子进程并把文本增量落到 INFLIGHT_PATH。

        stream-json 每行一个事件；文本增量在 content_block_delta 的 text_delta 里，
        最终完整文本在 type == "result" 的 result 字段。**解析以 result 事件为准**，
        增量拼接只作兜底 —— 观察窗坏了不能影响研究本身。
        """
        import json as _json
        import os
        import os as _os
        import pty as _pty
        import time

        inflight = Path(INFLIGHT_PATH)
        inflight.parent.mkdir(parents=True, exist_ok=True)
        inflight.write_text("", encoding="utf-8")
        # stdout 走**伪终端**而不是管道：CLI 检测到管道会按块缓冲（约 8KB），
        # 事件攒在它的缓冲区里不吐 —— 实测同一进程里一次调用流畅（2162 字），
        # 下一次 195 秒零字节。pty 让它以为在跟终端说话，恢复行刷新。
        master, slave = _pty.openpty()
        proc = subprocess.Popen(
            self.command(), stdin=subprocess.PIPE, stdout=slave,
            stderr=subprocess.PIPE, text=False, env=self.env,
        )
        _os.close(slave)
        deadline = time.monotonic() + self.timeout_seconds
        pieces: list[str] = []
        result_text: str | None = None

        def _lines():
            import select as _select

            buf = b""
            while True:
                # 阻塞读会让超时失效：CLI 思考阶段一个字节都不发时，
                # os.read 永远等待，deadline 检查根本轮不到执行 ——
                # 实测 run21 挂死 103 分钟而 1800s 超时从未触发。
                # select 以 5s 为拍轮询：无数据也回来查一次表。
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    proc.kill()
                    raise ProviderError(
                        f"{self.executable} 在 {self.timeout_seconds}s 内未返回；"
                        "任务交由队列重排"
                    )
                ready, _, _ = _select.select([master], [], [], min(5.0, remaining))
                if not ready:
                    if proc.poll() is not None:
                        chunk = b""      # 进程已退出且无残留输出
                    else:
                        continue         # 还在跑，只是没输出：回去查表
                else:
                    try:
                        chunk = _os.read(master, 65536)
                    except OSError:      # pty 关闭（进程结束）
                        chunk = b""
                if not chunk:
                    if buf.strip():
                        yield buf.decode("utf-8", errors="replace")
                    return
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    yield raw.decode("utf-8", errors="replace")

        try:
            assert proc.stdin is not None
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
            with inflight.open("a", encoding="utf-8") as sink:
                for line in _lines():
                    line = line.strip().rstrip("\r")
                    if not line:
                        continue
                    try:
                        event = _json.loads(line)
                    except ValueError:
                        continue
                    if event.get("type") == "stream_event":
                        delta = (event.get("event") or {}).get("delta") or {}
                        # 思考与正文都进观察窗：推理主体在 thinking_delta 里，
                        # 只捕 text_delta 会在扩展思考阶段显示 0 字
                        #（实测一次调用思考了 11 分钟，窗口全程空白）。
                        # 兜底拼接（pieces）只收正文 —— 它可能被当作最终输出解析，
                        # 思考文字混进去会污染 JSON。
                        if delta.get("type") == "thinking_delta":
                            sink.write(delta.get("thinking", ""))
                            sink.flush()
                        elif delta.get("type") == "text_delta":
                            piece = delta.get("text", "")
                            pieces.append(piece)
                            sink.write(piece)
                            sink.flush()
                    elif event.get("type") == "result":
                        result_text = event.get("result")
            proc.wait(timeout=30)
        finally:
            with contextlib_suppress():
                _os.close(master)
            with contextlib_suppress():
                os.remove(inflight)
        if proc.returncode not in (0, None):
            stderr = (proc.stderr.read() if proc.stderr else "").strip()[:400]
            raise ProviderError(f"{self.executable} 退出码 {proc.returncode}：{stderr}")
        text = result_text if result_text is not None else "".join(pieces)
        if not text.strip():
            raise ProviderError(f"{self.executable} 返回空输出")
        return text, {"streamed_chars": sum(len(x) for x in pieces)}


from contextlib import suppress as _suppress
from pathlib import Path


def contextlib_suppress():
    return _suppress(FileNotFoundError)
