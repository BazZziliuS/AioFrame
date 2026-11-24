from pydantic import BaseModel, ConfigDict, Field

from webapp.schemas.user import UserOut


class StatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # built from repositories.user.UserStats

    total: int
    new_day: int
    new_week: int
    active: int
    banned: int
    blocked: int


class UsersPage(BaseModel):
    items: list[UserOut]
    total: int
    offset: int
    limit: int


class UserUpdate(BaseModel):
    is_banned: bool


class BotSettingsOut(BaseModel):
    is_maintenance: bool


class BotSettingsUpdate(BaseModel):
    is_maintenance: bool = Field(description="Only admins can use the bot while enabled")
