import os
import tempfile
from pathlib import Path

# Configure the bot BEFORE any `tgbot` import: settings are read at import time
_TMP = Path(tempfile.mkdtemp(prefix="aioframe-tests-"))
os.environ.update(
    {
        "BOT_TOKEN": "123456:TEST-TOKEN",
        "ADMIN_IDS": "1",
        "DATABASE_URL": f"sqlite+aiosqlite:///{(_TMP / 'bot.db').as_posix()}",
        "PATH_LOGS": str(_TMP / "logs.log"),
        "REDIS_URL": "",
        "BOT_MODE": "polling",
        "THROTTLE_RATE": "0",  # anti-spam is tested separately
        "BROADCAST_RATE": "1000",
        "BOT_STATUS_NOTIFICATION": "true",
    }
)

import pytest  # noqa: E402

from tests.helpers import FakeSession, TgClient  # noqa: E402
from tgbot.database import Base, engine  # noqa: E402

ADMIN_ID = 1


@pytest.fixture
def tmp_dir() -> Path:
    return _TMP


@pytest.fixture(autouse=True)
async def db():
    """Fresh schema for every test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture(scope="session")
def dispatcher():
    """Routers are module-level singletons, so the dispatcher is built once."""
    from main import create_dispatcher
    from tgbot.services.api_session import AsyncRequestSession

    return create_dispatcher(AsyncRequestSession())


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


@pytest.fixture
async def tg(dispatcher, session):
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties

    bot = Bot("123456:TEST-TOKEN", session=session, default=DefaultBotProperties(parse_mode="HTML"))
    client = TgClient(dispatcher, bot, session)
    yield client
    await client.reset_states()
