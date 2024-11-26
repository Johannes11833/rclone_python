from pathlib import Path
import pytest


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
        remote_name="box",
        remote_test_dir_rel="test_dir",
        local_test_txt_file="tests/data/lorem.txt",
    )
