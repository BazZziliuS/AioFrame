import asyncio
import sqlite3

from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from tgbot.database import SettingsRepository, UserRepository, async_session
from tgbot.database.migrations import _alembic_config, run_migrations


async def test_user_repository_and_stats():
    async with async_session() as session:
        repo = UserRepository(session)
        for user_id in (10, 11, 12, 13):
            await repo.create_user(user_id=user_id, user_name=f"u{user_id}")
        assert await repo.set_banned(11, True)
        assert await repo.set_blocked(12, True)
        assert not await repo.set_banned(999, True)  # unknown user
        await session.commit()

    async with async_session() as session:
        repo = UserRepository(session)
        stats = await repo.get_stats()
        assert (stats.total, stats.banned, stats.blocked, stats.active) == (4, 1, 1, 2)
        assert stats.new_day == 4 and stats.new_week == 4
        assert sorted(await repo.get_reachable_ids()) == [10, 13]


async def test_settings_maintenance_toggle():
    async with async_session() as session:
        repo = SettingsRepository(session)
        assert await repo.is_maintenance() is False
        await repo.set_maintenance(True)
        await session.commit()

    async with async_session() as session:
        assert await SettingsRepository(session).is_maintenance() is True


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
    await asyncio.to_thread(command.check, _alembic_config(url))


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
                user_fullname, user_locale) VALUES (42, 'x', 'X', '', 'X', 'ru_ru');
            INSERT INTO storage_settings (status_work) VALUES (1);
            """
        )
    conn.close()

    url = _url(db_path)
    await run_migrations(url)

    engine = create_async_engine(url)
    async with engine.connect() as conn:
        user = (await conn.execute(text("SELECT user_id, is_banned FROM storage_users"))).one()
        query = text("SELECT is_maintenance FROM storage_settings")
        maintenance = (await conn.execute(query)).scalar()
    await engine.dispose()

    assert tuple(user) == (42, 0)  # data kept, new column defaults to False
    assert maintenance == 0  # unused status_work is reset: maintenance is off


async def test_downgrade_to_base(tmp_path):
    url = _url(tmp_path / "down.db")
    await run_migrations(url)
    await asyncio.to_thread(command.downgrade, _alembic_config(url), "base")
    assert await _tables(url) <= {"alembic_version"}
