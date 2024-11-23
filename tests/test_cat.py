import pytest
from rclone_python import rclone


@pytest.fixture(scope="module")
def lorem_ipsum_remote_file(default_test_setup):
    # uploads the lorem ipsum text file prior to the execution of the tests and deletes it afterwards

    # INITIALIZATION
    print("\nInitializing: uploading lorem ipsum file")
    remote_path = f"{default_test_setup.remote_test_data_dir}/{default_test_setup.local_test_txt_file.name}"

    rclone.copyto(
        str(default_test_setup.local_test_txt_file),
        remote_path,
        ignore_existing=True,
        show_progress=False,
    )

    yield remote_path

    # TEARDOWN
    print("\nTeardown: deleting lorem ipsum file")
    rclone.delete(remote_path)


def test_cat(default_test_setup, lorem_ipsum_remote_file):
    output = rclone.cat(lorem_ipsum_remote_file)

    assert output == default_test_setup.local_test_txt_file.read_text()


def test_cat_count(default_test_setup, lorem_ipsum_remote_file):
    count = 10

    output = rclone.cat(lorem_ipsum_remote_file, count=count)

    assert output == default_test_setup.local_test_txt_file.read_text()[:count]


def test_cat_head(default_test_setup, lorem_ipsum_remote_file):
    head = 10

    output = rclone.cat(lorem_ipsum_remote_file, head=head)

    assert output == default_test_setup.local_test_txt_file.read_text()[:head]


def test_cat_offset(default_test_setup, lorem_ipsum_remote_file):
    offset = 10
    count = 15

    # offset and count
    output = rclone.cat(lorem_ipsum_remote_file, offset=offset, count=count)
    assert (
        output
        == default_test_setup.local_test_txt_file.read_text()[offset : offset + count]
    )
