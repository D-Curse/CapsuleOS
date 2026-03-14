import os
import shutil

IMAGE_STORE = "./images"

class ImageManager:
    def list_images(self):
        return os.listdir(IMAGE_STORE)
    
    def image_path(self, name):
        path = f"{IMAGE_STORE}/{name}"

        if not os.path.exists(path):
            raise Exception("image not found")
        
        return path
    
    def unpack(self, name, rootfs):
        src = self.image_path(name)
        shutil.copytree(src, rootfs)