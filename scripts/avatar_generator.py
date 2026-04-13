#!/usr/bin/env python3
"""Avatar Generator - 使用预生成的数字人图片"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from .transition_manager import TransitionManager
except ImportError:
    from transition_manager import TransitionManager


class AvatarType(str, Enum):
    """数字人图片类型"""
    NEUTRAL = "neutral"  # 正面照 - 默认状态
    SPEAKING = "speaking"  # 说话 - 说话/工作状态
    EXPRESSION = "expression"  # 多种表情 - 不同情绪状态


@dataclass
class GenerationResult:
    success: bool
    image_path: Optional[str] = None
    error: Optional[str] = None
    avatar_type: Optional[AvatarType] = None


class AvatarGenerator:
    """数字人图片生成器 - 使用预生成的图片"""

    def __init__(self, assets_dir: Optional[Path] = None):
        # 默认使用 skill 目录下的 assets
        if assets_dir is None:
            # 从当前文件位置找到 assets 目录
            current_file = Path(__file__)
            skill_dir = current_file.parent.parent
            assets_dir = skill_dir / "assets"

        self.assets_dir = Path(assets_dir)
        self._image_cache = {}
        
        # 初始化过渡管理器
        self._transition_manager = TransitionManager(assets_dir)

        # 预加载图片列表
        self._load_images()

    def _load_images(self) -> None:
        """预加载视频/图片列表"""
        if not self.assets_dir.exists():
            return

        # 加载 neutral 目录
        neutral_dir = self.assets_dir / "neutral"
        if neutral_dir.exists():
            videos = list(neutral_dir.glob("*.mp4"))
            images = list(neutral_dir.glob("*.png"))
            self._image_cache.setdefault(AvatarType.NEUTRAL, []).extend(videos)
            self._image_cache.setdefault(AvatarType.NEUTRAL, []).extend(images)

        # 加载 speaking 目录
        speaking_dir = self.assets_dir / "speaking"
        if speaking_dir.exists():
            videos = list(speaking_dir.glob("*.mp4"))
            images = list(speaking_dir.glob("*.png"))
            self._image_cache.setdefault(AvatarType.SPEAKING, []).extend(videos)
            self._image_cache.setdefault(AvatarType.SPEAKING, []).extend(images)

        # 加载 expressions 目录
        expressions_dir = self.assets_dir / "expressions"
        if expressions_dir.exists():
            videos = list(expressions_dir.glob("*.mp4"))
            images = list(expressions_dir.glob("*.png"))
            self._image_cache.setdefault(AvatarType.EXPRESSION, []).extend(videos)
            self._image_cache.setdefault(AvatarType.EXPRESSION, []).extend(images)

        # 打印加载结果
        for avatar_type, files in self._image_cache.items():
            print(f"  {avatar_type.value}: {len(files)} 个文件")

    async def generate(
        self,
        prompt: str = "",
        avatar_type: AvatarType = AvatarType.NEUTRAL,
        random_seed: Optional[int] = None
    ) -> GenerationResult:
        """
        生成数字人图片（从预生成的图片中选择）

        Args:
            prompt: 提示词（保留兼容性，暂不使用）
            avatar_type: 图片类型
            random_seed: 随机种子（用于选择图片）

        Returns:
            GenerationResult: 生成结果
        """
        if not self._image_cache:
            return GenerationResult(
                success=False,
                error="未找到预生成的图片，请检查 assets 目录"
            )

        # 获取指定类型的图片列表
        images = self._image_cache.get(avatar_type, [])

        if not images:
            # 如果指定类型没有图片，使用 neutral 类型
            images = self._image_cache.get(AvatarType.NEUTRAL, [])

        if not images:
            return GenerationResult(
                success=False,
                error=f"未找到 {avatar_type.value} 类型的图片"
            )

        # 随机选择一张图片
        if random_seed is not None:
            random.seed(random_seed)
        selected_image = random.choice(images)

        return GenerationResult(
            success=True,
            image_path=str(selected_image),
            avatar_type=avatar_type
        )

    async def generate_by_expression(
        self,
        expression: str,
        random_seed: Optional[int] = None
    ) -> GenerationResult:
        """
        根据表情生成数字人图片/视频

        Args:
            expression: 表情类型（neutral, happy, thinking, sad, surprised, confused, working）
            random_seed: 随机种子

        Returns:
            GenerationResult: 生成结果
        """
        # 特殊表情直接从对应目录加载
        if expression == "neutral":
            neutral_dir = self.assets_dir / "neutral"
            if neutral_dir.exists():
                files = list(neutral_dir.glob("*.mp4")) + list(neutral_dir.glob("*.png"))
                if files:
                    return GenerationResult(
                        success=True,
                        image_path=str(files[0]),
                        avatar_type=AvatarType.NEUTRAL
                    )
        elif expression == "speaking":
            speaking_dir = self.assets_dir / "speaking"
            if speaking_dir.exists():
                files = list(speaking_dir.glob("*.mp4")) + list(speaking_dir.glob("*.png"))
                if files:
                    return GenerationResult(
                        success=True,
                        image_path=str(files[0]),
                        avatar_type=AvatarType.SPEAKING
                    )
        else:
            # 其他表情从 expressions 目录加载
            expressions_dir = self.assets_dir / "expressions"
            if expressions_dir.exists():
                # 查找匹配的表情文件
                pattern = f"*{expression}*.mp4"
                files = list(expressions_dir.glob(pattern))
                if not files:
                    pattern = f"*{expression}*.png"
                    files = list(expressions_dir.glob(pattern))
                if files:
                    return GenerationResult(
                        success=True,
                        image_path=str(files[0]),
                        avatar_type=AvatarType.EXPRESSION
                    )

        # 如果没找到，使用默认的 neutral
        return await self.generate(avatar_type=AvatarType.NEUTRAL, random_seed=random_seed)

    def get_available_types(self) -> list[AvatarType]:
        """获取可用的图片类型"""
        return list(self._image_cache.keys())

    def get_image_count(self, avatar_type: AvatarType) -> int:
        """获取指定类型的图片数量"""
        return len(self._image_cache.get(avatar_type, []))
    
    def get_transition_manager(self) -> TransitionManager:
        """获取过渡管理器"""
        return self._transition_manager
    
    async def start_transition(
        self,
        source_state: str,
        target_state: str,
        display_server
    ) -> bool:
        """
        开始状态过渡
        
        Args:
            source_state: 源状态
            target_state: 目标状态
            display_server: 显示服务器实例
            
        Returns:
            bool: 是否成功开始过渡
        """
        return await self._transition_manager.start_transition(
            source_state, target_state, display_server
        )
    
    def get_transition_video(self, source_state: str, target_state: str) -> Optional[Path]:
        """获取过渡视频"""
        return self._transition_manager.get_transition_video(source_state, target_state)
    
    def is_transitioning(self) -> bool:
        """检查是否正在过渡"""
        return self._transition_manager.is_transitioning()
    
    def get_current_state(self) -> str:
        """获取当前状态"""
        return self._transition_manager.get_current_state()


# 兼容旧版本的 API
class AvatarGeneratorLegacy(AvatarGenerator):
    """兼容旧版本的 AvatarGenerator"""

    async def generate(self, prompt: str, style: str = "anime", size: str = "1024x1024") -> GenerationResult:
        """兼容旧版本的 generate 方法"""
        # 忽略 prompt, style, size 参数，直接返回 neutral 类型的图片
        return await super().generate(avatar_type=AvatarType.NEUTRAL)
