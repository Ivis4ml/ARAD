"""脚本化 provider：让整个研究循环在不消耗任何真实调用的前提下端到端测试。

它不是玩具。循环的全部边界（盲化、预算、坏 JSON 降级、任务不丢）都要在这里
先跑通，再换成真实调用 —— 换的只是一个适配器。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import ProviderError, ProviderRequest, ProviderResponse


@dataclass
class MockProvider:
    """按角色返回脚本化输出。同一角色的多次调用依次消费脚本。"""

    scripts: dict[str, list[str]] = field(default_factory=dict)
    model_id: str = "mock"
    calls: list[ProviderRequest] = field(default_factory=list)
    fail_on_call: set[int] = field(default_factory=set)

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        self.calls.append(request)
        if len(self.calls) in self.fail_on_call:
            raise ProviderError(f"mock provider 在第 {len(self.calls)} 次调用上被要求失败")
        queue = self.scripts.get(request.role.value)
        if not queue:
            raise ProviderError(f"mock provider 没有为角色 {request.role.value!r} 准备脚本")
        text = queue.pop(0) if len(queue) > 1 else queue[0]
        return ProviderResponse(
            request_id=request.request_id,
            role=request.role,
            raw_text=text,
            model_id=self.model_id,
            output_tokens=len(text) // 4,
            attempt=len(self.calls),
        )
