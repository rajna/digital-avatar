# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Display Server - Web 展示服务 (v2.1.0 - Config Driven)"""
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


def load_config() -> dict:
    """从 skill 目录的 config.json 加载配置"""
    # 获取 skill 目录（scripts 的父目录）
    skill_dir = Path(__file__).parent.parent
    config_path = skill_dir / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"DisplayServer: 读取 config.json 失败 - {e}")
    return {}


def get_avatar_config() -> tuple[str, int, bool]:
    """
    从 skill 目录的 config.json 获取 avatar 配置
    Returns: (avatar_id, port, auto_open)
    """
    config = load_config()
    
    avatar_id = config.get("avatar", "pet1")  # 默认 pet1
    port = config.get("display_port", 18791)
    auto_open = config.get("auto_open", True)
    
    return avatar_id, port, auto_open


class DisplayServer:
    def __init__(self, port: int = 18791, avatar_id: str = "pet1", assets_dir: Optional[Path] = None):
        self.port = port
        self.avatar_id = avatar_id  # pet1 或 pet2
        self.avatar_dir = Path.home() / ".nanobot" / ".avatar"
        self.avatar_dir.mkdir(parents=True, exist_ok=True)
        self._server = None
        self._state = {"expression": "neutral", "status": "就绪", "bubble_text": "", "name": "火灵"}

        # 设置资源目录
        if assets_dir is None:
            current_file = Path(__file__)
            skill_dir = current_file.parent.parent
            self._assets_dir = skill_dir / "assets"
        else:
            self._assets_dir = assets_dir

        # 角色专属资源目录
        self._avatar_assets_dir = self._assets_dir / avatar_id
        if not self._avatar_assets_dir.exists():
            logger.warning(f"DisplayServer: 角色目录不存在 {self._avatar_assets_dir}，回退到默认目录")
            self._avatar_assets_dir = self._assets_dir / "pet1"  # 回退到 pet1

        # 视频文件映射
        self._videos = {}
        
        # 加载所有视频
        self._load_all_videos()

        # 过渡管理器
        self._transition_manager = TransitionManager(self._avatar_assets_dir)

        # 视频播放队列
        self._video_queue = VideoQueue()
        self._video_queue.set_task_callback(self._on_video_task_start)
        self._video_queue.set_completion_callback(self._on_video_task_complete)

        # 说话超时任务
        self._speaking_timeout_task = None

        # 过渡相关
        self._last_expression = "neutral"
        self._transition_lock = asyncio.Lock()
        self._is_transitioning = False
        self._pending_duration = 0

        # 音频文件路径
        self._speaking_audio_path = None
        self._pending_audio_path = None
        self._audio_process = None

        # WebSocket 连接
        self._websocket_clients = set()

    def _load_all_videos(self) -> None:
        """加载所有状态的视频（从角色专属目录）"""
        assets = self._avatar_assets_dir
        
        if not assets.exists():
            logger.error(f"DisplayServer: 资源目录不存在 {assets}")
            return

        # 加载 speaking 视频
        speaking_dir = assets / "speaking"
        if speaking_dir.exists():
            videos = list(speaking_dir.glob("*.mp4"))
            if videos:
                self._videos["speaking"] = videos[0]
                logger.info(f"加载了说话视频: {videos[0].name}")

        # 加载 neutral 视频
        neutral_dir = assets / "neutral"
        if neutral_dir.exists():
            videos = list(neutral_dir.glob("*.mp4"))
            if videos:
                self._videos["neutral"] = videos[0]
                logger.info(f"加载了正常状态视频: {videos[0].name}")

        # 加载 expressions 目录下的视频
        expressions_dir = assets / "expressions"
        if expressions_dir.exists():
            videos = list(expressions_dir.glob("*.mp4"))
            for video in videos:
                # 从文件名提取表情名称，如 "expression-happy.mp4" -> "happy"
                name = video.stem
                if name.startswith("expression-"):
                    expression = name.replace("expression-", "")
                    self._videos[expression] = video
                    logger.info(f"加载了表情视频: {expression} -> {video.name}")

    def _get_expression_video(self, expression: str) -> Optional[Path]:
        """获取表情视频路径"""
        return self._videos.get(expression)

    def _get_transition_video(self, source_state: str, target_state: str) -> Optional[Path]:
        """获取过渡视频路径"""
        return self._transition_manager.get_transition_video(source_state, target_state)

    def _has_transition(self, source_state: str, target_state: str) -> bool:
        """检查是否存在过渡视频"""
        return self._transition_manager.has_transition(source_state, target_state)

    def _get_expression_image(self, expression: str) -> Optional[Path]:
        """获取表情图片路径"""
        expressions_dir = self._avatar_assets_dir / "expressions"
        if expressions_dir.exists():
            pattern = f"*{expression}*.png"
            images = list(expressions_dir.glob(pattern))
            if images:
                return images[0]

        neutral_dir = self._avatar_assets_dir / "neutral"
        if expression == "neutral" and neutral_dir.exists():
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
        app.router.add_get("/ws", self._handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", self.port)
        await site.start()
        self._server = (runner, site)

        # 启动视频队列处理
        await self._video_queue.start_processing()

        logger.info(f"Avatar display server: http://127.0.0.1:{self.port}")
        logger.info(f"当前角色: {self.avatar_id}")
        if auto_open:
            await asyncio.sleep(0.5)
            webbrowser.open(f"http://127.0.0.1:{self.port}")

    async def update_avatar(self, image_path: str) -> None:
        import shutil
        src, dst = Path(image_path), self.avatar_dir / "avatar.png"
        if src.exists():
            shutil.copy(src, dst)

    async def update_expression(self, expression: str, duration: int = 0, skip_cancel_timeout: bool = False) -> None:
        """更新表情，可选指定自动重置时间"""
        async with self._transition_lock:
            self._last_expression = self._state["expression"]

            logger.info(f"DisplayServer: update_expression 调用 - 当前: {self._last_expression}, 目标: {expression}")

            if self._last_expression == expression:
                logger.info(f"当前状态已经是 {expression}，跳过")
                return

            if self._last_expression.startswith("transition:"):
                transition_target = self._last_expression.split("->")[-1]
                if transition_target == expression:
                    logger.info(f"过渡目标已是 {expression}，跳过")
                    return
                self._last_expression = transition_target

            if not skip_cancel_timeout and self._speaking_timeout_task:
                self._speaking_timeout_task.cancel()
                self._speaking_timeout_task = None

            has_transition = self._has_transition(self._last_expression, expression)
            logger.info(f"检查过渡视频 {self._last_expression} -> {expression}: {has_transition}")

            if has_transition:
                await self._video_queue.add_transition_task(
                    source=self._last_expression,
                    target=expression,
                    duration=0
                )
                await self._video_queue.add_video_task(
                    target=expression,
                    duration=duration
                )
            else:
                video = self._get_expression_video(expression)
                if video:
                    await self._video_queue.add_video_task(
                        target=expression,
                        duration=duration
                    )
                else:
                    logger.warning(f"没有对应视频，跳过播放 {expression}")

    def get_last_expression(self) -> str:
        return self._last_expression

    async def _reset_expression_after_delay(self, delay: int):
        try:
            await asyncio.sleep(delay)
            logger.info(f"自动重置表情为 neutral")
            await self.update_expression("neutral", 0, skip_cancel_timeout=True)
        except asyncio.CancelledError:
            logger.info("自动重置任务被取消")
        except Exception as e:
            logger.error(f"自动重置表情失败 - {e}")

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
        return web.json_response(self._state)

    async def _handle_update(self, request) -> Any:
        from aiohttp import web
        data = await request.json()
        logger.info(f"_handle_update 收到请求 - {data}")

        if "expression" in data:
            duration = data.get("duration", 0)
            await self.update_expression(data["expression"], duration)

        update_data = {k: v for k, v in data.items() if k not in ["duration", "expression"]}
        if update_data:
            self._state.update(update_data)
        return web.json_response({"success": True})

    async def _handle_audio_start(self, request) -> Any:
        from aiohttp import web
        data = await request.json()
        logger.info(f"_handle_audio_start 收到请求 - {data}")

        if "audio_path" in data:
            self._speaking_audio_path = data["audio_path"]
            self._pending_audio_path = data["audio_path"]
            logger.info(f"已注册 speaking 音频 - {self._speaking_audio_path}")

            if self._state.get("expression") == "speaking":
                self._play_audio(self._pending_audio_path)
                self._pending_audio_path = None
            else:
                logger.info("speaking 视频未开始，等待 video_playing 通知")

            if "audio_duration" in data and data["audio_duration"] > 0:
                audio_duration = data["audio_duration"]
                if self._speaking_timeout_task:
                    self._speaking_timeout_task.cancel()
                    self._speaking_timeout_task = None
                self._speaking_timeout_task = asyncio.create_task(
                    self._reset_expression_after_delay(audio_duration)
                )

        return web.json_response({"success": True})

    def _on_video_task_start(self, task: VideoTask) -> None:
        logger.info(f"视频任务开始 - {task}")

        if task.task_type == VideoTaskType.PLAY_TRANSITION:
            self._state["expression"] = f"transition:{task.source}->{task.target}"
        else:
            self._state["expression"] = task.target

        if task.target == "speaking" and self._pending_audio_path and task.task_type == VideoTaskType.PLAY_VIDEO:
            self._play_audio(self._pending_audio_path)
            self._pending_audio_path = None

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
        logger.info(f"视频任务完成 - {task}")

        if task.duration > 0 and self._speaking_timeout_task is None:
            self._speaking_timeout_task = asyncio.create_task(
                self._reset_expression_after_delay(task.duration)
            )

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
        if not self._websocket_clients:
            return

        message_str = json.dumps(message)
        clients = list(self._websocket_clients)

        for ws in clients:
            try:
                asyncio.create_task(ws.send_str(message_str))
            except Exception as e:
                logger.error(f"发送 WebSocket 消息失败 - {e}")

    def _play_audio(self, audio_file: str) -> None:
        from pathlib import Path
        import subprocess
        import platform

        if not Path(audio_file).exists():
            logger.warning(f"音频文件不存在 - {audio_file}")
            return

        self._stop_audio()

        try:
            system = platform.system()
            if system == "Darwin":
                self._audio_process = subprocess.Popen(
                    ["afplay", audio_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            elif system == "Linux":
                self._audio_process = subprocess.Popen(
                    ["aplay", audio_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            elif system == "Windows":
                self._audio_process = subprocess.Popen(
                    ["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            logger.info(f"已发送音频播放命令 - {audio_file}")
        except Exception as e:
            logger.error(f"播放音频失败 - {e}")

    def _stop_audio(self) -> None:
        if self._audio_process is not None:
            try:
                self._audio_process.terminate()
            except Exception:
                pass
            self._audio_process = None

        self._pending_audio_path = None
        self._speaking_audio_path = None

        if self._speaking_timeout_task is not None:
            self._speaking_timeout_task.cancel()
            self._speaking_timeout_task = None

    async def _handle_audio_stop(self, request) -> Any:
        from aiohttp import web
        self._stop_audio()
        cleared = self._video_queue.clear_pending_tasks()
        
        current_expr = self._state.get("expression", "")
        if current_expr.startswith("transition:"):
            target = current_expr.split("->")[-1]
            self._state["expression"] = target

        return web.json_response({"status": "ok", "cleared_tasks": cleared})

    async def _handle_reset(self, request) -> Any:
        from aiohttp import web
        self._state["expression"] = "neutral"
        self._last_expression = "neutral"
        self._video_queue.clear_pending_tasks()
        
        if "neutral" in self._videos:
            await self._video_queue.add_video_task(target="neutral", duration=0)

        return web.json_response({"success": True, "target": "neutral"})

    async def _handle_websocket(self, request) -> Any:
        from aiohttp import web, WSMsgType

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self._websocket_clients.add(ws)
        logger.info(f"WebSocket 客户端连接，当前连接数: {len(self._websocket_clients)}")

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get("type") == "task_complete":
                            self._video_queue.mark_task_completed()
                        elif data.get("type") == "video_playing":
                            target = data.get("target", "")
                            if target == "speaking" and self._pending_audio_path:
                                self._play_audio(self._pending_audio_path)
                                self._pending_audio_path = None
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket 错误 - {ws.exception()}")
        except Exception as e:
            logger.error(f"WebSocket 连接错误 - {e}")
        finally:
            self._websocket_clients.discard(ws)

        return ws

    async def _handle_queue_status(self, request) -> Any:
        from aiohttp import web
        return web.json_response(self._video_queue.get_queue_status())

    async def stop(self) -> None:
        if self._server:
            runner, site = self._server
            await site.stop()
            await runner.cleanup()
            self._server = None
        await self._video_queue.stop_processing()
        logger.info("DisplayServer: 服务器已停止")

    async def _handle_queue_complete(self, request) -> Any:
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
.bottom-bar{position:fixed;bottom:0;left:0;right:0;z-index:10;padding:40px 20px;background:linear-gradient(to top,rgba(0,0,0,0.7),transparent);display:flex;justify-content:center;gap:30px}
.control-btn{width:65px;height:65px;border-radius:50%;border:none;background:rgba(255,255,255,0.2);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s ease}
.control-btn:active{transform:scale(0.95)}
.control-btn svg{width:32px;height:32px;fill:#fff}
.control-btn.end-call{background:#ff4d4f}
.subtitle{position:fixed;bottom:150px;left:20px;right:20px;z-index:10;text-align:center}
.subtitle-text{display:inline-block;background:rgba(0,0,0,0.6);color:#fff;padding:10px 18px;border-radius:18px;font-size:15px;max-width:85%;line-height:1.5}
</style></head>
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
<div class="subtitle">
<div class="subtitle-text" id="bubble"></div>
</div>
<div class="bottom-bar">
<button class="control-btn" id="mute-btn" onclick="toggleMute()">
<svg id="mute-icon" viewBox="0 0 24 24"><path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l2.97 2.97c-.85.35-1.76.57-2.75.57-2.76 0-5.3-1.12-7.1-2.93L4.27 3z"/></svg>
</button>
<button class="control-btn end-call" onclick="endCall()">
<svg viewBox="0 0 24 24"><path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/></svg>
</button>
<button class="control-btn" id="speaker-btn" onclick="toggleSpeaker()">
<svg id="speaker-icon" viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
</button>
</div>
<script>
let lastExpression="",isMuted=true,isSpeakerOn=true,currentVideo=1;
let ws=null;

function goBack(){console.log("返回");}
function toggleMute(){isMuted=!isMuted;document.getElementById("mute-btn").classList.toggle("active",!isMuted);}
function endCall(){console.log("结束通话");}
function toggleSpeaker(){isSpeakerOn=!isSpeakerOn;document.getElementById("speaker-btn").classList.toggle("active",!isSpeakerOn);}

function connectWebSocket(){
    const protocol=window.location.protocol==='https:'?'wss:':'ws:';
    ws=new WebSocket(protocol+'//'+window.location.host+'/ws');
    ws.onopen=()=>console.log("WebSocket 连接成功");
    ws.onmessage=(e)=>{
        try{const data=JSON.parse(e.data);if(data.type==="video_task_start")handleVideoTask(data.task);}
        catch(err){console.error("解析消息失败",err);}
    };
    ws.onclose=()=>setTimeout(connectWebSocket,5000);
}

async function handleVideoTask(task){
    const currentVideoEl=document.getElementById("avatar-video-"+currentVideo);
    const nextVideo=currentVideo===1?2:1;
    const nextVideoEl=document.getElementById("avatar-video-"+nextVideo);
    const avatarImg=document.getElementById("avatar");
    
    try{
        if(task.task_type==="play_transition"){
            await preloadVideo(nextVideoEl,"/transition/"+task.source+"/"+task.target+"?t="+Date.now());
            currentVideoEl.style.display="none";currentVideoEl.pause();currentVideoEl.loop=false;
            nextVideoEl.style.display="block";nextVideoEl.loop=false;nextVideoEl.play();
            await waitForVideoEnd(nextVideoEl);
            await preloadVideo(nextVideoEl,"/video/"+task.target+"?t="+Date.now());
            nextVideoEl.loop=true;nextVideoEl.play();
        }else if(task.task_type==="play_video"){
            await preloadVideo(nextVideoEl,"/video/"+task.target+"?t="+Date.now());
            currentVideoEl.style.display="none";currentVideoEl.pause();currentVideoEl.loop=false;
            nextVideoEl.style.display="block";nextVideoEl.loop=true;nextVideoEl.play();
        }
        currentVideo=nextVideo;
        notifyTaskComplete();
    }catch(e){console.error("视频任务失败",e);notifyTaskComplete();}
}

function preloadVideo(videoEl,url){
    return new Promise((resolve,reject)=>{
        videoEl.src=url;videoEl.muted=true;
        videoEl.onloadeddata=()=>resolve();
        videoEl.onerror=(e)=>reject(e);
    });
}

function waitForVideoEnd(videoEl){
    return new Promise(resolve=>{videoEl.onended=()=>resolve();});
}

function notifyTaskComplete(){
    if(ws&&ws.readyState===WebSocket.OPEN)ws.send(JSON.stringify({type:"task_complete"}));
    else fetch("/queue/complete",{method:"POST"}).catch(()=>{});
}

async function update(){
    try{
        const r=await fetch("/state");const s=await r.json();
        document.getElementById("name").textContent=s.name||"火灵";
        const bubble=document.getElementById("bubble");
        if(s.bubble_text){bubble.textContent=s.bubble_text;bubble.style.display="inline-block";}
        else{bubble.style.display="none";}
    }catch(e){}
}

async function init(){
    try{
        const videoCheck=await fetch("/video/neutral",{method:"HEAD"});
        if(videoCheck.ok){
            const v1=document.getElementById("avatar-video-1");
            document.getElementById("avatar").style.display="none";
            v1.style.display="block";v1.src="/video/neutral?t="+Date.now();v1.loop=true;v1.play().catch(()=>{});
        }
    }catch(e){}
}

setInterval(update,1000);init();connectWebSocket();
</script></body></html>'''


_server_instance: Optional[DisplayServer] = None


def get_server(port: int = 18791, avatar_id: str = "pet1", assets_dir: Optional[Path] = None) -> DisplayServer:
    global _server_instance
    if _server_instance is None:
        _server_instance = DisplayServer(port=port, avatar_id=avatar_id, assets_dir=assets_dir)
    return _server_instance
