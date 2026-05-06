# logging_setup.py
import os
import sys

from loguru import logger


def setup_logging():
    level = os.getenv("LOG_LEVEL", "INFO")
    debug = os.getenv("DEBUG", False) == "True"

    logger.remove()

    if not debug:
        logger.add(
            sys.stdout,
            level=level,
            serialize=True,
            enqueue=True,
        )
    else:
        fmt = "<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>"
        logger.add(sys.stdout, level=level, format=fmt)

    return logger
