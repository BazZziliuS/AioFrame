from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from tgbot.data.config import settings

# SQLite: make sure the directory for the database file exists
if settings.sqlite_path is not None:
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
