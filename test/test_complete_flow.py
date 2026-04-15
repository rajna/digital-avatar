#!/usr/bin/env python3
"""测试完整的表情流程：working -> speaking -> auto-reset -> neutral"""

import asyncio
import aiohttp
import time
from loguru import logger


async def test_complete_flow():
    """测试完整的表情流程"""
    base_url = "http://localhost:18791"

    async with aiohttp.ClientSession() as session:
        # 1. 设置为 working 状态
        logger.info("步骤1: 设置为 working 状态")
        async with session.post(f"{base_url}/update", json={"expression": "working"}) as resp:
            result = await resp.json()
            logger.info(f"响应: {result}")

        await asyncio.sleep(2)

        # 2. 设置为 speaking 状态（带5秒自动重置）
        logger.info("步骤2: 设置为 speaking 状态（带5秒自动重置）")
        async with session.post(f"{base_url}/update", json={"expression": "speaking", "duration": 5}) as resp:
            result = await resp.json()
            logger.info(f"响应: {result}")

        # 3. 等待speaking任务完成
        logger.info("步骤3: 等待speaking任务完成...")
        await asyncio.sleep(3)

        # 4. 检查队列状态
        logger.info("步骤4: 检查队列状态")
        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            logger.info(f"队列状态: {queue_status}")

        # 5. 等待自动重置触发（5秒后）
        logger.info("步骤5: 等待自动重置触发（5秒后）...")
        await asyncio.sleep(5)

        # 6. 检查最终状态
        logger.info("步骤6: 检查最终状态")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            logger.info(f"最终状态: {state}")

        # 7. 再次检查队列状态
        logger.info("步骤7: 再次检查队列状态")
        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            logger.info(f"队列状态: {queue_status}")

        logger.info("✅ 测试完成！")


if __name__ == "__main__":
    logger.add("/tmp/test_complete_flow.log", rotation="10 MB")
    logger.info("开始测试完整流程...")
    asyncio.run(test_complete_flow())
