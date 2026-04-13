#!/usr/bin/env python3
"""TTS Engine - 文本转语音引擎"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Optional


class TTSEngine:
    """文本转语音引擎"""

    def __init__(self, voice: str = "Ting-Ting", rate: int = 200):
        """
        初始化TTS引擎

        Args:
            voice: 语音名称（macOS系统语音）
            rate: 语速（默认200）
        """
        self.voice = voice
        self.rate = rate

    def speak(self, text: str) -> bool:
        """
        同步播放语音

        Args:
            text: 要朗读的文本

        Returns:
            是否成功
        """
        try:
            # 使用macOS的say命令
            cmd = [
                "say",
                "-v", self.voice,
                "-r", str(self.rate),
                text
            ]
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print(f"TTS播放失败: {e}")
            return False

    async def speak_async(self, text: str) -> bool:
        """
        异步播放语音

        Args:
            text: 要朗读的文本

        Returns:
            是否成功
        """
        try:
            # 使用subprocess异步执行
            cmd = [
                "say",
                "-v", self.voice,
                "-r", str(self.rate),
                text
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()
            return process.returncode == 0
        except Exception as e:
            print(f"TTS异步播放失败: {e}")
            return False

    def get_available_voices(self) -> list[str]:
        """
        获取可用的语音列表

        Returns:
            语音名称列表
        """
        try:
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                check=True
            )
            # 解析语音列表
            voices = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    # 提取语音名称（第一个字段）
                    voice_name = line.split()[0]
                    voices.append(voice_name)
            return voices
        except Exception as e:
            print(f"获取语音列表失败: {e}")
            return []

    def set_voice(self, voice: str):
        """设置语音"""
        self.voice = voice

    def set_rate(self, rate: int):
        """设置语速"""
        self.rate = rate


# 预设的中文语音
CHINESE_VOICES = {
    "Ting-Ting": "婷婷（女声，标准普通话）",
    "Mei-Jia": "美佳（女声，台湾口音）",
    "Sin-ji": "欣怡（女声，香港口音）",
}

# 预设的英文语音
ENGLISH_VOICES = {
    "Samantha": "Samantha（女声，美式英语）",
    "Alex": "Alex（男声，美式英语）",
    "Daniel": "Daniel（男声，英式英语）",
}


if __name__ == "__main__":
    # 测试TTS引擎
    tts = TTSEngine(voice="Ting-Ting", rate=200)

    print("=== 可用语音列表 ===")
    voices = tts.get_available_voices()
    for voice in voices[:10]:  # 只显示前10个
        print(f"  - {voice}")

    print("\n=== 测试语音播放 ===")
    tts.speak("你好，我是小娜，很高兴见到你！")
