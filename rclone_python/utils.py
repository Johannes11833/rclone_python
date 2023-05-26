import subprocess
from typing import Dict, List
from rich.progress import Progress, TaskID


from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    DownloadColumn,
)
from rich.panel import Panel


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


# ---------------------------------------------------------------------------- #
#                          Progress related functions                          #
# ---------------------------------------------------------------------------- #


def create_progress_bar(pbar_title: str):
    pbar = Progress(
        TextColumn("[progress.description]{task.description}"),
        SpinnerColumn(),
        BarColumn(),
        TaskProgressColumn(),
        DownloadColumn(binary_units=True),
        TimeRemainingColumn(),
    )

    pbar.console.print(Panel(f"☁ {pbar_title}", expand=False))
    total_progress = pbar.add_task("[bold]Total Progress", total=None)
    pbar.start()

    return pbar, total_progress


def convert2bits(value: float, unit: str):
    exp = {
        "iB": 0,
        "KiB": 1,
        "MiB": 2,
        "GiB": 3,
        "TiB": 4,
    }

    return value * 1024 ** exp[unit]


def get_task(id: TaskID, progress: Progress):
    for task in progress.tasks:
        if task.id == id:
            return task

    return None


def complete_task(id: TaskID, progress: Progress):
    task = get_task(id, progress)

    if task.total is None:
        # reset columns to hide file size (we don't know it)
        progress.columns = Progress.get_default_columns()

    total = task.total or 1
    progress.update(id, completed=total, total=total)


def update_tasks(
    pbar: Progress, total_progress: TaskID, update_dict: Dict, subprocesses: Dict
):
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
            task_id = pbar.add_task(f"  {sp_file_name}", visible=False)
            subprocesses[sp_file_name] = task_id
        else:
            task_id = subprocesses[sp_file_name]

        pbar.update(
            task_id,
            completed=convert2bits(sp_size, sp_unit) * sp_progress / 100.0,
            total=convert2bits(sp_size, sp_unit),
            # hide subprocesses if we only upload a single file
            visible=len(subprocesses) > 1,
        )

    # make all processes invisible that are no longer provided by rclone (bc. their upload completed)
    missing = list(sorted(subprocesses.keys() - sp_names))
    for missing_sp_id in missing:
        pbar.update(subprocesses[missing_sp_id], visible=False)
