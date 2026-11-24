from typing import Any

from tgbot.database.models import Settings
from tgbot.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    model = Settings

    async def get_settings(self) -> Settings:
        settings = await self.get_one()
        if settings is None:
            settings = await self.create(is_maintenance=False)
        return settings

    async def update_settings(self, **values: Any) -> None:
        settings = await self.get_settings()
        await self.update_by(filters={"id": settings.id}, **values)

    async def is_maintenance(self) -> bool:
        return (await self.get_settings()).is_maintenance

    async def set_maintenance(self, enabled: bool) -> None:
        await self.update_settings(is_maintenance=enabled)
