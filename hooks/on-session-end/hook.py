"""On Session End Hook"""

from __future__ import annotations
from typing import Any

async def execute(context: dict[str, Any]) -> dict[str, Any]:
    server = context.get("_avatar_server")
    if not server:
        return context
    await server.update_expression("neutral")
    await server.update_status("就绪")
    await server.show_bubble("期待下次交流！")
    return context
