from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from tgbot.database.models import User
from tgbot.database.repositories.base import BaseRepository


@dataclass(frozen=True, slots=True)
class UserStats:
    total: int
    new_day: int
    new_week: int
    banned: int
    blocked: int

    @property
    def active(self) -> int:
        """Users who can receive messages (not banned and did not block the bot)."""
        return self.total - self.banned - self.blocked


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_user_id(self, user_id: int) -> User | None:
        return await self.get_one(user_id=user_id)

    async def create_user(
        self,
        user_id: int,
        user_login: str = "",
        user_name: str = "",
        user_surname: str = "",
        user_fullname: str = "",
        user_locale: str = "en_us",
    ) -> User:
        return await self.create(
            user_id=user_id,
            user_login=user_login,
            user_name=user_name,
            user_surname=user_surname,
            user_fullname=user_fullname,
            user_locale=user_locale,
        )

    async def update_user(self, user_id: int, **values: object) -> bool:
        return await self.update_by(filters={"user_id": user_id}, **values) > 0

    async def get_all_users(self) -> Sequence[User]:
        return await self.get_all()

    async def get_reachable_ids(self) -> list[int]:
        """Telegram IDs of users that can receive a broadcast."""
        stmt = select(User.user_id).where(User.is_banned.is_(False), User.is_blocked.is_(False))
        return list((await self._session.scalars(stmt)).all())

    async def set_banned(self, user_id: int, banned: bool) -> bool:
        """Ban or unban a user. Returns False if the user is unknown."""
        return await self.update_user(user_id, is_banned=banned)

    async def set_blocked(self, user_id: int, blocked: bool) -> bool:
        return await self.update_user(user_id, is_blocked=blocked)

    def _since(self, delta: timedelta) -> datetime:
        since = datetime.now(UTC) - delta
        # SQLite stores CURRENT_TIMESTAMP as naive UTC text
        if self._session.bind.dialect.name == "sqlite":
            since = since.replace(tzinfo=None)
        return since

    async def get_stats(self) -> UserStats:
        return UserStats(
            total=await self.count(),
            new_day=await self.count(User.created_at >= self._since(timedelta(days=1))),
            new_week=await self.count(User.created_at >= self._since(timedelta(days=7))),
            banned=await self.count(is_banned=True),
            blocked=await self.count(User.is_banned.is_(False), is_blocked=True),
        )
