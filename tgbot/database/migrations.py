import asyncio
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, pool
from sqlalchemy.ext.asyncio import create_async_engine

from tgbot.config import PROJECT_ROOT, settings

logger = logging.getLogger(__name__)

# Schema created by the old `Base.metadata.create_all()` startup corresponds to this revision
LEGACY_CREATE_ALL_REVISION = "b29ddd50d53e"


def alembic_config(database_url: str) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    config.attributes["database_url"] = database_url
    config.attributes["configure_logger"] = False
    return config


async def _table_names(database_url: str) -> set[str]:
    engine = create_async_engine(database_url, poolclass=pool.NullPool)
    try:
        async with engine.connect() as connection:
            return set(await connection.run_sync(lambda conn: inspect(conn).get_table_names()))
    finally:
        await engine.dispose()


async def run_migrations(database_url: str | None = None) -> None:
    """Bring the database schema up to date (`alembic upgrade head`).

    Databases created before migrations were applied on startup (tables exist,
    but there is no `alembic_version`) are stamped first, so upgrade does not
    try to create existing tables again.
    """
    database_url = database_url or settings.database_url
    config = alembic_config(database_url)

    tables = await _table_names(database_url)
    if "storage_users" in tables and "alembic_version" not in tables:
        logger.warning("Legacy database without alembic_version found, stamping it")
        await asyncio.to_thread(command.stamp, config, LEGACY_CREATE_ALL_REVISION)

    # Alembic's env.py runs its own event loop, so it must live in a separate thread
    await asyncio.to_thread(command.upgrade, config, "head")
