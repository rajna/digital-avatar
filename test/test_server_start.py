#!/usr/bin/env python3
"""测试服务器启动"""

import asyncio
from display_server import get_server


async def main():
    print("正在启动服务器...")
    server = get_server()
    await server.start(auto_open=False)
    print("服务器已启动")

    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        await server.stop()
        print("服务器已停止")


if __name__ == "__main__":
    asyncio.run(main())
