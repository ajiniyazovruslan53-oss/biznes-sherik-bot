"""
Logging configuration with console output and rotating file handler.
Handles read-only file systems (like Vercel serverless /var/task) safely.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.config import config, BASE_DIR

if os.getenv("VERCEL"):
    LOG_FILE = Path("/tmp/bot.log")
else:
    LOG_FILE = BASE_DIR / "bot.log"


def setup_logger(name: str = "biznes_sherik") -> logging.Logger:
    """Configures and returns a structured logger writing to stdout and rotating log file."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (safe against read-only file systems)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console only if file cannot be created
        console_handler.setLevel(logging.INFO)

    return logger


logger = setup_logger()
