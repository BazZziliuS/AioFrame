from tgbot.database.models import Settings
from tgbot.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    model = Settings

    async def get_settings(self) -> Settings:
        settings = await self.get_one()
        if settings is None:
            settings = await self.create(status_work=False)
        return settings

    async def update_settings(self, **values) -> None:
        settings = await self.get_settings()
        await self.update_by(filters={"id": settings.id}, **values)
