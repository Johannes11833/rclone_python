from rclone_python import rclone

if __name__ == '__main__':
    print(f'rclone installed: {rclone.is_installed()}')
    rclone.move('onedrive:data', 'tata')
