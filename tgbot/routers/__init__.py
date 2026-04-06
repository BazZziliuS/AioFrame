from aiogram import Dispatcher, F

from tgbot.routers import main_errors, main_missed, main_start
from tgbot.routers.admin import admin_menu
from tgbot.routers.user import user_menu
from tgbot.utils.misc.bot_filters import IsAdmin


# Register all routers
def register_all_routers(dp: Dispatcher):
    # Connect filters
    main_errors.router.message.filter(F.chat.type == "private")
    main_start.router.message.filter(F.chat.type == "private")

    user_menu.router.message.filter(F.chat.type == "private")
    admin_menu.router.message.filter(F.chat.type == "private", IsAdmin())

    main_missed.router.message.filter(F.chat.type == "private")

    # Connect needed routers
    dp.include_router(main_errors.router)  # Router - error
    dp.include_router(main_start.router)  # Router - main

    # Connect usebles routers (users и admins)
    dp.include_router(user_menu.router)  # Router - user
    dp.include_router(admin_menu.router)  # Router - admin

    # Connect needed routers
    dp.include_router(main_missed.router)  # Router - missed handlers
