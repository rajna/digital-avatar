# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Display Server - Web 展示服务"""
from __future__ import annotations

import asyncio
import json
import webbrowser
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from transition_manager import TransitionManager
from video_queue import VideoQueue, VideoTask, VideoTaskType

# 配置日志文件
logger.add(
    Path.home() / ".nanobot" / "logs" / "display_server.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)


class DisplayServer:
    def __init__(self, port: int = 18791, avatar_dir: Optional[Path] = None, assets_dir: Optional[Path] = None):
        self.port = port
        self.avatar_dir = avatar_dir or Path.home() / ".nanobot" / ".avatar"
        self.avatar_dir.mkdir(parents=True, exist_ok=True)
        self._server = None
        self._state = {"expression": "neutral", "status": "就绪", "bubble_text": "", "name": "火灵"}

        # 视频文件映射
        self._videos = {}
        self._assets_dir = assets_dir

        # 加载所有视频
        self._load_all_videos()

        # 过渡管理器（在_load_all_videos之后初始化，确保_assets_dir已设置）
        self._transition_manager = TransitionManager(self._assets_dir)

        # 视频播放队列
        self._video_queue = VideoQueue()
        self._video_queue.set_task_callback(self._on_video_task_start)
        self._video_queue.set_completion_callback(self._on_video_task_complete)

        # 说话超时任务
        self._speaking_timeout_task = None

        # 模式管理：normal（真人）或 pet（灵宠）
        self._mode = "normal"  # 当前模式

        # 过渡相关
        self._last_expression = "neutral"
        self._transition_lock = asyncio.Lock()
        self._is_transitioning = False
        self._pending_duration = 0  # 待处理的自动重置时长

        # 音频文件路径（speaking对应的音频）
        self._speaking_audio_path = None
        self._pending_audio_path = None  # 待播放的音频（TTS已生成，等待视频就绪后播放）
        self._audio_process = None  # 当前正在播放的音频进程

        # WebSocket 连接
        self._websocket_clients = set()

    def _load_all_videos(self) -> None:
        """加载所有状态的视频"""
        if self._assets_dir is None:
            # 从当前文件位置找到 assets 目录
            current_file = Path(__file__)
            skill_dir = current_file.parent.parent
            self._assets_dir = skill_dir / "assets"

        # 加载 speaking 视频优先
        speaking_dir = self._assets_dir / "speaking"
        if speaking_dir.exists():
            videos = list(speaking_dir.glob("*.mp4"))
            if videos:
                self._videos["speaking"] = videos[0]
                logger.info(f"加载了说话视频: {videos[0].name}")

        # 加载 neutral 视频优先
        neutral_dir = self._assets_dir / "neutral"
        if neutral_dir.exists():
            videos = list(neutral_dir.glob("*.mp4"))
            if videos:
                self._videos["neutral"] = videos[0]
                logger.info(f"加载了正常状态视频: {videos[0].name}")

        # 加载 pet 模式视频
        pet_neutral_dir = self._assets_dir / "pet" / "neutral"
        if pet_neutral_dir.exists():
            videos = list(pet_neutral_dir.glob("*.mp4"))
            if videos:
                self._videos["pet-neutral"] = videos[0]
                logger.info(f"加载了灵宠待机视频: {videos[0].name}")

        # 加载 pet speaking 视频
        pet_speaking_dir = self._assets_dir / "pet" / "speaking"
        if pet_speaking_dir.exists():
            videos = list(pet_speaking_dir.glob("*.mp4"))
            if videos:
                self._videos["pet-speaking"] = videos[0]
                logger.info(f"加载了灵宠说话视频: {videos[0].name}")

        # 加载 pet expressions 目录下的视频
        pet_expressions_dir = self._assets_dir / "pet" / "expressions"
        if pet_expressions_dir.exists():
            videos = list(pet_expressions_dir.glob("*.mp4"))
            for video in videos:
                # 从文件名提取表情名称，如 "pet-expression-working.mp4" -> "pet-working"
                name = video.stem
                if name.startswith("pet-expression-"):
                    expression = name.replace("pet-expression-", "")
                    key = f"pet-{expression}"
                    self._videos[key] = video
                    logger.info(f"加载了灵宠表情视频: {key} -> {video.name}")

        # 加载 expressions 目录下的视频
        expressions_dir = self._assets_dir / "expressions"
        if expressions_dir.exists():
            videos = list(expressions_dir.glob("*.mp4"))
            for video in videos:
                # 从文件名提取表情名称，如 "my-avatar-expression-happy.mp4" -> "happy"
                name = video.stem
                if name.startswith("my-avatar-expression-"):
                    expression = name.replace("my-avatar-expression-", "")
                    self._videos[expression] = video
                    logger.info(f"加载了表情视频: {expression} -> {video.name}")

    def _get_expression_video(self, expression: str) -> Optional[Path]:
        """获取表情视频路径，根据当前模式映射"""
        if self._mode == "pet":
            # pet 模式下：只查找 pet-{expression} 对应的视频
            pet_key = f"pet-{expression}"
            return self._videos.get(pet_key)
        return self._videos.get(expression)

    def _get_transition_video(self, source_state: str, target_state: str) -> Optional[Path]:
        """获取过渡视频路径，根据当前模式映射"""
        if self._mode == "pet":
            # pet 模式下优先查找 pet-{source}-{target}.mp4
            pet_key = f"pet-{source_state}-{target_state}"
            pet_video = self._transition_manager.get_transition_video(pet_key, "")
            if pet_video:
                return pet_video
            # 也尝试 source=pet-neutral, target=pet-speaking 等组合
            pet_source = f"pet-{source_state}" if not source_state.startswith("pet-") else source_state
            pet_target = f"pet-{target_state}" if not target_state.startswith("pet-") else target_state
            pet_video = self._transition_manager.get_transition_video(pet_source, pet_target)
            if pet_video:
                return pet_video
            # 回退：检查基础过渡视频（用于跨模式过渡，如 working→pet）
            base_video = self._transition_manager.get_transition_video(source_state, target_state)
            if base_video:
                return base_video
            return None
        return self._transition_manager.get_transition_video(source_state, target_state)

    def _has_transition(self, source_state: str, target_state: str) -> bool:
        """检查是否存在过渡视频，根据当前模式映射"""
        if self._mode == "pet":
            # pet 模式下检查 pet 版本的过渡视频
            pet_source = f"pet-{source_state}" if not source_state.startswith("pet-") else source_state
            pet_target = f"pet-{target_state}" if not target_state.startswith("pet-") else target_state
            if self._transition_manager.has_transition(pet_source, pet_target):
                return True
            # 也尝试 pet-{source}-{target} 格式
            if self._transition_manager.has_transition(f"pet-{source_state}-{target_state}", ""):
                return True
            # 回退：检查基础过渡视频（用于跨模式过渡，如 working→pet）
            if self._transition_manager.has_transition(source_state, target_state):
                return True
            return False
        return self._transition_manager.has_transition(source_state, target_state)

    def _get_expression_image(self, expression: str) -> Optional[Path]:
        """获取表情图片路径"""
        if self._assets_dir is None:
            return None

        # 检查 expressions 目录
        expressions_dir = self._assets_dir / "expressions"
        if expressions_dir.exists():
            # 查找对应的表情图片
            pattern = f"*{expression}*.png"
            images = list(expressions_dir.glob(pattern))
            if images:
                return images[0]

        # 检查 neutral 目录
        if expression == "neutral":
            neutral_dir = self._assets_dir / "neutral"
            if neutral_dir.exists():
                images = list(neutral_dir.glob("*.png"))
                if images:
                    return images[0]

        return None

    async def start(self, auto_open: bool = True) -> None:
        from aiohttp import web

        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/avatar.png", self._handle_avatar)
        app.router.add_get("/video/{expression}", self._handle_video)
        app.router.add_get("/transition/{source}/{target}", self._handle_transition)
        app.router.add_get("/state", self._handle_state)
        app.router.add_get("/queue", self._handle_queue_status)
        app.router.add_post("/update", self._handle_update)
        app.router.add_post("/queue/complete", self._handle_queue_complete)
        app.router.add_post("/audio/start", self._handle_audio_start)
        app.router.add_post("/audio/stop", self._handle_audio_stop)
        app.router.add_post("/reset", self._handle_reset)
        app.router.add_post("/mode", self._handle_mode)
        app.router.add_get("/mode", self._handle_get_mode)
        app.router.add_get("/ws", self._handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        self._server = (runner, site)

        # 启动视频队列处理
        await self._video_queue.start_processing()

        logger.info(f"Avatar display server: http://127.0.0.1:{self.port}")
        if auto_open:
            await asyncio.sleep(0.5)
            webbrowser.open(f"http://127.0.0.1:{self.port}")

    async def update_avatar(self, image_path: str) -> None:
        import shutil
        src, dst = Path(image_path), self.avatar_dir / "avatar.png"
        if src.exists():
            shutil.copy(src, dst)

    async def update_expression(self, expression: str, duration: int = 0, skip_cancel_timeout: bool = False) -> None:
        """更新表情，可选指定自动重置时间

        Args:
            expression: 表情名称
            duration: 自动重置时间（秒），0表示不自动重置
            skip_cancel_timeout: 是否跳过取消超时任务（用于自动重置）
        """
        # 使用锁防止并发更新
        async with self._transition_lock:
            self._last_expression = self._state["expression"]

            # 调试日志
            logger.info(f"DisplayServer: update_expression 调用 - 当前状态: {self._last_expression}, 目标状态: {expression}, 模式: {self._mode}")

            # 检查当前状态是否已经是目标状态
            if self._last_expression == expression:
                logger.info(f"DisplayServer: 当前状态已经是目标状态 {expression}，跳过更新")
                return

            # 检查当前状态是否是过渡状态，如果是，提取过渡的目标状态
            if self._last_expression.startswith("transition:"):
                transition_target = self._last_expression.split("->")[-1]
                if transition_target == expression:
                    logger.info(f"DisplayServer: 当前过渡状态的目标状态已经是 {expression}，跳过更新")
                    return
                self._last_expression = transition_target
                logger.info(f"DisplayServer: 当前状态是过渡状态，使用目标状态 {self._last_expression}")

            # 取消之前的超时任务（除非是自动重置调用）
            if not skip_cancel_timeout and self._speaking_timeout_task:
                self._speaking_timeout_task.cancel()
                self._speaking_timeout_task = None

            # 检查是否需要过渡
            has_transition = self._has_transition(self._last_expression, expression)
            logger.info(f"DisplayServer: 检查过渡视频 {self._last_expression} -> {expression}: {has_transition}")

            if has_transition:
                # 使用过渡动画
                logger.info(f"DisplayServer: 添加过渡任务到队列 {self._last_expression} -> {expression}")
                await self._video_queue.add_transition_task(
                    source=self._last_expression,
                    target=expression,
                    duration=0
                )
                logger.info(f"DisplayServer: 添加目标视频任务到队列 {expression}")
                await self._video_queue.add_video_task(
                    target=expression,
                    duration=duration
                )
            else:
                # 直接切换
                video = self._get_expression_video(expression)
                logger.info(f"DisplayServer: 添加视频任务到队列 {expression}, 视频映射结果: {video}")
                if video:
                    await self._video_queue.add_video_task(
                        target=expression,
                        duration=duration
                    )
                else:
                    # 没有对应视频（如 pet 模式下没有灵宠 working 视频），跳过不播放
                    logger.info(f"DisplayServer: 没有对应视频，跳过播放 {expression}")

    def get_last_expression(self) -> str:
        """获取上一个表情"""
        return self._last_expression

    async def _reset_expression_after_delay(self, delay: int):
        """延迟后重置表情为 neutral（由 _get_expression_video 根据模式自动映射视频）"""
        try:
            await asyncio.sleep(delay)
            logger.info(f"DisplayServer: 自动重置表情为 neutral（当前模式: {self._mode}）")
            await self.update_expression("neutral", 0, skip_cancel_timeout=True)
        except asyncio.CancelledError:
            logger.info(f"DisplayServer: 自动重置任务被取消")
        except Exception as e:
            logger.error(f"DisplayServer: 自动重置表情失败 - {e}")

    async def update_status(self, status: str) -> None:
        self._state["status"] = status

    async def show_bubble(self, text: str) -> None:
        self._state["bubble_text"] = text
        async def clear():
            await asyncio.sleep(3)
            self._state["bubble_text"] = ""
        asyncio.create_task(clear())

    async def set_name(self, name: str) -> None:
        self._state["name"] = name

    async def _handle_index(self, request) -> Any:
        from aiohttp import web
        return web.Response(text=self._get_html(), content_type="text/html")

    async def _handle_avatar(self, request) -> Any:
        from aiohttp import web
        avatar_path = self.avatar_dir / "avatar.png"
        return web.FileResponse(avatar_path) if avatar_path.exists() else web.Response(status=404)

    async def _handle_video(self, request) -> Any:
        from aiohttp import web
        expression = request.match_info.get("expression", "neutral")
        video_path = self._get_expression_video(expression)
        if video_path and video_path.exists():
            return web.FileResponse(video_path)
        return web.Response(status=404)

    async def _handle_transition(self, request) -> Any:
        from aiohttp import web
        source_state = request.match_info.get("source", "neutral")
        target_state = request.match_info.get("target", "working")
        video_path = self._get_transition_video(source_state, target_state)
        if video_path and video_path.exists():
            return web.FileResponse(video_path)
        return web.Response(status=404)

    async def _handle_state(self, request) -> Any:
        from aiohttp import web
        logger.debug(f"DisplayServer: 状态查询 - {self._state['expression']}")
        return web.json_response(self._state)

    async def _handle_update(self, request) -> Any:
        from aiohttp import web
        data = await request.json()

        logger.info(f"DisplayServer: _handle_update 收到请求 - {data}")

        # 如果有 expression 字段，调用 update_expression
        if "expression" in data:
            duration = data.get("duration", 0)
            await self.update_expression(data["expression"], duration)

        # 更新其他状态（排除 duration 和 expression，因为它们已经被 update_expression 处理）
        update_data = {k: v for k, v in data.items() if k not in ["duration", "expression"]}
        if update_data:
            logger.info(f"DisplayServer: _handle_update 更新状态 - {update_data}")
            self._state.update(update_data)
        return web.json_response({"success": True})

    async def _handle_audio_start(self, request) -> Any:
        """处理音频就绪通知：存储音频路径，等speaking视频就绪后播放
        
        音画同步规则：
        - 如果speaking视频已经在播放 → 立即播放音频
        - 如果speaking视频还没开始 → 存储路径，等前端 video_playing 通知后播放
        """
        from aiohttp import web
        data = await request.json()

        logger.info(f"DisplayServer: _handle_audio_start 收到请求 - {data}")

        # 注册speaking对应的音频文件路径
        if "audio_path" in data:
            self._speaking_audio_path = data["audio_path"]
            self._pending_audio_path = data["audio_path"]
            logger.info(f"DisplayServer: 已注册speaking音频文件 - {self._speaking_audio_path}")

            # ✅ 音画同步：只在speaking视频已经在播放时才立即播放音频
            # 否则存储路径，等前端 video_playing WebSocket 通知后播放
            if self._state.get("expression") == "speaking":
                logger.info(f"DisplayServer: speaking视频已在播放，立即播放音频 - {self._pending_audio_path}")
                self._play_audio(self._pending_audio_path)
                self._pending_audio_path = None
            else:
                logger.info(f"DisplayServer: speaking视频未开始，等待 video_playing 通知后播放音频")

            # ✅ 如果传入了音频时长，更新speaking视频的自动重置时长
            if "audio_duration" in data and data["audio_duration"] > 0:
                audio_duration = data["audio_duration"]
                logger.info(f"DisplayServer: 收到音频时长 {audio_duration}s，更新speaking自动重置")

                # 取消之前的超时任务
                if self._speaking_timeout_task:
                    self._speaking_timeout_task.cancel()
                    self._speaking_timeout_task = None

                # 用实际音频时长设置新的自动重置
                self._speaking_timeout_task = asyncio.create_task(
                    self._reset_expression_after_delay(audio_duration)
                )
                logger.info(f"DisplayServer: 已设置speaking将在 {audio_duration}s 后自动重置为neutral")

        return web.json_response({"success": True})

    def _on_video_task_start(self, task: VideoTask) -> None:
        """视频任务开始时的回调"""
        logger.info(f"DisplayServer: 视频任务开始 - {task}")

        # 更新状态
        if task.task_type == VideoTaskType.PLAY_TRANSITION:
            self._state["expression"] = f"transition:{task.source}->{task.target}"
        else:
            self._state["expression"] = task.target

        # ✅ 音画同步：speaking 视频任务开始时，如果有待播放的音频，立即播放
        # 必须是 PLAY_VIDEO 类型（非过渡任务），因为过渡任务的 target 也可能是 "speaking"
        if task.target == "speaking" and self._pending_audio_path and task.task_type == VideoTaskType.PLAY_VIDEO:
            logger.info(f"DisplayServer: speaking视频任务开始，播放待播放音频 - {self._pending_audio_path}")
            self._play_audio(self._pending_audio_path)
            self._pending_audio_path = None

        # 通过 WebSocket 通知所有客户端
        self._broadcast_to_websockets({
            "type": "video_task_start",
            "task": {
                "task_type": task.task_type.value,
                "source": task.source,
                "target": task.target,
                "duration": task.duration
            }
        })

    def _on_video_task_complete(self, task: VideoTask) -> None:
        """视频任务完成时的回调"""
        logger.info(f"DisplayServer: 视频任务完成 - {task}")

        # ✅ 修复：如果已经有自动重置任务（由 _handle_audio_start 设置），不要覆盖它
        # 这确保使用实际的音频时长而不是估算的 duration
        if task.duration > 0 and self._speaking_timeout_task is None:
            self._speaking_timeout_task = asyncio.create_task(
                self._reset_expression_after_delay(task.duration)
            )
            logger.info(f"DisplayServer: 已设置表情 {task.target}，将在 {task.duration} 秒后自动重置")
        elif self._speaking_timeout_task is not None:
            logger.info(f"DisplayServer: 跳过设置自动重置，因为已有定时器在运行（可能由音频时长设置）")

        # 通过 WebSocket 通知所有客户端
        self._broadcast_to_websockets({
            "type": "video_task_complete",
            "task": {
                "task_type": task.task_type.value,
                "source": task.source,
                "target": task.target,
                "duration": task.duration
            }
        })

    def _broadcast_to_websockets(self, message: dict) -> None:
        """向所有 WebSocket 客户端广播消息"""
        if not self._websocket_clients:
            return

        message_str = json.dumps(message)
        # 创建副本以避免在迭代时修改集合
        clients = list(self._websocket_clients)

        for ws in clients:
            try:
                asyncio.create_task(ws.send_str(message_str))
            except Exception as e:
                logger.error(f"DisplayServer: 发送 WebSocket 消息失败 - {e}")

    def _play_audio(self, audio_file: str) -> None:
        """播放音频文件（非阻塞）"""
        from pathlib import Path
        import subprocess
        import platform

        logger.info(f"DisplayServer: _play_audio 被调用 - {audio_file}")

        if not Path(audio_file).exists():
            logger.warning(f"DisplayServer: 音频文件不存在 - {audio_file}")
            return

        # 先停止当前正在播放的音频
        self._stop_audio()

        try:
            system = platform.system()
            logger.info(f"DisplayServer: 系统类型 - {system}")

            if system == "Darwin":
                logger.info(f"DisplayServer: 使用 afplay 播放音频 - {audio_file}")
                process = subprocess.Popen(
                    ["afplay", audio_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"DisplayServer: afplay 进程已启动 - PID: {process.pid}")
            elif system == "Linux":
                logger.info(f"DisplayServer: 使用 aplay 播放音频 - {audio_file}")
                process = subprocess.Popen(
                    ["aplay", audio_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"DisplayServer: aplay 进程已启动 - PID: {process.pid}")
            elif system == "Windows":
                logger.info(f"DisplayServer: 使用 powershell 播放音频 - {audio_file}")
                process = subprocess.Popen(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"DisplayServer: powershell 进程已启动 - PID: {process.pid}")

            self._audio_process = process
            logger.info(f"DisplayServer: 已发送音频播放命令 - {audio_file}")
        except FileNotFoundError as e:
            logger.error(f"DisplayServer: 音频播放命令未找到 - {e}")
        except Exception as e:
            logger.error(f"DisplayServer: 播放音频失败 - {e}")

    def _stop_audio(self) -> None:
        """停止当前正在播放的音频，并清理所有相关状态"""
        # 1. 终止音频进程
        if self._audio_process is not None:
            try:
                self._audio_process.terminate()
                logger.info(f"DisplayServer: 已停止音频播放 - PID: {self._audio_process.pid}")
            except Exception as e:
                logger.warning(f"DisplayServer: 停止音频失败 - {e}")
            self._audio_process = None

        # 2. 清理待播放音频路径
        if self._pending_audio_path is not None:
            logger.info(f"DisplayServer: 已清理待播放音频 - {self._pending_audio_path}")
            self._pending_audio_path = None

        # 3. 清理speaking音频路径
        self._speaking_audio_path = None

        # 4. 取消speaking自动重置定时器
        if self._speaking_timeout_task is not None:
            self._speaking_timeout_task.cancel()
            self._speaking_timeout_task = None
            logger.info("DisplayServer: 已取消speaking自动重置定时器")

    async def _handle_audio_stop(self, request) -> Any:
        """处理停止音频请求 — 停止音频并清空队列"""
        from aiohttp import web

        # 1. 停止音频并清理所有相关状态
        self._stop_audio()

        # 2. 清空视频队列中所有待执行的任务
        cleared = self._video_queue.clear_pending_tasks()
        if cleared > 0:
            logger.info(f"DisplayServer: 已清空队列中 {cleared} 个待执行任务")

        # 3. 修复状态卡死：如果当前状态是过渡状态，直接重置为目标状态
        current_expr = self._state.get("expression", "")
        if current_expr.startswith("transition:"):
            target = current_expr.split("->")[-1]
            self._state["expression"] = target
            logger.info(f"DisplayServer: audio_stop 修复过渡状态卡死: {current_expr} -> {target}")

        return web.json_response({"status": "ok", "message": "audio stopped", "cleared_tasks": cleared})

    async def _handle_reset(self, request) -> Any:
        """重置到 neutral（由 _get_expression_video 根据模式自动映射视频）"""
        from aiohttp import web
        logger.info(f"DisplayServer: 收到重置请求，目标为 neutral（当前模式: {self._mode}）")

        # 强制重置：直接设置状态，绕过 update_expression 的跳过逻辑
        # （防止状态卡在 transition:xxx->yyy 时 update_expression 跳过更新）
        self._state["expression"] = "neutral"
        self._last_expression = "neutral"
        logger.info(f"DisplayServer: 强制重置状态为 neutral")

        # 清空队列并添加 neutral 视频任务
        self._video_queue.clear_pending_tasks()
        if "neutral" in self._videos or self._get_expression_video("neutral"):
            await self._video_queue.add_video_task(target="neutral", duration=0)

        return web.json_response({"success": True, "target": "neutral"})

    async def _handle_mode(self, request) -> Any:
        """切换模式：normal（真人）或 pet（灵宠）"""
        from aiohttp import web
        data = await request.json()
        new_mode = data.get("mode", "normal")

        if new_mode not in ("normal", "pet"):
            return web.json_response({"success": False, "error": f"无效模式: {new_mode}"}, status=400)

        old_mode = self._mode
        self._mode = new_mode

        # 强制重置状态，防止卡在过渡状态
        self._state["expression"] = "neutral"
        self._last_expression = ""
        logger.info(f"DisplayServer: 模式切换 {old_mode} -> {self._mode}，强制重置状态")

        # 清空队列
        self._video_queue.clear_pending_tasks()

        if new_mode == "pet" and old_mode == "normal":
            # 真人→灵宠：播放 working-pet 过渡视频，然后播放 pet-neutral
            if self._has_transition("working", "pet"):
                logger.info(f"DisplayServer: 添加 working→pet 过渡任务")
                await self._video_queue.add_transition_task(source="working", target="pet", duration=0)
            await self._video_queue.add_video_task(target="neutral", duration=0)
        else:
            # 直接切换（pet→normal 或相同模式）
            if "neutral" in self._videos or self._get_expression_video("neutral"):
                await self._video_queue.add_video_task(target="neutral", duration=0)

        return web.json_response({"success": True, "mode": self._mode, "previous_mode": old_mode})

    async def _handle_get_mode(self, request) -> Any:
        """获取当前模式"""
        from aiohttp import web
        return web.json_response({"mode": self._mode})

    async def _handle_websocket(self, request) -> Any:
        """处理 WebSocket 连接"""
        from aiohttp import web
        from aiohttp import WSMsgType

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._websocket_clients.add(ws)
        logger.info(f"DisplayServer: WebSocket 客户端连接，当前连接数: {len(self._websocket_clients)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        logger.info(f"DisplayServer: 收到 WebSocket 消息 - {data}")

                        # 处理任务完成通知
                        if data.get("type") == "task_complete":
                            self._video_queue.mark_task_completed()

                        # 处理视频真正开始播放的通知（用于音视频同步）
                        elif data.get("type") == "video_playing":
                            target = data.get("target", "")
                            logger.info(f"DisplayServer: 前端通知视频开始播放 - target={target}, pending_audio={self._pending_audio_path}")
                            if target == "speaking" and self._pending_audio_path:
                                logger.info(f"DisplayServer: 视频已开始播放，同步播放音频 - {self._pending_audio_path}")
                                self._play_audio(self._pending_audio_path)
                                self._pending_audio_path = None

                    except json.JSONDecodeError as e:
                        logger.error(f"DisplayServer: WebSocket 消息解析失败 - {e}")
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"DisplayServer: WebSocket 错误 - {ws.exception()}")

        except Exception as e:
            logger.error(f"DisplayServer: WebSocket 连接错误 - {e}")
        finally:
            self._websocket_clients.discard(ws)
            logger.info(f"DisplayServer: WebSocket 客户端断开，当前连接数: {len(self._websocket_clients)}")

        return ws

    async def _handle_queue_status(self, request) -> Any:
        """处理队列状态查询"""
        from aiohttp import web
        return web.json_response(self._video_queue.get_queue_status())

    async def stop(self) -> None:
        """停止服务器"""
        if self._server:
            runner, site = self._server
            await site.stop()
            await runner.cleanup()
            self._server = None

        # 停止视频队列处理
        await self._video_queue.stop_processing()

        logger.info("DisplayServer: 服务器已停止")

    async def _handle_queue_complete(self, request) -> Any:
        """处理任务完成通知（HTTP 接口，备用）"""
        from aiohttp import web
        self._video_queue.mark_task_completed()
        return web.json_response({"success": True})

    def _get_html(self) -> str:
        return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>灵宠火灵通话中</title>
<style>*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#000;min-height:100vh;overflow:hidden;position:relative}
.video-background{position:fixed;top:0;left:0;width:100%;height:100%;z-index:1}
.video-background img,.video-background video{width:100%;height:100%;object-fit:cover}
.top-bar{position:fixed;top:0;left:0;right:0;z-index:10;padding:15px 20px;background:linear-gradient(to bottom,rgba(0,0,0,0.5),transparent);display:flex;align-items:center}
.back-btn{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,0.2);border:none;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;margin-right:15px;transition:all 0.2s ease}
.back-btn:hover{background:rgba(255,255,255,0.3)}
.back-btn svg{width:20px;height:20px;fill:#fff}
.caller-name{color:#fff;font-size:20px;font-weight:500;flex:1}
.pip-window{display:none;position:fixed;top:15px;right:15px;width:100px;height:140px;border-radius:12px;background:rgba(255,255,255,0.1);z-index:10;overflow:hidden;border:2px solid rgba(255,255,255,0.2)}
.pip-window img{width:100%;height:100%;object-fit:cover}
.bottom-bar{position:fixed;bottom:0;left:0;right:0;z-index:10;padding:40px 20px;background:linear-gradient(to top,rgba(0,0,0,0.7),transparent);display:flex;justify-content:center;gap:30px}
.control-btn{width:65px;height:65px;border-radius:50%;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s ease}
.control-btn:active{transform:scale(0.95)}
.control-btn svg{width:32px;height:32px;fill:#fff}
.control-btn.end-call{background:#ff4d4f}
.control-btn.end-call:active{background:#ff7875}
.control-btn.active{background:rgba(255,255,255,0.4)}
.subtitle{position:fixed;bottom:150px;left:20px;right:20px;z-index:10;text-align:center}
.subtitle-text{display:inline-block;background:rgba(0,0,0,0.6);color:#fff;padding:10px 18px;border-radius:18px;font-size:15px;max-width:85%;line-height:1.5;animation:fadeIn 0.3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.emoji-indicator{position:fixed;top:80px;left:20px;z-index:10;font-size:36px;animation:bounce 0.4s ease}
@keyframes bounce{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}</style></head>
<body>
<div class="video-background">
<img id="avatar" src="/avatar.png" style="display:block">
<video id="avatar-video-1" loop muted autoplay playsinline style="display:none"></video>
<video id="avatar-video-2" loop muted autoplay playsinline style="display:none"></video>
</div>
<div class="top-bar">
<button class="back-btn" onclick="goBack()">
<svg viewBox="0 0 24 24"><path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/></svg>
</button>
<div class="caller-name" id="name">火灵</div>
</div>
<div class="emoji-indicator" id="emoji-indicator" style="display:none">😊</div>
<div class="pip-window">
<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 140'%3E%3Crect fill='%23444' width='100' height='140'/%3E%3Ctext x='50' y='70' text-anchor='middle' fill='%23888' font-size='20'%3E👤%3C/text%3E%3C/svg%3E">
</div>
<div class="subtitle">
<div class="subtitle-text" id="bubble"></div>
</div>
<div class="bottom-bar">
<button class="control-btn" id="mute-btn" onclick="toggleMute()">
<svg id="mute-icon" viewBox="0 0 24 24"><path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l2.97 2.97c-.85.35-1.76.57-2.75.57-2.76 0-5.3-1.12-7.1-2.93L4.27 3z"/></svg>
</button>
<button class="control-btn" id="camera-btn" onclick="switchCamera()">
<svg viewBox="0 0 24 24"><path d="M9 3L7.17 5H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2h-3.17L15 3H9zm3 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>
</button>
<button class="control-btn end-call" onclick="endCall()">
<svg viewBox="0 0 24 24"><path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/></svg>
</button>
<button class="control-btn" id="speaker-btn" onclick="toggleSpeaker()">
<svg id="speaker-icon" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
</button>
</div>
<script>
const emojis={neutral:"😊",happy:"😄",thinking:"🤔",sad:"😢",surprised:"😲",confused:"😕",working:"💼",speaking:"🗣️",pet:"🐱"};
let lastExpression="",isMuted=true,isSpeakerOn=true,currentVideo=1,isTransitioning=false,transitionSource="",transitionTarget="";
let ws=null; // WebSocket 连接
let currentTask=null; // 当前正在执行的任务

function goBack(){console.log("返回");}
function toggleMute(){isMuted=!isMuted;const btn=document.getElementById("mute-btn");const icon=document.getElementById("mute-icon");
if(isMuted){icon.innerHTML='<path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l2.97 2.97c-.85.35-1.76.57-2.75.57-2.76 0-5.3-1.12-7.1-2.93L4.27 3z"/>';}
else{icon.innerHTML='<path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>';}
btn.classList.toggle("active",!isMuted);}
function switchCamera(){console.log("切换摄像头");}
function endCall(){console.log("结束通话");}
function toggleSpeaker(){isSpeakerOn=!isSpeakerOn;const btn=document.getElementById("speaker-btn");const icon=document.getElementById("speaker-icon");
if(isSpeakerOn){icon.innerHTML='<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>';}
else{icon.innerHTML='<path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>';}
btn.classList.toggle("active",!isSpeakerOn);}


// WebSocket 连接
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = protocol + '//' + window.location.host + '/ws';
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log("✅ WebSocket 连接成功");
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            console.log("📨 收到 WebSocket 消息:", data);
            
            if (data.type === "video_task_start") {
                handleVideoTask(data.task);
            } else if (data.type === "video_task_complete") {
                console.log("✅ 视频任务完成:", data.task);
            }
        } catch (e) {
            console.error("❌ 解析 WebSocket 消息失败:", e);
        }
    };
    
    ws.onerror = function(error) {
        console.error("❌ WebSocket 错误:", error);
    };
    
    ws.onclose = function() {
        console.log("🔌 WebSocket 连接关闭，5秒后重连...");
        setTimeout(connectWebSocket, 5000);
    };
}

// 通知服务器任务完成
function notifyTaskComplete() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "task_complete" }));
        console.log("✅ 已通知服务器任务完成");
    } else {
        // 如果 WebSocket 不可用，使用 HTTP 接口
        fetch("/queue/complete", { method: "POST" })
            .then(() => console.log("✅ 已通过 HTTP 通知服务器任务完成"))
            .catch(e => console.error("❌ 通知任务完成失败:", e));
    }
}

// ✅ 通知服务器视频已真正开始播放（用于音视频同步）
function notifyVideoPlaying(target) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "video_playing", target: target }));
        console.log("✅ 已通知服务器视频开始播放:", target);
    }
}

// 处理视频任务
async function handleVideoTask(task) {
    console.log("🎬 开始处理视频任务:", task);
    currentTask = task;

    const avatarImg = document.getElementById("avatar");
    avatarImg.style.display = "none";

    const currentVideoEl = document.getElementById("avatar-video-" + currentVideo);
    const nextVideo = currentVideo === 1 ? 2 : 1;
    const nextVideoEl = document.getElementById("avatar-video-" + nextVideo);

    try {
        if (task.task_type === "play_transition") {
            // 播放过渡视频
            console.log("▶️ 播放过渡视频:", task.source, "->", task.target);
            const transitionUrl = "/transition/" + task.source + "/" + task.target + "?t=" + Date.now();

            // 预加载过渡视频
            await preloadVideo(nextVideoEl, transitionUrl);

            // 立即切换到过渡视频
            currentVideoEl.style.display = "none";
            currentVideoEl.pause();
            currentVideoEl.loop = false;

            nextVideoEl.style.display = "block";
            nextVideoEl.loop = false;
            nextVideoEl.play();

            // 等待过渡视频播放完成
            await waitForVideoEnd(nextVideoEl);

            // 播放目标视频
            console.log("▶️ 播放目标视频:", task.target);
            const targetUrl = "/video/" + task.target + "?t=" + Date.now();

            // 预加载目标视频
            await preloadVideo(nextVideoEl, targetUrl);

            // 目标视频已经在 nextVideoEl 中，设置为循环播放并开始播放
            nextVideoEl.loop = true;
            nextVideoEl.play();

            // ✅ 通知服务器视频已开始播放（用于音视频同步）
            notifyVideoPlaying(task.target);

        } else if (task.task_type === "play_video") {
            // 直接播放视频
            console.log("▶️ 直接播放视频:", task.target);
            const videoUrl = "/video/" + task.target + "?t=" + Date.now();

            // 预加载视频
            await preloadVideo(nextVideoEl, videoUrl);

            // 立即切换到新视频
            currentVideoEl.style.display = "none";
            currentVideoEl.pause();
            currentVideoEl.loop = false;

            nextVideoEl.style.display = "block";
            nextVideoEl.loop = true;
            nextVideoEl.play();

            // ✅ 通知服务器视频已开始播放（用于音视频同步）
            notifyVideoPlaying(task.target);

        } else if (task.task_type === "show_image") {
            // 显示图片
            console.log("🖼️ 显示图片:", task.target);
            currentVideoEl.style.display = "none";
            currentVideoEl.pause();
            currentVideoEl.loop = false;

            nextVideoEl.style.display = "none";
            nextVideoEl.pause();
            nextVideoEl.loop = false;

            avatarImg.style.display = "block";
            avatarImg.src = "/avatar.png?t=" + Date.now();
        }

        currentVideo = nextVideo;

        // 通知服务器任务完成
        notifyTaskComplete();

    } catch (error) {
        console.error("❌ 视频任务执行失败:", error);
        // 如果失败，通知服务器任务完成
        notifyTaskComplete();
    }
}

// 预加载视频
function preloadVideo(videoEl, url) {
    return new Promise((resolve, reject) => {
        videoEl.src = url;
        videoEl.muted = true;

        // 清除之前的事件监听器
        videoEl.onloadeddata = null;
        videoEl.onerror = null;

        videoEl.onloadeddata = function() {
            console.log("✅ 视频预加载完成:", url);
            resolve();
        };

        videoEl.onerror = function(e) {
            console.error("❌ 视频预加载错误:", e);
            reject(e);
        };
    });
}

// 等待视频播放完成
function waitForVideoEnd(videoEl) {
    return new Promise((resolve) => {
        videoEl.onended = function() {
            console.log("✅ 视频播放完成");
            resolve();
        };
    });
}

async function update(){try{const r=await fetch("/state");const s=await r.json();
document.getElementById("name").textContent=s.name||"火灵";
const bubble=document.getElementById("bubble");
if(s.bubble_text){bubble.textContent=s.bubble_text;bubble.style.display="inline-block";}else{bubble.style.display="none";}
if(s.expression&&s.expression!==lastExpression){lastExpression=s.expression;
const emojiIndicator=document.getElementById("emoji-indicator");
if(emojis[s.expression]){emojiIndicator.textContent=emojis[s.expression];emojiIndicator.style.display="block";setTimeout(()=>{emojiIndicator.style.display="none";},2000);}}}
catch(e){console.log("更新错误:",e);}}
async function init(){try{const r=await fetch("/state");const s=await r.json();
const avatarImg=document.getElementById("avatar");
const avatarVideo1=document.getElementById("avatar-video-1");
const avatarVideo2=document.getElementById("avatar-video-2");
const videoUrl="/video/neutral";
console.log("初始化：检查neutral视频:",videoUrl);
const videoCheck=await fetch(videoUrl,{method:"HEAD"});
console.log("初始化：视频检查结果:",videoCheck.ok,videoCheck.status);
if(videoCheck.ok){console.log("初始化：neutral视频存在，使用视频模式");
avatarImg.style.display="none";avatarVideo1.style.display="block";avatarVideo2.style.display="none";
avatarVideo1.src=videoUrl+"?t="+Date.now();
avatarVideo1.loop=true;
avatarVideo1.onloadeddata=function(){console.log("初始化：neutral视频数据已加载，开始播放");avatarVideo1.play().catch(e=>console.log("初始化：视频播放失败:",e));};
avatarVideo1.onerror=function(e){console.log("初始化：视频加载错误:",e);};}else{console.log("初始化：neutral视频不存在，使用图片模式");
avatarVideo1.style.display="none";avatarVideo1.pause();avatarVideo2.style.display="none";avatarVideo2.pause();
avatarImg.style.display="block";avatarImg.src="/avatar.png?t="+Date.now();}}catch(e){console.log("初始化：初始化错误:",e);}}
setInterval(update,1000);init();connectWebSocket();
</script></body></html>'''


_server_instance: Optional[DisplayServer] = None

def get_server(port: int = 18791, assets_dir: Optional[Path] = None) -> DisplayServer:
    global _server_instance
    if _server_instance is None:
        _server_instance = DisplayServer(port=port, assets_dir=assets_dir)
    return _server_instance
