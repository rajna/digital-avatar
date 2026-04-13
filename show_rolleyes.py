#!/usr/bin/env python3
"""显示翻白眼表情"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from display_server import get_server

async def main():
    """启动显示服务器并显示翻白眼表情"""
    print("🎭 Digital Avatar - 翻白眼表情演示")
    print("=" * 50)
    
    # 获取服务器实例
    server = get_server()
    
    # 启动服务器
    print("启动显示服务器...")
    await server.start(port=18792, auto_open=True)
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    # 设置翻白眼表情
    print("设置翻白眼表情...")
    await server.update_expression("rolleyes", duration=5)
    await server.update_status("翻白眼中...")
    await server.show_bubble("无语了...")
    
    print("翻白眼表情已设置！")
    print("访问 http://127.0.0.1:18791 查看效果")
    print("表情将在5秒后自动重置")
    
    # 保持服务器运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    asyncio.run(main())