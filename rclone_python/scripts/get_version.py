from subprocess import check_output


def get_version() -> str:
    stdout = check_output("rclone version", shell=True, encoding="utf8")

    return stdout.split("\n")[0].replace("rclone ", "")
