#!/usr/bin/env python3
"""演示过渡功能的脚本"""

from __future__ import annotations

import asyncio
from pathlib import Path

from avatar_generator import AvatarGenerator
from display_server import DisplayServer


async def demo_smooth_transition():
    """演示平滑过渡功能"""
    print("🎭 演示平滑过渡功能")
    print("=" * 50)
    
    # 创建生成器和显示服务器
    generator = AvatarGenerator()
    server = DisplayServer(assets_dir=generator.assets_dir)
    
    # 启动显示服务器
    await server.start(auto_open=False)
    print("✅ 显示服务器已启动")
    
    # 等待服务器启动
    await asyncio.sleep(2)
    
    # 演示状态过渡
    print("\n🔄 演示状态过渡:")
    
    # 1. 从 neutral 开始
    print("1. 初始状态: neutral")
    await server.update_expression("neutral")
    await asyncio.sleep(2)
    
    # 2. 过渡到 working
    print("2. 过渡到 working (使用过渡视频)")
    await generator.start_transition("neutral", "working", server)
    await asyncio.sleep(3)
    
    # 3. 过渡回 neutral
    print("3. 过渡回 neutral (使用过渡视频)")
    await generator.start_transition("working", "neutral", server)
    await asyncio.sleep(3)
    
    # 4. 直接切换到 speaking (无过渡)
    print("4. 直接切换到 speaking (无过渡)")
    await server.update_expression("speaking")
    await asyncio.sleep(2)
    
    # 5. 直接切换到 neutral (无过渡)
    print("5. 直接切换到 neutral (无过渡)")
    await server.update_expression("neutral")
    await asyncio.sleep(2)
    
    print("\n✅ 过渡演示完成!")


async def demo_transition_video_info():
    """演示过渡视频信息"""
    print("\n🎬 过渡视频信息:")
    print("=" * 50)
    
    generator = AvatarGenerator()
    transition_manager = generator.get_transition_manager()
    
    # 检查可用的过渡视频
    print("📁 可用的过渡视频:")
    for source, target in transition_manager.get_available_transitions():
        config = transition_manager.get_transition_config(source, target)
        video_path = transition_manager.get_transition_video(source, target)
        
        print(f"  {source} -> {target}:")
        print(f"    过渡类型: {config.transition_type.value}")
        print(f"    过渡时长: {config.transition_duration}秒")
        print(f"    使用视频: {'是' if video_path else '否'}")
        if video_path:
            print(f"    视频路径: {video_path}")
        print()


async def main():
    """主函数"""
    print("🔥 火娃数字人过渡功能演示")
    print("=" * 50)
    
    # 演示过渡视频信息
    await demo_transition_video_info()
    
    # 演示平滑过渡
    await demo_smooth_transition()


if __name__ == "__main__":
    asyncio.run(main())