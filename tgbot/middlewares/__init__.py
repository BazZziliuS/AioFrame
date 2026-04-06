from aiogram import Dispatcher

from tgbot.middlewares.middleware_throttling import ThrottlingMiddleware
from tgbot.middlewares.middleware_user import ExistsUserMiddleware


# Register all middlewares
def register_all_middlewares(dp: Dispatcher):
    dp.callback_query.outer_middleware(ExistsUserMiddleware())
    dp.message.outer_middleware(ExistsUserMiddleware())

    dp.message.middleware(ThrottlingMiddleware())
