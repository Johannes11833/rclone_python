from rclone_python import rclone

if __name__ == '__main__':
    # rclone.create_remote('onedrive2', RemoteTypes.onedrive)
    # rclone.move('onedrive:test_dir', 'data')
    # rclone.move('data', 'onedrive:test_dir')

    print(rclone.check_remote_existing('onedrive:'))
