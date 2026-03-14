import os 
import subprocess
import psutil

def run(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return process

def get_cpu_usage(pid):
    try:
        p = psutil.Process(pid)
        return p.cpu_percent(interval=0.1)
    except:
        return 0
    
def get_memory_usuage(pid):
    try:
        p = psutil.Process(pid)
        return p.memory_info().rss
    except:
        return 0
    
def read_logs(cid):
    log_file = f"/containers/{cid}/logs.txt"
    
    if not os.path.exists(log_file):
        return ""
    
    with open(log_file) as f:
        return f.read()