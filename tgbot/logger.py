"""Logging setup: a file with everything from LOG_LEVEL and a colored console for warnings.

Call `setup_logging()` once at startup; modules use `logging.getLogger(__name__)`.
"""

import logging

import colorlog

from tgbot.config import settings

FILE_FORMAT = "%(levelname)s | %(asctime)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
CONSOLE_FORMAT = (
    "%(log_color)s%(levelname)s%(reset)s %(blue)s|%(reset)s %(asctime)s %(blue)s|%(reset)s "
    "%(name)s %(blue)s|%(reset)s %(message)s"
)

_configured = False


def setup_logging() -> None:
    """Attach file and console handlers to the root logger (idempotent)."""
    global _configured
    if _configured:
        return

    settings.path_logs.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(settings.path_logs, "a", "utf-8")
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
    file_handler.setLevel(settings.log_level)

    # Console: only warnings and errors, the rest is in the file
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        colorlog.ColoredFormatter(CONSOLE_FORMAT, datefmt="%d-%m-%Y %H:%M:%S")
    )
    console_handler.setLevel(logging.WARNING)

    # Handlers are attached explicitly: basicConfig() is a no-op if the root is configured
    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Per-update INFO lines from aiogram flood the file; keep its warnings
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    _configured = True
