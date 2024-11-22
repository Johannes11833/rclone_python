from pathlib import Path
import uuid
import pytest
from rclone_python import rclone


@pytest.fixture(scope="module")
def temporary_remote_folder(default_test_setup):
    remote_relative_test_dir = (
        f"{default_test_setup.remote_test_data_dir}/{uuid.uuid4()}"
    )

    rclone.mkdir(remote_relative_test_dir)
    print(f"Created temp test dir: {remote_relative_test_dir}")

    yield remote_relative_test_dir

    # TEARDOWN
    print(f"\nTeardown: deleting temp remote folder at {remote_relative_test_dir}")
    rclone.purge(remote_relative_test_dir)


@pytest.fixture(scope="module")
def large_tmp_local_file():
    # Create large local file
    local_file_path = Path("data/tmp_file.file")
    local_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_file_path, "wb") as out:
        out.truncate(10 * 1024 * 1024)

    yield local_file_path

    # TEARDOWN
    print(f"\nTeardown: Removing tmp file at {local_file_path}")
    local_file_path.unlink()


def test_copy(temporary_remote_folder, large_tmp_local_file):
    rclone.copy(str(large_tmp_local_file), temporary_remote_folder)

    assert rclone.ls(temporary_remote_folder)[0]["Path"] == large_tmp_local_file.name
