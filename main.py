import py_rclone
from py_rclone import rclone

if __name__ == '__main__':
    # rclone.create_remote('onedrive2', RemoteTypes.onedrive)
    rclone.copy('onedrive:data', 'da')
    # rclone.move('data', 'onedrive:test_dir')

    # rclone.delete('onedrive:data')
    # rclone.delete('onedrive:test_dir/video2.webm')
    # rclone.purge('onedrive:test_dir')
    print(py_rclone.VERSION)

    # print(rclone.check_remote_existing('onedrive:'))
