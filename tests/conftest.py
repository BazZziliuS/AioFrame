import os
import tempfile
from pathlib import Path

# Configure the bot BEFORE any `tgbot` import: settings are read at import time.
# Tests run on SQLite; set TEST_DATABASE_URL to run them on another database (PostgreSQL).
_TMP = Path(tempfile.mkdtemp(prefix="aioframe-tests-"))
DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or (
    f"sqlite+aiosqlite:///{(_TMP / 'bot.db').as_posix()}"
)
os.environ.update(
    {
        "BOT_TOKEN": "123456:TEST-TOKEN",
        "ADMIN_IDS": "1",
        "DATABASE_URL": DATABASE_URL,
        "PATH_LOGS": str(_TMP / "logs.log"),
        "REDIS_URL": "",
        "BOT_MODE": "polling",
        "THROTTLE_RATE": "0",  # anti-spam is tested separately
        "BROADCAST_RATE": "1000",
        "BOT_STATUS_NOTIFICATION": "true",
        "WEBAPP_ENABLED": "true",
        "WEBAPP_URL": "https://app.test",
        "CAPTCHA_ENABLED": "true",
        "CAPTCHA_COST": "1000",  # fast solving in tests
    }
)

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from tests.helpers import FakeSession, TgClient  # noqa: E402
from tgbot.database import Base, engine  # noqa: E402
from tgbot.logger import setup_logging  # noqa: E402

setup_logging()


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
    from tgbot.bot import create_dispatcher
    from tgbot.services.http import HttpClient

    return create_dispatcher(HttpClient())


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


@pytest.fixture
async def api(tg):
    """HTTP client for the FastAPI app (Mini App API, webhook, frontend)."""
    from webapp.app import create_app

    app = create_app(tg.bot, tg.dp)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
