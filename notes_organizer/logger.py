"""Small logging setup. Logs go to a file so the CLI output stays clean."""

import logging
from pathlib import Path

LOG_NAME = "notes_organizer"


def get_logger(log_dir: Path = None) -> logging.Logger:
    logger = logging.getLogger(LOG_NAME)
    if logger.handlers:  # already configured
        return logger

    logger.setLevel(logging.INFO)
    if log_dir is not None:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_dir / "notes.log", encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            )
            logger.addHandler(handler)
        except OSError:
            logger.addHandler(logging.NullHandler())
    else:
        logger.addHandler(logging.NullHandler())
    return logger
