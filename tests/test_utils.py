import json
from typing import Dict

import pytest
from rclone_python.utils import args2string, extract_rclone_progress


@pytest.fixture()
def valid_rclone_stats_update():
    return {
        "bytes": 1,
        "totalBytes": 10e6,
        "speed": 3.1419,
        "transferring": [
            {
                "name": "hello world/file 1.1.file",
                "size": 6e6,
                "bytes": 1.1e6,
                "speed": 2.1e3,
            },
            {
                "name": "hello world/file 1.2.file",
                "size": 18e6,
                "bytes": 12.1e6,
                "speed": 1.3e3,
            },
        ],
    }


def test_args2string():
    args = []

    result = args2string(args)

    assert result == ""

    args = ["--links", "--transfers", "40"]

    result = args2string(args)

    assert result == " --links --transfers 40"


def test_extract_rclone_progress_normal_update(valid_rclone_stats_update):
    # valid input where the total file size is already known
    input = valid_rclone_stats_update

    valid, output = extract_rclone_progress(
        json.dumps({"stats": input, "level": "info"})
    )
    assert valid
    # validate task summary
    assert output["total"] == pytest.approx(input["totalBytes"])
    assert output["sent"] == pytest.approx(input["bytes"])
    assert output["progress"] == pytest.approx(input["bytes"] / input["totalBytes"])
    assert output["transfer_speed"] == pytest.approx(input["speed"])
    assert output["rclone_output"] == input

    # validate individual task updates
    # we assume that the extract_rclone_progress function keeps the order of the tasks in the input
    for index in range(len(input["transferring"])):
        task_output = output["tasks"][index]
        task_input = input["transferring"][index]
        assert task_output["name"] == task_input["name"]
        assert task_output["total"] == pytest.approx(task_input["size"])
        assert task_output["sent"] == pytest.approx(task_input["bytes"])
        assert task_output["transfer_speed"] == pytest.approx(task_input["speed"])
        assert task_output["progress"] == pytest.approx(
            task_input["bytes"] / task_input["size"]
        )


def test_extract_rclone_progress_uninitialized(valid_rclone_stats_update):
    input = valid_rclone_stats_update

    # ----------------------- total size not yet available ----------------------- #
    # case 1: totalBytes is zero
    input["totalBytes"] = 0
    valid, output = extract_rclone_progress(json.dumps({"stats": input}))
    assert not valid
    assert output is None

    # case 2: totalBytes is not present
    input.pop("totalBytes")
    valid, output = extract_rclone_progress(json.dumps({"stats": input}))
    assert not valid
    assert output is None


def test_extract_rclone_progress_invalid_input(valid_rclone_stats_update):
    # --------------------------- valid json w/o stats --------------------------- #
    valid, output = extract_rclone_progress(
        json.dumps(
            {
                "level": "info",
                "message": "hello world!",
            }
        )
    )
    assert not valid and output is None

    # ------------------------------- invalid json ------------------------------- #
    valid, output = extract_rclone_progress(
        'this is not valid json { {"hello":"world"}}'
    )
    assert not valid and output is None
