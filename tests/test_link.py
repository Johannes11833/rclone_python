from rclone_python import rclone
import re


def validate_url(url: str):
    # url validator used in django: https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return re.match(regex, url) is not None


def test_link(default_test_setup, tmp_remote_folder):
    dest = f"{tmp_remote_folder}/folder 3 /text  1.txt"
    rclone.copyto(default_test_setup.local_test_txt_file, dest, show_progress=False)
    link = rclone.link(dest)
    assert validate_url(link)
