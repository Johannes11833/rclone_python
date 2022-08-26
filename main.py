from rclone_python import rclone

if __name__ == '__main__':
    # rclone.create_remote('test1', remote_types.RemoteTypes.box)
    print(rclone.get_remotes())
    print(rclone.ls('onedrive:data', max_depth=1, files_only=True))
    rclone.copy('data', 'onedrive:data2', args=['--create-empty-src-dirs'])
