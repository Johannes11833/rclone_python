import os
from pathlib import Path
import tempfile
from typing import Dict, List, Union
import uuid
import pytest
from rclone_python import rclone


@pytest.fixture(scope="function")
def tmp_remote_folder(default_test_setup):
    remote_relative_test_dir = (
        f"{default_test_setup.remote_test_data_dir}/{uuid.uuid4()}"
    )

    yield remote_relative_test_dir

    # TEARDOWN
    print(f"\nTeardown: deleting temp remote folder at {remote_relative_test_dir}")
    rclone.purge(remote_relative_test_dir)


@pytest.fixture(scope="function")
def tmp_local_folder():
    # create a local tmp folder that will be automatically removed.
    with tempfile.TemporaryDirectory() as path:
        print("created temporary directory:", path)
        yield Path(path)

    print("Teardown: removed local tmp folder")


class Recorder:
    def __init__(self):
        self.history = []

    def update(self, update: dict):
        self.history.append(update)

    def get_summary_stats(self, stat_name: str) -> List[any]:
        return [update[stat_name] for update in self.history]

    def get_task_stats(self, stat_name: str, task_name: str) -> List[any]:
        return [
            task_update[stat_name]
            for update in self.history
            for task_update in update["tasks"]
            if task_update["name"] == task_name
        ]


def create_tmp_local_file(
    path: Union[str, Path], size_mb: float, file_name: str = "tmp_file.file"
) -> Path:
    # Create large local file
    local_file_path = Path(path) / file_name
    local_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_file_path, "wb") as out:
        out.truncate(int(size_mb * 1024 * 1024))

    return local_file_path


def test_copy(default_test_setup, tmp_remote_folder, tmp_local_folder):
    tmp_local_file = create_tmp_local_file(
        tmp_local_folder, default_test_setup.tmp_local_file_size_mb
    )

    # upload: copy local to remote
    rclone.copy(tmp_local_folder, tmp_remote_folder)
    assert rclone.ls(tmp_remote_folder)[0]["Path"] == tmp_local_file.name

    # download: copy remote to local
    download_path = tmp_local_folder / "download"
    rclone.copy(
        tmp_remote_folder,
        download_path,
    )
    assert (download_path / tmp_local_file.name).is_file()


@pytest.mark.parametrize(
    "method,show_progress",
    [
        (rclone.copy, True),
        (rclone.copy, False),
        (rclone.copyto, True),
        (rclone.copyto, False),
        (rclone.sync, True),
        (rclone.sync, False),
        (rclone.move, True),
        (rclone.move, False),
        (rclone.moveto, True),
        (rclone.moveto, False),
    ],
)
def test_progress_listener(tmp_remote_folder, tmp_local_folder, show_progress, method):
    # check if the listener is successfully provided with updates
    # file size should be large enough to receive progress updates
    tmp_file_1 = create_tmp_local_file(tmp_local_folder, 10.25, file_name="file_1")
    tmp_file_2 = create_tmp_local_file(tmp_local_folder, 15.776, file_name="file_2")

    recorder = Recorder()

    # upload: copy local to remote and record all updates
    method(
        tmp_local_folder,
        tmp_remote_folder,
        listener=recorder.update,
        show_progress=show_progress,
    )

    # check that all fields are there
    unique_fields = set([key for update in recorder.history for key in update])
    expected_fields = {
        "total",
        "sent",
        "progress",
        "rclone_output",
        "transfer_speed",
        "tasks",
    }
    assert expected_fields.issubset(unique_fields)

    # check summary progress
    assert len(recorder.history) > 0
    assert recorder.get_summary_stats("progress")[0] == pytest.approx(0, abs=0.1)
    assert recorder.get_summary_stats("progress")[-1] == pytest.approx(1)

    # check file_1 progress
    file_1_progress = recorder.get_task_stats("progress", tmp_file_1.name)
    assert len(file_1_progress) > 0
    assert file_1_progress[0] == pytest.approx(0, abs=0.1)
    assert file_1_progress[-1] == pytest.approx(1)

    # check file_2 progress
    file_2_progress = recorder.get_task_stats("progress", tmp_file_2.name)
    assert len(file_2_progress) > 0
    assert file_2_progress[0] == pytest.approx(0, abs=0.1)
    assert file_2_progress[-1] == pytest.approx(1)


def test_move(default_test_setup, tmp_remote_folder, tmp_local_folder):
    tmp_local_file = create_tmp_local_file(
        tmp_local_folder, default_test_setup.tmp_local_file_size_mb
    )

    # upload: move to remote
    assert tmp_local_file.is_file()
    rclone.move(tmp_local_file, tmp_remote_folder)
    assert rclone.ls(tmp_remote_folder)[0]["Path"] == tmp_local_file.name
    assert not tmp_local_file.is_file()

    # download: move to local
    rclone.move(tmp_remote_folder, tmp_local_file.parent)
    assert len(rclone.ls(tmp_remote_folder)) == 0
    assert tmp_local_file.is_file()
