"""Application logging setup."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_FOLDER


def setup_logger(name: str = "email_agent") -> logging.Logger:
    """Return a configured logger that avoids logging private email content."""
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(LOG_FOLDER / "email_agent.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
