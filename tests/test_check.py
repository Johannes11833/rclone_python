from pathlib import Path
import tempfile
import pytest

from rclone_python import rclone


@pytest.fixture(scope="module")
def check_command_setup(default_test_setup):
    # uploads the lorem ipsum text file prior to the execution of the tests and deletes it afterwards

    # INITIALIZATION
    # LOCAL
    local_path = tempfile.TemporaryDirectory()
    text = default_test_setup.local_test_txt_file.read_text()
    for i in range(5):
        Path(local_path.name, f"file  {i}").write_text(f"This is file #{i}.\n{text}")
    print(
        "\ncreated temporary directory:",
        local_path.name,
        "with content:",
        list(Path(local_path.name).iterdir()),
    )

    # REMOTE
    remote_path = f"{default_test_setup.remote_test_data_dir}"
    rclone.copy(
        local_path.name,
        remote_path,
        show_progress=False,
    )

    yield Path(local_path.name), remote_path

    # TEARDOWN
    print(f"\nTeardown: remote {remote_path} and local: {local_path.name}")
    rclone.delete(remote_path)
    local_path.cleanup()


def test_check_matching(check_command_setup):
    # here, dest and source match
    local_path, remote_path = check_command_setup
    local_files = [x.name for x in local_path.iterdir() if x.is_file()]

    expected = [("=", f) for f in local_files]
    valid, output = rclone.check(local_path, remote_path)

    print("output: ", output)
    print("expected:", expected)

    assert valid
    # order might be different, so check that there is no difference between the 2 sets
    assert not set(expected) ^ set(output)


def test_check_not_matching(check_command_setup):
    # same as above: here, dest and source match at first
    local_path, remote_path = check_command_setup
    local_files = [x.name for x in local_path.iterdir() if x.is_file()]

    # alter first file locally
    local_path.iterdir().__next__().write_text(
        "The content of the first file is now different locally."
    )
    # add another file locally that is missing on remote
    new_file = Path(local_path, "new_file")
    new_file.write_text("The content of the new local file")

    # create expected list
    expected = [("=", f) for f in local_files]
    expected.append(("+", new_file.name))
    expected[0] = ("*", expected[0][1])  # the first file was altered

    valid, output = rclone.check(local_path, remote_path)
    print("output: ", output)
    print("expected:", expected)

    assert not valid
    # order might be different, so check that there is no difference between the 2 sets
    assert not set(expected) ^ set(output)
