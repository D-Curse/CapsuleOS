import psutil
from runtime.container import Container

def get_container_stats(cid):
    container = Container.load(cid)
    
    if container.pid is None:
        return {
            "cpu": 0,
            "memory": 0
        }
        
    try:
        p = psutil.Process(container.pid)
        
        return {
            "cpu": p.cpu_percent(interval=0.1),
            "memory": p.memory_info().rss
        }
        
    except:
        return {
            "cpu": 0,
            "memory": 0
        }