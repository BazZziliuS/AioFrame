from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Dialect, Integer, String, false, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware UTC datetime on every database.

    PostgreSQL stores `timestamptz` natively. SQLite has no time zones: values are stored
    as naive UTC (like its CURRENT_TIMESTAMP) and get `tzinfo=UTC` back when loaded.
    Without this, SQLite returns naive datetimes that clients treat as local time.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetime: use datetime.now(UTC)")
        value = value.astimezone(UTC)
        return value.replace(tzinfo=None) if dialect.name == "sqlite" else value

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=func.now(),
        index=True,  # statistics and "newest first" lists
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "storage_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    # Raw Telegram values: escape them when building HTML messages (tgbot.utils.text.escape)
    user_login: Mapped[str] = mapped_column(String, default="")
    user_name: Mapped[str] = mapped_column(String, default="")
    user_surname: Mapped[str] = mapped_column(String, default="")
    user_fullname: Mapped[str] = mapped_column(String, default="")
    user_locale: Mapped[str] = mapped_column(String, default="en_us")
    # Lowercased "fullname login" for case-insensitive search: SQLite lower() is ASCII-only
    search_text: Mapped[str] = mapped_column(String, default="", server_default="")
    # Banned by an admin: all updates from the user are ignored
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # The user blocked the bot (detected during broadcasts)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    @staticmethod
    def build_search_text(fullname: str, login: str) -> str:
        return f"{fullname} {login}".strip().lower()

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, login={self.user_login})>"


class Settings(Base):
    """Bot-wide settings: a single row with id=1 (created by the migration)."""

    __tablename__ = "storage_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Maintenance mode: the bot answers only to admins
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    def __repr__(self) -> str:
        return f"<Settings(is_maintenance={self.is_maintenance})>"
