import logging
from rich.logging import RichHandler

logger = logging.getLogger("rclone_python")

if not logger.handlers:
    handler = RichHandler()
    handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
    logger.addHandler(handler)

logger.setLevel(logging.INFO)
logger.propagate = False
