"""On Bootstrap Hook - 启动时加载数字人形象"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_hook_dir = Path(__file__).parent
_scripts_dir = _hook_dir.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))


async def execute(context: dict[str, Any]) -> dict[str, Any]:
    """启动时加载数字人形象"""
    from loguru import logger

    options = context.get("_options", {})
    workspace = context.get("workspace") or Path.home() / ".nanobot" / "workspace"

    try:
        # 1. 构建人格
        from persona_builder import PersonaBuilder
        persona = PersonaBuilder(Path(workspace)).build()

        # 2. 加载预生成的数字人图片
        avatar_dir = Path.home() / ".nanobot" / ".avatar"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        avatar_path = avatar_dir / "avatar.png"

        # 检查是否需要生成/复制图片
        # need_generate = not avatar_path.exists()

        # if not need_generate:
        #     import time
        #     age_days = (time.time() - avatar_path.stat().st_mtime) / 86400
        #     if age_days > options.get("regenerate_days", 7):
        #         need_generate = True

        # if need_generate:
        #     from avatar_generator import AvatarGenerator

        #     # 获取 assets 目录
        #     skill_dir = _hook_dir.parent.parent
        #     assets_dir = skill_dir / "assets"

        #     # 使用预生成的图片
        #     generator = AvatarGenerator(assets_dir=assets_dir)

        #     # 打印可用图片信息
        #     for avatar_type in generator.get_available_types():
        #         count = generator.get_image_count(avatar_type)

        #     # 生成默认图片（neutral 类型）
        #     result = await generator.generate(avatar_type="neutral")

        #     if result.success and result.image_path:
        #         import shutil
        #         shutil.copy(result.image_path, avatar_path)
        #     else:
        #         avatar_path = None

        # 3. 启动展示服务
        await _start_server(context, persona, options, avatar_path)

    except Exception as e:
        logger.error(f"Digital Avatar: 启动失败 - {e}")
        import traceback
        logger.debug(traceback.format_exc())

    return context


async def _start_server(context, persona, options, avatar_path) -> None:
    """启动展示服务"""
    from loguru import logger
    from display_server import get_server

    # 获取 assets 目录
    skill_dir = _hook_dir.parent.parent
    assets_dir = skill_dir / "assets"

    server = get_server(assets_dir=assets_dir)
    server.port = options.get("display_port", 18791)
    await server.start(auto_open=options.get("auto_open", True))
    await server.set_name(persona.name)
    await server.update_status("就绪")
    if avatar_path and avatar_path.exists():
        await server.update_avatar(str(avatar_path))

    context["_avatar_server"] = server
    context["_persona"] = persona
