"""Entry point: prepares the database, starts the bot (polling or webhook) and the web server."""

import asyncio
import logging
from contextlib import suppress

import colorama
from aiogram import Bot, Dispatcher

from tgbot.bot import (
    create_bot,
    create_dispatcher,
    create_scheduler,
    set_commands,
    setup_menu_button,
)
from tgbot.config import settings
from tgbot.database import SettingsRepository, async_session, engine
from tgbot.database.migrations import run_migrations
from tgbot.logger import setup_logging
from tgbot.services.http import HttpClient
from tgbot.services.notifications import notify_admins_started

logger = logging.getLogger(__name__)


async def prepare_database() -> None:
    if settings.uses_legacy_data_dir:
        logger.warning(
            "Using the database in tgbot/data/ (older layout). "
            "Move it to data/database.db or set DATABASE_URL explicitly."
        )
    await run_migrations()  # alembic upgrade head

    async with async_session() as session:
        await SettingsRepository(session).get_settings()
        await session.commit()


async def run_bot(bot: Bot, dp: Dispatcher) -> None:
    """Receive updates by polling or webhook; run the web server when it is needed."""
    from webapp.server import create_web_server

    allowed_updates = dp.resolve_used_update_types()
    server = create_web_server(bot, dp) if settings.web_server_enabled else None

    if settings.bot_mode == "webhook":
        assert server is not None  # webhook mode always enables the web server
        secret = settings.webhook_secret.get_secret_value() if settings.webhook_secret else None
        await bot.set_webhook(
            settings.webhook_url,
            secret_token=secret,
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
    colorama.init()
    print(colorama.Fore.LIGHTYELLOW_EX + f"~~~~~ Bot was started - @{username} ~~~~~")
    print(colorama.Fore.LIGHTBLUE_EX + "~~~~~ TG developer - @BazZziliuS ~~~~~")
    print(colorama.Fore.RESET)

    if not settings.admin_ids:
        print("***** ENTER ADMIN_IDS IN .env *****")


async def main() -> None:
    await prepare_database()

    http_client = HttpClient()
    bot = create_bot()
    dp = create_dispatcher(http_client)
    scheduler = create_scheduler(bot)

    try:
        await set_commands(bot)
        await setup_menu_button(bot)
        await notify_admins_started(bot)
        scheduler.start()

        logger.warning("Bot started (%s mode)", settings.bot_mode)
        if settings.web_server_enabled:
            logger.warning(
                "Web server on %s:%s (Mini App: %s)",
                settings.webapp_host,
                settings.webapp_port,
                settings.webapp_url if settings.webapp_enabled else "disabled",
            )
        print_banner((await bot.get_me()).username)

        await run_bot(bot, dp)
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await http_client.close()
        await dp.storage.close()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.exception("Bot crashed")
        raise
    finally:
        logger.warning("Bot stopped")
