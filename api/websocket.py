from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import os
import json

from .stats import get_container_stats
from runtime.exec import open_container_pty, set_pty_size
from runtime.container import Container

BASE_DIR = "/containers"

async def stats_stream(ws: WebSocket, cid):
    await ws.accept()
    try:
        while True:
            stats = get_container_stats(cid)
            await ws.send_json(stats)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
            
        
async def log_stream(ws, cid):
    await ws.accept()
    log_file = f"{BASE_DIR}/{cid}/logs.txt"
    try:
        with open(log_file, "r") as f:
            while True:
                line = f.readline()
                if line:
                    await ws.send_text(line)
                else:
                    await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        pass
    
    
async def exec_stream(ws: WebSocket, cid: str):
    await ws.accept()

    container = Container.load(cid)

    if not container.pid:
        await ws.send_text("Error: container has no pid")
        await ws.close(code=1008)
        return

    pid = container.pid
    if isinstance(pid, list):
        pid = pid[0]
    pid = int(pid)

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        await ws.send_text(f"Error: process {pid} not running")
        await ws.close(code=1008)
        return

    master_fd, bash_pid = open_container_pty(pid, container.id)

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    async def pty_to_ws():
        while not stop.is_set():
            try:
                # Blocking read in thread — this is correct
                data = await loop.run_in_executor(None, lambda: os.read(master_fd, 1024))
                if not data:
                    break
                await ws.send_text(data.decode(errors="replace"))
            except OSError as e:
                print(f"pty_to_ws error: {e}")
                break

    async def ws_to_pty():
        try:
            while True:
                msg = await ws.receive_text()
                packet = json.loads(msg)

                if packet["type"] == "input":
                    os.write(master_fd, packet["data"].encode())
                elif packet["type"] == "resize":
                    set_pty_size(master_fd, packet["rows"], packet["cols"])

        except (WebSocketDisconnect, Exception) as e:
            print(f"ws_to_pty error: {e}")
            stop.set()

    await asyncio.gather(pty_to_ws(), ws_to_pty())

    os.close(master_fd)
    try:
        os.kill(bash_pid, 9)
        os.waitpid(bash_pid, 0)
    except Exception:
        pass