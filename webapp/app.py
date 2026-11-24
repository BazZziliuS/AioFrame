"""FastAPI application: Telegram webhook, Mini App API and the built frontend."""

from aiogram import Bot, Dispatcher
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import PlainTextResponse

from tgbot.config import settings
from webapp.api import api_router
from webapp.frontend import register_frontend
from webapp.webhook import register_webhook


def create_app(bot: Bot, dp: Dispatcher) -> FastAPI:
    # Interactive API docs are disabled: the API is private to the Mini App
    app = FastAPI(title="AioFrame", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.bot = bot
    app.state.dp = dp

    # The bundle is ~250 kB: compress it, Mini Apps are often opened on mobile networks
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.get("/health", include_in_schema=False)
    async def health() -> PlainTextResponse:
        return PlainTextResponse("ok")

    if settings.bot_mode == "webhook":
        register_webhook(app, bot, dp)

    if settings.webapp_enabled:
        app.include_router(api_router)

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        include_in_schema=False,
    )
    async def api_not_found(path: str) -> None:
        """Unknown API paths get a JSON 404 instead of the SPA fallback."""
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    if settings.webapp_enabled:
        register_frontend(app)  # catch-all: must be the last route
    return app
