#!/usr/bin/env python3
"""测试 speaking 表情修复效果"""

import asyncio
import aiohttp
import time


async def test_speaking_expression():
    """测试 speaking 表情是否正确显示"""

    print("=" * 60)
    print("测试 speaking 表情修复效果")
    print("=" * 60)

    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 1. 获取当前状态
        print("\n[1] 获取当前状态...")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 2. 模拟 before-llm-call: 设置 working
        print("\n[2] 模拟 before-llm-call: 设置 working...")
        async with session.post(f"{base_url}/update", json={"expression": "working"}) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")
        await asyncio.sleep(1)

        # 3. 获取状态
        print("\n[3] 获取状态...")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 4. 模拟 after-llm-call: 不发送 neutral（已修复）
        print("\n[4] 模拟 after-llm-call: 不发送 neutral（已修复）...")
        print("    (跳过 neutral 请求)")
        await asyncio.sleep(1)

        # 5. 获取状态
        print("\n[5] 获取状态...")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 6. 模拟 on-response: 设置 speaking
        print("\n[6] 模拟 on-response: 设置 speaking...")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        # 7. 立即获取状态（应该显示 speaking）
        print("\n[7] 立即获取状态（应该显示 speaking）...")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 8. 等待 2 秒后再次获取状态
        print("\n[8] 等待 2 秒后再次获取状态...")
        await asyncio.sleep(2)
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 9. 等待 3 秒后获取状态（应该回到 neutral）
        print("\n[9] 等待 3 秒后获取状态（应该回到 neutral）...")
        await asyncio.sleep(3)
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_speaking_expression())
