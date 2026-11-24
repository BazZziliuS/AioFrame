import uvicorn
from aiogram import Bot, Dispatcher

from tgbot.config import settings
from webapp.app import create_app


def create_web_server(bot: Bot, dp: Dispatcher) -> uvicorn.Server:
    """FastAPI app (webhook + Mini App) served by uvicorn inside the bot's event loop."""
    config = uvicorn.Config(
        create_app(bot, dp),
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_config=None,  # use the bot's logging setup
        access_log=False,
        lifespan="off",  # the bot lifecycle is managed by main()
    )
    return uvicorn.Server(config)
