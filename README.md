[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![PyPI version](https://badge.fury.io/py/rclone-python.svg)](https://badge.fury.io/py/rclone-python)

# rclone-python ☁️

A python wrapper for rclone that makes rclone's functionality usable in python.
rclone needs to be installed on the system for the wrapper to work.

![demo gif](https://raw.githubusercontent.com/Johannes11833/rclone_python/master/demo/demo.gif)

## Features ⚒️

- Copy and move files between remotes
- Delete and prune files/directories
- List files in a directory including properties of the files.
- List available remotes.
- Create new remotes
- Check available remotes

## Installation 💾

_rclone_python_ can be installed using pip

```shell
pip install rclone-python
```

or by cloning this repository and running from within the root of the project

```shell
pip install .
```

## How to use 💡

All functionally of this wrapper is accessible through `rclone`.
The following example checks if rclone is installed.

```python
from rclone_python import rclone

print(rclone.is_installed())
# True
```

### Create new remote

Create a new rclone remote connection with rclone's default client-id and client-secret.

```python
from rclone_python import rclone
from rclone_python.remote_types import RemoteTypes

rclone.create_remote('onedrive', RemoteTypes.onedrive)
```

Additionally, client-id and client-secret can be used with many cloud providers.

```python
from rclone_python import rclone
from rclone_python.remote_types import RemoteTypes

rclone.create_remote('onedrive', RemoteTypes.onedrive, client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')
```

### Copy

```python
from rclone_python import rclone

# copy all file in the test_dir on OneDrive to the local data folder.
rclone.copy('onedrive:data', 'data', ignore_existing=True, args=['--create-empty-src-dirs'])
# ☁ Copying:  48%|████▊     | 151.1/315.309 MiB, 13.9 MiB/s, ETA: 11s

```

### Delete

Delete a file or a directory. When deleting a directory, only the files in the directory (and all it's subdirectories)
are deleted, but the folders remain.

```python
from rclone_python import rclone

# delete a specific file on onedrive
rclone.delete('onedrive:data/video1.mp4')

```

### Prune

```python
from rclone_python import rclone

# remove the entire test_dir folder (and all files contained in it and it's subdirectories) on onedrive
rclone.purge('onedrive:test_dir')
```

