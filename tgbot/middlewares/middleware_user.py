from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from tgbot.database.engine import async_session
from tgbot.database.repositories import UserRepository
from tgbot.services.locale import Locale, language_code_to_locale
from tgbot.utils.const_functions import clear_html


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

        user_name = clear_html(this_user.first_name)
        user_surname = clear_html(this_user.last_name)
        actual = {
            "user_login": (this_user.username or "").lower(),
            "user_name": user_name,
            "user_surname": user_surname,
            "user_fullname": f"{user_name} {user_surname}".strip(),
            "user_locale": language_code_to_locale(this_user.language_code),
        }

        async with async_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_user_id(this_user.id)

            if user is None:
                user = await repo.create_user(user_id=this_user.id, **actual)
            else:
                changes = {
                    key: value for key, value in actual.items() if getattr(user, key) != value
                }
                # The user writes to the bot again, so they unblocked it
                if user.is_blocked:
                    changes["is_blocked"] = False

                if changes:
                    await repo.update_user(user.user_id, **changes)
                    for key, value in changes.items():
                        setattr(user, key, value)

            await session.commit()

        data["User"] = user
        data["locale"] = Locale(user.user_locale)

        return await handler(event, data)
