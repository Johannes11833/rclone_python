from enum import Enum


class HashTypes(Enum):
    """These are all the hash algorithms support by rclone (generated with v1.63.1).
    A more detailed overview can be found here: https://rclone.org/commands/rclone_hashsum/
    """

    md5 = "md5"
    sha1 = "sha1"
    whirlpool = "whirlpool"
    crc32 = "crc32"
    sha256 = "sha256"
    dropbox = "dropbox"
    hidrive = "hidrive"
    mailru = "mailru"
    quickxor = "quickxor"
