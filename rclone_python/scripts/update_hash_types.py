#!/usr/bin/python3


import json
import subprocess as sp
from rclone_python import rclone


def update_hashes(output_path: str):
    """Updates the hash_types.py file to include all supported hash algorithms.

    Args:
        output_path str: Where to save the output file to.
    """

    # get all supported backends
    rclone_output = sp.check_output("rclone hashsum", shell=True, encoding="utf8")
    lines = rclone_output.splitlines()

    hashes = []

    for l in lines[1:]:
        hashes.append(l.replace("*", "").strip())

    with open(output_path, "w") as o:
        o.write("from enum import Enum")
        o.write("\nclass RemoteTypes(Enum):")
        o.write(
            f'\n\t"""These are all the hash algorithms support by rclone (generated with {rclone.version()}).'
        )
        o.write(
            "\n\tA more detailed overview can be found here: https://rclone.org/commands/rclone_hashsum/"
        )
        o.write('\n\t"""')
        for h in hashes:
            o.write(f'\n\t{h}="{h}"')


if __name__ == "__main__":
    update_hashes(output_path="rclone_python/hash_types.py")
