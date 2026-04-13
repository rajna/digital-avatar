#!/usr/bin/env python3
"""最终验证测试 - 完整的数字人表情切换流程"""

import asyncio
import aiohttp


async def final_verification():
    """最终验证测试"""

    print("=" * 80)
    print("最终验证测试 - 完整的数字人表情切换流程")
    print("=" * 80)

    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 测试 1: speaking 表情 + 自动重置
        print("\n" + "=" * 80)
        print("测试 1: speaking 表情 + 自动重置")
        print("=" * 80)

        print("\n[1] 设置 speaking 表情，5秒后自动重置")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'transition:working->speaking', "❌ 过渡状态错误"

        print("\n[3] 等待 12 秒（过渡 6s + 自动重置 5s + 缓冲 1s）")
        await asyncio.sleep(12)

        print("\n[4] 获取状态（应该回到 neutral）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'neutral', "❌ 自动重置失败"

        # 测试 2: 情绪表情 + 自动重置
        print("\n" + "=" * 80)
        print("测试 2: 情绪表情 + 自动重置")
        print("=" * 80)

        print("\n[1] 设置 happy 表情，3秒后自动重置")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "happy", "duration": 3}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该显示 happy）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'happy', "❌ 情绪表情错误"

        print("\n[3] 等待 4 秒")
        await asyncio.sleep(4)

        print("\n[4] 获取状态（应该回到 neutral）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'neutral', "❌ 自动重置失败"

        # 测试 3: 过渡保护
        print("\n" + "=" * 80)
        print("测试 3: 过渡保护")
        print("=" * 80)

        print("\n[1] 先设置 working 表情")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "working"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 设置 speaking 表情，5秒后自动重置")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking", "duration": 5}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[3] 立即发送 working 请求（应该被忽略）")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "working"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[4] 获取状态（应该仍然显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'transition:working->speaking', "❌ 过渡保护失败"

        print("\n[5] 等待 12 秒（过渡 6s + 自动重置 5s + 缓冲 1s）")
        await asyncio.sleep(12)

        print("\n[6] 获取状态（应该回到 neutral）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'neutral', "❌ 自动重置失败"

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(final_verification())
