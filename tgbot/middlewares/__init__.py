from aiogram import Dispatcher

from tgbot.data.config import settings
from tgbot.middlewares.middleware_access import AccessMiddleware
from tgbot.middlewares.middleware_throttling import ThrottlingMiddleware
from tgbot.middlewares.middleware_user import ExistsUserMiddleware


# Register all middlewares (order matters: user sync -> access check -> throttling)
def register_all_middlewares(dp: Dispatcher) -> None:
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(ExistsUserMiddleware())
        observer.outer_middleware(AccessMiddleware())

    dp.message.middleware(ThrottlingMiddleware(default_rate=settings.throttle_rate))
