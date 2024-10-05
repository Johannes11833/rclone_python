from rclone_python import rclone, remote_types
from rclone_python.hash_types import HashTypes

if __name__ == "__main__":
    rclone.create_remote("box", remote_types.RemoteTypes.box)
    print(rclone.get_remotes())
    print(rclone.ls("box:data", max_depth=1, files_only=True))
    rclone.copy("box:data", "data")
    rclone.copy("some_local_folder/image.jpg", "box:new_image.jpg")

    print(rclone.hash(HashTypes.sha1, "box:data"))
