import re
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from rich.progress import Progress, TaskID, Task
from pathlib import Path

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    DownloadColumn,
)

# ---------------------------------------------------------------------------- #
#                               General Functions                              #
# ---------------------------------------------------------------------------- #


def args2string(args: List[str]) -> str:
    out = ""

    for item in args:
        # separate flags/ named arguments by a space
        out += f" {item}"

    return out


def run_cmd(
    command: str, args: List[str] = (), shell=True, encoding="utf-8"
) -> subprocess.CompletedProcess:
    # add optional arguments and flags to the command
    args_str = args2string(args)
    command = f"{command} {args_str}"

    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        encoding=encoding,
    )


def shorten_filepath(in_path: str, max_length: int) -> str:
    if len(in_path) > max_length:
        if ":" in in_path:
            in_path = (
                in_path[in_path.index(":") + 1 :]
                if in_path.index(":") + 1 < len(in_path)
                else in_path[0 : in_path.index(":")]
            )
        return Path(in_path).name
    else:
        return in_path


def convert2bits(value: float, unit: str) -> float:
    """Returns the corresponding bit value to a value with a certain binary prefix (based on powers of 2) like KiB or MiB.

    Args:
        value (float): Bit value using a certain binary prefix like KiB or MiB.
        unit (str): The binary prefix.

    Returns:
        float: The corresponding bit value.
    """
    exp = {
        "B": 0,
        "KiB": 1,
        "MiB": 2,
        "GiB": 3,
        "TiB": 4,
        "PiB": 5,
        "EiB": 6,
        "ZiB": 7,
        "YiB": 8,
    }

    return value * 1024 ** exp[unit]


# ---------------------------------------------------------------------------- #
#                          Progressbar related functions                       #
# ---------------------------------------------------------------------------- #


def rclone_progress(
    command: str,
    pbar_title: str,
    stderr=subprocess.PIPE,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    debug=False,
    pbar: Optional[Progress] = None,
) -> subprocess.Popen:
    buffer = ""
    total_progress_id = None
    subprocesses = {}

    if show_progress:
        if pbar is None:
            pbar = create_progress_bar()
        pbar.start()
        total_progress_id = pbar.add_task(pbar_title, total=None)

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=stderr, shell=True
    )
    for line in iter(process.stdout.readline, b""):
        var = line.decode()

        valid, update_dict = extract_rclone_progress(buffer)

        if valid:
            if show_progress:
                update_tasks(pbar, total_progress_id, update_dict, subprocesses)

            # call the listener
            if listener:
                listener(update_dict)

            if debug:
                pbar.log(buffer)

            # reset the buffer
            buffer = ""
        else:
            # buffer until we
            buffer += var

    if show_progress:
        complete_task(total_progress_id, pbar)
        for _, task_id in subprocesses.items():
            # hide all subprocesses
            pbar.update(task_id=task_id, visible=False)
        pbar.stop()

    return process


def extract_rclone_progress(buffer: str) -> Tuple[bool, Union[Dict[str, Any], None]]:
    # matcher that checks if the progress update block is completely buffered yet (defines start and stop)
    # it gets the sent bits, total bits, progress, transfer-speed and eta
    reg_transferred = re.findall(
        r"Transferred:\s+(\d+.\d+ \w+) \/ (\d+.\d+ \w+), (\d{1,3})%, (\d+.\d+ \w+\/\w+), ETA (\S+)",
        buffer,
    )

    if reg_transferred:  # transferred block is completely buffered
        # get the progress of the individual files
        # matcher gets the currently transferring files and their individual progress
        # returns list of tuples: (name, progress, file_size, unit)
        prog_transferring = []
        prog_regex = re.findall(
            r"\* +(.+):[ ]+(\d{1,3})% \/(\d+.\d+)([a-zA-Z]+),", buffer
        )
        for item in prog_regex:
            prog_transferring.append(
                (
                    item[0],
                    int(item[1]),
                    float(item[2]),
                    # the suffix B of the unit is missing for subprocesses
                    item[3] + "B",
                )
            )

        out = {"prog_transferring": prog_transferring}
        sent_bits, total_bits, progress, transfer_speed_str, eta = reg_transferred[0]
        out["progress"] = float(progress.strip())
        out["total_bits"] = float(re.findall(r"\d+.\d+", total_bits)[0])
        out["sent_bits"] = float(re.findall(r"\d+.\d+", sent_bits)[0])
        out["unit_sent"] = re.findall(r"[a-zA-Z]+", sent_bits)[0]
        out["unit_total"] = re.findall(r"[a-zA-Z]+", total_bits)[0]
        out["transfer_speed"] = float(re.findall(r"\d+.\d+", transfer_speed_str)[0])
        out["transfer_speed_unit"] = re.findall(
            r"[a-zA-Z]+/[a-zA-Z]+", transfer_speed_str
        )[0]
        out["eta"] = eta

        return True, out

    else:
        return False, None


def create_progress_bar() -> Progress:
    pbar = Progress(
        TextColumn("[progress.description]{task.description}"),
        SpinnerColumn(),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(binary_units=True),
        TimeRemainingColumn(),
    )

    return pbar


def get_task(id: TaskID, progress: Progress) -> Task:
    """Returns the task with the specified TaskID.

    Args:
        id (TaskID): The id of the task.
        progress (Progress): The rich progress.

    Returns:
        Task: The task with the specified TaskID.
    """
    for task in progress.tasks:
        if task.id == id:
            return task

    return None


def complete_task(id: TaskID, progress: Progress):
    """Manually sets the progress of the task with the specified TaskID to 100%.

    Args:
        id (TaskID): The task that should be completed.
        progress (Progress): The rich progress.
    """

    task = get_task(id, progress)

    if task.total is None:
        # reset columns to hide file size (we don't know it)
        progress.columns = Progress.get_default_columns()

    total = task.total or 1
    progress.update(id, completed=total, total=total)


def update_tasks(
    pbar: Progress,
    total_progress: TaskID,
    update_dict: Dict[str, Any],
    subprocesses: Dict[str, TaskID],
):
    """Updates the total progress as well as all subprocesses (the individual files that are currently uploading).

    Args:
        pbar (Progress): The rich progress.
        total_progress (TaskID): The TaskID of the total progress.
        update_dict (Dict): The update dict generated by the _extract_rclone_progress function.
        subprocesses (Dict): A dictionary containing all the  subprocesses.
    """

    pbar.update(
        total_progress,
        completed=convert2bits(update_dict["sent_bits"], update_dict["unit_sent"]),
        total=convert2bits(update_dict["total_bits"], update_dict["unit_total"]),
    )

    sp_names = set()
    for sp_file_name, sp_progress, sp_size, sp_unit in update_dict["prog_transferring"]:
        task_id = None
        sp_names.add(sp_file_name)

        if sp_file_name not in subprocesses:
            task_id = pbar.add_task(" ", visible=False)
            subprocesses[sp_file_name] = task_id
        else:
            task_id = subprocesses[sp_file_name]

        pbar.update(
            task_id,
            # set the description every time to reset the '├'
            description=f" ├─{sp_file_name}",
            completed=convert2bits(sp_size, sp_unit) * sp_progress / 100.0,
            total=convert2bits(sp_size, sp_unit),
            # hide subprocesses if we only upload a single file
            visible=len(subprocesses) > 1,
        )

    # make all processes invisible that are no longer provided by rclone (bc. their upload completed)
    missing = list(sorted(subprocesses.keys() - sp_names))
    for missing_sp_id in missing:
        pbar.update(subprocesses[missing_sp_id], visible=False)

    # change symbol for the last visible process
    for task in reversed(pbar.tasks):
        if task.visible:
            pbar.update(task.id, description=task.description.replace("├", "└"))
            break
