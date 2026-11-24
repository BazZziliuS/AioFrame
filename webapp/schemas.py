from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from tgbot.database.models import User


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_login: str
    user_fullname: str
    user_locale: str
    is_banned: bool
    is_blocked: bool
    created_at: datetime


class MeOut(BaseModel):
    user: UserOut
    is_admin: bool
    photo_url: str | None = None

    @classmethod
    def build(cls, user: User, *, is_admin: bool, photo_url: str | None) -> MeOut:
        return cls(user=UserOut.model_validate(user), is_admin=is_admin, photo_url=photo_url)


class StatsOut(BaseModel):
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
