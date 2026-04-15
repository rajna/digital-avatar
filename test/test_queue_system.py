#!/usr/bin/env python3
"""测试视频队列系统"""

import asyncio
import aiohttp
import time


async def test_queue_system():
    """测试视频队列系统"""
    base_url = "http://127.0.0.1:18791"

    print("=" * 60)
    print("测试视频队列系统")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 测试1: 查询队列状态
        print("\n📊 测试1: 查询队列状态")
        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"队列状态: {queue_status}")

        # 测试2: 添加多个任务到队列
        print("\n📝 测试2: 添加多个任务到队列")
        tasks = [
            ("working", 0),
            ("speaking", 5),
            ("neutral", 0)
        ]

        for expression, duration in tasks:
            print(f"  添加任务: {expression} (duration={duration})")
            async with session.post(
                f"{base_url}/update",
                json={"expression": expression, "duration": duration}
            ) as resp:
                result = await resp.json()
                print(f"  响应: {result}")

            # 等待一段时间，让任务开始执行
            await asyncio.sleep(1)

        # 测试3: 查询队列状态
        print("\n📊 测试3: 查询队列状态（添加任务后）")
        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"队列状态: {queue_status}")

        # 测试4: 等待所有任务完成
        print("\n⏳ 测试4: 等待所有任务完成")
        for i in range(15):
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/queue") as resp:
                queue_status = await resp.json()
                print(f"  [{i+1}s] 队列状态: is_playing={queue_status['is_playing']}, queue_size={queue_status['queue_size']}")

            if not queue_status['is_playing'] and queue_status['queue_size'] == 0:
                print("  ✅ 所有任务已完成")
                break

        # 测试5: 测试过渡动画
        print("\n🎬 测试5: 测试过渡动画")
        print("  添加任务: neutral -> working")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "working"}
        ) as resp:
            result = await resp.json()
            print(f"  响应: {result}")

        await asyncio.sleep(2)

        print("  添加任务: working -> speaking")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"  响应: {result}")

        # 等待过渡完成
        await asyncio.sleep(8)

        # 测试6: 查询最终状态
        print("\n📊 测试6: 查询最终状态")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"当前状态: {state}")

        async with session.get(f"{base_url}/queue") as resp:
            queue_status = await resp.json()
            print(f"队列状态: {queue_status}")

    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_queue_system())
