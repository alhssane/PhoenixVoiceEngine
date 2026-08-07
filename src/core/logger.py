"""
Phoenix Voice Studio
Logging System
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import LOGS_DIR


LOG_FILE = LOGS_DIR / "phoenix.log"


def create_logger(name: str = "Phoenix") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = create_logger()