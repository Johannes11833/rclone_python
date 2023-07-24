from rclone_python import rclone

if __name__ == "__main__":
    # rclone.create_remote('test1', remote_types.RemoteTypes.box)
    print(rclone.get_remotes())

    # print(rclone.about("onedrive"))
    # rclone.copy("data/abc", "onedrive:data_new/ac7")
    # # rclone.copy("data/image.jpg", "onedrive:new_image.jpg")
    # rclone.sync("test_bisync", "box:data_new")
    # print(rclone.hash("sha1", "box:data_new"))
    # print(rclone.hash("sha1", "box:data_new/video2.webm"))
    # print(rclone.hash("sha1", "box:data_new", checkfile="checkfile"))
    print(rclone.hash("sha1", "box:data_new/video1.webm", checkfile="checkfile_vid1"))

    # print(f"#{rclone.version(check=True)}#")
    # print(f"#{rclone.version(check=False)}#")
