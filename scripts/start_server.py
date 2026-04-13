#!/usr/bin/env python3
import asyncio
from display_server import DisplayServer

async def main():
    server = DisplayServer(port=18791)
    await server.start(auto_open=False)
    await asyncio.Event().wait()

asyncio.run(main())
