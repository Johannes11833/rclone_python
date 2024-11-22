from rclone_python.utils import args2string


def test_args2string():
    args = []

    result = args2string(args)

    assert result == ""

    args = ["--links", "--transfers", "40"]

    result = args2string(args)

    assert result == " --links --transfers 40"
