from rclone_python import rclone

if __name__ == '__main__':
    rclone.create_remote('onedrive2', rclone.RemoteTypes.onedrive)
    # rclone.copy('data', 'test_dir', remote_name_dest='onedriv', remote_name_src=None)
    # rclone.copy('test_dir', 'data', remote_name_src='onedrive', remote_name_dest=None)
    # rclone.delete('onedrive', 'test_dir')
