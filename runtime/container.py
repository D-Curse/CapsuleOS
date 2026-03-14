import os
import json

CONTAINER_DIR = "/containers"

class Container:
    
    def __init__(self, cid, image, command, cpu, memory):
        
        self.id = cid
        self.image = image
        self.command = command
        self.cpu = cpu
        self.memory = memory
        self.pid = None
        self.status = "created"
        
    def config_path(self):
        return f"{CONTAINER_DIR}/{self.id}/config.json"
    
    def save(self):
        os.makedirs(f"{CONTAINER_DIR}/{self.id}", exist_ok=True)
        log_path = f"{CONTAINER_DIR}/{self.id}/logs.txt"
        open(log_path, "a").close()
        
        data = {
            "id": self.id,
            "image": self.image,
            "command": self.command,
            "cpu": self.cpu,
            "memory": self.memory,
            "pid": self.pid,
            "status": self.status
        }
        
        with open(self.config_path(), "w") as f:
            json.dump(data, f)
            
            
    @staticmethod
    def load(cid):
        path = f"{CONTAINER_DIR}/{cid}/config.json"
        
        if not os.path.exists(path):
            raise Exception("container not found")
        
        with open(path) as f:
            data = json.load(f)
            
        c = Container(
            data["id"],
            data["image"],
            data["command"],
            data["cpu"],
            data["memory"]
        )
        
        c.pid = data["pid"]
        c.status = data["status"]
        
        return c
    
    def stop(self):
        if self.pid:
            os.kill(self.pid, 15)
            self.status = "stopped"
            self.save()
            
    def delete(self):
        path = f"{CONTAINER_DIR}/{self.id}"
        
        if os.path.exists(path):
            os.system(f"rm -rf {path}")