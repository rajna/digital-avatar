#!/usr/bin/env python3
"""测试 speaking 状态的切换流程"""

import asyncio
import aiohttp


async def test_speaking_flow():
    """测试 speaking 状态切换"""

    print("=" * 80)
    print("测试 speaking 状态切换流程")
    print("=" * 80)

    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 先重置到 neutral 状态
        print("\n[0] 重置到 neutral 状态")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "neutral"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        await asyncio.sleep(1)

        # 测试 1: neutral -> working (有过渡视频)
        print("\n" + "=" * 80)
        print("测试 1: neutral -> working (有过渡视频)")
        print("=" * 80)

        print("\n[1] 设置 working 表情")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "working"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'transition:neutral->working', "❌ 应该显示过渡状态"

        print("\n[3] 等待 7 秒（过渡 6s + 缓冲 1s）")
        await asyncio.sleep(7)

        print("\n[4] 获取状态（应该显示 working）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'working', "❌ 应该显示 working"

        # 测试 2: working -> speaking (有过渡视频)
        print("\n" + "=" * 80)
        print("测试 2: working -> speaking (有过渡视频)")
        print("=" * 80)

        print("\n[1] 设置 speaking 表情")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "speaking"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'transition:working->speaking', "❌ 应该显示过渡状态"

        print("\n[3] 等待 7 秒（过渡 6s + 缓冲 1s）")
        await asyncio.sleep(7)

        print("\n[4] 获取状态（应该显示 speaking）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'speaking', "❌ 应该显示 speaking"

        # 测试 3: speaking -> neutral (没有过渡视频)
        print("\n" + "=" * 80)
        print("测试 3: speaking -> neutral (没有过渡视频)")
        print("=" * 80)

        print("\n[1] 设置 neutral 表情")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "neutral"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该直接显示 neutral）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'neutral', "❌ 应该直接显示 neutral"
            assert not state.get('expression', '').startswith('transition:'), "❌ 不应该显示过渡状态"

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_speaking_flow())
