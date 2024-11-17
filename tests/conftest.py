from pathlib import Path
import pytest


class TestRemote:
    def __init__(
        self,
        remote_name,
        remote_test_dir,
        local_test_txt_file,
    ):
        self.remote_name: str = remote_name
        self.remote_test_data_dir: str = remote_test_dir
        self.local_test_txt_file: Path = Path(local_test_txt_file)


@pytest.fixture(scope="session")
def default_remote():
    return TestRemote("box", "box:test_dir", "tests/data/lorem.txt")
