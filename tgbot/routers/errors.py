import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.error(
    ExceptionTypeFilter(TelegramBadRequest),
    F.exception.message.contains("message is not modified"),
)
async def ignore_not_modified(event: ErrorEvent) -> None:
    """Editing a message to the same content is harmless (e.g. a double click)."""


@router.error()
async def log_unhandled(event: ErrorEvent) -> None:
    logger.error(
        "Unhandled exception in update %s",
        event.update.update_id,
        exc_info=event.exception,
    )
