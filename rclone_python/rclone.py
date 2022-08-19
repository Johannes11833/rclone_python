import logging
import os
import re
import subprocess
from functools import wraps
from shutil import which
from typing import Union, List

from alive_progress import alive_bar

from rclone_python.remote_types import RemoteTypes


def __check_installed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_installed:
            raise Exception('rclone is not installed on this system. Please install it here: https://rclone.org/')

        return func(*args, **kwargs)

    return wrapper


def is_installed() -> bool:
    return which('rclone') is not None


@__check_installed
def check_remote_existing(remote_name: str) -> bool:
    # get the available remotes
    remotes = get_remotes()

    # add the trailing ':' if it is missing
    if not remote_name.endswith(':'):
        remote_name = f'{remote_name}:'

    return remote_name in remotes


@__check_installed
def create_remote(remote_name, remote_type: Union[str, RemoteTypes], client_id=None, client_secret=None):
    if isinstance(remote_type, RemoteTypes):
        remote_type = remote_type.value

    if not check_remote_existing(remote_name):
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


def copy(in_path: str, out_path: str, ignore_existing=False):
    _copy_move(in_path, out_path, ignore_existing=ignore_existing, move_files=False)


def move(in_path: str, out_path: str, ignore_existing=False):
    _copy_move(in_path, out_path, ignore_existing=ignore_existing, move_files=True)


@__check_installed
def _copy_move(in_path: str, out_path: str, ignore_existing=False, move_files=False):
    if move_files:
        command = f'rclone move'
        prog_title = f'Moving'
    else:
        command = f'rclone copy'
        prog_title = f'Copying'

    # add global rclone flags
    if ignore_existing:
        command += ' --ignore-existing'
    command += ' --progress'

    # in path
    command += f' {in_path}'
    # out path
    command += f' {out_path}'

    # execute the upload command
    process = _rclone_progress(command, prog_title)

    if process.wait() == os.EX_OK:
        logging.info('Cloud upload completed.')
    else:
        _, err = process.communicate()
        raise Exception(f'Copy/Move operation from {in_path} to {out_path}'
                        f' failed with error message:\n{err.decode("utf-8")}')


@__check_installed
def get_remotes() -> List[str]:
    remotes = subprocess.check_output('rclone listremotes', shell=True, encoding='UTF-8').split()
    if remotes is None:
        remotes = []

    print(remotes)

    return remotes


@__check_installed
def purge(path: str):
    process = subprocess.run(f'rclone purge {path}', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=True)
    if process.returncode == os.EX_OK:
        logging.info(f'Successfully purged {path}')
    else:
        raise Exception(
            f'Purging path \"{path}\" failed with error message:\n{process.stderr}')


@__check_installed
def delete(path: str):
    command = 'delete'
    process = subprocess.run(f'rclone {command} {path}', stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             shell=True)
    if process.returncode == os.EX_OK:
        logging.info(f'Successfully deleted {path}')
    else:
        raise Exception(
            f'Deleting path \"{path}\" failed with error message:\n{process.stderr}')


def _rclone_progress(command: str, pbar_title: str, stderr=subprocess.PIPE,
                     **kwargs) -> subprocess.Popen:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=stderr, shell=True, **kwargs)

    progress = 0
    buffer = ""
    with alive_bar(manual=True, dual_line=True, stats=False) as pbar:
        if pbar_title:
            pbar.title = pbar_title

        for c in iter(lambda: process.stdout.read(1), b''):
            var = c.decode('utf-8')
            if '\n' not in var:
                buffer += var
            else:
                # matcher that checks if the progress update block is completely buffered yet (defines start and stop)
                reg_block = re.findall(r'Transferred:(?:.|\n)+ETA \d+s', buffer)

                if reg_block:  # transferred block is completely buffered
                    transferred_block = reg_block[0]

                    # matcher for the currently transferring files and their individual progress
                    reg_transferring_names = re.findall(r'\* +(\S+):[ ]+(\d{1,2})%', transferred_block)
                    str_transferring = ''
                    for f_name, f_prog in reg_transferring_names:
                        str_transferring += f'{f_name} ({f_prog}%),'
                    pbar.text = f"-> Currently transferring {str_transferring.removesuffix(',')}"

                    # matcher that gets sent bits, total bits, progress, transfer-speed and eta
                    reg_transferred = re.findall(
                        r'Transferred:\s+(\d+.\d+ \w+) \/ (\d+.\d+ \w+), (\d{1,3})%, (\d+.\d+ \w+\/\w+), ETA (\d+s)',
                        transferred_block)
                    sent_bits, total_bits, progress, transfer_speed, eta = reg_transferred[0]
                    pbar(int(progress) / 100.0)
                    pbar.title = f'{pbar_title} {sent_bits}/{total_bits}'
                    pbar.stats = '{rate}'

                    # reset the buffer
                    buffer = ""

        pbar(1)
    return process
