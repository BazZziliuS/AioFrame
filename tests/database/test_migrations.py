import asyncio
import sqlite3
from datetime import UTC

from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.helpers import DATABASE_URL
from tgbot.database import Base, SettingsRepository, UserRepository, async_session
from tgbot.database.migrations import alembic_config, run_migrations


def _url(path) -> str:
    return f"sqlite+aiosqlite:///{path.as_posix()}"


async def _tables(url: str) -> set[str]:
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
    await engine.dispose()
    return names


async def test_migrations_create_schema_matching_models(tmp_path):
    url = _url(tmp_path / "fresh.db")
    await run_migrations(url)
    assert {"storage_users", "storage_settings", "alembic_version"} <= await _tables(url)

    # `alembic check` fails if models and migrations diverge
    await asyncio.to_thread(command.check, alembic_config(url))


async def test_legacy_create_all_database_is_stamped_and_upgraded(tmp_path):
    """Databases created by the old `create_all()` startup must migrate without errors."""
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE storage_users (
                id INTEGER PRIMARY KEY, user_id BIGINT NOT NULL UNIQUE,
                user_login VARCHAR NOT NULL, user_name VARCHAR NOT NULL,
                user_surname VARCHAR NOT NULL, user_fullname VARCHAR NOT NULL,
                user_locale VARCHAR NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE storage_settings (id INTEGER PRIMARY KEY, status_work BOOLEAN NOT NULL);
            INSERT INTO storage_users (user_id, user_login, user_name, user_surname,
                user_fullname, user_locale)
                VALUES (42, 'ivan', 'Иван &lt;3', '', 'Иван &lt;3', 'ru_ru');
            INSERT INTO storage_settings (status_work) VALUES (1);
            """
        )
    conn.close()

    url = _url(db_path)
    await run_migrations(url)

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        user_query = text(
            "SELECT user_id, is_banned, user_fullname, search_text FROM storage_users"
        )
        user = (await conn.execute(user_query)).one()
        query = text("SELECT id, is_maintenance FROM storage_settings")
        settings_rows = (await conn.execute(query)).all()
    await engine.dispose()

    # Data kept, new flags default to False, escaped names restored, search filled
    assert tuple(user) == (42, 0, "Иван <3", "иван <3 ivan")
    # Unused status_work is reset (maintenance off), the settings row has id=1
    assert [tuple(row) for row in settings_rows] == [(1, 0)]


async def test_downgrade_to_base(tmp_path):
    url = _url(tmp_path / "down.db")
    await run_migrations(url)
    await asyncio.to_thread(command.downgrade, alembic_config(url), "base")
    assert await _tables(url) <= {"alembic_version"}


async def test_settings_row_is_created_by_migration(tmp_path):
    url = _url(tmp_path / "seed.db")
    await run_migrations(url)
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        rows = (await conn.execute(text("SELECT id, is_maintenance FROM storage_settings"))).all()
    await engine.dispose()
    assert [tuple(row) for row in rows] == [(1, 0)]


async def test_migrations_on_configured_database():
    """Full upgrade -> check -> downgrade -> upgrade cycle on the database under test.

    On CI this runs against PostgreSQL (TEST_DATABASE_URL), the rest uses SQLite files.
    """
    from tgbot.database import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

    config = alembic_config(DATABASE_URL)
    await run_migrations(DATABASE_URL)
    await asyncio.to_thread(command.check, config)
    await asyncio.to_thread(command.downgrade, config, "base")
    await asyncio.to_thread(command.upgrade, config, "head")

    async with async_session() as session:
        assert await SettingsRepository(session).is_maintenance() is False
        user, created = await UserRepository(session).get_or_create(1, user_fullname="Тест")
        await session.commit()
    assert created and user.created_at.tzinfo is UTC

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
