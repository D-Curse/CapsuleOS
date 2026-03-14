from fastapi import FastAPI, WebSocket
from .container_manager import manager
from .schemas import ContainerCreate
from .stats import get_container_stats
from .websocket import stats_stream, log_stream

app = FastAPI()

@app.post("/container/create")
def create_container(req: ContainerCreate):
    return manager.create(req)

@app.post("/container/start/{cid}")
def start_container(cid: str):
    return manager.start(cid)

@app.post("/container/stop/{cid}")
def stop_container(cid: str):
    return manager.stop(cid)

@app.delete("/container/delete/{cid}")
def delete_container(cid:str):
    return manager.delete(cid)
    
@app.get("/containers")
def list_containers():
    return manager.list()

@app.get("/container/{cid}/stats")
def stats(cid:str):
    return get_container_stats(cid)

@app.websocket("/ws/{cid}/stats")
async def ws_status(ws: WebSocket, cid: str):
    await stats_stream(ws, cid)
    
@app.websocket("/ws/{cid}/logs")
async def ws_logs(ws: WebSocket, cid: str):
    await log_stream(ws, cid)