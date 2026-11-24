"""Bot assembly: Bot, Dispatcher, FSM storage, scheduler, commands and the menu button."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    MenuButtonDefault,
    MenuButtonWebApp,
    WebAppInfo,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import settings
from tgbot.middlewares import register_middlewares
from tgbot.routers import register_routers
from tgbot.services.http import HttpClient
from tgbot.services.locale import DEFAULT_LOCALE, Locale, get_available_locales
from tgbot.services.notifications import send_backup_to_admins

logger = logging.getLogger(__name__)

USER_COMMANDS = ("start", "menu", "feedback", "cancel")
ADMIN_COMMANDS = (*USER_COMMANDS, "admin", "stats", "broadcast", "log", "db")


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_storage() -> BaseStorage:
    """FSM storage: Redis keeps dialogs between restarts, memory is for development."""
    if settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        return RedisStorage.from_url(settings.redis_url)
    return MemoryStorage()


def create_dispatcher(http_client: HttpClient) -> Dispatcher:
    dp = Dispatcher(storage=create_storage())
    dp["http_client"] = http_client  # injected into handlers as `http_client`

    register_middlewares(dp)
    register_routers(dp)
    return dp


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    # Daily database backup to admins
    scheduler.add_job(
        send_backup_to_admins, trigger="cron", hour=settings.autobackup_hour, args=(bot,)
    )
    return scheduler


def _commands(names: tuple[str, ...], locale: Locale) -> list[BotCommand]:
    return [BotCommand(command=name, description=locale(f"commands.{name}")) for name in names]


async def set_commands(bot: Bot) -> None:
    """Command menus for users and admins, in every available language."""
    for lang in get_available_locales():
        locale = Locale(lang)
        # The default locale also serves users whose language has no translation
        language_code = None if lang == DEFAULT_LOCALE else locale.language_code

        await bot.set_my_commands(
            _commands(USER_COMMANDS, locale),
            scope=BotCommandScopeDefault(),
            language_code=language_code,
        )

        for admin in settings.admin_ids:
            try:
                await bot.set_my_commands(
                    _commands(ADMIN_COMMANDS, locale),
                    scope=BotCommandScopeChat(chat_id=admin),
                    language_code=language_code,
                )
            except TelegramAPIError as error:
                logger.warning("Failed to set commands for admin %s: %s", admin, error)


async def setup_menu_button(bot: Bot) -> None:
    """Chat menu button opens the Mini App when it is enabled, otherwise shows commands."""
    if settings.webapp_enabled and settings.webapp_url:
        button = MenuButtonWebApp(
            text=Locale()("menu.webapp_button"), web_app=WebAppInfo(url=settings.webapp_url)
        )
        await bot.set_chat_menu_button(menu_button=button)
    else:
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())
