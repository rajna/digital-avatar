"""After LLM Call Hook - 设置情感表情并播放声音"""

from __future__ import annotations

import asyncio
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import aiohttp

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

# TTS配置
TTS_VOICE = "zh-CN-XiaoxiaoNeural"  # 中文女声
TTS_OUTPUT_DIR = Path.home() / ".nanobot" / ".tts"
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 缓存已生成的语音文件
_tts_cache = {}


def _detect_emotion(text: str) -> str:
    """检测文本中的情绪，返回对应的表情名称"""
    if not text:
        return "neutral"

    # 注意：灵宠/真人模式切换由 before-llm-call hook 通过 /mode 接口处理
    # 这里不再检测模式关键词，避免把 "pet" 当作 expression 发送到 /update

    # 笑的表情符号
    laugh_emojis = ["😄", "😆", "😂", "🤣", "😊", "😁", "😃", "😀"]

    # 困惑的表情符号
    confused_emojis = ["😕", "🤔", "😟", "😰"]

    # 爱的表情符号
    love_emojis = ["❤️", "💕", "💖", "💗", "💓", "💝", "😍", "🥰", "😘","💋"]

    # 翻白眼的表情符号
    rolleyes_emojis = ["🙄", "😒"]

    # 眨眼的表情符号
    wink_emojis = ["😉", "😜"]

    # 笑的关键词
    happy_keywords = ["哈哈", "呵呵", "嘻嘻", "嘿嘿", "哈哈大笑", "笑死", "好笑", "有趣"]

    # 困惑的关键词
    confused_keywords = ["困惑", "不明白", "不懂", "奇怪", "疑惑", "搞不懂", "怎么回事", "为什么"]

    # 爱的关键词
    love_keywords = ["kiss","爱"]

    # 翻白眼的关键词
    rolleyes_keywords = ["翻白眼", "无语", "无语了","🙄"]

    # 大笑的关键词
    laugh_keywords = ["大笑", "爆笑", "笑死我了", "笑喷了", "哈哈哈哈", "笑翻了"]

    # 眨眼的关键词
    wink_keywords = ["眨眼", "wink"]

   # 假笑后翻白眼的关键词
    fakesmilerolleyes_keywords = ["假笑", "尴尬笑", "苦笑", "无奈笑"]

    # 检查表情符号
    for emoji in laugh_emojis:
        if emoji in text:
            return "happy"

    for emoji in confused_emojis:
        if emoji in text:
            return "confused"

    for emoji in love_emojis:
        if emoji in text:
            return "kiss"

    for emoji in rolleyes_emojis:
        if emoji in text:
            return "rolleyes"

    for emoji in wink_emojis:
        if emoji in text:
            return "wink"

    # 检查关键词
    for keyword in happy_keywords:
        if keyword in text:
            return "happy"

    for keyword in confused_keywords:
        if keyword in text:
            return "confused"

    for keyword in love_keywords:
        if keyword in text:
            return "kiss"

    for keyword in rolleyes_keywords:
        if keyword in text:
            return "rolleyes"

    for keyword in laugh_keywords:
        if keyword in text:
            return "laugh"

    for keyword in wink_keywords:
        if keyword in text:
            return "wink"

    for keyword in fakesmilerolleyes_keywords:
        if keyword in text:
            return "fakesmilerolleyes"

    return "neutral"


async def _play_sound(sound_text: str):
    """播放声音（已禁用，避免与on-response hook重复播放）"""
    # 音频播放功能已禁用，避免与on-response hook重复播放
    pass


def _play_audio_file(audio_path: Path):
    """播放音频文件（已禁用，避免与on-response hook重复播放）"""
    # 音频播放功能已禁用，避免与on-response hook重复播放
    pass


async def execute(context: dict[str, Any]) -> dict[str, Any]:
    """LLM 调用后 - 表情设置已禁用，避免与 on-response hook 竞争"""
    # 注意：表情设置已完全移至 on-response hook，避免两个 hook 竞争导致表情循环
    # after-llm-call hook 现在只负责情绪检测（供日志/debug使用），不发送表情更新
    
    # 获取回复内容
    response = context.get("response")
    if not response:
        return context

    ai_content = getattr(response, "content", "") or ""

    # 仅检测情绪用于调试，不发送表情更新
    emotion = _detect_emotion(ai_content)
    if emotion != "neutral":
        print(f"[DEBUG] Detected Emotion (not applied): {emotion}", file=sys.stderr)

    return context
