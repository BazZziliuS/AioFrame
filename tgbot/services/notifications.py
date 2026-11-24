"""Service messages to admins: startup notice and the scheduled database backup."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from tgbot.config import settings
from tgbot.services.backup import database_backup
from tgbot.services.locale import Locale
from tgbot.utils.telegram import send_admins
from tgbot.utils.text import format_now

logger = logging.getLogger(__name__)


async def notify_admins_started(bot: Bot) -> None:
    if settings.admin_ids and settings.bot_status_notification:
        await send_admins(bot, Locale()("admin.bot_started"))


async def send_backup_to_admins(bot: Bot) -> None:
    """Scheduled job: send a database snapshot to every admin."""
    backup = await database_backup()
    if backup is None:
        logger.info("Autobackup skipped: only SQLite databases are supported")
        return

    caption = f"<b>{Locale()('admin.autobackup_caption', date=format_now())}</b>"
    for admin in settings.admin_ids:
        try:
            await bot.send_document(admin, backup, caption=caption)
        except TelegramAPIError as error:
            logger.warning("Failed to send backup to admin %s: %s", admin, error)
