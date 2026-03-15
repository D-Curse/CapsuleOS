import os

CGROUP_BASE = "/sys/fs/cgroup"

def create_cgroups(cid, cpu_limit, mem_limit):
    cgroup_path = f"{CGROUP_BASE}/mini_{cid}"

    os.makedirs(cgroup_path, exist_ok=True)

    # Enable cpu and memory controllers
    with open(f"{CGROUP_BASE}/cgroup.subtree_control", "w") as f:
        f.write("+cpu +memory")

    # cpu.max format is "quota period" (period defaults to 100000 microseconds)
    with open(f"{cgroup_path}/cpu.max", "w") as f:
        f.write(f"{cpu_limit} 100000")

    with open(f"{cgroup_path}/memory.max", "w") as f:
        f.write(str(mem_limit))

def join_cgroups(cid):
    cgroup_path = f"{CGROUP_BASE}/mini_{cid}"

    with open(f"{cgroup_path}/cgroup.procs", "w") as f:
        f.write(str(os.getpid()))
        
def cleanup_cgroups(cid):
    cgroup_path = f"{CGROUP_BASE}/mini_{cid}"
    try:
        os.rmdir(cgroup_path)
    except FileNotFoundError:
        pass