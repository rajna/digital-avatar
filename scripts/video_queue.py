#!/usr/bin/env python3
"""视频播放队列系统"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
from loguru import logger


class VideoTaskType(Enum):
    """视频任务类型"""
    PLAY_VIDEO = "play_video"  # 直接播放视频
    PLAY_TRANSITION = "play_transition"  # 播放过渡视频
    SHOW_IMAGE = "show_image"  # 显示图片


@dataclass
class VideoTask:
    """视频播放任务"""
    task_type: VideoTaskType
    source: str  # 源状态（用于过渡）
    target: str  # 目标状态
    duration: int = 0  # 自动重置时间（秒），0表示不自动重置
    priority: int = 0  # 优先级，数字越大优先级越高

    def __repr__(self):
        return f"VideoTask({self.task_type.value}, {self.source}->{self.target}, duration={self.duration})"


class VideoQueue:
    """视频播放队列管理器"""

    def __init__(self):
        self._queue: asyncio.Queue[VideoTask] = asyncio.Queue()
        self._current_task: Optional[VideoTask] = None
        self._is_playing = False
        self._processing_task: Optional[asyncio.Task] = None
        self._task_callback: Optional[Callable[[VideoTask], None]] = None
        self._completion_callback: Optional[Callable[[VideoTask], None]] = None
        self._task_completed_event: Optional[asyncio.Event] = None

    def set_task_callback(self, callback: Callable[[VideoTask], None]) -> None:
        """设置任务回调函数（当任务开始执行时调用）"""
        self._task_callback = callback

    def set_completion_callback(self, callback: Callable[[VideoTask], None]) -> None:
        """设置完成回调函数（当任务完成时调用）"""
        self._completion_callback = callback

    async def add_task(self, task: VideoTask) -> None:
        """添加视频播放任务到队列"""
        await self._queue.put(task)
        logger.info(f"VideoQueue: 添加任务到队列 - {task}, 队列长度: {self._queue.qsize()}")

    async def add_video_task(self, target: str, duration: int = 0, priority: int = 0) -> None:
        """添加直接播放视频任务"""
        task = VideoTask(
            task_type=VideoTaskType.PLAY_VIDEO,
            source="",
            target=target,
            duration=duration,
            priority=priority
        )
        await self.add_task(task)

    async def add_transition_task(
        self,
        source: str,
        target: str,
        duration: int = 0,
        priority: int = 0
    ) -> None:
        """添加过渡视频任务"""
        task = VideoTask(
            task_type=VideoTaskType.PLAY_TRANSITION,
            source=source,
            target=target,
            duration=duration,
            priority=priority
        )
        await self.add_task(task)

    async def add_image_task(self, target: str, duration: int = 0, priority: int = 0) -> None:
        """添加显示图片任务"""
        task = VideoTask(
            task_type=VideoTaskType.SHOW_IMAGE,
            source="",
            target=target,
            duration=duration,
            priority=priority
        )
        await self.add_task(task)

    def get_current_task(self) -> Optional[VideoTask]:
        """获取当前正在执行的任务"""
        return self._current_task

    def is_playing(self) -> bool:
        """是否正在播放视频"""
        return self._is_playing

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()

    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            "is_playing": self._is_playing,
            "current_task": str(self._current_task) if self._current_task else None,
            "queue_size": self._queue.qsize()
        }

    async def start_processing(self) -> None:
        """开始处理队列"""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_queue())
            logger.info("VideoQueue: 开始处理队列")

    async def stop_processing(self) -> None:
        """停止处理队列"""
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            logger.info("VideoQueue: 停止处理队列")

    async def _process_queue(self) -> None:
        """处理队列中的任务"""
        while True:
            try:
                # 如果没有正在播放的任务，从队列中获取下一个任务
                if not self._is_playing and not self._queue.empty():
                    task = await self._queue.get()
                    logger.info(f"VideoQueue: 从队列获取任务 - {task}")
                    await self._execute_task(task)

                # 短暂休眠，避免忙等待
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("VideoQueue: 队列处理被取消")
                break
            except Exception as e:
                logger.error(f"VideoQueue: 处理队列时出错 - {e}")
                await asyncio.sleep(0.5)

    async def _execute_task(self, task: VideoTask) -> None:
        """执行视频播放任务"""
        self._current_task = task
        self._is_playing = True
        self._task_completed_event = asyncio.Event()

        logger.info(f"VideoQueue: 开始执行任务 - {task}")

        # 调用任务回调（通知前端开始播放）
        if self._task_callback:
            try:
                self._task_callback(task)
            except Exception as e:
                logger.error(f"VideoQueue: 任务回调出错 - {e}")

        # 等待任务完成（前端会通过 WebSocket 通知任务完成）
        # 设置超时时间：过渡视频 10 秒，普通视频 5 秒
        timeout = 10 if task.task_type == VideoTaskType.PLAY_TRANSITION else 5
        try:
            await asyncio.wait_for(self._task_completed_event.wait(), timeout=timeout)
            logger.info(f"VideoQueue: 任务完成（前端通知）- {task}")
        except asyncio.TimeoutError:
            logger.warning(f"VideoQueue: 任务超时，自动标记完成 - {task}")
            # 超时后自动标记任务完成
            self.mark_task_completed()

    def mark_task_completed(self) -> None:
        """标记当前任务完成"""
        logger.info(f"VideoQueue: mark_task_completed 被调用，当前任务: {self._current_task}, is_playing: {self._is_playing}")
        if self._current_task:
            logger.info(f"VideoQueue: 任务完成 - {self._current_task}")

            # 调用完成回调
            if self._completion_callback:
                try:
                    self._completion_callback(self._current_task)
                except Exception as e:
                    logger.error(f"VideoQueue: 完成回调出错 - {e}")

            # 设置任务完成事件
            if self._task_completed_event:
                self._task_completed_event.set()
                self._task_completed_event = None

            self._current_task = None
            self._is_playing = False
            logger.info(f"VideoQueue: 任务完成，已重置状态，is_playing: {self._is_playing}")
        else:
            logger.warning(f"VideoQueue: mark_task_completed 被调用，但没有当前任务")

    def clear_queue(self) -> None:
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("VideoQueue: 队列已清空")

    def clear_pending_tasks(self) -> int:
        """清空队列中所有未执行的任务，并取消当前正在执行的任务。
        
        Returns:
            清除的任务数量
        """
        cleared = 0

        # 1. 取消当前正在执行的任务
        if self._current_task:
            logger.info(f"VideoQueue: 取消当前任务 - {self._current_task}")
            if self._task_completed_event:
                self._task_completed_event.set()
                self._task_completed_event = None
            self._current_task = None
            self._is_playing = False
            cleared += 1

        # 2. 清空队列中所有待执行的任务
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                cleared += 1
            except asyncio.QueueEmpty:
                break

        logger.info(f"VideoQueue: 已清除 {cleared} 个任务")
        return cleared

    async def cancel_current_task(self) -> None:
        """取消当前任务"""
        if self._current_task:
            logger.info(f"VideoQueue: 取消当前任务 - {self._current_task}")

            # 设置任务完成事件，以便 _execute_task 能够继续执行
            if self._task_completed_event:
                self._task_completed_event.set()
                self._task_completed_event = None

            self._current_task = None
            self._is_playing = False
            logger.info(f"VideoQueue: 当前任务已取消，is_playing: {self._is_playing}")
