#!/usr/bin/env python3
"""测试 speaking 视频播放修复"""

import asyncio
import aiohttp
import time
from loguru import logger


async def test_speaking_video():
    """测试 speaking 视频播放"""
    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 1. 设置 working 状态
        logger.info("步骤 1: 设置 working 状态")
        async with session.post(f"{base_url}/update", json={"expression": "working"}) as resp:
            result = await resp.json()
            logger.info(f"设置 working 状态: {result}")

        await asyncio.sleep(2)

        # 2. 设置 speaking 状态（应该触发 working->speaking 过渡）
        logger.info("步骤 2: 设置 speaking 状态（应该触发 working->speaking 过渡）")
        async with session.post(f"{base_url}/update", json={"expression": "speaking", "duration": 5}) as resp:
            result = await resp.json()
            logger.info(f"设置 speaking 状态: {result}")

        # 3. 监控队列状态
        logger.info("步骤 3: 监控队列状态")
        for i in range(10):
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/queue") as resp:
                queue_status = await resp.json()
                logger.info(f"队列状态 [{i+1}/10]: {queue_status}")

            # 检查当前状态
            async with session.get(f"{base_url}/state") as resp:
                state = await resp.json()
                logger.info(f"当前状态: {state['expression']}")

        logger.info("测试完成！")


if __name__ == "__main__":
    logger.info("开始测试 speaking 视频播放修复")
    asyncio.run(test_speaking_video())
