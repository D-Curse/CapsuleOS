import os
import fcntl
import termios
import struct

def open_container_pty(pid, cid):
    rootfs = f"/containers/{cid}/rootfs"

    ns_path = f"/proc/{pid}/ns/mnt"
    if not os.path.exists(ns_path):
        raise Exception(f"Process {pid} not found at {ns_path}")

    master_fd, slave_fd = os.openpty()
    bash_pid = os.fork()

    if bash_pid == 0:
        try:
            os.close(master_fd)
            os.setsid()
            fcntl.ioctl(slave_fd, termios.TIOCSCTTY, 0)
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.close(slave_fd)

            # Enter namespaces manually by opening and calling setns via libc
            # Then chroot into the overlay rootfs ourselves
            import ctypes
            libc = ctypes.CDLL("libc.so.6", use_errno=True)

            # Enter each namespace
            for ns in ["mnt", "uts", "ipc", "net", "pid"]:
                ns_fd = os.open(f"/proc/{pid}/ns/{ns}", os.O_RDONLY)
                ret = libc.setns(ns_fd, 0)
                os.close(ns_fd)
                if ret != 0:
                    raise Exception(f"setns {ns} failed: {ctypes.get_errno()}")

            # Now chroot into the container's rootfs
            # This works because we're now in the container's mount namespace
            # where the overlay IS mounted at rootfs
            os.chroot(rootfs)
            os.chdir("/")

            # Set up a clean environment
            os.environ["TERM"] = "xterm-256color"
            os.environ["HOME"] = "/root"
            os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            os.environ.pop("OLDPWD", None)

            os.execvp("/bin/bash", ["/bin/bash"])

        except Exception as e:
            with open(f"/tmp/exec_error_{pid}.txt", "w") as f:
                f.write(str(e))
            os._exit(1)

    os.close(slave_fd)
    return master_fd, bash_pid

def set_pty_size(master_fd, rows, cols):
    size = struct.pack("HHHH", rows, cols, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, size)