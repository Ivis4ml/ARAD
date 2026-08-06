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

#: 默认命令模板。`{model}` 与 `{effort}` 由配置填充；prompt 走 stdin，不进命令行，
#: 避免超长 prompt 触发参数长度限制，也避免 prompt 出现在进程列表里。
DEFAULT_ARGS: tuple[str, ...] = ("-p",)


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
        return [self.executable, *self.extra_args]

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
        try:
            completed = subprocess.run(
                self.command(),
                input=request.prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=self.env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                f"{self.executable} 在 {self.timeout_seconds}s 内未返回；任务交由队列重排"
            ) from exc
        if completed.returncode != 0:
            raise ProviderError(
                f"{self.executable} 退出码 {completed.returncode}："
                f"{completed.stderr.strip()[:400]}"
            )
        if not completed.stdout.strip():
            raise ProviderError(f"{self.executable} 返回空输出")
        return ProviderResponse(
            request_id=request.request_id,
            role=request.role,
            raw_text=completed.stdout,
            model_id=self.model_id,
            output_tokens=len(completed.stdout) // 4,
            meta={"command": self.command()},
        )
