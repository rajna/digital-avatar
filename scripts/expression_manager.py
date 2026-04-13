#!/usr/bin/env python3
"""Expression Manager - 表情管理器"""

from __future__ import annotations

from enum import Enum
from typing import Any


class Expression(str, Enum):
    """表情类型"""
    NEUTRAL = "neutral"  # 平静
    HAPPY = "happy"  # 开心
    THINKING = "thinking"  # 思考
    SAD = "sad"  # 悲伤
    SURPRISED = "surprised"  # 惊讶
    CONFUSED = "confused"  # 困惑
    WORKING = "working"  # 工作中
    SPEAKING = "speaking"  # 说话
    ROLLEYES = "rolleyes"  # 翻白眼
    AWKWARD_SMILE = "fakesmilerolleyes"  # 尴尬笑


class ExpressionManager:
    """表情管理器"""

    # 关键词映射
    KEYWORD_MAP = {
        # 开心
        "happy": Expression.HAPPY,
        "开心": Expression.HAPPY,
        "成功": Expression.HAPPY,
        "完成": Expression.HAPPY,
        "好的": Expression.HAPPY,
        "太棒了": Expression.HAPPY,
        "谢谢": Expression.HAPPY,
        "你好": Expression.HAPPY,
        "您好": Expression.HAPPY,
        "嗨": Expression.HAPPY,
        "欢迎": Expression.HAPPY,
        "哈哈": Expression.HAPPY,
        "呵呵": Expression.HAPPY,
        "嘻嘻": Expression.HAPPY,
        "笑话": Expression.HAPPY,
        "有趣": Expression.HAPPY,
        "好玩": Expression.HAPPY,
        "😄": Expression.HAPPY,
        "😂": Expression.HAPPY,
        "🤣": Expression.HAPPY,

        # 思考
        "think": Expression.THINKING,
        "思考": Expression.THINKING,
        "分析": Expression.THINKING,
        "让我想想": Expression.THINKING,
        "计算": Expression.THINKING,

        # 困惑
        "confused": Expression.CONFUSED,
        "困惑": Expression.CONFUSED,
        "错误": Expression.CONFUSED,
        "失败": Expression.CONFUSED,
        "不清楚": Expression.CONFUSED,
        "不确定": Expression.CONFUSED,
        "不明白": Expression.CONFUSED,
        "不懂": Expression.CONFUSED,
        "不太明白": Expression.CONFUSED,

        # 惊讶
        "surprised": Expression.SURPRISED,
        "惊讶": Expression.SURPRISED,
        "哇": Expression.SURPRISED,
        "天哪": Expression.SURPRISED,
        "真的吗": Expression.SURPRISED,

        # 悲伤
        "sad": Expression.SAD,
        "抱歉": Expression.SAD,
        "遗憾": Expression.SAD,
        "对不起": Expression.SAD,
        "不好意思": Expression.SAD,
        "难过": Expression.SAD,
        "伤心": Expression.SAD,
        "难过": Expression.SAD,

        # 工作中
        "working": Expression.WORKING,
        "执行": Expression.WORKING,
        "处理": Expression.WORKING,
        "调用": Expression.WORKING,
        "读取": Expression.WORKING,
        "写入": Expression.WORKING,
        "搜索": Expression.WORKING,

        # 说话
        "speaking": Expression.SPEAKING,
        "说": Expression.SPEAKING,
        "告诉": Expression.SPEAKING,
        "回答": Expression.SPEAKING,

        # 翻白眼
        "rolleyes": Expression.ROLLEYES,
        "翻白眼": Expression.ROLLEYES,
        "无语": Expression.ROLLEYES,
        "无语了": Expression.ROLLEYES,
        "无语": Expression.ROLLEYES,
        "呵呵": Expression.ROLLEYES,
        "哼": Expression.ROLLEYES,
        "切": Expression.ROLLEYES,
        
        # 尴尬笑
        "awkward": Expression.AWKWARD_SMILE,
        "尴尬": Expression.AWKWARD_SMILE,
        "尴尬笑": Expression.AWKWARD_SMILE,
        "假笑": Expression.AWKWARD_SMILE,
        "假笑": Expression.AWKWARD_SMILE,
        "尴尬": Expression.AWKWARD_SMILE,
        "尴尬": Expression.AWKWARD_SMILE,
    }

    def detect_from_text(self, text: str) -> Expression:
        """
        从文本中检测表情

        Args:
            text: 输入文本

        Returns:
            Expression: 检测到的表情
        """
        if not text:
            return Expression.NEUTRAL

        text_lower = text.lower()

        # 检查关键词
        for keyword, expression in self.KEYWORD_MAP.items():
            if keyword.lower() in text_lower:
                return expression

        return Expression.NEUTRAL

    def detect_from_context(self, context: dict) -> Expression:
        """
        从上下文中检测表情

        Args:
            context: 上下文字典

        Returns:
            Expression: 检测到的表情
        """
        # 检查工具名称
        tool_name = context.get("tool_name", "")
        if tool_name:
            if tool_name in ["read_file", "write_file", "exec", "execute"]:
                return Expression.WORKING
            elif tool_name in ["web_search", "web_fetch"]:
                return Expression.THINKING
            elif tool_name in ["message"]:
                return Expression.SPEAKING

        # 检查消息内容
        messages = context.get("messages", [])
        if messages:
            last_msg = messages[-1] if messages else {}
            content = last_msg.get("content", "")
            if isinstance(content, str):
                return self.detect_from_text(content)

        return Expression.NEUTRAL

    def get_avatar_type(self, expression: Expression) -> str:
        """
        获取表情对应的图片类型

        Args:
            expression: 表情类型

        Returns:
            str: 图片类型（neutral, speaking, expression）
        """
        # 映射表情到图片类型
        expression_to_type = {
            Expression.NEUTRAL: "neutral",
            Expression.HAPPY: "expression",
            Expression.THINKING: "speaking",
            Expression.SAD: "expression",
            Expression.SURPRISED: "expression",
            Expression.CONFUSED: "expression",
            Expression.WORKING: "speaking",
            Expression.SPEAKING: "speaking",
            Expression.ROLLEYES: "expression",
            Expression.AWKWARD_SMILE: "expression",
        }

        return expression_to_type.get(expression, "neutral")

    def get_prompt_modifier(self, expression: Expression) -> str:
        """
        获取表情对应的提示词修饰符（保留兼容性）

        Args:
            expression: 表情类型

        Returns:
            str: 提示词修饰符
        """
        modifiers = {
            Expression.NEUTRAL: "calm and peaceful expression",
            Expression.HAPPY: "warm smile, happy expression",
            Expression.THINKING: "thoughtful expression, focused",
            Expression.SAD: "slightly sad expression",
            Expression.SURPRISED: "wide eyes, surprised",
            Expression.CONFUSED: "confused expression",
            Expression.WORKING: "focused, concentrated",
            Expression.SPEAKING: "speaking, animated expression",
        }
        return modifiers.get(expression, modifiers[Expression.NEUTRAL])
