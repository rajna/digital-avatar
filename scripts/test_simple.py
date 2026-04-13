#!/usr/bin/env python3
"""
简单测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加技能路径
sys.path.append(str(Path(__file__).parent.parent))

from display_server import get_server

async def test_simple():
    print("🧪 开始简单测试...")
    
    # 获取服务器实例
    server = get_server(port=18794)
    
    # 启动服务器
    print("🚀 启动服务器...")
    await server.start(auto_open=False)
    
    print("✅ 服务器启动成功")
    
    # 测试更新表情
    print("🎭 测试更新表情...")
    await server.update_expression("happy")
    print("✅ 已更新为happy表情")
    
    # 等待一下
    await asyncio.sleep(2)
    
    # 测试另一个表情
    await server.update_expression("thinking")
    print("✅ 已更新为thinking表情")
    
    await asyncio.sleep(2)
    
    await server.update_expression("rolleyes")
    print("✅ 已更新为rolleyes表情")
    
    print("🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_simple())