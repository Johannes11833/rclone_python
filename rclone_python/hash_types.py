from enum import Enum


class HashTypes(Enum):
    """These are all the hash algorithms support by rclone (generated with v1.72.1).
    A more detailed overview can be found here: https://rclone.org/commands/rclone_hashsum/
    """

    blake3 = "blake3"
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
    xxh128 = "xxh128"
    xxh3 = "xxh3"
