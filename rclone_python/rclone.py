import json
import re
import logging
from functools import wraps
from shutil import which
from typing import Optional, Union, List, Dict, Callable

from rclone_python import utils
from rclone_python.hash_types import HashTypes
from rclone_python.remote_types import RemoteTypes

# debug flag enables/disables raw output of rclone progresses in the terminal
DEBUG = False


def __check_installed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_installed():
            raise Exception(
                "rclone is not installed on this system. Please install it here: https://rclone.org/"
            )

        return func(*args, **kwargs)

    return wrapper


def is_installed() -> bool:
    """
    :return: True if rclone is correctly installed on the system.
    """
    return which("rclone") is not None


@__check_installed
def about(remote_name: str):
    """
    Executes the rclone about command and returns the retrieved json as a dictionary.
    :param remote_name: The name of the remote to examine.
    :return: Dictionary with remote properties.
    """
    if not remote_name.endswith(":"):
        # if the remote name missed the colon manually add it.
        remote_name += ":"

    process = utils.run_cmd(f"rclone about {remote_name} --json")

    if process.returncode == 0:
        return json.loads(process.stdout)
    else:
        raise Exception(
            f"An error occurred while executing the about command: {process.stderr}"
        )


@__check_installed
def check_remote_existing(remote_name: str) -> bool:
    """
    Returns True, if the specified rclone remote is already configured.
    :param remote_name: The name of the remote to check.
    :return: True if the remote exists, False otherwise.
    """
    # get the available remotes
    remotes = get_remotes()

    # add the trailing ':' if it is missing
    if not remote_name.endswith(":"):
        remote_name = f"{remote_name}:"

    return remote_name in remotes


@__check_installed
def create_remote(
    remote_name: str,
    remote_type: Union[str, RemoteTypes],
    client_id: Union[str, None] = None,
    client_secret: Union[str, None] = None,
    **kwargs,
):
    """Creates a new remote with name, type and options.

    Args:
        remote_name (str): Name of the new remote.
        remote_type (Union[str, RemoteTypes]): The type of the remote (e.g. "onedrive", RemoteTypes.dropbox, ...)
        client_id (str, optional): OAuth Client Id.
        client_secret (str, optional): OAuth Client Secret.
        **kwargs: Additional key value pairs that can be used with the "rclone config create" command.
    """
    if isinstance(remote_type, RemoteTypes):
        remote_type = remote_type.value

    if not check_remote_existing(remote_name):
        # set up the selected cloud
        command = f'rclone config create "{remote_name}" "{remote_type}"'

        if client_id and client_secret:
            logging.info("Using the provided client id and client secret.")

            kwargs["client_id"] = client_id
            kwargs["client_secret"] = client_secret
        else:
            logging.warning(
                "The drive client id and the client secret have not been set. Using defaults."
            )

        # add the options as key-value pairs
        for key, value in kwargs.items():
            command += f' {key}="{value}"'

        # run the setup command
        process = utils.run_cmd(command)

        if process.returncode != 0:
            raise Exception(process.stderr)
    else:
        raise Exception(
            f"A rclone remote with the name '{remote_name}' already exists!"
        )


def mkdir(
    path: str,
    args=None,
):
    """
    Make the path if it doesn't already exist.
    :param path: The path to the file to run the mkdir command on.
    :param args: List of additional arguments/ flags.
    """
    if args is None:
        args = []

    process = utils.run_cmd(f"rclone mkdir {path}", args=args)

    if process.returncode == 0:
        return process.stdout
    else:
        raise Exception(
            f"An error occurred while executing the mkdir command: {process.stderr}"
        )


def cat(
    path: str,
    count: Optional[int] = None,
    head: Optional[int] = None,
    offset: Optional[int] = None,
    tail: Optional[int] = None,
    args=None,
) -> str:
    """
    Outputs a single file.
    :param path: The path to the file to run the cat command on.
    :param count: Only print N characters.
    :param head: Only print the first N characters.
    :param offset: Start printing at offset N (or from end when offset is negative)
    :param tail: Only print the last N characters.
    :param args: List of additional arguments/ flags.
    """
    if args is None:
        args = []

    if count is not None:
        args.append(f"--count {count}")
    if head is not None:
        args.append(f"--head {head}")
    if offset is not None:
        args.append(f"--offset {offset}")
    if tail is not None:
        args.append(f"--tail {tail}")

    process = utils.run_cmd(f"rclone cat {path}", args=args)

    if process.returncode == 0:
        return process.stdout
    else:
        raise Exception(
            f"An error occurred while executing the cat command: {process.stderr}"
        )


def copy(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """
    Copies a file or a directory from a src path to a destination path.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
    :param pbar: Optional progress bar for integration with custom TUI
    """
    if args is None:
        args = []

    _rclone_transfer_operation(
        in_path,
        out_path,
        ignore_existing=ignore_existing,
        command="rclone copy",
        command_descr="Copying",
        show_progress=show_progress,
        listener=listener,
        args=args,
        pbar=pbar,
    )


def copyto(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """
    Copies a file or a directory from a src path to a destination path and is typically used when renaming a file is necessary.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
    :param pbar: Optional progress bar for integration with custom TUI
    """
    if args is None:
        args = []

    _rclone_transfer_operation(
        in_path,
        out_path,
        ignore_existing=ignore_existing,
        command="rclone copyto",
        command_descr="Copying",
        show_progress=show_progress,
        listener=listener,
        args=args,
        pbar=pbar,
    )


def move(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """
    Moves a file or a directory from a src path to a destination path.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
    :param pbar: Optional progress bar for integration with custom TUI
    """
    if args is None:
        args = []

    _rclone_transfer_operation(
        in_path,
        out_path,
        ignore_existing=ignore_existing,
        command="rclone move",
        command_descr="Moving",
        show_progress=show_progress,
        listener=listener,
        args=args,
        pbar=pbar,
    )


def moveto(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """
    Moves a file or a directory from a src path to a destination path and is typically used when renaming is necessary.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
    :param pbar: Optional progress bar for integration with custom TUI
    """
    if args is None:
        args = []

    _rclone_transfer_operation(
        in_path,
        out_path,
        ignore_existing=ignore_existing,
        command="rclone moveto",
        command_descr="Moving",
        show_progress=show_progress,
        listener=listener,
        args=args,
        pbar=pbar,
    )


def sync(
    src_path: str,
    dest_path: str,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """
    Sync the source to the destination, changing the destination only. Doesn't transfer files that are identical on source and destination, testing by size and modification time or MD5SUM.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
    :param pbar: Optional progress bar for integration with custom TUI
    """
    if args is None:
        args = []

    _rclone_transfer_operation(
        src_path,
        dest_path,
        command="rclone sync",
        command_descr="Syncing",
        show_progress=show_progress,
        listener=listener,
        args=args,
        pbar=pbar,
    )


@__check_installed
def get_remotes() -> List[str]:
    """
    :return: A list of all available remotes.
    """
    command = "rclone listremotes"
    remotes = utils.run_cmd(command).stdout.split()
    if remotes is None:
        remotes = []

    return remotes


@__check_installed
def purge(path: str, args=None):
    """
    Purges the specified folder. This means that unlike with delete, also all the folders are removed.
    :param args: List of additional arguments/ flags.
    :param path: The path of the folder that should be purged.
    """
    if args is None:
        args = []

    command = f'rclone purge "{path}"'
    process = utils.run_cmd(command, args)
    if process.returncode == 0:
        logging.info(f"Successfully purged {path}")
    else:
        raise Exception(
            f'Purging path "{path}" failed with error message:\n{process.stderr}'
        )


@__check_installed
def delete(path: str, args=None):
    """
    Deletes a file or a folder. When deleting a folder, all the files in it and it's subdirectories are removed,
    but not the folder structure itself.
    :param args: List of additional arguments/ flags.
    :param path: The path of the folder that should be deleted.
    """
    if args is None:
        args = []

    command = f'rclone delete "{path}"'
    process = utils.run_cmd(command, args)

    if process.returncode == 0:
        logging.info(f"Successfully deleted {path}")
    else:
        raise Exception(
            f'Deleting path "{path}" failed with error message:\n{process.stderr}'
        )


@__check_installed
def link(
    path: str,
    expire: Union[str, None] = None,
    unlink=False,
    args=None,
) -> str:
    """
    Generates a public link to a file/directory.
    :param path: The path to the file/directory that a public link should be created, retrieved or removed for.
    :param expire: The amount of time that the link will be valid (not supported by all backends).
    :param unlink: If true, remove existing public links to the file or directory (not supported by all backends).
    :param args: List of additional arguments/ flags.
    :return: The link to the given file or directory.
    """
    if args is None:
        args = []

    command = f'rclone link "{path}"'

    # add optional parameters
    if expire is not None:
        args.append(f"--expire {expire}")
    if unlink:
        args.append(f"--unlink")

    process = utils.run_cmd(command, args)

    if process.returncode != 0:
        raise Exception(process.stderr)
    else:
        return process.stdout


@__check_installed
def ls(
    path: str,
    max_depth: Union[int, None] = None,
    dirs_only=False,
    files_only=False,
    args=None,
) -> List[Dict[str, Union[int, str]]]:
    """
    Lists the files in a directory.
    :param path: The path to the folder that should be examined.
    :param max_depth: The maximum depth for file search. If max_depth=1 only the files in the selected folder but not
    in its subdirectories will be included.
    :param files_only: If true only files will be returned.
    :param dirs_only: If true, only dirs will be returned.
    :param args: List of additional arguments/ flags.
    :return: List of dicts containing file properties.
    """
    if args is None:
        args = []

    command = f'rclone lsjson "{path}"'

    # add optional parameters
    if max_depth is not None:
        args.append(f"--max-depth {max_depth}")
    if dirs_only:
        args.append(f"--dirs-only")
    if files_only:
        args.append("--files-only")

    process = utils.run_cmd(command, args)

    if process.returncode == 0:
        return json.loads(process.stdout)
    else:
        raise Exception(f"ls operation on {path} failed with:\n{process.stderr}")


def tree(
    path: str,
    args: List[str] = None,
) -> str:
    """Returns the contents of the remote path in a tree like fashion.

    Args:
        path (str): The path from which the tree should be generated
        args (List[str], optional): Optional additional list of flags.

    Returns:
        str: String containing the file tree.
    """
    if args is None:
        args = []

    process = utils.run_cmd(f'rclone tree "{path}"', args)

    if process.returncode != 0:
        raise Exception(process.stderr)
    else:
        return process.stdout


@__check_installed
def hash(
    hash: Union[str, HashTypes],
    path: str,
    download=False,
    checkfile: Optional[str] = None,
    output_file: Optional[str] = None,
    args: List[str] = None,
) -> Union[None, str, bool, Dict[str, str], Dict[str, bool]]:
    """Produces a hashsum file for all the objects in the path.

    Args:
        hash (Union[str, HashTypes]): The hash algorithm to use, e.g. sha1. Depends on the backend used.
        path (str): The path to the file/ folder to generate hashes for.
        download (bool, optional): Download the file and hash it locally. Useful when the backend does not support the selected hash algorithm.
        checkfile (Optional[str], optional):  Validate hashes against a given SUM file instead of printing them.
        output_file (Optional[str], optional): Output hashsums to a file rather than the terminal (same format as the checkfile).
        args (List[str], optional): Optional additional list of flags.

    Raises:
        Exception: Raised when the rclone command does not succeed.

    Returns:
        Union[None, str, bool, Dict[str, str], Dict[str, bool]]: 3 different modes apply based on the inputs:
            1)  Nothing is returned when output file is set.
            2)  When checkfile is set, a dictionary is returned with file names as keys.
                The values are either True or False, depending on wether the file is valid ot not.
                In the special case of only a single file, True or False is directly returned.
            3)  If neither checkfile nor output_file is set, a dictionary is returned with file names as keys.
                The values are the individual hash sums.
                In the special case of only a single file, the hashsum is directly returned.
    """

    if isinstance(hash, HashTypes):
        hash = hash.value

    if args is None:
        args = []

    if download:
        args.append("--download")

    if checkfile is not None:
        args.append(f'--checkfile "{checkfile}"')

    if output_file is not None:
        args.append(f'--output-file "{output_file}"')

    process: str = utils.run_cmd(f'rclone hashsum "{hash}" "{path}"', args)

    lines = process.stdout.splitlines()

    exception = False

    if process.returncode != 0:
        if checkfile is None:
            exception = True
        else:
            # validate that the checkfile command succeeded, by checking if the output has the expected form
            for l in lines:
                if not (l.startswith("= ") or l.startswith("* ")):
                    exception = True
                    break

    if exception:
        raise Exception(
            f"hashsum operation on {path} with hash='{hash}' failed with:\n{process.stderr}"
        )

    if output_file is None:
        # each line contains the hashsum first, followed by the name of the file
        hashsums = {}

        for l in lines:
            if len(l) > 0:
                value, key = l.split("  ", maxsplit=1)

                if checkfile is None:
                    hashsums[key] = value
                else:
                    # in checkfile mode, value is '=' for valid and '*' for invalid files
                    hashsums[key] = value == "="

        # for only a single file return the value instead of the dict
        if len(hashsums) == 1:
            return next(iter(hashsums.values()))

        return hashsums


@__check_installed
def version(
    check=False,
    args: List[str] = None,
) -> Union[str, List[str]]:
    """Get the rclone version number.

    Args:
        check (bool, optional): Whether to do an online check to compare your version with the latest release and the latest beta. Defaults to False.
        args (List[str], optional): Optional additional list of flags. Defaults to None.

    Returns:
        Union[str, Set[str, str, str]]: When check is False, returns string of current version. When check is True returns installed version, lastest version and latest beta version.
    """
    if args is None:
        args = []

    if check:
        args.append("--check")

    process = utils.run_cmd("rclone version", args)

    if process.returncode != 0:
        raise Exception(process.stderr)

    stdout = process.stdout

    if not check:
        return stdout.split("\n")[0].replace("rclone ", "")
    else:
        yours = re.findall(r"yours:\s+([\d.]+)", stdout)[0]
        latest = re.findall(r"latest:\s+([\d.]+)", stdout)[0]
        # beta version might include dashes and word characters e.g. '1.64.0-beta.7161.9169b2b5a'
        beta = re.findall(r"beta:\s+([.\w-]+)", stdout)[0]
        return yours, latest, beta


class RcloneException(ChildProcessError):
    def __init__(self, description, error_msg):
        self.description = description
        self.error_msg = error_msg
        super().__init__(f"{description}. Error message: \n{error_msg}")


@__check_installed
def _rclone_transfer_operation(
    in_path: str,
    out_path: str,
    command: str,
    command_descr: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
    pbar=None,
):
    """Executes the rclone transfer operation (e.g. copyto, move, ...) and displays the progress of every individual file.

    Args:
        in_path (str): The source path to use. Specify the remote with 'remote_name:path_on_remote'
        out_path (str): The destination path to use. Specify the remote with 'remote_name:path_on_remote'
        command (str): The rclone command to execute (e.g. rclone copyto)
        command_descr (str): The description to this command that should be displayed.
        ignore_existing (bool, optional): If True, all existing files are ignored and not overwritten.
        show_progress (bool, optional): If true, show a progressbar.
        listener (Callable[[Dict], None], optional): An event-listener that is called with every update of rclone.
        args: List of additional arguments/ flags.
        pbar: a rich.Progress created under a parent live session
    """
    if args is None:
        args = []

    prog_title = f"{command_descr} [bold magenta]{utils.shorten_filepath(in_path, 20)}[/bold magenta] to [bold magenta]{utils.shorten_filepath(out_path, 20)}"

    # add global rclone flags
    if ignore_existing:
        command += " --ignore-existing"

    # in path
    command += f' "{in_path}"'
    # out path
    command += f' "{out_path}"'

    command += " --stats 0.1s --stats-unit bytes --use-json-log -v"

    # optional named arguments/flags
    command += utils.args2string(args)

    # execute the upload command
    process = utils.rclone_progress(
        command,
        prog_title,
        listener=listener,
        show_progress=show_progress,
        debug=DEBUG,
        pbar=pbar,
    )

    if process.wait() == 0:
        logging.info("Cloud upload completed.")
    else:
        _, err = process.communicate()
        raise RcloneException(
            description=f"{command_descr} from {in_path} to {out_path} failed",
            error_msg=err.decode("utf-8"),
        )
