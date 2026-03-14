from pydantic import BaseModel
from typing import List

class ContainerCreate(BaseModel):
    image: str
    command: List[str]
    cpu: int
    memory: int
    
    
class ContainerResponse(BaseModel):
    id: str
    image: str
    status: str
    cpu: int
    memory: int
    pid: int | None