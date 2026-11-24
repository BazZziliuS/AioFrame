from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tgbot.config import settings

SQLITE_PRAGMAS = (
    # Readers do not block the writer: the bot, webhook and Mini App work concurrently
    "PRAGMA journal_mode=WAL",
    # Wait for a lock instead of failing at once with "database is locked"
    "PRAGMA busy_timeout=5000",
    # Safe with WAL and much faster than FULL
    "PRAGMA synchronous=NORMAL",
    "PRAGMA foreign_keys=ON",
)


def _configure_sqlite(dbapi_connection: Any, _: Any) -> None:
    cursor = dbapi_connection.cursor()
    for pragma in SQLITE_PRAGMAS:
        cursor.execute(pragma)
    cursor.close()


def create_engine(url: str) -> AsyncEngine:
    is_sqlite = url.startswith("sqlite")
    engine = create_async_engine(url, pool_pre_ping=not is_sqlite)
    if is_sqlite:
        event.listen(engine.sync_engine, "connect", _configure_sqlite)
    return engine


# SQLite: make sure the directory for the database file exists
if settings.sqlite_path is not None:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
