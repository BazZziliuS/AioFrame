from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from tgbot.config import settings
from tgbot.database.engine import async_session
from tgbot.database.models import User as UserModel
from tgbot.database.repositories import SettingsRepository
from tgbot.services.locale import Locale


class AccessMiddleware(BaseMiddleware):
    """Drops updates from banned users and closes the bot during maintenance.

    Admins are never affected. Must be registered after `UserMiddleware`.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        db_user: UserModel | None = data.get("db_user")

        if tg_user is None or db_user is None or settings.is_admin(tg_user.id):
            return await handler(event, data)

        # Banned: ignore silently (only stop the loading spinner on buttons)
        if db_user.is_banned:
            if isinstance(event, CallbackQuery):
                await event.answer()
            return None

        async with async_session() as session:
            is_maintenance = await SettingsRepository(session).is_maintenance()

        if is_maintenance:
            locale: Locale = data["locale"]
            text = locale("access.maintenance")
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(text)
            return None

        return await handler(event, data)
