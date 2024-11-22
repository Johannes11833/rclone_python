from pathlib import Path
import pytest


class TestSetup:
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
def default_test_setup():
    return TestSetup(
        remote_name="box",
        remote_test_dir="box:test_dir",
        local_test_txt_file="tests/data/lorem.txt",
    )
