import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Return a configured logger for the given module name.

    If *level* is not specified, the logger inherits the root logger's level
    so that --log-level DEBUG propagates to all modules automatically.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    if level:
        # Explicit level requested: attach own handler, don't propagate
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.propagate = False
    else:
        # No explicit level: propagate to root logger (set by setup_root_logger)
        # Do NOT add a handler — root already has one
        logger.setLevel(logging.NOTSET)
        logger.propagate = True
    return logger


def setup_root_logger(level: str = "INFO") -> None:
    """Configure the root logger once at application startup."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )
