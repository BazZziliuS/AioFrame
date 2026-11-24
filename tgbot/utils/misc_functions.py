from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from tgbot.data.config import settings
from tgbot.services.backup import database_backup
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import get_date, send_admins
from tgbot.utils.misc.bot_logging import bot_logger


# Notification after run bot (for all admins)
async def startup_notify(bot: Bot) -> None:
    if settings.admin_ids and settings.bot_status_notification:
        locale = Locale()
        await send_admins(bot, locale("admin.bot_started"))


# Autobackup Database
async def autobackup_admin(bot: Bot) -> None:
    backup = await database_backup()
    if backup is None:
        bot_logger.info("Autobackup skipped: only SQLite databases are supported")
        return

    locale = Locale()
    for admin in settings.admin_ids:
        try:
            await bot.send_document(
                admin,
                backup,
                caption=f"<b>{locale('admin.autobackup_caption', date=get_date())}</b>",
            )
        except TelegramAPIError as error:
            bot_logger.warning("Failed to send backup to admin %s: %s", admin, error)
