import json
from pathlib import Path
import re
from functools import wraps
from shutil import which
import tempfile
from typing import Optional, Tuple, Union, List, Dict, Callable

from rclone_python import utils
from rclone_python.hash_types import HashTypes
from rclone_python.remote_types import RemoteTypes
from rclone_python.logs import logger


def __check_installed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_installed():
            raise Exception(
                "rclone is not installed on this system. Please install it here: https://rclone.org/"
            )

        return func(*args, **kwargs)

    return wrapper


def set_config_file(config_file: str):
    """Change the config file used by this wrapper."""
    utils.Config(config_file)


def set_log_level(level: int):
    """Change the log level of this wrapper.

    Args:
        level (int): The log level to use.
    """
    logger.setLevel(level)


def is_installed() -> bool:
    """
    :return: True if rclone is correctly installed on the system.
    """
    return which("rclone") is not None


@__check_installed
def about(path: str) -> Dict:
    """
    Executes the rclone about command and returns the retrieved json as a dictionary.
    All sizes are in number of bytes. This command can be run with local and remote paths.
    :param remote_name: The name of the remote to examine.
    :return: Dictionary with remote properties.
    """

    stdout, _ = utils.run_rclone_cmd(f'about "{path}" --json')

    return json.loads(stdout)


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
        command = f'config create "{remote_name}" "{remote_type}"'

        if client_id and client_secret:
            logger.info("Using the provided client id and client secret.")

            kwargs["client_id"] = client_id
            kwargs["client_secret"] = client_secret
        else:
            logger.warning(
                "The drive client id and the client secret have not been set. Using defaults."
            )

        # add the options as key-value pairs
        for key, value in kwargs.items():
            command += f' {key}="{value}"'

        # run the setup command
        utils.run_rclone_cmd(command)
    else:
        raise Exception(
            f"A rclone remote with the name '{remote_name}' already exists!"
        )


@__check_installed
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

    utils.run_rclone_cmd(f'mkdir "{path}"', args=args)


@__check_installed
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

    stdout, _ = utils.run_rclone_cmd(f'cat "{path}"', args=args)
    return stdout


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
    command = "listremotes"
    stdout, _ = utils.run_rclone_cmd(command)
    remotes = stdout.split()
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

    command = f'purge "{path}"'
    utils.run_rclone_cmd(command, args)


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

    command = f'delete "{path}"'
    utils.run_rclone_cmd(command, args)


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

    command = f'link "{path}"'

    # add optional parameters
    if expire is not None:
        args.append(f"--expire {expire}")
    if unlink:
        args.append(f"--unlink")

    stdout, _ = utils.run_rclone_cmd(command, args)

    return stdout


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

    command = f'lsjson "{path}"'

    # add optional parameters
    if max_depth is not None:
        args.append(f"--max-depth {max_depth}")
    if dirs_only:
        args.append(f"--dirs-only")
    if files_only:
        args.append("--files-only")

    stdout, _ = utils.run_rclone_cmd(command, args)
    return json.loads(stdout)


@__check_installed
def size(
    path: str,
    args: List[str] = None,
) -> Dict:
    """Returns the total size and number of objects in the path.

    Args:
        path (str): The path to calculate the total size on.
        args (List[str], optional): Optional additional list of flags.

    Returns:
        Dict: Dictionary containing the file count, total file size in bytes and number of empty items.
    """
    if args is None:
        args = []

    stdout, _ = utils.run_rclone_cmd(f'size "{path}" --json', args)
    return json.loads(stdout)


@__check_installed
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

    stdout, _ = utils.run_rclone_cmd(f'tree "{path}"', args)
    return stdout


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
        RcloneException: Raised when the rclone command does not succeed.

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

    returncode, stdout, stderr = utils.run_rclone_cmd(
        f'hashsum "{hash}" "{path}"', args, raise_errors=False
    )

    lines = stdout.splitlines()

    exception = False

    if returncode != 0:
        if checkfile is None:
            exception = True
        else:
            # validate that the checkfile command succeeded, by checking if the output has the expected form
            for l in lines:
                if not (l.startswith("= ") or l.startswith("* ")):
                    exception = True
                    break

    if exception:
        raise utils.RcloneException(
            f'hashsum command failed on path "{path}" with hash="{hash}"',
            stderr,
        )

    if output_file is None:
        # each line contains the hashsum first, followed by the name of the file
        hashsums = {}

        for l in lines:
            if len(l) > 0:
                # in checkfile mode only a single space separates key and value (key=matching, value=filename)
                # while in normal mode a double space is used.
                value, key = [item.strip() for item in l.split(" ", maxsplit=1)]

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
def check(
    source: str,
    dest: str,
    combined: str = None,
    size_only: bool = False,
    download: bool = False,
    one_way: bool = False,
    args: List[str] = None,
) -> Tuple[bool, List[Tuple[str, str]]]:
    """Checks the files in the source and destination match.

    Args:
        source (str): The source path.
        dest (str): The destination path.
        combined (str, optional): Path to the combined file. Defaults to None.
        size_only (bool, optional): Only compare the sizes not the hashes as well. Use this for a quick check. Defaults to False.
        download (bool, optional): Download the data from both remotes and check them against each other on the fly. This can be useful for remotes that don't support hashes or if you really want to check all the data. Defaults to False.
        one_way (bool, optional): Only check that files in the source match the files in the destination, not the other way around. This means that extra files in the destination that are not in the source will not be detected. Defaults to False.
        args (List[str], optional): Optional additional list of flags and arguments. Defaults to None.

    Raises:
        utils.RcloneException: Raised when the rclone command does not succeed.

    Returns:
        Tuple[bool, List[Tuple[str, str]]]: The bool is true if source and dest match.
                                            The list contains a symbol and all file paths in both directories. The following symbols are used:
                                                "=" path means path was found in source and destination and was identical
                                                "-" path means path was missing on the source, so only in the destination
                                                "+" path means path was missing on the destination, so only in the source
                                                "*" path means path was present in source and destination but different.
                                                "!" path means there was an error reading or hashing the source or dest.

    """
    if args is None:
        args = []
    if size_only:
        args.append("--size-only")
    if download:
        args.append("--download")
    if one_way:
        args.append("--one-way")

    tmp = None
    if not combined:
        tmp = tempfile.TemporaryDirectory()
        combined = Path(tmp.name, "combined_file")
    # even if --combined is also specified by the user through args,
    # this one will be used as apparently rclone uses the last specification.
    args.append(f'--combined "{combined}"')

    returncode, _, stderr = utils.run_rclone_cmd(
        f'check "{source}" "{dest}"', args, raise_errors=False
    )

    logger.debug(f"Rclone check stderr output:\n{stderr}")

    # read the combined file and extract all elements
    combined_file = Path(combined)
    if returncode != 0 and not combined_file.is_file():
        raise utils.RcloneException(
            f'check command failed on source: "{source}" dest: "{dest}"',
            stderr,
        )
    out = [
        # the file holds the symbol followed by a space and then the filepath
        tuple(line.split(" ", maxsplit=1))
        for line in combined_file.read_text().splitlines()
    ]

    if tmp:
        tmp.cleanup()

    return returncode == 0, out


@__check_installed
def version(
    check=False,
    args: List[str] = None,
) -> Union[str, Tuple[str]]:
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

    stdout, stderr = utils.run_rclone_cmd("version", args)

    if not check:
        return stdout.splitlines()[0].replace("rclone ", "")
    else:
        yours = re.findall(r"yours:\s+([\d.]+)", stdout)[0]
        latest = re.findall(r"latest:\s+([\d.]+)", stdout)
        latest = latest[0] if latest else None
        # beta version might include dashes and word characters e.g. '1.64.0-beta.7161.9169b2b5a'
        beta = re.findall(r"beta:\s+([.\w-]+)", stdout)
        beta = beta[0] if beta else None

        if not latest or not beta:
            logger.warning(
                f"Failed to get latest rclone versions. The following error was output by rclone:\n{stderr}"
            )

        return yours, latest, beta


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
    process, errors = utils.rclone_progress(
        command,
        prog_title,
        listener=listener,
        show_progress=show_progress,
        pbar=pbar,
    )

    if process.wait() == 0:
        logger.info("Cloud upload completed.")
    else:
        raise utils.RcloneException(
            description=f"{command_descr} from {in_path} to {out_path} failed",
            error_msg="\n".join(errors),
        )
