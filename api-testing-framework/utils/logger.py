"""
utils/logger.py
───────────────
Centralised logging configuration for the test framework.

Usage
-----
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Test started")

The root logger is configured once (idempotent).  Subsequent calls to
`get_logger` simply return a child logger with the correct name.

Outputs
-------
  • Console  – INFO and above, coloured by level when a TTY is detected.
  • File     – DEBUG and above, written to  reports/framework.log
                (path is configurable via the LOG_FILE env-var or the
                 LOG_FILE_PATH constant below).
"""

import logging
import os
import sys
from pathlib import Path

# ── Configuration constants ──────────────────────────────────
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s – %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE_PATH = Path(os.getenv("LOG_FILE", "reports/framework.log"))
CONSOLE_LEVEL = logging.INFO
FILE_LEVEL = logging.DEBUG

_CONFIGURED = False  # Guard against double-initialisation


# ── Optional ANSI colour support ─────────────────────────────
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
}
_RESET = "\033[0m"


class ColouredFormatter(logging.Formatter):
    """Add ANSI colour codes to level names when writing to a TTY."""

    def format(self, record: logging.LogRecord) -> str:
        if sys.stdout.isatty():
            colour = _COLOURS.get(record.levelname, "")
            record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


# ── Public API ────────────────────────────────────────────────

def configure_logging() -> None:
    """
    Set up root logger with console + file handlers.
    Called automatically by `get_logger`; safe to call multiple times.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    # Ensure the reports directory exists
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)   # handlers filter individually

    # ── Console handler ──────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(CONSOLE_LEVEL)
    console_handler.setFormatter(ColouredFormatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console_handler)

    # ── File handler ─────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(FILE_LEVEL)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(file_handler)

    # Silence overly chatty third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, initialising root logging on first call.

    Parameters
    ----------
    name : str
        Typically ``__name__`` of the calling module.
    """
    configure_logging()
    return logging.getLogger(name)
