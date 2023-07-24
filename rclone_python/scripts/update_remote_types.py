#!/usr/bin/python3


import json
import subprocess as sp
from rclone_python import rclone


def extract_remote_names(output_path: str = None) -> str:
    """Updates the remote_types.py file to the newest supported backends.

    Args:
        output_path str: Where to save the output file to.
    """

    # get all supported backends
    rclone_output = sp.check_output("rclone config providers", shell=True)
    data = json.loads(rclone_output)

    providers = []

    for p in data:
        name: str = p["Name"]

        if name == "alias":
            # don't include alias in the output
            continue

        var_name = name.replace(" ", "_")

        providers.append((var_name, name))

    with open(output_path, "w") as o:
        o.write("from enum import Enum")
        o.write("\nclass RemoteTypes(Enum):")
        o.write(
            f'\n\t"""These are all the cloud systems support by rclone (generated with {rclone.version()}).'
        )
        o.write(
            "\n\tA more detailed overview can be found here: https://rclone.org/overview/"
        )
        o.write('\n\t"""')
        for p in providers:
            o.write(f'\n\t{p[0]}="{p[1]}"')


if __name__ == "__main__":
    extract_remote_names(output_path="rclone_python/remote_types.py")
