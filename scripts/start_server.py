#!/usr/bin/env python3
"""启动数字人显示服务器 (v2.1.0 - Config Driven)"""
import asyncio
from display_server import DisplayServer, get_avatar_config

async def main():
    # 从 config.json 读取配置
    avatar_id, port, auto_open = get_avatar_config()
    print(f"🎭 启动数字人服务")
    print(f"   角色: {avatar_id}")
    print(f"   端口: {port}")
    print(f"   自动打开: {auto_open}")
    
    server = DisplayServer(port=port, avatar_id=avatar_id)
    await server.start(auto_open=auto_open)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
