import os
import shutil

IMAGES_DIR = "/images"

def setup_rootfs(image, container_dir):
    image_path = f"{IMAGES_DIR}/{image}"
    if not os.path.exists(image_path):
        raise Exception(f"Image not found: {image_path}")
    
    # OverlayFS needs three dirs: upper (writes), work (overlay internals), merged (mount point)
    upper = f"{container_dir}/upper"
    work = f"{container_dir}/work"
    merged = f"{container_dir}/rootfs" # This is our chroot inside container
    
    # rootfs = f"{container_dir}/rootfs"
    # if os.path.exists(rootfs):
    #     shutil.rmtree(rootfs)

    # shutil.copytree(image_path, rootfs, symlinks=True) 
    
    for d in[upper, work, merged]:
        os.makedirs(d, exist_ok = True)
    
    mount_opts = f"lowerdir={image_path},upperdir={upper},workdir={work}"
    ret = os.system(f"mount -t overlay overlay -o {mount_opts} {merged}")
    
    if ret != 0:
        raise Exception("overlay mount failed")
    
    return merged

def teardown_rootfs(container_dir):
    merged = f"{container_dir}/rootfs"
    os.system(f"umount {merged}")