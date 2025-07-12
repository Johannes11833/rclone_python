from pathlib import Path
import tempfile
import uuid
import pytest
from rclone_python import rclone, utils


class TestSetup:
    def __init__(
        self,
        remote_name: str,
        remote_test_dir_rel: str,
        local_test_txt_file: str,
        tmp_local_file_size_mb: int = 1.2,
    ):
        self.remote_name: str = remote_name
        self.remote_test_data_dir: str = f"{remote_name}:{remote_test_dir_rel}"
        self.local_test_txt_file: Path = Path(local_test_txt_file)
        self.tmp_local_file_size_mb = tmp_local_file_size_mb


@pytest.fixture(scope="session")
def default_test_setup():
    return TestSetup(
        remote_name="test_server_s3",
        remote_test_dir_rel="testdir",
        local_test_txt_file="tests/data/lorem.txt",
    )


@pytest.fixture(scope="function")
def tmp_remote_folder(default_test_setup):
    # automatically removes this folder after a test function compted.
    # only the teardown is done, the folder is not created and the test should upload to that path.
    remote_relative_test_dir = (
        f"{default_test_setup.remote_test_data_dir}/{uuid.uuid4()}"
    )

    yield remote_relative_test_dir

    # TEARDOWN
    print(f"\nTeardown: deleting temp remote folder at {remote_relative_test_dir}")
    try:
        rclone.purge(remote_relative_test_dir)
    except utils.RcloneException:
        pass


@pytest.fixture(scope="function")
def tmp_local_folder():
    # create a local tmp folder that will be automatically removed.
    with tempfile.TemporaryDirectory() as path:
        print("created temporary directory:", path)
        yield Path(path)

    print("Teardown: removed local tmp folder")
