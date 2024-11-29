from typing import Tuple
from rclone_python import rclone


def test_version():
    # v is the installed version
    v = rclone.version(check=False)
    assert isinstance(v, str) and len(v) > 0

    ## v is a tuple holding the installed, latest and latest beta version
    v = rclone.version(check=True)
    assert isinstance(v, Tuple) and len(v) == 3
    for v_i in v:
        assert isinstance(v_i, str) and len(v_i) > 0
