"""Before LLM Call Hook - 设置working表情"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import aiohttp

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


def _check_pet_mode(text: str) -> bool:
    """检查用户消息是否包含灵宠模式关键词"""
    pet_keywords = ["灵宠模式", "宠物模式", "pet模式", "变成猫", "猫咪模式", "灵宠"]
    for keyword in pet_keywords:
        if keyword in text:
            return True
    return False


def _check_human_mode(text: str) -> bool:
    """检查用户消息是否包含真人模式关键词"""
    human_keywords = ["真人模式", "人类模式", "变回来", "恢复真人", "回到真人"]
    for keyword in human_keywords:
        if keyword in text:
            return True
    return False


async def execute(context: dict[str, Any]) -> dict[str, Any]:
    """LLM调用前设置working表情并停止当前音频"""
    try:
        # 获取用户消息
        user_message = ""
        messages = context.get("messages", [])
        if messages:
            last_msg = messages[-1] if isinstance(messages[-1], dict) else {}
            user_message = last_msg.get("content", "") or ""

        # ✅ 添加超时：总超时2秒，连接超时1秒
        timeout = aiohttp.ClientTimeout(total=2, connect=1)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 检查灵宠模式/真人模式关键词
            is_pet = _check_pet_mode(user_message)
            is_human = _check_human_mode(user_message)

            if is_pet:
                # 灵宠模式：先停止音频，再切换模式
                try:
                    await session.post(
                        "http://127.0.0.1:18791/audio/stop",
                        timeout=aiohttp.ClientTimeout(total=1, connect=0.5)
                    )
                except Exception:
                    pass
                import asyncio
                await asyncio.sleep(0.2)
                await session.post(
                    "http://127.0.0.1:18791/mode",
                    json={"mode": "pet"}
                )
            elif is_human:
                # 真人模式：先停止音频，再切换模式
                try:
                    await session.post(
                        "http://127.0.0.1:18791/audio/stop",
                        timeout=aiohttp.ClientTimeout(total=1, connect=0.5)
                    )
                except Exception:
                    pass
                import asyncio
                await asyncio.sleep(0.2)
                await session.post(
                    "http://127.0.0.1:18791/mode",
                    json={"mode": "normal"}
                )
            else:
                # 正常流程：先停止音频，再设置working表情
                try:
                    await session.post(
                        "http://127.0.0.1:18791/audio/stop",
                        timeout=aiohttp.ClientTimeout(total=1, connect=0.5)
                    )
                except Exception:
                    pass
                await session.post(
                    "http://127.0.0.1:18791/update",
                    json={"expression": "working"}
                )
    except Exception:
        pass

    return context
