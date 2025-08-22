"""Logging configuration for the trading bot."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_PATH = os.getenv("LOG_PATH", "bot.log")


def setup_logging() -> None:
    """Configure root logger with rotating file and console handlers."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    if logger.handlers:
        return  # already configured
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)


__all__ = ["setup_logging"]
