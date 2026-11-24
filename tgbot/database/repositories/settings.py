from typing import Any

from tgbot.database.models import Settings
from tgbot.database.repositories.base import BaseRepository

SETTINGS_ID = 1  # the single settings row, created by a migration


class SettingsRepository(BaseRepository[Settings]):
    model = Settings

    async def get_settings(self) -> Settings:
        settings = await self.get_by_id(SETTINGS_ID)
        if settings is None:  # databases created without migrations (e.g. tests)
            settings = await self.create(id=SETTINGS_ID, is_maintenance=False)
        return settings

    async def update_settings(self, **values: Any) -> None:
        await self.get_settings()
        await self.update_by(filters={"id": SETTINGS_ID}, **values)

    async def is_maintenance(self) -> bool:
        return (await self.get_settings()).is_maintenance

    async def set_maintenance(self, enabled: bool) -> None:
        await self.update_settings(is_maintenance=enabled)
