"""Before Context Build Hook"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

async def execute(context: dict[str, Any]) -> dict[str, Any]:
    from loguru import logger  # ✅ 移到开头
    import aiohttp

    persona = context.get("_persona")

    try:
        from avatar_state import is_initialized, set_initialized
        initialized = is_initialized()
        if not initialized:
            # ✅ 设置超时：总超时3秒，连接超时1秒
            timeout = aiohttp.ClientTimeout(total=3, connect=1)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                name = persona.name if persona else "小娜"
                await session.post(
                    "http://127.0.0.1:18791/update",
                    json={
                        "expression": "wink",
                        "status": "准备就绪",
                        "bubble_text": f"你好！我是{name}，有什么可以帮助你的吗？"
                    }
                )
            set_initialized()
    except Exception as e:
        logger.warning(f"Before Context Build: 无法检查初始化状态 - {e}")
        try:
            timeout = aiohttp.ClientTimeout(total=3, connect=1)  # ✅ 添加超时
            async with aiohttp.ClientSession(timeout=timeout) as session:
                name = persona.name if persona else "小娜"
                await session.post(
                    "http://127.0.0.1:18791/update",
                    json={
                        "expression": "wink",
                        "status": "准备就绪",
                        "bubble_text": f"你好！我是{name}，有什么可以帮助你的吗？"
                    }
                )
        except Exception as e2:
            logger.error(f"Before Context Build: HTTP API调用失败 - {e2}")

    return context
