"""研究员的方法说明（skill）：显式装载、经闸门、内容寻址（M17）。

为什么不用 Claude Code 自带的 skill 发现机制（`.claude/skills/` 目录）：
那是一条**环境通道** —— 任何人往目录里放一个文件，研究员的上下文就变了，
而账本对此一无所知，盲化断言也扫不到它。本项目的全部价值建立在
「研究员看到过什么是可核对的」之上，因此方法说明必须走与 prompt 同一条路：
读成字符串 → 过 `assert_blinded` → 算内容指纹 → 作为 `ProviderRequest.system_prompt`
的一部分发出 → 指纹进账本。

同理，`claude -p` 的调用参数里关掉了 skill 发现、MCP 与全部设置来源
（见 providers/claude_cli.py 的 DEFAULT_ARGS）。研究员进程的上下文因此只有两段文本，
两段都在这里被检查过。

**更新规则**：本文件承载的教训只能来自机械失败（解析失败、schema 不合、
事前功效筛拦下、语义审计判不一致），它们全部发生在读取结果之前。
任何来自判决的教训都不得写入 —— 那会让方法说明变成结果回流的通道（决定 0006）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..memory.ledger import content_id
from ..providers.base import Role, assert_blinded

SKILL_DIR = Path("configs/skills")

#: 本文件本身也要被审：更新规则写在 skill 的 frontmatter 里，
#: 装载时核对，避免有人把它改成结果通道而无人察觉。
REQUIRED_UPDATE_RULE = "mechanical_failures_only"


class SkillError(RuntimeError):
    """方法说明不合法。宁可不发，也不发一份来路不明的说明。"""


@dataclass(frozen=True)
class Skill:
    skill_id: str
    version: int
    role: str
    body: str

    @property
    def content_id(self) -> str:
        return content_id({
            "skill_id": self.skill_id,
            "version": self.version,
            "role": self.role,
            "body": self.body,
        })

    def describe(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "role": self.role,
            "content_id": self.content_id,
            "chars": len(self.body),
        }


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise SkillError("方法说明必须以 frontmatter 起始（skill_id/version/role/update_rule）")
    _, block, body = text.split("---", 2)
    meta: dict = {}
    for line in block.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def load_skill(skill_id: str, *, role: Role = Role.PROPOSER,
               skill_dir: str | Path = SKILL_DIR) -> Skill:
    """读一份方法说明并过盲化闸门。任何一步不合规都拒绝装载。"""
    path = Path(skill_dir) / f"{skill_id}.md"
    if not path.exists():
        raise SkillError(f"找不到方法说明 {path}")
    meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
    for key in ("skill_id", "version", "role", "update_rule"):
        if key not in meta:
            raise SkillError(f"{path} 的 frontmatter 缺 {key}")
    if meta["skill_id"] != skill_id:
        raise SkillError(f"{path} 声明的 skill_id 是 {meta['skill_id']!r}，与文件名不符")
    if meta["update_rule"] != REQUIRED_UPDATE_RULE:
        raise SkillError(
            f"{path} 的 update_rule 是 {meta['update_rule']!r}；"
            f"只接受 {REQUIRED_UPDATE_RULE!r} —— 方法说明不得承载来自判决的教训"
        )
    if not re.fullmatch(r"\d+", meta["version"]):
        raise SkillError(f"{path} 的 version 必须是整数")
    # 装载即检查：这份文本会原样进模型上下文，与 prompt 同等对待。
    assert_blinded(body, role)
    return Skill(skill_id=skill_id, version=int(meta["version"]),
                 role=meta["role"], body=body)


def render_system_prompt(skill: Skill) -> str:
    """方法说明 → system_prompt 文本。

    刻意不加任何「你很擅长」之类的角色渲染：研究员的行为应由方法与契约决定，
    不由语气决定。开头一句声明来源与版本，便于在响应里追认。
    """
    return (
        f"[ARAD 方法说明 {skill.skill_id} v{skill.version} "
        f"content_id={skill.content_id[:12]}]\n\n{skill.body}"
    )
