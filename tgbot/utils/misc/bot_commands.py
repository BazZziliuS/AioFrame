from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from tgbot.data.config import settings
from tgbot.services.locale import DEFAULT_LOCALE, Locale, get_available_locales
from tgbot.utils.misc.bot_logging import bot_logger

USER_COMMANDS = ("start", "menu", "feedback", "cancel")
ADMIN_COMMANDS = (*USER_COMMANDS, "admin", "stats", "broadcast", "log", "db")


def _commands(names: tuple[str, ...], locale: Locale) -> list[BotCommand]:
    return [BotCommand(command=name, description=locale(f"commands.{name}")) for name in names]


# Set commands (descriptions in every available language)
async def set_commands(bot: Bot) -> None:
    for lang in get_available_locales():
        locale = Locale(lang)
        # Default locale is also used for users whose language has no translation
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
                bot_logger.warning("Failed to set commands for admin %s: %s", admin, error)
