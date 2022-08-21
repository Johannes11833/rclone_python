from rclone_python import rclone

if __name__ == '__main__':
    print(rclone.ls('onedrive:data', max_depth=1))
    rclone.copy('onedrive:data', 'data')
