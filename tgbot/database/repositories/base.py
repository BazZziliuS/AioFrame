from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.models import Base


class BaseRepository[Model: Base]:
    model: type[Model]

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, record_id: int) -> Model | None:
        return await self._session.get(self.model, record_id)

    async def get_one(self, **filters) -> Model | None:
        stmt = select(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, **filters) -> Sequence[Model]:
        stmt = select(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, **kwargs) -> Model:
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def update_by(self, filters: dict, **values) -> None:
        stmt = update(self.model).filter_by(**filters).values(**values)
        await self._session.execute(stmt)

    async def delete_by(self, **filters) -> None:
        stmt = delete(self.model).filter_by(**filters)
        await self._session.execute(stmt)
