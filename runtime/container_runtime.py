import os
import uuid
import signal

from .namespaces import setup_namespaces
from .cgroups import create_cgroups, join_cgroups, cleanup_cgroups
from .filesystem import setup_rootfs
from .network import allocate_ip, setup_container_network, teardown_container_network

BASE_DIR = "/containers"

def reap_children(signum, frame):
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break
        
signal.signal(signal.SIGCHLD, reap_children)


class ContainerRuntime:

    def create(self, image, command, cpu, memory):
        cid = uuid.uuid4().hex[:12]
        container_dir = f"{BASE_DIR}/{cid}"
        os.makedirs(container_dir, exist_ok=True)

        # Just create the dirs, don't mount yet
        upper  = f"{container_dir}/upper"
        work   = f"{container_dir}/work"
        merged = f"{container_dir}/rootfs"
        for d in [upper, work, merged]:
            os.makedirs(d, exist_ok=True)

        return {
            "id": cid, "image": image, "command": command,
            "cpu": cpu, "memory": memory, "status": "created"
        }

    def start(self, config):
        cid    = config["id"]
        cpu    = config["cpu"]
        memory = config["memory"]
        image  = config["image"]

        container_dir = f"{BASE_DIR}/{cid}"
        rootfs        = f"{container_dir}/rootfs"
        log_file      = f"{container_dir}/logs.txt"

        create_cgroups(cid, cpu, memory)
        log_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        pid = os.fork()

        if pid == 0:
            try:
                signal.signal(signal.SIGCHLD, signal.SIG_DFL)

                os.dup2(log_fd, 1)
                os.dup2(log_fd, 2)
                os.close(log_fd)

                # 1. Enter new namespaces (creates new mount namespace)
                setup_namespaces()
                join_cgroups(cid)

                # 2. Mount overlay INSIDE the new mount namespace
                #    Now this mount is private to the container
                image_path = f"/images/{image}"
                upper      = f"{container_dir}/upper"
                work       = f"{container_dir}/work"
                mount_opts = f"lowerdir={image_path},upperdir={upper},workdir={work}"
                ret = os.system(f"mount -t overlay overlay -o {mount_opts} {rootfs} 2>/containers/{cid}/mount_error.txt")
                if ret != 0:
                    raise Exception("overlay mount failed")

                # 3. Now chroot into the freshly mounted overlay
                os.chroot(rootfs)
                os.chdir("/")

                os.system("mount -t proc proc /proc")

                os.execvp(config["command"][0], config["command"])

            except Exception as e:
                with open(f"{container_dir}/runtime_error.txt", "w") as f:
                    f.write(str(e))
                os._exit(1)

        os.close(log_fd)
        container_ip = allocate_ip()
        setup_container_network(cid, pid, container_ip)
        return pid, container_ip
    
    def stop(self, pid, cid):
        try:
            os.kill(pid, signal.SIGTERM)
            
            for _ in range(50):
                try:
                    result = os.waitpid(pid, os.WNOHANG)
                    if result[0] != 0:
                        break
                    
                except ChildProcessError:
                    break
                
                import time
                time.sleep(0.1)
            else:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
        
        except ProcessLookupError:
            pass
        finally:
            teardown_container_network(cid)
            cleanup_cgroups(cid)