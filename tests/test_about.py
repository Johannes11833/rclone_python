from rclone_python import rclone


def test_about(default_test_setup):
    expected_fields = set(["total", "used", "free"])

    output = rclone.about(default_test_setup.remote_name)
    assert expected_fields.issubset(set(output.keys()))
    for field in expected_fields:
        assert isinstance(output[field], (int, float))

    output = rclone.about(default_test_setup.remote_name + ":")
    assert expected_fields.issubset(set(output.keys()))
    for field in expected_fields:
        assert isinstance(output[field], (int, float))
