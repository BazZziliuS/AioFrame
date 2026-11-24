from typing import Protocol

from tgbot.database.engine import async_session
from tgbot.database.models import User
from tgbot.database.repositories import UserRepository
from tgbot.services.locale import language_code_to_locale
from tgbot.utils.const_functions import clear_html


class TelegramUserLike(Protocol):
    """Fields shared by aiogram `User` (bot updates) and `WebAppUser` (Mini App initData)."""

    id: int
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None


async def sync_user(tg_user: TelegramUserLike) -> User:
    """Create the user or refresh their profile from Telegram data."""
    user_name = clear_html(tg_user.first_name)
    user_surname = clear_html(tg_user.last_name)
    actual = {
        "user_login": (tg_user.username or "").lower(),
        "user_name": user_name,
        "user_surname": user_surname,
        "user_fullname": f"{user_name} {user_surname}".strip(),
        "user_locale": language_code_to_locale(tg_user.language_code),
    }

    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_user_id(tg_user.id)

        if user is None:
            user = await repo.create_user(user_id=tg_user.id, **actual)
        else:
            changes: dict[str, object] = {
                key: value for key, value in actual.items() if getattr(user, key) != value
            }
            # The user interacts with the bot again, so they unblocked it
            if user.is_blocked:
                changes["is_blocked"] = False

            if changes:
                await repo.update_user(user.user_id, **changes)
                for key, value in changes.items():
                    setattr(user, key, value)

        await session.commit()

    return user
