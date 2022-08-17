import re

import rclone

if __name__ == '__main__':
    # rclone.create('cloud', rclone.RemoteTypes.google)
    rclone.copy('cloud', 'data', 'test_dir', ignore_existing=False)
