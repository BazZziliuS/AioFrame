"""Telegram webhook endpoint: verifies the secret token and feeds updates to the dispatcher."""

import asyncio
import logging
import secrets
from typing import Annotated, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status

from tgbot.config import settings

logger = logging.getLogger(__name__)

# Updates are processed in background tasks: keep references until they finish
_update_tasks: set[asyncio.Task[Any]] = set()


def _on_update_done(task: asyncio.Task[Any]) -> None:
    _update_tasks.discard(task)
    if not task.cancelled() and task.exception() is not None:
        logger.error("Update processing failed", exc_info=task.exception())


def register_webhook(app: FastAPI, bot: Bot, dp: Dispatcher) -> None:
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
