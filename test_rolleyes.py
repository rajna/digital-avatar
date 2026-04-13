#!/usr/bin/env python3
"""测试翻白眼表情"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.expression_manager import ExpressionManager

def test_rolleyes():
    """测试翻白眼表情检测"""
    manager = ExpressionManager()

    # 测试关键词
    test_cases = [
        "翻白眼",
        "无语",
        "无语了",
        "呵呵",
        "哼",
        "切",
    ]

    print("翻白眼表情测试:")
    print("=" * 50)

    for text in test_cases:
        expression = manager.detect_from_text(text)
        avatar_type = manager.get_avatar_type(expression)
        print(f"文本: '{text}'")
        print(f"  表情: {expression.value}")
        print(f"  图片类型: {avatar_type}")
        print(f"  图片文件: my-avatar-expression-rolleyes.mp4")
        print()

if __name__ == "__main__":
    test_rolleyes()
