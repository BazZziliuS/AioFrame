import asyncio

import colorama
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.data.config import settings
from tgbot.database import SettingsRepository, async_session, engine
from tgbot.database.migrations import run_migrations
from tgbot.middlewares import register_all_middlewares
from tgbot.routers import register_all_routers
from tgbot.services.api_session import AsyncRequestSession
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


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def webhook_secret() -> str | None:
    return settings.webhook_secret.get_secret_value() if settings.webhook_secret else None


async def health(_: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_webhook_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """aiohttp app: Telegram updates on WEBHOOK_PATH, health check on /health."""
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    app = web.Application()
    app.router.add_get("/health", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=webhook_secret()).register(
        app, path=settings.webhook_path
    )
    setup_application(app, dp, bot=bot)
    return app


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    app = create_webhook_app(bot, dp)

    await bot.set_webhook(
        settings.webhook_url,
        secret_token=webhook_secret(),
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host=settings.webapp_host, port=settings.webapp_port).start()
    bot_logger.warning(
        "Webhook server listening on %s:%s", settings.webapp_host, settings.webapp_port
    )

    try:
        await asyncio.Event().wait()  # Run until cancelled (Ctrl+C / SIGTERM)
    finally:
        await runner.cleanup()


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
        await startup_notify(bot)  # Notification that bot was started
        scheduler.start()

        bot_logger.warning("BOT WAS STARTED (%s mode)", settings.bot_mode)
        print_banner((await bot.get_me()).username)

        if settings.bot_mode == "webhook":
            await run_webhook(bot, dp)
        else:
            await run_polling(bot, dp)
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
