import os
import shutil

IMAGES_DIR = "/images"

def setup_rootfs(image, container_dir):
    image_path = f"{IMAGES_DIR}/{image}"
    rootfs = f"{container_dir}/rootfs"

    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")

    if os.path.exists(rootfs):
        shutil.rmtree(rootfs)

    shutil.copytree(image_path, rootfs, symlinks=True) 

    return rootfs