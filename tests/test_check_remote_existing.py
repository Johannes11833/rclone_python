from rclone_python import rclone


def test_check_remote_existing(default_test_setup):
    assert rclone.check_remote_existing(default_test_setup.remote_name) is True
    assert rclone.check_remote_existing(default_test_setup.remote_name + ":") is True
    assert rclone.check_remote_existing("new_remote123") is False
