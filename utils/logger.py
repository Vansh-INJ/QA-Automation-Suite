import logging
import os

from utils.run_manager import (
    get_run_folder
)

RUN_FOLDER = get_run_folder()

LOG_FOLDER = os.path.join(
    RUN_FOLDER,
    "logs"
)

LOG_FILE = os.path.join(
    LOG_FOLDER,
    "execution.log"
)

logger = logging.getLogger(
    "QA-Automation"
)

logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.handlers:

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )
    file_handler.setFormatter(
        formatter
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )
    logger.addHandler(
        console_handler
    )