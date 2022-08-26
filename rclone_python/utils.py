import subprocess
from typing import List


def args2string(args: List[str]) -> str:
    out = ""

    for item in args:
        # separate flags/ named arguments by a space
        out += f' {item}'

    return out


def run_cmd(command: str, args: List[str] = (), shell=True, encoding='utf-8') -> subprocess.CompletedProcess:
    # add optional arguments and flags to the command
    args_str = args2string(args)
    command = f'{command} {args_str}'

    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell, encoding=encoding)
