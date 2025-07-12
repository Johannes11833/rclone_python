from pathlib import Path
import subprocess
from typing import Callable, List, Union
import pytest
from rclone_python import rclone
from unittest.mock import patch

from rclone_python.utils import RcloneException


class Recorder:
    # Records all updates provided to the update function.
    def __init__(self):
        self.history = []

    def update(self, update: dict):
        self.history.append(update)

    def get_summary_stats(self, stat_name: str) -> List[any]:
        # returns the stats related to the overall transfer task.
        return [update[stat_name] for update in self.history]

    def get_subtask_stats(self, stat_name: str, task_name: str) -> List[any]:
        # returns stats related to a specific subtask.
        return [
            task_update[stat_name]
            for update in self.history
            for task_update in update["tasks"]
            if task_update["name"] == task_name
        ]


def create_local_file(
    path: Union[str, Path], size_mb: float, file_name: str = "tmp_file.file"
) -> Path:
    # Create local file of specific size.
    local_file_path = Path(path) / file_name
    local_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_file_path, "wb") as out:
        out.truncate(int(size_mb * 1024 * 1024))

    return local_file_path


@pytest.mark.parametrize(
    "wrapper_command,rclone_command",
    [
        (rclone.copy, "rclone copy"),
        (rclone.copyto, "rclone copyto"),
        (rclone.sync, "rclone sync"),
        (rclone.move, "rclone move"),
        (rclone.moveto, "rclone moveto"),
    ],
)
def test_rclone_command_called(wrapper_command: Callable, rclone_command: str):
    # this test checks that the correct underlying rclone command is called
    # when calling one of the 5 transfer-operation commands of the wrapper.

    with patch.object(
        # mock Popen inside the utils module to access the keyword arguments.
        # the rclone command is not executed.
        rclone.utils.subprocess,
        "Popen",
        return_value=subprocess.Popen(
            "rclone help", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        ),
    ) as mock:
        wrapper_command("nothing/not_a.file", "fake_remote:unicorn/folder")

    assert mock.call_count == 1
    _, kwargs = mock.call_args_list[0]
    assert kwargs["args"].startswith(rclone_command)


@pytest.mark.parametrize(
    "command",
    [
        rclone.copy,
        rclone.copyto,
    ],
)
def test_copy(default_test_setup, tmp_remote_folder, tmp_local_folder, command):
    tmp_local_file = create_local_file(
        tmp_local_folder, default_test_setup.tmp_local_file_size_mb
    )

    # upload: copy local to remote
    command(tmp_local_folder, tmp_remote_folder)
    assert rclone.ls(tmp_remote_folder)[0]["Path"] == tmp_local_file.name

    # download: copy remote to local
    download_path = tmp_local_folder / "download"
    command(
        tmp_remote_folder,
        download_path,
    )
    assert (download_path / tmp_local_file.name).is_file()

    # upload with errors (no such directory)
    with pytest.raises(RcloneException, match="directory not found") as e_info:
        command(str(tmp_local_folder) + "_foo", tmp_remote_folder)


def test_sync(default_test_setup, tmp_remote_folder, tmp_local_folder):
    tmp_local_file_1 = create_local_file(
        tmp_local_folder, default_test_setup.tmp_local_file_size_mb, file_name="file_1"
    )
    tmp_local_file_2 = create_local_file(
        tmp_local_folder, default_test_setup.tmp_local_file_size_mb, file_name="file_2"
    )

    # copy lorem.txt to remote
    rclone.copy(default_test_setup.local_test_txt_file, tmp_remote_folder)

    # sync local to remote --> this should remove the just uploaded test_txt_file
    rclone.sync(tmp_local_folder, tmp_remote_folder)
    paths = [file["Path"] for file in rclone.ls(tmp_remote_folder)]
    assert len(paths) == 2
    assert tmp_local_file_1.name in paths and tmp_local_file_2.name


def test_move(default_test_setup, tmp_remote_folder, tmp_local_folder):
    tmp_local_file = create_local_file(
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
    tmp_file_1 = create_local_file(tmp_local_folder, 10.25, file_name="file_1")
    tmp_file_2 = create_local_file(tmp_local_folder, 15.776, file_name="file_2")

    recorder = Recorder()

    # upload: copy local to remote and record all updates
    method(
        tmp_local_folder,
        tmp_remote_folder,
        listener=recorder.update,
        show_progress=show_progress,
        # limit the bandwidth to see progress updates
        args=["--bwlimit 10M"],
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

    THRESHOLD = 0.25

    # check summary progress
    assert len(recorder.history) > 0
    assert recorder.get_summary_stats("progress")[0] == pytest.approx(0, abs=THRESHOLD)
    assert recorder.get_summary_stats("progress")[-1] == pytest.approx(1, abs=THRESHOLD)

    # check file_1 progress
    file_1_progress = recorder.get_subtask_stats("progress", tmp_file_1.name)
    assert len(file_1_progress) > 0
    assert file_1_progress[0] == pytest.approx(0, abs=THRESHOLD)
    assert file_1_progress[-1] == pytest.approx(1, abs=THRESHOLD)

    # check file_2 progress
    file_2_progress = recorder.get_subtask_stats("progress", tmp_file_2.name)
    assert len(file_2_progress) > 0
    assert file_2_progress[0] == pytest.approx(0, abs=THRESHOLD)
    assert file_2_progress[-1] == pytest.approx(1, abs=THRESHOLD)


def test_rclone_transfer_operation_error_message(default_test_setup, tmp_local_folder):
    faulty_remote_name = default_test_setup.remote_name + "s:"

    try:
        rclone.copy(faulty_remote_name, tmp_local_folder)
        assert False
    except RcloneException as exception:
        # check that a rclone exception message is set
        assert len(exception.description) > 0
        assert len(exception.error_msg) > 0
