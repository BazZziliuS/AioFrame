from aiogram import Dispatcher, F

from tgbot.routers import errors, fallback, start
from tgbot.routers.admin import broadcast, panel
from tgbot.routers.user import feedback, menu

# Order matters: the first matching handler wins
ROUTERS = (
    errors.router,  # error handlers
    start.router,  # /start, /cancel
    menu.router,  # user menu
    feedback.router,  # FSM example
    panel.router,  # admin panel (IsAdmin filter inside)
    broadcast.router,  # admin broadcast (IsAdmin filter inside)
    fallback.router,  # unknown messages and buttons: must be the last one
)


def register_routers(dp: Dispatcher) -> None:
    for router in ROUTERS:
        router.message.filter(F.chat.type == "private")  # the bot works in private chats
        dp.include_router(router)
