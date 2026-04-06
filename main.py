# - *- coding: utf- 8 - *-
import asyncio
import os
import sys

import colorama
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from tgbot.data.config import BOT_TOKEN, BOT_SCHEDULER, get_admins
from tgbot.database import engine, async_session, Base, SettingsRepository
from tgbot.middlewares import register_all_middlewares
from tgbot.routers import register_all_routers
from tgbot.services.api_session import AsyncRequestSession
from tgbot.utils.misc.bot_commands import set_commands
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc_functions import autobackup_admin, startup_notify

colorama.init()


# Start schedulers
async def scheduler_start(bot):
    BOT_SCHEDULER.add_job(
        autobackup_admin, trigger="cron", hour=00, args=(bot,)
    )  # Ежедневный Автобэкап в 00:00


# Start bot and basic functions
async def main():
    BOT_SCHEDULER.start()  # Start scheduler
    dp = Dispatcher()  # Dispatcher image
    arSession = AsyncRequestSession()  # Async session pool (aiohttp)

    bot = Bot(  # Образ Бота
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    register_all_middlewares(dp)  # Register all middlewares
    register_all_routers(dp)  # Register all routers

    try:
        # Initialize database tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            await SettingsRepository(session).get_settings()
            await session.commit()

        await set_commands(bot)  # Set commands for users
        await startup_notify(bot)  # Notification that bot was started
        await scheduler_start(bot)  # Connect schedulers

        bot_logger.warning("BOT WAS STARTED")
        print(
            colorama.Fore.LIGHTYELLOW_EX
            + f"~~~~~ Bot was started - @{(await bot.get_me()).username} ~~~~~"
        )
        print(colorama.Fore.LIGHTBLUE_EX + "~~~~~ TG developer - @BazZziliuS ~~~~~")
        print(colorama.Fore.RESET)

        if not get_admins():
            print("***** ENTER ADMIN_IDS IN .env *****")

        await bot.delete_webhook()  # Deletes webhooks, if they was have
        await bot.get_updates(offset=-1)  # Reset update pengings

        # Run bot (polling method)
        await dp.start_polling(
            bot,
            arSession=arSession,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await arSession.close()  # Close async session (aiohttp)
        await bot.session.close()  # Close bot session


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        bot_logger.warning("Bot was stopped")
    finally:
        if sys.platform.startswith("win"):
            os.system("cls")
        else:
            os.system("clear")
