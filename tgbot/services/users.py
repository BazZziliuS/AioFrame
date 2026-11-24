from typing import Protocol

from tgbot.database.engine import async_session
from tgbot.database.models import User
from tgbot.database.repositories import UserRepository
from tgbot.services.locale import language_code_to_locale


class TelegramUserLike(Protocol):
    """Fields shared by aiogram `User` (bot updates) and `WebAppUser` (Mini App initData)."""

    @property
    def id(self) -> int: ...
    @property
    def first_name(self) -> str: ...
    @property
    def last_name(self) -> str | None: ...
    @property
    def username(self) -> str | None: ...
    @property
    def language_code(self) -> str | None: ...


def profile_from_telegram(tg_user: TelegramUserLike) -> dict[str, str]:
    """Raw profile values as Telegram sends them (escape only when rendering HTML)."""
    first_name = tg_user.first_name or ""
    last_name = tg_user.last_name or ""
    return {
        "user_login": (tg_user.username or "").lower(),
        "user_name": first_name,
        "user_surname": last_name,
        "user_fullname": f"{first_name} {last_name}".strip(),
        "user_locale": language_code_to_locale(tg_user.language_code),
    }


async def sync_user(tg_user: TelegramUserLike) -> User:
    """Create the user or refresh their profile from Telegram data."""
    profile = profile_from_telegram(tg_user)

    async with async_session() as session:
        repo = UserRepository(session)
        user, created = await repo.get_or_create(tg_user.id, **profile)

        if not created:
            changes: dict[str, object] = {
                key: value for key, value in profile.items() if getattr(user, key) != value
            }
            # The user interacts with the bot again, so they unblocked it
            if user.is_blocked:
                changes["is_blocked"] = False
            await repo.update_profile(user, **changes)

        await session.commit()

    return user
