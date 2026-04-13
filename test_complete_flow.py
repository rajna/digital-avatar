#!/usr/bin/env python3
"""测试完整的表情流程"""

import asyncio
import aiohttp


async def test_complete_flow():
    """测试完整的表情流程"""
    base_url = "http://127.0.0.1:18791"

    print("=" * 60)
    print("测试完整的表情流程")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 测试1: neutral -> working (有过渡)
        print("\n📝 测试1: neutral -> working (有过渡)")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "working"}
        ) as resp:
            result = await resp.json()
            print(f"  响应: {result}")

        await asyncio.sleep(8)  # 等待过渡完成

        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"  当前状态: {state['expression']}")

        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"  队列状态: {queue_status}")

        # 测试2: working -> speaking (有过渡)
        print("\n📝 测试2: working -> speaking (有过渡)")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"  响应: {result}")

        await asyncio.sleep(8)  # 等待过渡完成

        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"  当前状态: {state['expression']}")

        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"  队列状态: {queue_status}")

        # 测试3: 等待自动重置
        print("\n⏳ 测试3: 等待自动重置 (5秒)")
        for i in range(6):
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/state") as resp:
                state = await resp.json()
                print(f"  [{i+1}s] 当前状态: {state['expression']}")

        # 测试4: speaking -> neutral (有过渡)
        print("\n📝 测试4: speaking -> neutral (有过渡)")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "neutral"}
        ) as resp:
            result = await resp.json()
            print(f"  响应: {result}")

        await asyncio.sleep(8)  # 等待过渡完成

        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"  当前状态: {state['expression']}")

        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"  队列状态: {queue_status}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_complete_flow())
