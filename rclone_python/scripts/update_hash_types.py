#!/usr/bin/python3


import subprocess as sp

from get_version import get_version


def update_hashes(output_path: str):
    """Updates the hash_types.py file to include all supported hash algorithms.

    Args:
        output_path str: Where to save the output file to.
    """

    # get all supported backends
    rclone_output = sp.check_output("rclone hashsum", shell=True, encoding="utf8")
    lines = rclone_output.splitlines()

    hashes = [line.replace("*", "").strip() for line in lines[1:]]

    with open(output_path, "w") as o:
        o.write("from enum import Enum")
        o.write("\nclass HashTypes(Enum):")
        o.write(
            f'\n\t"""These are all the hash algorithms support by rclone (generated with {get_version()}).'
        )
        o.write(
            "\n\tA more detailed overview can be found here: https://rclone.org/commands/rclone_hashsum/"
        )
        o.write('\n\t"""')
        for h in sorted(hashes):
            o.write(f'\n\t{h}="{h}"')


if __name__ == "__main__":
    update_hashes(output_path="rclone_python/hash_types.py")
