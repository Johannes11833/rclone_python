import json
import subprocess as sp


def extract_remote_names(output_path: str = None) -> str:
    """Extracts all the remote types supported by rclone.

    Args:
        output_path (str, optional): If provided, save the remote names as a .txt file.

    Returns:
        str: String containing remote type names as "var_name = remote_name"
    """
    rclone_output = sp.check_output("rclone config providers", shell=True)
    data = json.loads(rclone_output)

    output = ""

    for provider in data:
        name: str = provider["Name"]

        if name == "alias":
            # don't include alias in the output
            continue

        var_name = name.replace(" ", "_")

        output += f'{var_name}="{name}"\n'

    if output_path:
        with open(output_path, "w") as o:
            o.write(output)

    return output


if __name__ == "__main__":
    extract_remote_names(output_path="rclone_remote_names.txt")
