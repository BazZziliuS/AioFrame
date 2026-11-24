from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import CursorResult, Insert, insert, or_, select
from sqlalchemy.dialects import postgresql, sqlite

from tgbot.database.models import User
from tgbot.database.repositories.base import BaseRepository

PROFILE_FIELDS = ("user_login", "user_name", "user_surname", "user_fullname", "user_locale")


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

    def _insert_ignoring_duplicates(self, values: dict[str, Any]) -> Insert:
        """INSERT that does nothing if the user already exists (concurrent first updates)."""
        dialect = self._session.get_bind().dialect.name
        if dialect == "postgresql":
            return (
                postgresql.insert(User)
                .values(values)
                .on_conflict_do_nothing(index_elements=[User.user_id])
            )
        if dialect == "sqlite":
            return (
                sqlite.insert(User)
                .values(values)
                .on_conflict_do_nothing(index_elements=[User.user_id])
            )
        return insert(User).values(values)

    async def get_or_create(self, user_id: int, **profile: str) -> tuple[User, bool]:
        """Return the user, creating it if needed. Safe when called concurrently.

        Returns (user, created).
        """
        user = await self.get_by_user_id(user_id)
        if user is not None:
            return user, False

        values = {"user_id": user_id, **profile}
        values["search_text"] = User.build_search_text(
            profile.get("user_fullname", ""), profile.get("user_login", "")
        )
        statement = self._insert_ignoring_duplicates(values)
        result = cast(CursorResult[Any], await self._session.execute(statement))
        user = await self.get_by_user_id(user_id)
        if user is None:  # pragma: no cover - the row exists after the INSERT
            raise RuntimeError(f"User {user_id} was not created")
        return user, bool(result.rowcount)

    async def create_user(self, user_id: int, **profile: str) -> User:
        user, _ = await self.get_or_create(user_id, **profile)
        return user

    async def update_profile(self, user: User, **changes: Any) -> None:
        """Apply changes to the user (and the search index when names change)."""
        if not changes:
            return
        if {"user_fullname", "user_login"} & changes.keys():
            changes["search_text"] = User.build_search_text(
                changes.get("user_fullname", user.user_fullname),
                changes.get("user_login", user.user_login),
            )
        await self.update_by(filters={"user_id": user.user_id}, **changes)
        for key, value in changes.items():
            setattr(user, key, value)

    async def update_user(self, user_id: int, **values: Any) -> bool:
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

    async def get_stats(self) -> UserStats:
        now = datetime.now(UTC)
        return UserStats(
            total=await self.count(),
            new_day=await self.count(User.created_at >= now - timedelta(days=1)),
            new_week=await self.count(User.created_at >= now - timedelta(days=7)),
            banned=await self.count(is_banned=True),
            blocked=await self.count(User.is_banned.is_(False), is_blocked=True),
        )

    async def search(
        self, query: str = "", *, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[User], int]:
        """Users matching name / @login / Telegram ID, newest first, plus the total count."""
        conditions = []
        query = query.strip().lstrip("@").lower()
        if query:
            matches = [User.search_text.contains(query, autoescape=True)]
            if query.isdigit():
                matches.append(User.user_id == int(query))
            conditions.append(or_(*matches))

        stmt = (
            select(User)
            .where(*conditions)
            .order_by(User.created_at.desc(), User.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = (await self._session.scalars(stmt)).all()
        return items, await self.count(*conditions)
