#!/usr/bin/env python3
"""翻白眼表情演示"""

from expression_manager import ExpressionManager

def demo():
    """演示翻白眼表情"""
    manager = ExpressionManager()

    print("🎭 Digital Avatar - 翻白眼表情演示")
    print("=" * 60)
    print()

    # 模拟对话场景
    scenarios = [
        {
            "user": "帮我写个代码",
            "assistant": "好的，让我帮你写个代码...",
            "expected": "thinking"
        },
        {
            "user": "代码写好了，运行一下",
            "assistant": "好的，正在运行代码...",
            "expected": "working"
        },
        {
            "user": "运行失败了，怎么办？",
            "assistant": "让我看看错误信息...",
            "expected": "thinking"
        },
        {
            "user": "你能不能别再犯这种低级错误了？",
            "assistant": "😅 翻白眼...我下次会注意的。",
            "expected": "rolleyes"
        },
        {
            "user": "好吧，这次算你厉害",
            "assistant": "谢谢！😊",
            "expected": "happy"
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"场景 {i}:")
        print(f"  用户: {scenario['user']}")
        print(f"  助手: {scenario['assistant']}")

        # 检测助手回复的表情
        assistant_text = scenario['assistant']
        detected = manager.detect_from_text(assistant_text)
        avatar_type = manager.get_avatar_type(detected)

        print(f"  检测到的表情: {detected.value}")
        print(f"  对应图片: my-avatar-expression-{detected.value}.mp4")
        print()

    print("=" * 60)
    print("💡 提示: 在实际对话中，当你说出包含以下关键词的句子时，")
    print("   数字人会自动显示翻白眼表情:")
    print("   - 翻白眼")
    print("   - 无语")
    print("   - 无语了")
    print("   - 呵呵")
    print("   - 哼")
    print("   - 切")
    print()

if __name__ == "__main__":
    demo()
