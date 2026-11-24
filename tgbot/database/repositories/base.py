from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.models import Base


class BaseRepository[Model: Base]:
    model: type[Model]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, record_id: int) -> Model | None:
        return await self._session.get(self.model, record_id)

    async def get_one(self, **filters: Any) -> Model | None:
        stmt = select(self.model).filter_by(**filters).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **filters: Any) -> Sequence[Model]:
        stmt = select(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count(self, *where: Any, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).where(*where).filter_by(**filters)
        return int(await self._session.scalar(stmt) or 0)

    async def create(self, **kwargs: Any) -> Model:
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def update_by(self, filters: dict[str, Any], **values: Any) -> int:
        """Update matching rows and return how many were changed."""
        stmt = update(self.model).filter_by(**filters).values(**values)
        result = cast(CursorResult[Any], await self._session.execute(stmt))
        return result.rowcount

    async def delete_by(self, **filters: Any) -> int:
        """Delete matching rows and return how many were removed."""
        stmt = delete(self.model).filter_by(**filters)
        result = cast(CursorResult[Any], await self._session.execute(stmt))
        return result.rowcount
