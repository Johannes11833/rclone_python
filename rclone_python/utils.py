import json
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from rich.progress import Progress, TaskID, Task
from pathlib import Path
from rclone_python.logs import logger

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    DownloadColumn,
)


class RcloneException(ChildProcessError):
    def __init__(self, description: str, error_msg: str):
        self.description = description
        self.error_msg = error_msg
        super().__init__(f"{description}. Error message: \n{error_msg}")


# ---------------------------------------------------------------------------- #
#                               General Functions                              #
# ---------------------------------------------------------------------------- #


class Config:
    """Config set up as singleton"""

    _instance = None
    _initialized = False
    config_path = None

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the Config class if it doesn't exist yet."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Union[str, Path] = None):
        if not self._initialized:
            self.config_path = config_path
            self.__class__._initialized = True


def args2string(args: List[str]) -> str:
    # separate flags/ named arguments by a space
    if args:
        return " " + " ".join(args)

    return ""


def run_rclone_cmd(
    command: str,
    args: List[str] = (),
    shell=True,
    encoding="utf-8",
    raise_errors: bool = True,
) -> Union[Tuple[str, str], Tuple[int, str, str]]:
    # Set the config path if defined by the user,
    # otherwise the default rclone config path is used:
    config = Config()
    if config.config_path is not None:
        base_command = f"rclone --config={config.config_path}"
    else:
        base_command = "rclone"

    # add optional arguments and flags to the command
    args_str = args2string(args)
    full_command = f"{base_command} {command} {args_str}"

    logger.debug(f"Running command: {full_command}")

    process = subprocess.run(
        full_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        encoding=encoding,
    )

    if process.returncode != 0 and raise_errors:
        msg = f'Rclone "{command}" command failed'
        if len(args) > 0:
            msg += 'with args "{args_str}"'

        raise RcloneException(msg, process.stderr)

    if raise_errors is True:
        return process.stdout, process.stderr
    else:
        return process.returncode, process.stdout, process.stderr


def shorten_filepath(in_path: Union[str, Path], max_length: int) -> str:
    in_path = str(in_path)

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


# ---------------------------------------------------------------------------- #
#                          Progressbar related functions                       #
# ---------------------------------------------------------------------------- #


def rclone_progress(
    command: str,
    pbar_title: str,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    pbar: Optional[Progress] = None,
) -> Tuple[subprocess.Popen, List[str]]:
    total_progress_id = None
    subprocesses = {}
    errors = []

    # Set the config path if defined by the user,
    # otherwise the default rclone config path is used:
    config = Config()
    if config.config_path is not None:
        command += f' --config="{config.config_path}"'

    if show_progress:
        if pbar is None:
            pbar = create_progress_bar()
        pbar.start()
        total_progress_id = pbar.add_task(pbar_title, total=None)

    process = subprocess.Popen(
        args=command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )

    # rclone prints stats to stderr. each line is one update
    for line in iter(process.stderr.readline, b""):
        line = line.decode()

        valid, update_dict = extract_rclone_progress(line)

        if valid:
            if show_progress:
                update_tasks(pbar, total_progress_id, update_dict, subprocesses)

            # call the listener
            if listener:
                listener(update_dict)

            logger.debug(line)

        else:
            if update_dict is not None:
                obj = update_dict.get("object", "")
                msg = update_dict.get("msg", "<Error message missing>")
                errors.append((obj + ": " if obj else "") + msg)
                logger.warning(f"Rclone omitted an error: {update_dict}")

    if show_progress:
        if process.wait() == 0:
            complete_task(total_progress_id, pbar)
            for _, task_id in subprocesses.items():
                # hide all subprocesses
                pbar.update(task_id=task_id, visible=False)
        pbar.stop()

    return process, errors


def extract_rclone_progress(line: str) -> Tuple[bool, Union[Dict[str, Any], None]]:
    """Extracts and returns the progress updates from the rclone transfer operation.
    The returned Dictionary includes the original rclone stats output inside of "rclone_output".
    All file sizes and speeds are give in bytes.

    Args:
        line (str): One output line of the rclone transfer operation with the --use-json-log flag enabled.

    Returns:
        Tuple[bool, Union[Dict[str, Any], None]]: The retrieved update Dictionary or error message.
    """
    stats = None

    try:
        log_item: Dict = json.loads(line)
        level = log_item.get("level", None)
        if level != "info":
            if level in ("error", "critical"):
                # return error message
                return False, log_item
        else:
            # stats updates use the "info" level
            stats = log_item.get("stats", None)
    except ValueError:
        stats = None

    if stats is not None and stats.get("totalBytes", 0) > 0:
        # get the progress of the individual files
        tasks = []
        for t in stats.get("transferring", []):
            total = t.get("size", 0)
            sent = t.get("bytes", 0)
            tasks.append(
                {
                    # sometime not all the task information is available right from the start
                    "name": t.get("name", "N/A"),
                    "total": total,
                    "sent": sent,
                    "progress": sent / total if total != 0 else 0,
                    "transfer_speed": t.get("speed", 0),
                }
            )

        out = {
            "tasks": tasks,
            "total": stats["totalBytes"],
            "sent": stats["bytes"],
            "progress": (
                stats["bytes"] / stats["totalBytes"] if stats["totalBytes"] != 0 else 0
            ),
            "transfer_speed": stats["speed"],
            "rclone_output": stats,
        }

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
        completed=update_dict["sent"],
        total=update_dict["total"],
    )

    task_names = set()
    for task in update_dict["tasks"]:
        task_id = None

        task_name = task["name"]
        task_size = task["total"]
        task_sent = task["sent"]

        task_names.add(task_name)

        if task_name not in subprocesses:
            task_id = pbar.add_task(" ", visible=False)
            subprocesses[task_name] = task_id
        else:
            task_id = subprocesses[task_name]

        pbar.update(
            task_id,
            # set the description every time to reset the '├'
            description=f" ├─{task_name}",
            completed=task_sent,
            total=task_size,
            # hide subprocesses if we only upload a single file
            visible=len(subprocesses) > 1,
        )

    # make all processes invisible that are no longer provided by rclone (bc. their upload completed)
    missing = list(sorted(subprocesses.keys() - task_names))
    for missing_task_id in missing:
        pbar.update(subprocesses[missing_task_id], visible=False)

    # change symbol for the last visible process
    for task in reversed(pbar.tasks):
        if task.visible:
            pbar.update(task.id, description=task.description.replace("├", "└"))
            break
