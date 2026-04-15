#!/usr/bin/env python3
"""简单的 WebSocket 测试"""

import asyncio
import websockets
import json


async def test_websocket():
    """测试 WebSocket 连接"""
    uri = "ws://127.0.0.1:18791/ws"

    print("尝试连接到 WebSocket 服务器...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")

            # 发送一个测试消息
            test_message = json.dumps({"type": "test"})
            await websocket.send(test_message)
            print("✅ 已发送测试消息")

            # 等待响应
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"✅ 收到响应: {response}")
            except asyncio.TimeoutError:
                print("⏳ 等待响应超时（这是正常的，因为服务器可能不会响应测试消息）")

            print("✅ WebSocket 测试完成")

    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
