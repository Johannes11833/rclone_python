from rclone_python import rclone


def test_mkdir(tmp_remote_folder):
    folder_name = "dir1  v2"
    rclone.mkdir(f"{tmp_remote_folder}/{folder_name}")

    output = rclone.ls(tmp_remote_folder)

    assert len(output) == 1
    assert output[0]["Path"] == folder_name
    assert output[0]["IsDir"] is True
