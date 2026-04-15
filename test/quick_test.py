#!/usr/bin/env python3
"""快速测试完整流程"""

import asyncio
import aiohttp


async def quick_test():
    """快速测试完整流程"""

    print("=" * 80)
    print("🚀 快速测试完整流程")
    print("=" * 80)

    base_url = "http://127.0.0.1:18791"

    async with aiohttp.ClientSession() as session:
        # 测试完整流程: neutral -> working -> speaking -> neutral
        test_cases = [
            ("neutral", "working", "有过渡视频"),
            ("working", "speaking", "有过渡视频"),
            ("speaking", "neutral", "没有过渡视频"),
        ]

        for i, (source, target, has_transition) in enumerate(test_cases, 1):
            print(f"\n{'=' * 80}")
            print(f"测试 {i}: {source} -> {target} ({has_transition})")
            print(f"{'=' * 80}")

            # 发送请求
            print(f"\n[1] 设置 {target} 表情")
            async with session.post(
                f"{base_url}/update",
                json={"expression": target}
            ) as resp:
                result = await resp.json()
                print(f"    请求结果: {result}")

            # 立即获取状态
            print(f"\n[2] 立即获取状态")
            async with session.get(f"{base_url}/state") as resp:
                state = await resp.json()
                current = state.get('expression', 'unknown')
                print(f"    当前状态: {current}")

                if has_transition == "有过渡视频":
                    if current.startswith('transition:'):
                        print(f"    ✅ 正确显示过渡状态")
                    else:
                        print(f"    ❌ 应该显示过渡状态，实际: {current}")
                else:
                    if current == target:
                        print(f"    ✅ 直接切换到目标状态")
                    else:
                        print(f"    ❌ 应该直接显示 {target}，实际: {current}")

            # 等待过渡完成
            if has_transition == "有过渡视频":
                print(f"\n[3] 等待过渡完成 (7秒)")
                await asyncio.sleep(7)

                print(f"\n[4] 获取最终状态")
                async with session.get(f"{base_url}/state") as resp:
                    state = await resp.json()
                    current = state.get('expression', 'unknown')
                    print(f"    当前状态: {current}")

                    if current == target:
                        print(f"    ✅ 过渡完成，状态正确")
                    else:
                        print(f"    ❌ 应该显示 {target}，实际: {current}")
            else:
                print(f"\n[3] 等待 1 秒")
                await asyncio.sleep(1)

    print(f"\n{'=' * 80}")
    print("✅ 测试完成！")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(quick_test())
