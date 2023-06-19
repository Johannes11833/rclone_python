import json
import logging
from functools import wraps
from shutil import which
from typing import Union, List, Dict, Callable, Any

from rclone_python import utils
from rclone_python.remote_types import RemoteTypes


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


def copy(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
):
    """
    Copies a file or a directory from a src path to a destination path.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
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
    )


def move(
    in_path: str,
    out_path: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
):
    """
    Moves a file or a directory from a src path to a destination path.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param ignore_existing: If True, all existing files are ignored and not overwritten.
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
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
    )


def sync(
    src_path: str,
    dest_path: str,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
):
    """
    Sync the source to the destination, changing the destination only. Doesn't transfer files that are identical on source and destination, testing by size and modification time or MD5SUM.
    :param in_path: The source path to use. Specify the remote with 'remote_name:path_on_remote'
    :param out_path: The destination path to use. Specify the remote with 'remote_name:path_on_remote'
    :param show_progress: If true, show a progressbar.
    :param listener: An event-listener that is called with every update of rclone.
    :param args: List of additional arguments/ flags.
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
        raise Exception(f"ls operation on {path} failed with {process.stderr}")


def tree(
    path: str,
    args: List[str] = None,
) -> str:
    """Returns the contents of the remote path in a tree like fashion.

    Args:
        path (str): The path from which the tree should be generated
        args (List[str], optional): Optional additional list of flags (e.g. ['--all', '--modtime']).

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
def _rclone_transfer_operation(
    in_path: str,
    out_path: str,
    command: str,
    command_descr: str,
    ignore_existing=False,
    show_progress=True,
    listener: Callable[[Dict], None] = None,
    args=None,
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
    """
    if args is None:
        args = []

    prog_title = f"{command_descr} [bold magenta]{utils.shorten_filepath(in_path, 20)}[/bold magenta] to [bold magenta]{utils.shorten_filepath(out_path, 20)}"

    # add global rclone flags
    if ignore_existing:
        command += " --ignore-existing"
    command += " --progress"

    # in path
    command += f' "{in_path}"'
    # out path
    command += f' "{out_path}"'

    # optional named arguments/flags
    command += utils.args2string(args)

    # execute the upload command
    process = utils.rclone_progress(
        command, prog_title, listener=listener, show_progress=show_progress
    )

    if process.wait() == 0:
        logging.info("Cloud upload completed.")
    else:
        _, err = process.communicate()
        raise Exception(
            f"Copy/Move operation from {in_path} to {out_path}"
            f' failed with error message:\n{err.decode("utf-8")}'
        )
