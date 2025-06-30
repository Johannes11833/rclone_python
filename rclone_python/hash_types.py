from enum import Enum


class HashTypes(Enum):
    """These are all the hash algorithms support by rclone (generated with v1.70.2).
    A more detailed overview can be found here: https://rclone.org/commands/rclone_hashsum/
    """

    crc32 = "crc32"
    dropbox = "dropbox"
    hidrive = "hidrive"
    mailru = "mailru"
    md5 = "md5"
    quickxor = "quickxor"
    sha1 = "sha1"
    sha256 = "sha256"
    sha512 = "sha512"
    whirlpool = "whirlpool"
