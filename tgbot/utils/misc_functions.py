from aiogram import Bot
from aiogram.types import FSInputFile

from tgbot.data.config import get_admins, PATH_DATABASE, BOT_STATUS_NOTIFICATION
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import get_date, send_admins


# Notification after run bot (for all admins)
async def startup_notify(bot: Bot):
    if get_admins() and BOT_STATUS_NOTIFICATION:
        locale = Locale()
        await send_admins(bot, locale("admin.bot_started"))


# Autobackup Database
async def autobackup_admin(bot: Bot):
    locale = Locale()
    for admin in get_admins():
        try:
            await bot.send_document(
                admin,
                FSInputFile(PATH_DATABASE),
                caption=f"<b>{locale('admin.autobackup_caption', date=get_date())}</b>",
            )
        except Exception:
            pass
