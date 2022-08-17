import logging
import os
import re
import subprocess
from enum import Enum
from shutil import which
from typing import Union

from alive_progress import alive_bar


class RemoteTypes(Enum):
    google = "drive"
    dropbox = "dropbox"
    onedrive = "onedrive"
    box = "box"


def create(remote_name, remote_type: Union[str, RemoteTypes], client_id=None, client_secret=None):
    if isinstance(remote_type, RemoteTypes):
        remote_type = remote_type.value

    if not _check_installed:
        raise Exception('rclone is not installed on this system. Please install it here: https://rclone.org/')

    if _check_remote_existing(remote_name):
        # setup is not yet complete

        # set up the selected cloud
        command = f"rclone config create \"{remote_name}\" {remote_type}"

        if client_id and client_secret:
            logging.info('Using the provided client id and client secret.')

            command += f" --{remote_type}-client-id \"{client_id}\"" \
                       f" --{remote_type}-client-secret \"{client_secret}\""
        else:
            logging.warning('The drive client id and the client secret have not been set. Using defaults.')
        # run the setup command
        o = subprocess.run(command, shell=True, stderr=subprocess.PIPE)

        if o.returncode != 0:
            raise Exception(o.stderr)
    else:
        raise Exception(f'A rclone remote with the name \'{remote_name}\' already exists!')


def copy(remote_name: str, in_path: str, out_path: str, ignore_existing=False):
    if not _check_remote_existing(remote_name):
        raise Exception(f'The rclone remote \'{remote_name}\' does not exist!')

    command = f'rclone copy --progress'

    # add flags
    if ignore_existing:
        command += ' --ignore-existing'

    command += f' \"{in_path}\" \"{remote_name}:{out_path}\"'

    # execute the upload command
    process = _rclone_progress(command, f'Uploading to {remote_name}')

    if process.returncode == os.EX_OK:
        logging.info('Cloud upload completed.')
    else:
        raise Exception(f'Cloud upload failed with error message:\n{process.stderr}')


def _rclone_progress(command: str, pbar_title: str, stderr=subprocess.PIPE,
                     **kwargs) -> subprocess.Popen:
    print(command)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr, shell=True, **kwargs)

    progress = 0
    buffer = ""
    with alive_bar(manual=True, dual_line=True) as pbar:
        pbar.title = pbar_title
        for c in iter(lambda: process.stdout.read(1), b''):
            var = c.decode('utf-8')
            if '\n' not in var:
                buffer += var
            else:
                # matcher that finds the line with transferred update that includes the total progress
                transferred_block = re.findall(r'Transferred:(?:.|\n)+ETA \d+s', buffer)

                # update the progress
                if transferred_block:  # transferred block is completely buffered
                    transferred_block = transferred_block[0]

                    # matcher that finds the transferred line with the total progress
                    transferred_lines = re.findall(r'Transferred.*\ds', transferred_block)

                    # matcher for the currently transferring files
                    transferring_files = re.findall(r'\* +(\S+):', transferred_block)
                    pbar.text = f"-> Currently processing {', '.join(transferring_files)}"

                    buffer = ""
                    reg = re.findall('[0-9]+%', transferred_lines[0])
                    progress = int(reg[-1][:-1]) if reg else progress
                    pbar(progress / 100.0)

    process.communicate()

    return process


def _check_installed() -> bool:
    return which('rclone') is not None


def _check_remote_existing(remote_name: str) -> bool:
    # get the available remotes
    remotes = subprocess.check_output('rclone listremotes', shell=True, encoding='UTF-8').split()
    return f"{remote_name}:" in remotes
