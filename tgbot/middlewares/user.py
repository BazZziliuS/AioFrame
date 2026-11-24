from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from tgbot.services.locale import Locale
from tgbot.services.users import sync_user


class UserMiddleware(BaseMiddleware):
    """Creates or refreshes the user in the database.

    Injects into handler data:
    - `db_user`: the database model (`tgbot.database.models.User`)
    - `locale`: translations in the user's language
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")

        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        db_user = await sync_user(tg_user)
        data["db_user"] = db_user
        data["locale"] = Locale(db_user.user_locale)

        return await handler(event, data)
