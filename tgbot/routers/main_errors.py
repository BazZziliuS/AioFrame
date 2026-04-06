from aiogram import Router
from aiogram.filters import ExceptionMessageFilter
from aiogram.handlers import ErrorHandler

from tgbot.utils.misc.bot_logging import bot_logger

router = Router(name=__name__)


# Error: duplicate message edit (safe to ignore)
@router.errors(
    ExceptionMessageFilter(
        "Bad Request: message is not modified: specified new message content"
        " and reply markup are exactly the same as a current content"
        " and reply markup of the message"
    )
)
class DuplicateEditHandler(ErrorHandler):
    async def handle(self):
        pass


# Catch-all for unhandled exceptions
@router.errors()
class UnhandledErrorHandler(ErrorHandler):
    async def handle(self):
        bot_logger.exception(
            "Unhandled exception: %s: %s",
            self.exception_name,
            self.exception_message,
        )
