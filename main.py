import asyncio
from contextlib import suppress

import colorama
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonDefault, MenuButtonWebApp, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.data.config import settings
from tgbot.database import SettingsRepository, async_session, engine
from tgbot.database.migrations import run_migrations
from tgbot.middlewares import register_all_middlewares
from tgbot.routers import register_all_routers
from tgbot.services.api_session import AsyncRequestSession
from tgbot.services.locale import Locale
from tgbot.utils.misc.bot_commands import set_commands
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.utils.misc_functions import autobackup_admin, startup_notify

colorama.init()


def create_storage() -> BaseStorage:
    """FSM storage: Redis keeps dialogs between restarts, memory is for development."""
    if settings.redis_url:
        from aiogram.fsm.storage.redis import RedisStorage

        return RedisStorage.from_url(settings.redis_url)
    return MemoryStorage()


def create_dispatcher(ar_session: AsyncRequestSession) -> Dispatcher:
    dp = Dispatcher(storage=create_storage())
    dp["arSession"] = ar_session  # Available in handlers as `arSession`

    register_all_middlewares(dp)  # Register all middlewares
    register_all_routers(dp)  # Register all routers
    return dp


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    # Daily database backup to admins
    scheduler.add_job(autobackup_admin, trigger="cron", hour=settings.autobackup_hour, args=(bot,))
    return scheduler


async def prepare_database() -> None:
    await run_migrations()  # alembic upgrade head

    async with async_session() as session:
        await SettingsRepository(session).get_settings()
        await session.commit()


def create_web_server(bot: Bot, dp: Dispatcher) -> uvicorn.Server:
    """FastAPI app (webhook + Mini App) served by uvicorn inside the bot's event loop."""
    from webapp.app import create_app

    config = uvicorn.Config(
        create_app(bot, dp),
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_config=None,  # use the bot's logging setup
        access_log=False,
        lifespan="off",  # bot lifecycle is managed by main()
    )
    return uvicorn.Server(config)


async def setup_menu_button(bot: Bot) -> None:
    """Chat menu button opens the Mini App when WEBAPP_URL is set."""
    if settings.webapp_url:
        button = MenuButtonWebApp(
            text=Locale()("menu.webapp_button"), web_app=WebAppInfo(url=settings.webapp_url)
        )
        await bot.set_chat_menu_button(menu_button=button)
    else:
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())


async def run_bot(bot: Bot, dp: Dispatcher) -> None:
    allowed_updates = dp.resolve_used_update_types()
    server = create_web_server(bot, dp) if settings.web_server_enabled else None

    if settings.bot_mode == "webhook":
        assert server is not None
        await bot.set_webhook(
            settings.webhook_url,
            secret_token=settings.webhook_secret.get_secret_value()
            if settings.webhook_secret
            else None,
            allowed_updates=allowed_updates,
            drop_pending_updates=True,
        )
        await server.serve()
        return

    await bot.delete_webhook(drop_pending_updates=True)
    if server is None:
        await dp.start_polling(bot, allowed_updates=allowed_updates)
        return

    # Polling + Mini App server: uvicorn handles Ctrl+C, then polling is stopped
    polling = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=allowed_updates, handle_signals=False)
    )
    try:
        await server.serve()
    finally:
        with suppress(RuntimeError):  # polling may not have started yet
            await dp.stop_polling()
        await asyncio.gather(polling, return_exceptions=True)


def print_banner(username: str | None) -> None:
    print(colorama.Fore.LIGHTYELLOW_EX + f"~~~~~ Bot was started - @{username} ~~~~~")
    print(colorama.Fore.LIGHTBLUE_EX + "~~~~~ TG developer - @BazZziliuS ~~~~~")
    print(colorama.Fore.RESET)

    if not settings.admin_ids:
        print("***** ENTER ADMIN_IDS IN .env *****")


# Start bot and basic functions
async def main() -> None:
    await prepare_database()

    ar_session = AsyncRequestSession()  # Async session pool (aiohttp)
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher(ar_session)
    scheduler = create_scheduler(bot)

    try:
        await set_commands(bot)  # Set commands for users and admins
        await setup_menu_button(bot)  # Mini App button (or the default one)
        await startup_notify(bot)  # Notification that bot was started
        scheduler.start()

        bot_logger.warning("BOT WAS STARTED (%s mode)", settings.bot_mode)
        print_banner((await bot.get_me()).username)

        if settings.web_server_enabled:
            bot_logger.warning(
                "Web server on %s:%s (Mini App: %s)",
                settings.webapp_host,
                settings.webapp_port,
                settings.webapp_url or "disabled",
            )
        await run_bot(bot, dp)
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await ar_session.close()  # Close async session (aiohttp)
        await dp.storage.close()
        await bot.session.close()  # Close bot session
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        bot_logger.exception("Bot crashed")
        raise
    finally:
        bot_logger.warning("Bot was stopped")
