import time

import pytest
from pydantic import ValidationError

from tgbot.data.config import Settings
from tgbot.services.locale import Locale, get_translations, language_code_to_locale


################################### CONFIG ###################################
def make_settings(**env: str) -> Settings:
    return Settings(_env_file=None, **{"bot_token": "123:abc", **env})  # type: ignore[arg-type]


def test_admin_ids_parsed_from_comma_separated_string():
    assert make_settings(admin_ids="1, 2,3,").admin_ids == [1, 2, 3]
    assert make_settings(admin_ids="").admin_ids == []


def test_invalid_admin_id_fails_fast():
    with pytest.raises(ValidationError):
        make_settings(admin_ids="1,abc")


@pytest.mark.parametrize("token", ["", "abc", "123:", ":abc"])
def test_invalid_token_fails_fast(token):
    with pytest.raises(ValidationError, match="BOT_TOKEN"):
        make_settings(bot_token=token)


def test_unknown_timezone_fails_fast():
    with pytest.raises(ValidationError, match="timezone"):
        make_settings(bot_timezone="Mars/Olympus")


def test_webhook_mode_requires_url():
    with pytest.raises(ValidationError, match="WEBHOOK_BASE_URL"):
        make_settings(bot_mode="webhook")

    s = make_settings(bot_mode="webhook", webhook_base_url="https://x.io/", webhook_path="hook")
    assert s.webhook_url == "https://x.io/hook"


def test_webapp_switch_requires_https_url():
    off = make_settings(webapp_enabled="false", webapp_url="")
    assert off.web_server_enabled is False
    with pytest.raises(ValidationError, match="WEBAPP_URL is required"):
        make_settings(webapp_enabled="true", webapp_url="")
    with pytest.raises(ValidationError, match="https"):
        make_settings(webapp_enabled="true", webapp_url="http://insecure.test")
    s = make_settings(webapp_enabled="true", webapp_url="https://app.test")
    assert s.web_server_enabled is True


def test_empty_optional_values_become_none():
    s = make_settings(redis_url="", webhook_secret=" ")
    assert s.redis_url is None
    assert s.webhook_secret is None


def test_sqlite_path():
    assert make_settings(database_url="sqlite+aiosqlite:///data/bot.db").sqlite_path is not None
    assert make_settings(database_url="sqlite+aiosqlite:///:memory:").sqlite_path is None
    pg = make_settings(database_url="postgresql+asyncpg://u:p@localhost/db")
    assert pg.sqlite_path is None


################################### LOCALE ###################################
def test_locale_format_and_fallback():
    ru = Locale("ru_ru")
    assert ru("start.greeting", user_name="Иван").startswith("🔸 Привет, Иван")
    assert ru("no.such.key") == "no.such.key"
    assert Locale("xx_xx")("menu.user_button") == "User button"  # unknown locale -> default


def test_all_locales_have_the_same_keys():
    import json

    from tgbot.services.locale import LOCALES_DIR

    def keys(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                yield from keys(value, f"{prefix}{key}.")
            else:
                yield f"{prefix}{key}"

    files = sorted(LOCALES_DIR.glob("*.json"))
    reference = set(keys(json.loads(files[0].read_text(encoding="utf-8"))))
    for file in files[1:]:
        assert set(keys(json.loads(file.read_text(encoding="utf-8")))) == reference, file.name


def test_translations_cover_all_languages():
    assert get_translations("menu.admin_button") == {"Admin button", "Админ панель"}


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("ru", "ru_ru"),
        ("en", "en_us"),
        ("RU", "ru_ru"),
        ("en-GB", "en_us"),
        ("de", "en_us"),
        (None, "en_us"),
    ],
)
def test_language_code_to_locale(code, expected):
    assert language_code_to_locale(code) == expected


################################# THROTTLING #################################
async def test_throttling_escalation_warns_once(monkeypatch):
    from aiogram.types import User

    from tgbot.middlewares.middleware_throttling import ThrottlingMiddleware

    clock = [1000.0]
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])

    replies: list[str] = []

    class FakeMessage:
        async def reply(self, text):
            replies.append(text)

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

    from tgbot.middlewares.middleware_throttling import ThrottlingMiddleware

    calls = 0

    async def handler(event, data):
        nonlocal calls
        calls += 1

    middleware = ThrottlingMiddleware(default_rate=0)
    data = {"event_from_user": User(id=8, is_bot=False, first_name="x")}
    for _ in range(10):
        await middleware(handler, object(), data)
    assert calls == 10
