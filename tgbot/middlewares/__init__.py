from aiogram import Dispatcher

from tgbot.config import settings
from tgbot.middlewares.access import AccessMiddleware
from tgbot.middlewares.throttling import ThrottlingMiddleware
from tgbot.middlewares.user import UserMiddleware


def register_middlewares(dp: Dispatcher) -> None:
    """Order matters: user sync -> access check (ban, maintenance) -> anti-spam."""
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(UserMiddleware())
        observer.outer_middleware(AccessMiddleware())

    dp.message.middleware(ThrottlingMiddleware(default_rate=settings.throttle_rate))
