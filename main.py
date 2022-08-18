from rclone_python import rclone

if __name__ == '__main__':
    # rclone.create_remote('onedrive2', RemoteTypes.onedrive)
    # rclone.copy('onedrive:test_dir', 'data')
    # rclone.move('data', 'onedrive:test_dir')

    rclone.delete('onedrive:data')
    # rclone.delete('onedrive:test_dir/video2.webm')
    # rclone.purge('onedrive:test_dir')

    # print(rclone.check_remote_existing('onedrive:'))
