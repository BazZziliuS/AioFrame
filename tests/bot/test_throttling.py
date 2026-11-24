import time

from tgbot.config import Settings
from tgbot.services.locale import Locale


################################### CONFIG ###################################
def make_settings(**env: str) -> Settings:
    return Settings(_env_file=None, **{"bot_token": "123:abc", **env})  # type: ignore[arg-type]


async def test_throttling_escalation_warns_once(monkeypatch):
    from unittest.mock import AsyncMock, Mock

    from aiogram.types import Message, User

    from tgbot.middlewares.throttling import ThrottlingMiddleware

    clock = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])

    replies: list[str] = []

    def FakeMessage() -> Mock:
        message = Mock(spec=Message)
        message.reply = AsyncMock(side_effect=lambda text: replies.append(text))
        return message

    handled = 0

    async def handler(event, data):
        nonlocal handled
        handled += 1

    middleware = ThrottlingMiddleware(default_rate=0.5)
    data = {"event_from_user": User(id=7, is_bot=False, first_name="x"), "locale": Locale()}

    for _ in range(5):  # burst: 3 pass, 4th warned, 5th silently dropped
        await middleware(handler, FakeMessage(), data)
    assert handled == 3
    assert replies == [Locale()("throttling.spam_warning")]

    clock[0] += 60  # cooldown passed
    await middleware(handler, FakeMessage(), data)
    assert handled == 4


async def test_throttling_disabled_with_zero_rate():
    from aiogram.types import User

    from tgbot.middlewares.throttling import ThrottlingMiddleware

    calls = 0

    async def handler(event, data):
        nonlocal calls
        calls += 1

    middleware = ThrottlingMiddleware(default_rate=0)
    data = {"event_from_user": User(id=8, is_bot=False, first_name="x")}
    for _ in range(10):
        await middleware(handler, object(), data)
    assert calls == 10
