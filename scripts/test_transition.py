#!/usr/bin/env python3
"""测试数字人状态过渡功能"""

import asyncio
import sys
from pathlib import Path

# 添加scripts目录到路径
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from display_server import DisplayServer

async def test_transition():
    """测试neutral到working的过渡"""
    server = DisplayServer(port=9999)
    
    print("启动数字人服务器...")
    await server.start(auto_open=False)
    
    print("等待3秒...")
    await asyncio.sleep(3)
    
    print("测试neutral -> working过渡...")
    await server.update_expression("working")
    
    print("等待5秒观察过渡效果...")
    await asyncio.sleep(5)
    
    print("测试working -> neutral过渡...")
    await server.update_expression("neutral")
    
    print("等待5秒观察过渡效果...")
    await asyncio.sleep(5)
    
    print("测试完成！")

if __name__ == "__main__":
    asyncio.run(test_transition())