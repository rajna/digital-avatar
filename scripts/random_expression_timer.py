#!/usr/bin/env python3
"""
Random Expression Timer - 让数字人每10秒随机做一个表情

这个脚本会启动digital-avatar服务，并每10秒随机切换一次表情。
"""

import asyncio
import random
import sys
import os
from pathlib import Path

# 添加技能路径
sys.path.append(str(Path(__file__).parent.parent))

from display_server import get_server

# 支持的表情列表
EXPRESSIONS = [
    "neutral",     # 默认状态
    "happy",       # 开心
    "thinking",    # 思考
    "sad",         # 悲伤
    "surprised",   # 惊讶
    "confused",    # 困惑
    "working",     # 工作
    "speaking",    # 说话
    "rolleyes"     # 翻白眼
]

# 表情对应的emoji显示
EXPRESSION_EMOJIS = {
    "neutral": "😊",
    "happy": "😄",
    "thinking": "🤔",
    "sad": "😢",
    "surprised": "😲",
    "confused": "😕",
    "working": "💼",
    "speaking": "🗣️",
    "rolleyes": "🙄"
}

async def random_expression_timer(interval: int = 10, port: int = 18791):
    """
    每10秒随机切换表情
    
    Args:
        interval: 切换间隔（秒）
        port: 服务器端口
    """
    print(f"🎭 启动随机表情定时器，每{interval}秒切换一次表情")
    print("=" * 50)
    
    # 获取服务器实例
    server = get_server(port=port)
    
    # 启动服务器
    print("🚀 启动数字人服务器...")
    await server.start(auto_open=False)  # 不自动打开浏览器
    
    print("✅ 服务器已启动，开始随机表情切换")
    print(f"📱 访问地址: http://127.0.0.1:{port}")
    print("🎯 按 Ctrl+C 停止")
    print()
    
    try:
        while True:
            # 随机选择一个表情
            expression = random.choice(EXPRESSIONS)
            emoji = EXPRESSION_EMOJIS.get(expression, "😊")
            
            # 更新表情
            await server.update_expression(expression, duration=0)
            
            # 显示当前表情
            print(f"🎭 切换表情: {expression} {emoji}")
            
            # 等待指定时间
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 停止随机表情定时器")
        # 恢复默认表情
        await server.update_expression("neutral")
        print("✅ 已恢复默认表情")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        await server.update_expression("neutral")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数字人随机表情定时器")
    parser.add_argument("--interval", type=int, default=10, 
                       help="表情切换间隔（秒，默认10秒）")
    parser.add_argument("--port", type=int, default=18791,
                       help="服务器端口（默认18791）")
    
    args = parser.parse_args()
    
    print("🎭 数字人随机表情定时器")
    print("=" * 30)
    print(f"切换间隔: {args.interval}秒")
    print(f"服务器端口: {args.port}")
    print()
    
    # 运行定时器
    asyncio.run(random_expression_timer(args.interval, args.port))

if __name__ == "__main__":
    main()