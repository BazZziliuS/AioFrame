import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import text

from tests.helpers import sqlite_only
from tgbot.database import SettingsRepository, UserRepository, async_session


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


async def test_dates_are_timezone_aware_utc():
    async with async_session() as session:
        await UserRepository(session).create_user(user_id=20)
        await session.commit()
    async with async_session() as session:
        loaded = await UserRepository(session).get_by_user_id(20)
    assert loaded is not None
    assert loaded.created_at.tzinfo is UTC
    assert abs((datetime.now(UTC) - loaded.created_at).total_seconds()) < 60


async def test_search_is_case_insensitive_for_any_alphabet():
    async with async_session() as session:
        repo = UserRepository(session)
        await repo.create_user(user_id=30, user_fullname="Иван Петров", user_login="ivan_p")
        await repo.create_user(user_id=31, user_fullname="100% Real", user_login="")
        await session.commit()

        for query in ("иван", "ИВАН", "петров", "@IVAN_P", "30"):
            items, _ = await repo.search(query)
            assert [u.user_id for u in items] == [30], query
        # LIKE wildcards in the query are literal characters
        assert [u.user_id for u in (await repo.search("100%"))[0]] == [31]
        assert (await repo.search("%"))[1] == 1


async def test_search_index_follows_profile_changes():
    async with async_session() as session:
        repo = UserRepository(session)
        user = await repo.create_user(user_id=40, user_fullname="Old Name", user_login="old")
        await repo.update_profile(user, user_fullname="Новое Имя")
        await session.commit()
        assert [u.user_id for u in (await repo.search("новое"))[0]] == [40]
        assert (await repo.search("old name"))[1] == 0


async def test_concurrent_first_contact_creates_one_user():
    from tgbot.services.users import sync_user

    tg_user = SimpleNamespace(
        id=50, first_name="Race", last_name=None, username=None, language_code="en"
    )
    results = await asyncio.gather(*(sync_user(tg_user) for _ in range(10)))
    assert {user.user_id for user in results} == {50}
    async with async_session() as session:
        assert await UserRepository(session).count(user_id=50) == 1


async def test_names_are_stored_raw():
    from tgbot.services.users import sync_user

    tg_user = SimpleNamespace(
        id=60, first_name="A&B", last_name="<x>", username="Name", language_code="ru"
    )
    user = await sync_user(tg_user)
    assert (user.user_fullname, user.user_login) == ("A&B <x>", "name")


@sqlite_only
async def test_sqlite_runs_in_wal_mode():
    from tgbot.database import engine

    async with engine.connect() as conn:
        mode = (await conn.execute(text("PRAGMA journal_mode"))).scalar()
        timeout = (await conn.execute(text("PRAGMA busy_timeout"))).scalar()
    assert (mode, timeout) == ("wal", 5000)
