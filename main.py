from src.rclone_python import rclone

if __name__ == '__main__':
    # rclone.create('onedrive', rclone.RemoteTypes.onedrive)
    rclone.copy('onedrive', 'data', 'test_dir', ignore_existing=False)
    # rclone.delete('onedrive', 'test_dir')
