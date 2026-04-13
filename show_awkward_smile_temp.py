#!/usr/bin/env python3
"""显示尴尬笑表情"""

import asyncio
import sys
import os
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from display_server import get_server

async def main():
    """启动显示服务器并显示尴尬笑表情"""
    print("🎭 Digital Avatar - 尴尬笑表情演示")
    print("=" * 50)
    
    # 获取服务器实例，使用不同的端口
    server = get_server()
    server.port = 18793
    
    # 启动服务器
    print("启动显示服务器...")
    await server.start(auto_open=True)
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    # 设置尴尬笑表情
    print("设置尴尬笑表情...")
    await server.update_expression("fakesmilerolleyes", duration=5)
    await server.update_status("尴尬笑中...")
    await server.show_bubble("呵呵...")
    
    print("尴尬笑表情已设置！")
    print("访问 http://127.0.0.1:18793 查看效果")
    print("表情将在5秒后自动重置")
    
    # 保持服务器运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    asyncio.run(main())