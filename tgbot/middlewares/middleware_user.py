from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from tgbot.services.locale import Locale
from tgbot.services.users import sync_user


class ExistsUserMiddleware(BaseMiddleware):
    """Creates or refreshes the user in the database.

    Injects `User` (database model) and `locale` into handler data.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        this_user: TgUser | None = data.get("event_from_user")

        if this_user is None or this_user.is_bot:
            return await handler(event, data)

        user = await sync_user(this_user)
        data["User"] = user
        data["locale"] = Locale(user.user_locale)

        return await handler(event, data)
