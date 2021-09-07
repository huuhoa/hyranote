import os
import shutil


def copy_resources(input_dir, dst):
    resources = os.path.join(input_dir, 'resources')
    shutil.copytree(resources, dst, dirs_exist_ok=True)
