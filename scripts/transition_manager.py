#!/usr/bin/env python3
"""Transition Manager - 数字人状态过渡管理器"""

from pathlib import Path
from typing import Optional, Dict, Tuple
from loguru import logger


class TransitionManager:
    """管理数字人状态之间的平滑过渡"""

    def __init__(self, assets_dir: Optional[Path] = None):
        self._assets_dir = assets_dir
        self._transitions: Dict[Tuple[str, str], Path] = {}
        self._load_transitions()

    def _load_transitions(self) -> None:
        """加载所有过渡视频"""
        if self._assets_dir is None:
            return

        transition_dir = self._assets_dir / "transition"
        if not transition_dir.exists():
            logger.info("TransitionManager: transition目录不存在")
            return

        # 加载所有过渡视频
        for video_file in transition_dir.glob("*.mp4"):
            # 从文件名提取过渡信息
            # 2段: "neutral-working.mp4" -> ("neutral", "working")
            # 3段: "pet-neutral-working.mp4" -> ("pet-neutral", "pet-working")
            name = video_file.stem
            if "-" in name:
                parts = name.split("-")
                if len(parts) == 2:
                    source_state, target_state = parts
                    self._transitions[(source_state, target_state)] = video_file
                    logger.info(f"TransitionManager: 加载过渡视频 {source_state} -> {target_state}: {video_file.name}")
                elif len(parts) == 3:
                    prefix, source_state, target_state = parts
                    key = (f"{prefix}-{source_state}", f"{prefix}-{target_state}")
                    self._transitions[key] = video_file
                    logger.info(f"TransitionManager: 加载过渡视频 {key[0]} -> {key[1]}: {video_file.name}")
                elif len(parts) == 4:
                    # "pet-working-pet-speaking.mp4" -> ("pet-working", "pet-speaking")
                    source_state = f"{parts[0]}-{parts[1]}"
                    target_state = f"{parts[2]}-{parts[3]}"
                    key = (source_state, target_state)
                    self._transitions[key] = video_file
                    logger.info(f"TransitionManager: 加载过渡视频 {key[0]} -> {key[1]}: {video_file.name}")

    def has_transition(self, source_state: str, target_state: str) -> bool:
        """检查是否存在从source_state到target_state的过渡视频"""
        return (source_state, target_state) in self._transitions

    def get_transition_video(self, source_state: str, target_state: str) -> Optional[Path]:
        """获取从source_state到target_state的过渡视频路径"""
        return self._transitions.get((source_state, target_state))

    def get_all_transitions(self) -> Dict[Tuple[str, str], Path]:
        """获取所有过渡视频"""
        return self._transitions.copy()