#!/usr/bin/python3


import json
import subprocess as sp
from rclone_python import rclone


def extract_remote_names(output_path: str = None) -> str:
    """Updates the remote_types.py file to the newest supported backends.

    Args:
        output_path (str, optional): If provided, save the remote names as a .txt file.

    Returns:
        str: String containing remote type names as "var_name = remote_name"
    """

    # get all supported backends
    rclone_output = sp.check_output("rclone config providers", shell=True)
    data = json.loads(rclone_output)

    # get current version

    output = ""

    for provider in data:
        name: str = provider["Name"]

        if name == "alias":
            # don't include alias in the output
            continue

        var_name = name.replace(" ", "_")

        output += f'    {var_name} = "{name}"\n'

    if output_path:
        with open(output_path, "w") as o:
            o.write("from enum import Enum")
            o.write("\n\n\nclass RemoteTypes(Enum):")
            o.write(
                f'\n    """These are all the cloud systems support by rclone (generated with {rclone.version()}).'
            )
            o.write(
                "\n    A more detailed overview can be found here: https://rclone.org/overview/"
            )
            o.write('\n    """\n\n')
            o.write(f"{output}")

    return output


if __name__ == "__main__":
    extract_remote_names(output_path="rclone_python/remote_types.py")
