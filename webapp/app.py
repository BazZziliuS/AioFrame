"""Web server: Telegram webhook, Mini App API and the built frontend (one process with the bot)."""

import asyncio
import secrets
from pathlib import Path
from typing import Annotated, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import FileResponse, PlainTextResponse

from tgbot.data.config import settings
from tgbot.utils.misc.bot_logging import bot_logger
from webapp.routers import admin, me

STATIC_DIR = Path(__file__).resolve().parent / "static"  # `npm run build` output

# Webhook updates are processed in background tasks: keep references until done
_update_tasks: set[asyncio.Task[Any]] = set()


def _on_update_done(task: asyncio.Task[Any]) -> None:
    _update_tasks.discard(task)
    if not task.cancelled() and task.exception() is not None:
        bot_logger.error("Update processing failed", exc_info=task.exception())


def _add_webhook_route(app: FastAPI, bot: Bot, dp: Dispatcher) -> None:
    secret = settings.webhook_secret.get_secret_value() if settings.webhook_secret else None

    @app.post(settings.webhook_path, include_in_schema=False)
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
    ) -> dict[str, bool]:
        if secret and not secrets.compare_digest(x_telegram_bot_api_secret_token or "", secret):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)

        update = Update.model_validate(await request.json(), context={"bot": bot})
        # Answer Telegram immediately, handle the update in background
        task = asyncio.create_task(dp.feed_update(bot, update))
        _update_tasks.add(task)
        task.add_done_callback(_on_update_done)
        return {"ok": True}


def _add_frontend_routes(app: FastAPI) -> None:
    """Serve the built React app; unknown paths fall back to index.html (SPA routing)."""

    @app.get("/{path:path}", include_in_schema=False, response_model=None)
    async def frontend(path: str) -> FileResponse | PlainTextResponse:
        index = STATIC_DIR / "index.html"
        if not index.is_file():
            return PlainTextResponse(
                "Frontend is not built: run `npm run build` in frontend/",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        file = (STATIC_DIR / path).resolve()
        if path and file.is_file() and file.is_relative_to(STATIC_DIR):
            # Hashed assets never change, index.html must always be fresh
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else None
            return FileResponse(file, headers={"Cache-Control": cache} if cache else None)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})


def create_app(bot: Bot, dp: Dispatcher) -> FastAPI:
    # Interactive API docs are disabled: the API is private to the Mini App
    app = FastAPI(title="AioFrame", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.bot = bot
    app.state.dp = dp

    @app.get("/health", include_in_schema=False)
    async def health() -> PlainTextResponse:
        return PlainTextResponse("ok")

    if settings.bot_mode == "webhook":
        _add_webhook_route(app, bot, dp)

    app.include_router(me.router)
    app.include_router(admin.router)

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        include_in_schema=False,
    )
    async def api_not_found(path: str) -> None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    _add_frontend_routes(app)  # must be the last: catch-all route
    return app
