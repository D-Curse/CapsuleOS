import uuid
import os
from runtime.container import Container
from runtime.container_runtime import ContainerRuntime

runtime = ContainerRuntime()

class ContainerManager:
    
    def __init__(self):
        self.containers = {}
        
    def create(self, req):
        config = runtime.create(
            image=req.image,
            command=req.command,
            cpu=req.cpu,
            memory=req.memory
        )
        
        cid = config["id"]
        
        container = Container(
            cid,
            req.image,
            req.command,
            req.cpu,
            req.memory
        )
        
        container.save()
        
        self.containers[cid] = container
        return container.__dict__
    
    def start(self, cid):
        container = Container.load(cid)
        pid = runtime.start({
            "id": container.id,
            "image": container.image,
            "command": container.command,
            "cpu": container.cpu,
            "memory": container.memory
        })
        
        container.pid = pid
        container.status = "running"
        container.save()
        
        return container.__dict__
    
    def stop(self, cid):
        container = Container.load(cid)
        container.stop()
        return {"status": "stopped"}
    
    def delete(self, cid):
        container = Container.load(cid)
        container.delete()
        return {"status": "deleted"}
    
    def list(self):
        base = "/containers"
        
        if not os.path.exists(base):
            return []
        
        containers = []
        for cid in os.listdir(base):
            try:
                container = Container.load(cid)
                containers.append(container.__dict__)
            except Exception as e:
                continue
            
        return containers
    
manager = ContainerManager()
        
        