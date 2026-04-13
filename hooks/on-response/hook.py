"""On Response Hook - 在响应发送后设置speaking表情并播放语音"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import aiohttp

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

# TTS配置
TTS_VOICE = "zh-CN-XiaoxiaoNeural"
TTS_OUTPUT_DIR = Path.home() / ".nanobot" / ".tts"
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ✅ 移除模块级别的 asyncio.run() 检查
# 改为在第一次使用时懒加载检查
_tts_available = None
_tts_cache = {}


async def _check_tts_available() -> bool:
    """检查 edge-tts 是否可用（仅检查二进制文件是否存在，不运行 --list-voices 避免超时）"""
    global _tts_available
    if _tts_available is not None:
        return _tts_available

    import shutil
    tts_bin = shutil.which("edge-tts")
    _tts_available = tts_bin is not None

    if not _tts_available:
        from loguru import logger
        logger.warning("Edge-TTS 不可用: 未找到 edge-tts 二进制文件")

    return _tts_available


async def _reset_expression_after_delay(delay: int = 3):
    """后台任务：延迟后重置表情为基础状态（neutral 或 pet）"""
    await asyncio.sleep(delay)
    try:
        timeout = aiohttp.ClientTimeout(total=2, connect=1)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 使用 /reset 端点重置到基础状态（而非硬编码neutral）
            await session.post("http://127.0.0.1:18791/reset")
        try:
            from avatar_state import clear_speaking
            clear_speaking()
        except Exception:
            pass
    except Exception:
        pass


def _get_audio_duration(audio_file: str) -> float:
    """使用 ffprobe 获取音频文件的实际时长（秒）"""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", audio_file],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            from loguru import logger
            logger.info(f"音频实际时长: {duration:.1f}s - {audio_file}")
            return duration
    except Exception as e:
        from loguru import logger
        logger.warning(f"获取音频时长失败: {e}")
    return 0


def _calculate_speaking_duration(text: str) -> int:
    """根据文本长度估算说话持续时间（备用方案，当无法获取音频时长时使用）"""
    if not text:
        return 5
    base_duration = 5
    length_factor = min(len(text) // 15, 15)
    return base_duration + length_factor


async def _generate_audio_only(text: str) -> str:
    """仅生成音频文件，不播放（用于音视频同步）"""
    if not text:
        return None

    # ✅ 检查 TTS 是否可用
    if not await _check_tts_available():
        return None

    # 检查缓存
    if text in _tts_cache:
        audio_file = _tts_cache[text]
        if Path(audio_file).exists():
            return audio_file
        else:
            del _tts_cache[text]

    # 生成文件名
    import hashlib
    hash_obj = hashlib.md5(text.encode('utf-8'))
    filename = f"tts_{hash_obj.hexdigest()[:8]}.mp3"
    audio_file = TTS_OUTPUT_DIR / filename

    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        process = await asyncio.create_subprocess_exec(
            "edge-tts", "--text", text, "--voice", TTS_VOICE, "--write-media", str(audio_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20)
        except asyncio.TimeoutError:
            process.kill()
            from loguru import logger
            logger.error("Edge-TTS: 命令执行超时")
            return None

        if process.returncode != 0:
            from loguru import logger
            logger.error(f"Edge-TTS: 命令执行失败")
            return None

        _tts_cache[text] = str(audio_file)
        return str(audio_file)

    except Exception as e:
        from loguru import logger
        logger.error(f"Edge-TTS: 生成语音失败 {e}")
        return None


async def _text_to_speech(text: str) -> str:
    """将文本转换为语音并通知server播放"""
    if not text:
        return None

    # ✅ 首先尝试 edge-tts
    if await _check_tts_available():
        # 检查缓存
        if text in _tts_cache:
            audio_file = _tts_cache[text]
            if Path(audio_file).exists():
                _notify_server_audio(audio_file)
                return audio_file
            else:
                del _tts_cache[text]

        # 生成文件名
        import hashlib
        hash_obj = hashlib.md5(text.encode('utf-8'))
        filename = f"tts_{hash_obj.hexdigest()[:8]}.mp3"
        audio_file = TTS_OUTPUT_DIR / filename

        TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        try:
            process = await asyncio.create_subprocess_exec(
                "edge-tts", "--text", text, "--voice", TTS_VOICE, "--write-media", str(audio_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=20)
            except asyncio.TimeoutError:
                process.kill()
                from loguru import logger
                logger.error("Edge-TTS: 命令执行超时")
                # 继续尝试备用方案
            else:
                if process.returncode == 0:
                    _tts_cache[text] = str(audio_file)
                    _notify_server_audio(str(audio_file))
                    return str(audio_file)
                else:
                    from loguru import logger
                    logger.error(f"Edge-TTS: 命令执行失败")
                    # 继续尝试备用方案

        except Exception as e:
            from loguru import logger
            logger.error(f"Edge-TTS: 生成语音失败 {e}")
            # 继续尝试备用方案

    # ✅ edge-tts 不可用
    from loguru import logger
    logger.warning("Edge-TTS 不可用，无法播放语音")
    return None


def _notify_server_audio(audio_file: str):
    """通知server音频文件路径和时长，由server负责播放"""
    if not Path(audio_file).exists():
        return

    # 获取音频实际时长
    audio_duration = _get_audio_duration(audio_file)
    # 额外加1秒缓冲，确保视频不会提前结束
    speaking_duration = int(audio_duration) + 2 if audio_duration > 0 else 0

    try:
        import requests
        payload = {"audio_path": audio_file}
        if speaking_duration > 0:
            payload["audio_duration"] = speaking_duration
        requests.post(
            "http://127.0.0.1:18791/audio/start",
            json=payload,
            timeout=1
        )
        from loguru import logger
        #logger.info(f"Digital Avatar (on-response): 已通知server音频文件 - {audio_file}, 时长={speaking_duration}s")
    except Exception as e:
        from loguru import logger
        #logger.error(f"Digital Avatar (on-response): 通知server音频失败 - {e}")


async def execute(context: dict[str, Any]) -> dict[str, Any]:
    """响应发送后更新表情和图片，并播放语音"""
    from loguru import logger
    #logger.info("=== [on-response hook] execute() called ===")
    try:
        response = context.get("response")
        #logger.info(f"=== [on-response hook] response = {response}")
        if not response:
            logger.warning("=== [on-response hook] response is None, skipping ===")
            return context

        ai_content = getattr(response, "content", "") or ""
        #logger.info(f"=== [on-response hook] ai_content = [{ai_content[:50]}...] ===")
        expression = _detect_expression_from_text(ai_content)
        speaking_duration = _calculate_speaking_duration(ai_content)

        timeout = aiohttp.ClientTimeout(total=2, connect=1)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 发送speaking表情（_get_expression_video 会根据模式自动映射到 pet-speaking 或 speaking）
            await session.post(
                "http://127.0.0.1:18791/update",
                json={"expression": "speaking", "duration": speaking_duration, "status": "回复中", "priority": True}
            )
            

            if ai_content and len(ai_content) > 10:
                summary = ai_content[:100] + "..." if len(ai_content) > 100 else ai_content
                await session.post(
                    "http://127.0.0.1:18791/update",
                    json={"bubble_text": summary}
                )

        try:
            from avatar_state import set_speaking
            set_speaking(speaking_duration)
        except Exception:
            pass

        # ✅ 移除 _switch_to_expression 调用，避免在speaking任务执行过程中发送额外请求
        # if expression not in ["neutral", "speaking"]:
        #     asyncio.ensure_future(_switch_to_expression(expression, speaking_duration))
        #     asyncio.ensure_future(_reset_expression_after_delay(speaking_duration + 3))

        tts_text = _extract_tts_text(ai_content)
        #logger.info(f"=== [on-response hook] tts_text = [{tts_text[:80]}...] ===")
        if tts_text:
            #logger.info(f"=== [on-response hook] Calling _text_to_speech for: [{tts_text[:80]}...] ===")
            asyncio.ensure_future(_text_to_speech(tts_text))

    except Exception as e:
        from loguru import logger
        logger.error(f"Digital Avatar (on-response): 更新表情失败 - {e}")
        import traceback
        logger.error(f"Digital Avatar (on-response): traceback - {traceback.format_exc()}")

    return context



def extract_chinese(text: str) -> str:
    import re
    """
    从文本中提取所有中文字符（包括中文标点符号）
    
    Args:
        text: 输入文本
        
    Returns:
        所有中文字符组成的字符串
    """
    # 正则表达式匹配中文字符和中文标点
    # \u4e00-\u9fff 是中文字符范围
    # \u3000-\u303f 是中文标点符号范围
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3000-\u303f]+')
    
    # 查找所有匹配的中文部分
    chinese_parts = chinese_pattern.findall(text)
    
    # 将所有中文部分连接成一个字符串
    return ''.join(chinese_parts)

def _is_chinese_or_english(text: str) -> bool:
    if not text:
        return False
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    has_english = any('a' <= char.lower() <= 'z' for char in text)
    for char in text:
        if char.isdigit() or char.isspace() or char in '.,!?;:，。！？；：、""''（）()[]【】':
            continue
        if '\u4e00' <= char <= '\u9fff' or 'a' <= char.lower() <= 'z':
            continue
        return False
    return has_chinese or has_english


def _extract_tts_text(text: str) -> str:
    """提取用于TTS的完整文本（中文+英文+数字，去除markdown/代码等）"""
    if not text:
        return ""
    import re
    # 去除markdown标记、代码块、链接等
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接保留文字
    text = re.sub(r'#{1,6}\s*', '', text)  # 标题标记
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # 粗体/斜体
    text = re.sub(r'[-*+]\s+', '', text)  # 列表标记
    text = re.sub(r'\n{2,}', '。', text)  # 多换行变句号
    text = re.sub(r'\n', '，', text)  # 单换行变逗号
    # 保留中文、英文、数字、基本标点
    text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303fa-zA-Z0-9\s，。！？；：、""''（）()【】\[\].,!?;:\-]', '', text)
    text = text.strip()
    if len(text) > 500:
        text = text[:500]
    return text


def _detect_expression_from_text(text: str) -> str:
    if not text:
        return "neutral"
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["难过", "遗憾", "抱歉", "sorry", "sad"]):
        return "sad"
    elif any(word in text_lower for word in ["惊讶", "哇", "天哪", "surprised", "wow", "大惊", "Error"]):
        return "surprised"
    elif any(word in text_lower for word in ["困惑", "不确定", "confused", "unsure"]):
        return "confused"
    elif any(word in text_lower for word in ["大笑", "爆笑", "笑死我了", "笑喷了", "哈哈哈哈", "笑翻了", "laugh"]):
        return "laugh"
    elif any(word in text_lower for word in ["眨眼", "wink", "😉", "😜"]):
        return "wink"
    elif any(word in text_lower for word in ["假笑", "尴尬笑", "苦笑", "无奈笑"]):
        return "fakesmilerolleyes"
    elif any(word in text_lower for word in ["kiss", "爱"]):
        return "kiss"
    elif any(word in text_lower for word in ["翻白眼", "无语", "无语了","🙄"]):
        return "rolleyes"
    elif any(word in text_lower for word in ["开心", "高兴", "哈哈", "太好了", "棒", "喜欢", "happy", "great", "good"]):
        return "happy"
    elif any(word in text_lower for word in ["思考", "想想", "分析", "考虑", "thinking", "think"]):
        return "thinking"

    return "neutral"


async def _switch_to_expression(expression: str, delay: int = 2):
    """后台任务：延迟后切换到指定表情"""
    await asyncio.sleep(delay)
    try:
        timeout = aiohttp.ClientTimeout(total=2, connect=1)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await session.post(
                "http://127.0.0.1:18791/update",
                json={"expression": expression, "status": "回复中"}
            )
    except Exception:
        pass
