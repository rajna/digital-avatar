#!/usr/bin/env python3
"""测试自动重置功能"""

import asyncio
import aiohttp


async def test_auto_reset():
    """测试自动重置功能"""

    print("=" * 70)
    print("测试自动重置功能")
    print("=" * 70)

    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 1. 设置 speaking 表情，5秒后自动重置
        print("\n[1] 设置 speaking 表情，5秒后自动重置")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        # 2. 立即获取状态（应该显示过渡状态）
        print("\n[2] 立即获取状态（应该显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 3. 等待 2 秒后获取状态
        print("\n[3] 等待 2 秒后获取状态")
        await asyncio.sleep(2)
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 4. 等待 4 秒后获取状态（应该显示 speaking）
        print("\n[4] 等待 4 秒后获取状态（应该显示 speaking）")
        await asyncio.sleep(4)
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

        # 5. 等待 3 秒后获取状态（应该回到 neutral）
        print("\n[5] 等待 3 秒后获取状态（应该回到 neutral）")
        await asyncio.sleep(3)
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_auto_reset())
