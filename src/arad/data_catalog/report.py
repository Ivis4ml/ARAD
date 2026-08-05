"""从 SourceManifest 生成人类可读审计报告。"""

from __future__ import annotations

from .schema import SourceManifest


def render(manifests: list[SourceManifest]) -> str:
    lines: list[str] = ["# ARAD 数据源审计报告（M1）", ""]
    for m in manifests:
        lines += [f"## {m.source_id}", ""]
        lines += [f"- 根路径：`{m.root_uri}`"]
        lines += [f"- 指纹：`{m.fingerprint[:16]}…`  生成于 {m.generated_at}"]
        if m.source_snapshot:
            lines += [
                f"- 内容身份：`{m.source_snapshot.method}` = `{m.source_snapshot.digest[:16]}…`",
                f"  - 保证等级：{m.source_snapshot.guarantee}",
            ]
        for k, v in m.facts.items():
            if isinstance(v, list) and len(v) > 12:
                v = f"[{len(v)} items]"
            lines += [f"- {k}: {v}"]
        banned = sorted(m.banned_fields())
        if banned:
            lines += [f"- **禁用字段**：{', '.join(banned)}"]
        lines += ["", "| 严重度 | 代码 | 说明 |", "|---|---|---|"]
        for f in m.findings:
            lines += [f"| {f.severity.value} | `{f.code}` | {f.message} |"]
        lines += [""]
        lines += [
            f"质量闸门：{'通过' if m.gate_passed() else '**未通过（存在 error 级发现，Study 只能 blocked）**'}",
            "",
        ]
    return "\n".join(lines)
