from rclone_python import rclone


def test_about(tmp_local_folder):
    # NOTE: rclone about does not work on s3 --> do locally instead
    expected_fields = set(["total", "used", "free"])

    output = rclone.about(tmp_local_folder)
    assert expected_fields.issubset(set(output.keys()))
    for field in expected_fields:
        assert isinstance(output[field], (int, float))
