"""Avatar状态管理模块 - 全局共享状态"""

from __future__ import annotations
import time

# 全局speaking状态管理器
_avatar_state = {
    "speaking": False,
    "speaking_until": 0,  # Unix时间戳，speaking表情应该播放到这个时间
    "initialized": False  # 是否已经初始化过
}


def is_speaking() -> bool:
    """检查是否正在播放speaking表情"""
    if not _avatar_state["speaking"]:
        return False

    # 检查speaking时间是否已过
    if time.time() > _avatar_state["speaking_until"]:
        _avatar_state["speaking"] = False
        return False

    return True


def set_speaking(duration: int):
    """设置speaking状态，持续duration秒"""
    _avatar_state["speaking"] = True
    _avatar_state["speaking_until"] = time.time() + duration


def clear_speaking():
    """清除speaking状态"""
    _avatar_state["speaking"] = False
    _avatar_state["speaking_until"] = 0


def is_initialized() -> bool:
    """检查是否已经初始化过"""
    return _avatar_state["initialized"]


def set_initialized():
    """设置已初始化标志"""
    _avatar_state["initialized"] = True
