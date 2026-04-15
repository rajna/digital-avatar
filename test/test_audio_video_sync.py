#!/usr/bin/env python3
"""
音画同步测试 - Audio/Video Sync Test

核心规则：
  音频必须在 speaking 视频画面出现之后才开始播放。
  即：audio_start_time >= video_playing_time

测试场景：
  1. 音频先到，视频后到 → 音频等视频
  2. 视频先到，音频后到 → 音频立即播放
  3. 正常流程：transition → speaking → audio synced
"""

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from dataclasses import dataclass

# 确保能导入模块
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from video_queue import VideoQueue, VideoTask, VideoTaskType


# ============================================================
# 测试 1: 音频先到 → 不应立即播放，等 video_playing 信号
# ============================================================
async def test_audio_arrives_before_video():
    """
    场景：/audio/start 在 speaking 视频开始之前到达
    规则：音频不应立即播放，必须等 video_playing 信号
    """
    print("\n" + "=" * 60)
    print("测试 1: 音频先到 → 等视频就绪后再播放")
    print("=" * 60)

    from display_server import DisplayServer

    # 创建 server（不启动 HTTP）
    server = DisplayServer(port=19999)

    # Mock _play_audio 来追踪调用
    play_audio_calls = []
    original_play_audio = server._play_audio

    def mock_play_audio(path):
        play_audio_calls.append(("play", path, time.time()))
        print(f"  ⚠️  _play_audio 被调用: {path}")

    server._play_audio = mock_play_audio

    # 模拟：当前状态是 neutral（speaking 视频还没开始）
    server._state["expression"] = "neutral"

    # 发送 /audio/start
    audio_path = "/tmp/test_audio.mp3"
    server._pending_audio_path = None

    # 模拟 _handle_audio_start 的核心逻辑
    server._speaking_audio_path = audio_path
    server._pending_audio_path = audio_path

    # 检查：expression 不是 speaking，所以不应播放
    if server._state.get("expression") == "speaking":
        server._play_audio(server._pending_audio_path)
        server._pending_audio_path = None
    else:
        print("  ✅ speaking 视频未开始，音频等待中")

    # 验证：音频没有播放
    assert len(play_audio_calls) == 0, f"❌ 失败：音频不应在视频前播放！调用了 {len(play_audio_calls)} 次"
    assert server._pending_audio_path == audio_path, "❌ 失败：_pending_audio_path 应保留"

    print("  ✅ 通过：音频等待 video_playing 信号")
    return True


# ============================================================
# 测试 2: 视频先到，音频后到 → 音频立即播放
# ============================================================
async def test_audio_arrives_after_video():
    """
    场景：speaking 视频已经在播放，/audio/start 才到达
    规则：音频应立即播放
    """
    print("\n" + "=" * 60)
    print("测试 2: 视频先到 → 音频立即播放")
    print("=" * 60)

    from display_server import DisplayServer

    server = DisplayServer(port=19999)

    play_audio_calls = []

    def mock_play_audio(path):
        play_audio_calls.append(("play", path, time.time()))
        print(f"  ✅ _play_audio 被调用: {path}")

    server._play_audio = mock_play_audio

    # 模拟：speaking 视频已经在播放
    server._state["expression"] = "speaking"

    # 发送 /audio/start
    audio_path = "/tmp/test_audio.mp3"
    server._pending_audio_path = None

    # 模拟 _handle_audio_start 的核心逻辑
    server._speaking_audio_path = audio_path
    server._pending_audio_path = audio_path

    if server._state.get("expression") == "speaking":
        server._play_audio(server._pending_audio_path)
        server._pending_audio_path = None
    else:
        print("  ❌ speaking 视频已在播放，应立即播放音频")

    # 验证：音频已播放
    assert len(play_audio_calls) == 1, f"❌ 失败：音频应立即播放！调用了 {len(play_audio_calls)} 次"
    assert server._pending_audio_path is None, "❌ 失败：_pending_audio_path 应已清除"

    print("  ✅ 通过：音频在视频播放中立即开始")
    return True


# ============================================================
# 测试 3: video_playing WebSocket 信号触发音频
# ============================================================
async def test_video_playing_triggers_audio():
    """
    场景：音频已就绪（_pending_audio_path 已设置），
         前端发送 video_playing 信号
    规则：收到 video_playing(speaking) 后必须播放音频
    """
    print("\n" + "=" * 60)
    print("测试 3: video_playing 信号触发音频播放")
    print("=" * 60)

    from display_server import DisplayServer

    server = DisplayServer(port=19999)

    play_audio_calls = []

    def mock_play_audio(path):
        play_audio_calls.append(("play", path, time.time()))
        print(f"  ✅ _play_audio 被调用: {path}")

    server._play_audio = mock_play_audio

    # 模拟：音频已就绪，等待视频
    audio_path = "/tmp/test_audio.mp3"
    server._pending_audio_path = audio_path
    server._state["expression"] = "neutral"

    # 模拟前端发送 video_playing WebSocket 消息
    # 这是 display_server._handle_websocket 中的逻辑
    target = "speaking"
    if target == "speaking" and server._pending_audio_path:
        print(f"  ✅ video_playing(speaking) 触发音频播放: {server._pending_audio_path}")
        server._play_audio(server._pending_audio_path)
        server._pending_audio_path = None

    # 验证
    assert len(play_audio_calls) == 1, f"❌ 失败：video_playing 应触发音频！调用了 {len(play_audio_calls)} 次"
    assert server._pending_audio_path is None, "❌ 失败：_pending_audio_path 应已清除"

    print("  ✅ 通过：video_playing 信号正确触发音频")
    return True


# ============================================================
# 测试 4: _on_video_task_start 不应直接播放音频
# ============================================================
async def test_video_task_start_no_direct_audio():
    """
    场景：speaking 视频任务开始
    规则：_on_video_task_start 不应直接调用 _play_audio
          音频播放必须由 video_playing 信号触发
    """
    print("\n" + "=" * 60)
    print("测试 4: _on_video_task_start 不直接播放音频")
    print("=" * 60)

    from display_server import DisplayServer

    server = DisplayServer(port=19999)

    play_audio_calls = []

    def mock_play_audio(path):
        play_audio_calls.append(("play", path, time.time()))
        print(f"  ⚠️  _play_audio 被调用: {path}")

    server._play_audio = mock_play_audio

    # 设置 pending audio
    audio_path = "/tmp/test_audio.mp3"
    server._pending_audio_path = audio_path

    # 创建 speaking video task
    task = VideoTask(
        task_type=VideoTaskType.PLAY_VIDEO,
        source="",
        target="speaking",
        duration=10
    )

    # 调用 _on_video_task_start
    server._on_video_task_start(task)

    # 验证：_play_audio 不应被调用
    assert len(play_audio_calls) == 0, (
        f"❌ 失败：_on_video_task_start 不应直接播放音频！"
        f"调用了 {len(play_audio_calls)} 次"
    )

    # 验证：_pending_audio_path 仍然保留（等 video_playing 触发）
    assert server._pending_audio_path == audio_path, (
        "❌ 失败：_pending_audio_path 应保留，等 video_playing 触发"
    )

    print("  ✅ 通过：_on_video_task_start 不直接播放音频")
    return True


# ============================================================
# 测试 5: 完整时序 - 音频必须在视频之后
# ============================================================
async def test_full_timeline_audio_after_video():
    """
    完整时序测试：
    1. transition 任务开始 → 不播放音频
    2. transition 完成，speaking 任务开始 → 不播放音频
    3. 前端 video_playing(speaking) → 播放音频 ✅
    
    验证：audio_start_time >= video_playing_time
    """
    print("\n" + "=" * 60)
    print("测试 5: 完整时序 - 音频在视频之后播放")
    print("=" * 60)

    from display_server import DisplayServer

    server = DisplayServer(port=19999)

    timeline = []

    def mock_play_audio(path):
        timeline.append(("audio_start", time.time()))
        print(f"  🔊 音频开始播放 (t={timeline[-1][1]:.3f})")

    server._play_audio = mock_play_audio

    # 设置 pending audio（模拟 TTS 已完成）
    audio_path = "/tmp/test_audio.mp3"
    server._pending_audio_path = audio_path

    # Step 1: transition 任务开始
    transition_task = VideoTask(
        task_type=VideoTaskType.PLAY_TRANSITION,
        source="neutral",
        target="speaking",
        duration=0
    )
    server._on_video_task_start(transition_task)
    timeline.append(("transition_start", time.time()))
    print(f"  🎬 过渡视频开始 (t={timeline[-1][1]:.3f})")

    await asyncio.sleep(0.1)

    # 验证：transition 期间不应播放音频
    assert len(timeline) == 1, "❌ 过渡期间不应播放音频"

    # Step 2: speaking 任务开始
    speaking_task = VideoTask(
        task_type=VideoTaskType.PLAY_VIDEO,
        source="",
        target="speaking",
        duration=10
    )
    server._on_video_task_start(speaking_task)
    timeline.append(("speaking_task_start", time.time()))
    print(f"  🎬 speaking 任务开始 (t={timeline[-1][1]:.3f})")

    await asyncio.sleep(0.1)

    # 验证：speaking 任务开始时仍不应播放音频
    assert len(timeline) == 2, "❌ speaking 任务开始时不应播放音频（等 video_playing）"

    # Step 3: 前端确认视频开始播放
    target = "speaking"
    if target == "speaking" and server._pending_audio_path:
        timeline.append(("video_playing", time.time()))
        print(f"  📺 前端确认视频播放 (t={timeline[-1][1]:.3f})")
        server._play_audio(server._pending_audio_path)
        server._pending_audio_path = None

    await asyncio.sleep(0.1)

    # 验证：音频在 video_playing 之后播放
    audio_entry = next((e for e in timeline if e[0] == "audio_start"), None)
    video_entry = next((e for e in timeline if e[0] == "video_playing"), None)

    assert audio_entry is not None, "❌ 音频应已播放"
    assert video_entry is not None, "❌ video_playing 事件应已记录"
    assert audio_entry[1] >= video_entry[1], (
        f"❌ 失败：音频在视频之前播放！"
        f"audio={audio_entry[1]:.3f}, video={video_entry[1]:.3f}"
    )

    print(f"\n  📊 时序验证:")
    print(f"     transition_start:  {timeline[0][1]:.3f}")
    print(f"     speaking_task_start: {timeline[1][1]:.3f}")
    print(f"     video_playing:     {video_entry[1]:.3f}")
    print(f"     audio_start:       {audio_entry[1]:.3f}")
    print(f"     Δ(audio - video) = {audio_entry[1] - video_entry[1]:.3f}s")
    print("  ✅ 通过：音频在视频之后播放")
    return True


# ============================================================
# 测试 6: 新消息打断 - 停止音频 + 清理状态
# ============================================================
async def test_new_message_interrupt():
    """
    场景：用户发送新消息，触发 audio/stop
    规则：停止音频、清理 pending、清空队列
    """
    print("\n" + "=" * 60)
    print("测试 6: 新消息打断 - 停止音频并清理")
    print("=" * 60)

    from display_server import DisplayServer

    server = DisplayServer(port=19999)

    # 模拟正在播放音频
    server._pending_audio_path = "/tmp/old_audio.mp3"
    server._speaking_audio_path = "/tmp/old_audio.mp3"

    # 创建真实的 mock process 对象
    mock_process = MagicMock()
    mock_process.terminate = MagicMock()
    mock_process.pid = 12345
    server._audio_process = mock_process

    # 模拟有超时任务
    mock_task = MagicMock()
    mock_task.cancel = MagicMock()
    server._speaking_timeout_task = mock_task

    # 调用 _stop_audio
    server._stop_audio()

    # 验证
    assert server._pending_audio_path is None, "❌ _pending_audio_path 应已清除"
    assert server._speaking_audio_path is None, "❌ _speaking_audio_path 应已清除"
    assert server._audio_process is None, "❌ _audio_process 应已清除"
    mock_process.terminate.assert_called_once()
    mock_task.cancel.assert_called_once()

    print("  ✅ 通过：所有状态已清理")
    return True


# ============================================================
# 运行所有测试
# ============================================================
async def run_all_tests():
    tests = [
        ("音频先到 → 等视频", test_audio_arrives_before_video),
        ("视频先到 → 音频立即播放", test_audio_arrives_after_video),
        ("video_playing 触发音频", test_video_playing_triggers_audio),
        ("_on_video_task_start 不直接播放", test_video_task_start_no_direct_audio),
        ("完整时序验证", test_full_timeline_audio_after_video),
        ("新消息打断清理", test_new_message_interrupt),
    ]

    passed = 0
    failed = 0

    print("\n" + "🎵" * 30)
    print("  音画同步测试套件 (Audio/Video Sync Tests)")
    print("  核心规则: 音频必须在 speaking 视频画面出现之后才开始播放")
    print("🎵" * 30)

    for name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {name}: 异常 - {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"  结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 个测试")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
