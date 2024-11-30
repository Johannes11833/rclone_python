import shutil
from typing import Dict

from rclone_python import rclone


def __get_item(output: Dict, path: str):
    return next(filter(lambda item: item["Path"] == path, output), None)


def __validate_output(output: dict):
    for item in output:
        assert set(["IsDir", "Size", "Path"]).issubset(item.keys())
        assert isinstance(item["IsDir"], bool)
        assert isinstance(item["Size"], int)
        assert isinstance(item["Path"], str)


def test_ls(default_test_setup, tmp_remote_folder, tmp_local_folder):
    file_paths = [
        "file_1",
        "folder 1/file 2",
        "folder 2/file 3",
        "folder 2/file 4",
        "folder 2/subfolder/file 5",
    ]

    file_depths = {
        1: ["file_1"],
        2: [
            "file_1",
            "folder 1/file 2",
            "folder 2/file 3",
            "folder 2/file 4",
        ],
        3: [
            "file_1",
            "folder 1/file 2",
            "folder 2/file 3",
            "folder 2/file 4",
            "folder 2/subfolder/file 5",
        ],
    }

    folder_depths = {
        1: ["folder 1", "folder 2"],
        2: ["folder 1", "folder 2", "folder 2/subfolder"],
        3: ["folder 1", "folder 2", "folder 2/subfolder"],
    }

    # create local file structure and upload
    for f in file_paths:
        path = tmp_local_folder / f
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(default_test_setup.local_test_txt_file, path)
    rclone.copy(tmp_local_folder, tmp_remote_folder, show_progress=False)

    # depth 1
    output = rclone.ls(tmp_remote_folder)
    __validate_output(output)
    assert len(output) == 3
    for file_name in file_depths[1]:
        assert __get_item(output, file_name)["IsDir"] is False
    for folder_name in folder_depths[1]:
        assert __get_item(output, folder_name)["IsDir"] is True

    # depth 2
    output = rclone.ls(tmp_remote_folder, max_depth=2)
    print(output)
    assert len(output) == 7
    __validate_output(output)
    for file_name in file_depths[2]:
        assert __get_item(output, file_name)["IsDir"] is False
    for folder_name in folder_depths[2]:
        assert __get_item(output, folder_name)["IsDir"] is True

    # depth 3
    output = rclone.ls(tmp_remote_folder, max_depth=3)
    print(output)
    assert len(output) == 8
    __validate_output(output)
    for file_name in file_depths[3]:
        assert __get_item(output, file_name)["IsDir"] is False
    for folder_name in folder_depths[3]:
        assert __get_item(output, folder_name)["IsDir"] is True
