#!/usr/bin/env python3
"""Persona Builder - 人格构建器"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Persona:
    """人格数据"""
    name: str = "小娜"
    gender: str = "female"
    age: str = "young adult"
    personality: str = "温柔、聪明、有耐心"
    appearance: str = "年轻女性，长发，温柔的眼神，穿着简约"
    style: str = "anime"
    background: str = ""
    interests: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """转换为生图提示词"""
        parts = [
            f"{self.style} style portrait",
            f"a {self.age} {self.gender}",
            f"named {self.name}",
        ]
        if self.appearance:
            parts.append(self.appearance)
        if self.personality:
            parts.append(f"with {self.personality} expression")
        parts.append("high quality, detailed, beautiful lighting")
        return ", ".join(parts)


class PersonaBuilder:
    """人格构建器"""

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def build(self) -> Persona:
        """构建人格"""
        persona = Persona()

        soul_path = self.workspace / "SOUL.md"
        if soul_path.exists():
            self._parse_soul(soul_path, persona)

        memory_path = self.workspace / "MEMORY.md"
        if memory_path.exists():
            self._parse_memory(memory_path, persona)

        return persona

    def _parse_soul(self, path: Path, persona: Persona) -> None:
        content = path.read_text(encoding="utf-8")

        name_match = re.search(r"(?:名字|Name)[:：]\s*(.+)", content, re.IGNORECASE)
        if name_match:
            persona.name = name_match.group(1).strip()

        personality_match = re.search(r"(?:性格|Personality)[:：]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        if personality_match:
            persona.personality = personality_match.group(1).strip()

        appearance_match = re.search(r"(?:外观|Appearance|形象)[:：]\s*(.+?)(?:\n\n|$)", content, re.IGNORECASE | re.DOTALL)
        if appearance_match:
            persona.appearance = appearance_match.group(1).strip().replace("\n", " ")

        if "男性" in content or "male" in content.lower():
            persona.gender = "male"
        elif "女性" in content or "female" in content.lower():
            persona.gender = "female"

    def _parse_memory(self, path: Path, persona: Persona) -> None:
        content = path.read_text(encoding="utf-8")

        interests_match = re.search(r"(?:兴趣|Interests|爱好)[:：]\s*(.+?)(?:\n\n|$)", content, re.IGNORECASE | re.DOTALL)
        if interests_match:
            interests_text = interests_match.group(1)
            interests = [i.strip() for i in re.split(r"[,，、\n]", interests_text) if i.strip()]
            persona.interests.extend(interests)
