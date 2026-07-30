"""
Custom Logging Module for ResearchGPT.
Configures structured console and file output for operational tracking and debugging.
"""

import logging
import sys
from config import settings


def setup_logger(name: str = "ResearchGPT") -> logging.Logger:
    """Creates and returns a pre-configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Prevent adding duplicate handlers if logger is instantiated multiple times
    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console output handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File output handler
    log_file_path = settings.LOGS_DIR / "app.log"
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()