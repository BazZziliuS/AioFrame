from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, false, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "storage_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    user_login: Mapped[str] = mapped_column(String, default="")
    user_name: Mapped[str] = mapped_column(String, default="")
    user_surname: Mapped[str] = mapped_column(String, default="")
    user_fullname: Mapped[str] = mapped_column(String, default="")
    user_locale: Mapped[str] = mapped_column(String, default="en_us")
    # Banned by an admin: all updates from the user are ignored
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # The user blocked the bot (detected during broadcasts)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, login={self.user_login})>"


class Settings(Base):
    __tablename__ = "storage_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Maintenance mode: the bot answers only to admins
    is_maintenance: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    def __repr__(self) -> str:
        return f"<Settings(is_maintenance={self.is_maintenance})>"
