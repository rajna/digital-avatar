#!/usr/bin/env python3
"""测试 WebSocket 连接"""

import asyncio
import websockets
import json


async def test_websocket():
    """测试 WebSocket 连接"""
    uri = "ws://127.0.0.1:18791/ws"

    print("=" * 60)
    print("测试 WebSocket 连接")
    print("=" * 60)

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 连接成功")

            # 监听消息
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    print(f"📨 收到消息: {data}")

                    # 如果收到任务开始消息，发送任务完成通知
                    if data.get("type") == "video_task_start":
                        print(f"  🎬 任务开始: {data['task']}")
                        # 模拟视频播放完成，发送任务完成通知
                        await asyncio.sleep(2)  # 模拟视频播放时间
                        complete_message = json.dumps({"type": "task_complete"})
                        await websocket.send(complete_message)
                        print(f"  ✅ 已发送任务完成通知")

                except asyncio.TimeoutError:
                    print("⏳ 等待消息超时，继续监听...")
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")
                    break

    except Exception as e:
        print(f"❌ WebSocket 连接失败: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
