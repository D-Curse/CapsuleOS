import os
import uuid
import signal

from .namespaces import setup_namespaces
from .cgroups import create_cgroups, join_cgroups, cleanup_cgroups
from .filesystem import setup_rootfs

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

        rootfs = setup_rootfs(image, container_dir)
        if not os.path.exists(rootfs):
            raise Exception("rootfs creation failed")

        config = {
            "id": cid,
            "image": image,
            "command": command,
            "cpu": cpu,
            "memory": memory,
            "status": "created"
        }

        return config

    def start(self, config):

        cid = config["id"]
        cpu = config["cpu"]
        memory = config["memory"]

        rootfs = f"{BASE_DIR}/{cid}/rootfs"
        log_file = f"{BASE_DIR}/{cid}/logs.txt"

        if not os.path.exists(rootfs):
            raise Exception("rootfs does not exist")

        create_cgroups(cid, cpu, memory)
        
        log_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        pid = os.fork()
                
        if pid == 0:
            try:
                signal.signal(signal.SIGCHLD, signal.SIG_DFL)
                
                
                # Open log file BEFORE chroot, while host paths are still valid
                # log_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(log_fd, 1)
                os.dup2(log_fd, 2)
                os.close(log_fd)
                
                setup_namespaces()
                join_cgroups(cid)


                # Now safe to chroot — stdout/stderr are already redirected to host fd
                os.chroot(rootfs)
                os.chdir("/")

                os.system("mount -t proc proc /proc")

                os.execvp(config["command"][0], config["command"])

            except Exception as e:

                error_file = f"{BASE_DIR}/{cid}/runtime_error.txt"

                with open(error_file, "w") as f:
                    f.write(str(e))

                os._exit(1)
        os.close(log_fd)

        return pid
    
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
            cleanup_cgroups(cid)