"""Before Context Build Hook - 优化版本"""

from __future__ import annotations
import sys
import asyncio
import aiohttp
from pathlib import Path
from typing import Any

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

async def execute(context: dict[str, Any]) -> dict[str, Any]:
    from loguru import logger

    persona = context.get("_persona")

    try:
        from avatar_state import is_initialized, set_initialized
        
        # 快速检查初始化状态
        initialized = is_initialized()
        if not initialized:
            logger.info("开始初始化数字人状态...")
            
            # 创建超时会话
            timeout = aiohttp.ClientTimeout(total=2, connect=1)
            
            # 使用更简单的请求，只更新必要的状态
            async with aiohttp.ClientSession(timeout=timeout) as session:
                name = persona.name if persona else "火灵"
                
                # 分步骤更新，避免复杂请求
                try:
                    # 1. 先只更新状态文本（快速）
                    await session.post(
                        "http://127.0.0.1:18791/update",
                        json={"status": "准备就绪"},
                        timeout=aiohttp.ClientTimeout(total=1)
                    )
                    
                    # 2. 再更新对话气泡（快速）
                    await session.post(
                        "http://127.0.0.1:18791/update", 
                        json={"bubble_text": f"你好！我是{name}，有什么可以帮助你的吗？"},
                        timeout=aiohttp.ClientTimeout(total=1)
                    )
                    
                    # 3. 最后更新表情（可能较慢，但不阻塞响应）
                    asyncio.create_task(
                        safe_update_expression(session, "wink", name)
                    )
                    
                except Exception as e:
                    logger.warning(f"部分更新失败，但不影响初始化: {e}")
            
            # 标记为已初始化，避免重复调用
            set_initialized()
            logger.info("数字人状态初始化完成")
            
    except Exception as e:
        logger.warning(f"Before Context Build: 初始化过程中出现警告 - {e}")
        # 不抛出异常，避免影响正常流程

    return context

async def safe_update_expression(session, expression: str, name: str):
    from loguru import logger
    """安全地更新表情，不阻塞主流程"""
    try:
        await session.post(
            "http://127.0.0.1:18791/update",
            json={"expression": expression},
            timeout=aiohttp.ClientTimeout(total=3)
        )
        logger.info(f"表情更新成功: {expression}")
    except asyncio.TimeoutError:
        logger.warning(f"表情更新超时: {expression}")
    except Exception as e:
        logger.warning(f"表情更新失败: {expression} - {e}")