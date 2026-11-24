import logging as bot_logger

import colorlog

from tgbot.data.config import settings

LOG_FORMAT = "%(levelname)s | %(asctime)s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

# Logging format
log_formatter_file = bot_logger.Formatter(LOG_FORMAT)
log_formatter_console = colorlog.ColoredFormatter(
    "%(purple)s%(levelname)s %(blue)s|%(purple)s %(asctime)s %(blue)s|%(purple)s "
    "%(filename)s:%(lineno)d %(blue)s|%(purple)s %(message)s%(reset)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)

# Logging in file (directory is created if missing)
settings.path_logs.parent.mkdir(parents=True, exist_ok=True)
file_handler = bot_logger.FileHandler(settings.path_logs, "a", "utf-8")
file_handler.setFormatter(log_formatter_file)
file_handler.setLevel(settings.log_level)

# Logging in console: only warnings and errors, the rest goes to the file
console_handler = bot_logger.StreamHandler()
console_handler.setFormatter(log_formatter_console)
console_handler.setLevel(bot_logger.WARNING)

# Connect handlers explicitly: basicConfig() is a no-op if the root logger is already configured
_root = bot_logger.getLogger()
_root.setLevel(settings.log_level)
_root.addHandler(file_handler)
_root.addHandler(console_handler)
