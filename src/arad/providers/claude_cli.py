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
        import time

        inflight = Path(INFLIGHT_PATH)
        inflight.parent.mkdir(parents=True, exist_ok=True)
        inflight.write_text("", encoding="utf-8")
        proc = subprocess.Popen(
            self.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=self.env,
        )
        deadline = time.monotonic() + self.timeout_seconds
        pieces: list[str] = []
        result_text: str | None = None
        try:
            assert proc.stdin is not None and proc.stdout is not None
            proc.stdin.write(prompt)
            proc.stdin.close()
            with inflight.open("a", encoding="utf-8") as sink:
                for line in proc.stdout:
                    if time.monotonic() > deadline:
                        proc.kill()
                        raise ProviderError(
                            f"{self.executable} 在 {self.timeout_seconds}s 内未返回；"
                            "任务交由队列重排"
                        )
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = _json.loads(line)
                    except ValueError:
                        continue
                    if event.get("type") == "stream_event":
                        delta = (event.get("event") or {}).get("delta") or {}
                        if delta.get("type") == "text_delta":
                            piece = delta.get("text", "")
                            pieces.append(piece)
                            sink.write(piece)
                            sink.flush()
                    elif event.get("type") == "result":
                        result_text = event.get("result")
            proc.wait(timeout=30)
        finally:
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
