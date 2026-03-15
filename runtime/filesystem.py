import os
import shutil

IMAGES_DIR = "/images"

def setup_rootfs(image, container_dir):
    image_path = f"{IMAGES_DIR}/{image}"
    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")

    for d in ["upper", "work", "rootfs"]:
        os.makedirs(f"{container_dir}/{d}", exist_ok=True)
        
    ret = os.system(f"mount -t overlay overlay -o {mount_opts} {rootfs} 2>/containers/{cid}/mount_error.txt")
    if ret != 0:
        raise Exception("overlay mount failed")

    return f"{container_dir}/rootfs"

def teardown_rootfs(container_dir):
    merged = f"{container_dir}/rootfs"
    os.system(f"umount {merged}")