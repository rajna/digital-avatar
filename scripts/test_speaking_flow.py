#!/usr/bin/env python3
"""测试 speaking 表达的完整流程"""

import asyncio
import aiohttp
import json
import time

async def test_speaking_flow():
    """测试 speaking 表达的完整流程"""
    base_url = "http://127.0.0.1:18791"

    print("=== 测试 speaking 表达的完整流程 ===\n")

    async with aiohttp.ClientSession() as session:
        # 1. 设置 working 状态
        print("1️⃣ 设置 working 状态")
        async with session.post(f"{base_url}/update", json={"expression": "working"}) as resp:
            print(f"   状态码: {resp.status}")
            result = await resp.json()
            print(f"   响应: {result}\n")

        await asyncio.sleep(2)

        # 2. 设置 speaking 状态（带过渡）
        print("2️⃣ 设置 speaking 状态（带过渡）")
        async with session.post(f"{base_url}/update", json={"expression": "speaking", "duration": 5}) as resp:
            print(f"   状态码: {resp.status}")
            result = await resp.json()
            print(f"   响应: {result}\n")

        # 3. 监控状态变化
        print("3️⃣ 监控状态变化（10秒）")
        for i in range(10):
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/state") as resp:
                state = await resp.json()
                print(f"   [{i+1}s] 状态: {state['expression']}")

        # 4. 检查队列状态
        print("\n4️⃣ 检查队列状态")
        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"   队列状态: {queue_status}\n")

    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_speaking_flow())
