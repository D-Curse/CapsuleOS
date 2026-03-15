from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .container_manager import manager
from .schemas import ContainerCreate
from .stats import get_container_stats
from .websocket import stats_stream, log_stream, exec_stream
from runtime.network import setup_bridge

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    setup_bridge()

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
    
@app.websocket("/ws/{cid}/exec")
async def ws_exec(ws: WebSocket, cid: str):
    await exec_stream(ws, cid)