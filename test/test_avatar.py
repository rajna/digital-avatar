#!/usr/bin/env python3
"""测试数字人系统"""

import asyncio
from pathlib import Path
import sys

# 添加 scripts 目录到路径
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from avatar_generator import AvatarGenerator
from expression_manager import ExpressionManager


async def test_avatar_generator():
    """测试图片生成器"""
    print("=" * 60)
    print("测试 AvatarGenerator")
    print("=" * 60)

    generator = AvatarGenerator()

    # 显示可用图片
    print("\n可用图片类型:")
    for avatar_type in generator.get_available_types():
        count = generator.get_image_count(avatar_type)
        print(f"  {avatar_type.value}: {count} 张")

    # 测试生成不同类型的图片
    print("\n测试生成图片:")
    for avatar_type in ["neutral", "speaking", "expression"]:
        result = await generator.generate(avatar_type=avatar_type)
        if result.success:
            print(f"  ✓ {avatar_type}: {Path(result.image_path).name}")
        else:
            print(f"  ✗ {avatar_type}: {result.error}")

    # 测试根据表情生成图片
    print("\n测试根据表情生成图片:")
    for expression in ["neutral", "happy", "thinking", "sad", "surprised", "confused", "working", "speaking"]:
        result = await generator.generate_by_expression(expression)
        if result.success:
            print(f"  ✓ {expression}: {Path(result.image_path).name}")
        else:
            print(f"  ✗ {expression}: {result.error}")


def test_expression_manager():
    """测试表情管理器"""
    print("\n" + "=" * 60)
    print("测试 ExpressionManager")
    print("=" * 60)

    manager = ExpressionManager()

    # 测试文本检测
    print("\n文本表情检测:")
    test_texts = [
        ("你好！", "neutral"),
        ("让我想想...", "thinking"),
        ("抱歉，我做不到", "sad"),
        ("哇，太棒了！", "happy"),
        ("正在处理中...", "thinking"),
        ("我不确定", "confused"),
        ("真的吗？", "surprised"),
        ("执行命令", "working"),
    ]

    for text, expected in test_texts:
        expression = manager.detect_from_text(text)
        status = "✓" if expression.value == expected else "✗"
        print(f"  {status} \"{text}\" -> {expression.value} (期望: {expected})")

    # 测试上下文检测
    print("\n上下文表情检测:")
    test_contexts = [
        ({"tool_name": "read_file"}, "working"),
        ({"tool_name": "web_search"}, "thinking"),
        ({"tool_name": "message"}, "speaking"),
        ({"tool_name": "write_file"}, "working"),
    ]

    for ctx, expected in test_contexts:
        expression = manager.detect_from_context(ctx)
        status = "✓" if expression.value == expected else "✗"
        print(f"  {status} {ctx} -> {expression.value} (期望: {expected})")

    # 测试表情到图片类型的映射
    print("\n表情到图片类型映射:")
    for expression in ["neutral", "happy", "thinking", "sad", "surprised", "confused", "working", "speaking"]:
        avatar_type = manager.get_avatar_type(expression)
        print(f"  {expression} -> {avatar_type}")


async def main():
    """主测试函数"""
    print("\n🎨 Digital Avatar 测试\n")

    await test_avatar_generator()
    test_expression_manager()

    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
