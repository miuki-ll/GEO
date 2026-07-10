import logging
import sys
from typing import Optional

from app.core.config import settings


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    log_level = (level or ("DEBUG" if settings.is_dev else "INFO")).upper()

    if not logger.handlers:
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger
