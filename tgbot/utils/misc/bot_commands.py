from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from tgbot.data.config import get_admins
from tgbot.utils.misc.bot_logging import bot_logger

# Commands for users
user_commands = [
    BotCommand(command="start", description="♻️ Restart bot"),
    BotCommand(command="menu", description="🌀 Get keyboards"),
]

# Commands for admins
admin_commands = [
    BotCommand(command="start", description="♻️ Restart bot"),
    BotCommand(command="menu", description="🌀 Get keyboards"),
    BotCommand(command="log", description="🖨 Get Logs"),
    BotCommand(command="db", description="📦 Get Database"),
]


# Set commands
async def set_commands(bot: Bot):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    for admin in get_admins():
        try:
            await bot.set_my_commands(
                admin_commands, scope=BotCommandScopeChat(chat_id=admin)
            )
        except TelegramAPIError as error:
            bot_logger.warning("Failed to set commands for admin %s: %s", admin, error)
