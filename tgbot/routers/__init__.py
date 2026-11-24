from aiogram import Dispatcher, F

from tgbot.routers import main_errors, main_missed, main_start
from tgbot.routers.admin import admin_broadcast, admin_menu
from tgbot.routers.user import user_feedback, user_menu

# Order matters: the first matching handler wins
ROUTERS = (
    main_errors.router,  # Error handlers
    main_start.router,  # /start, /cancel
    user_menu.router,  # User routes
    user_feedback.router,  # FSM example
    admin_menu.router,  # Admin routes (IsAdmin filter inside)
    admin_broadcast.router,  # Admin broadcast (IsAdmin filter inside)
    main_missed.router,  # Fallback handlers: must be the last one
)


# Register all routers
def register_all_routers(dp: Dispatcher) -> None:
    for router in ROUTERS:
        # The bot works in private chats only
        router.message.filter(F.chat.type == "private")
        dp.include_router(router)
