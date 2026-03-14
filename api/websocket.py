from fastapi import WebSocket
import asyncio
import os
from .stats import get_container_stats

async def stats_stream(ws: WebSocket, cid):
    await ws.accept()
    while True:
        stats = get_container_stats(cid)
        await ws.send_json(stats)
        await asyncio.sleep(1)
        
async def log_stream(ws, cid):

    await ws.accept()

    log_file = f"/containers/{cid}/logs.txt"
    offset = 0

    while True:

        if not os.path.exists(log_file):
            await asyncio.sleep(1)
            continue

        with open(log_file) as f:

            f.seek(offset)
            data = f.read()
            offset = f.tell()

        if data:
            await ws.send_text(data)

        await asyncio.sleep(1)