import ctypes
import os

CLONE_NEWUTS = 0x04000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNS = 0x00020000
CLONE_NEWNET = 0x40000000

libc = ctypes.CDLL("libc.so.6", use_errno=True)

def setup_namespaces():

    flags = (
        CLONE_NEWUTS |
        CLONE_NEWPID |
        CLONE_NEWNS  |
        CLONE_NEWNET
    )

    if libc.unshare(flags) != 0:
        errno = ctypes.get_errno()
        raise Exception(f"unshare failed: errno {errno} -  {os.strerror(errno)}")

    hostname = b"capsule"

    if libc.sethostname(hostname, len(hostname)) != 0:
        errno = ctypes.get_errno()
        raise Exception(f"sethostname failed: errno {errno} - {os.strerror(errno)}")