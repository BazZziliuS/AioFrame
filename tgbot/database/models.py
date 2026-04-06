from datetime import datetime

from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, func
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
    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    user_login: Mapped[str] = mapped_column(String, default="")
    user_name: Mapped[str] = mapped_column(String, default="")
    user_surname: Mapped[str] = mapped_column(String, default="")
    user_fullname: Mapped[str] = mapped_column(String, default="")
    user_locale: Mapped[str] = mapped_column(String, default="en_us")

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, login={self.user_login})>"


class Settings(Base):
    __tablename__ = "storage_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_work: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Settings(status_work={self.status_work})>"
