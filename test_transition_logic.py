#!/usr/bin/env python3
"""测试过渡逻辑：有过渡视频 vs 没有过渡视频"""

import asyncio
import aiohttp


async def test_transition_logic():
    """测试过渡逻辑"""

    print("=" * 80)
    print("测试过渡逻辑：有过渡视频 vs 没有过渡视频")
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

        # 测试 1: 有过渡视频的情况 (neutral -> working)
        print("\n" + "=" * 80)
        print("测试 1: 有过渡视频的情况 (neutral -> working)")
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

        # 测试 2: 没有过渡视频的情况 (working -> happy)
        print("\n" + "=" * 80)
        print("测试 2: 没有过渡视频的情况 (working -> happy)")
        print("=" * 80)

        print("\n[1] 设置 happy 表情")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "happy"}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该直接显示 happy，不显示过渡状态）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'happy', "❌ 应该直接显示 happy"
            assert not state.get('expression', '').startswith('transition:'), "❌ 不应该显示过渡状态"

        print("\n[3] 等待 2 秒，确保状态稳定")
        await asyncio.sleep(2)

        print("\n[4] 再次获取状态（应该仍然显示 happy）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'happy', "❌ 应该仍然显示 happy"

        # 测试 3: 没有过渡视频 + 自动重置 (happy -> neutral)
        print("\n" + "=" * 80)
        print("测试 3: 没有过渡视频 + 自动重置 (happy -> neutral)")
        print("=" * 80)

        print("\n[1] 设置 happy 表情，3秒后自动重置")
        async with session.post(
            f"{base_url}/update",
            json={"expression": "happy", "duration": 3}
        ) as resp:
            result = await resp.json()
            print(f"    请求结果: {result}")

        print("\n[2] 立即获取状态（应该直接显示 happy）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'happy', "❌ 应该直接显示 happy"

        print("\n[3] 等待 4 秒（自动重置 3s + 缓冲 1s）")
        await asyncio.sleep(4)

        print("\n[4] 获取状态（应该回到 neutral）")
        async with session.get(f"{base_url}/state") as resp:
            state = await resp.json()
            print(f"    当前状态: {state.get('expression', 'unknown')}")
            assert state.get('expression') == 'neutral', "❌ 应该回到 neutral"

    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_transition_logic())
