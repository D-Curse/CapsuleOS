import os
import uuid

from .namespaces import setup_namespaces
from .cgroups import create_cgroups, join_cgroups
from .filesystem import setup_rootfs

BASE_DIR = "/containers"


class ContainerRuntime:

    def create(self, image, command, cpu, memory):

        cid = uuid.uuid4().hex[:12]
        container_dir = f"{BASE_DIR}/{cid}"

        os.makedirs(container_dir, exist_ok=True)

        rootfs = setup_rootfs(image, container_dir)
        print("rootfs: ", rootfs)

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
        pid = os.fork()
                
        if pid == 0:
            try:
                setup_namespaces()
                join_cgroups(cid)

                # Open log file BEFORE chroot, while host paths are still valid
                log_fd = os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
                os.dup2(log_fd, 1)
                os.dup2(log_fd, 2)
                os.close(log_fd)

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

        return pid