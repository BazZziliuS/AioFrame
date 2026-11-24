import pytest
from pydantic import ValidationError

from tgbot.config import Settings


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


def test_relative_paths_are_resolved_against_project_root():
    from tgbot.config import PROJECT_ROOT

    s = make_settings(database_url="sqlite+aiosqlite:///data/bot.db", path_logs="logs/bot.log")
    assert s.sqlite_path == (PROJECT_ROOT / "data" / "bot.db").resolve()
    assert s.path_logs == PROJECT_ROOT / "logs" / "bot.log"
    # Other databases are kept as is
    pg = "postgresql+asyncpg://u:p@localhost/db"
    assert make_settings(database_url=pg).database_url == pg


def test_empty_database_settings_fall_back_to_defaults():
    from tgbot.config import DATA_DIR

    s = make_settings(database_url="", path_logs="")
    assert s.sqlite_path is not None and s.sqlite_path.name == "database.db"
    assert s.path_logs == DATA_DIR / "logs.log"
    with pytest.raises(ValidationError, match="SQLAlchemy URL"):
        make_settings(database_url="not a url")


def test_sqlite_path():
    assert make_settings(database_url="sqlite+aiosqlite:///data/bot.db").sqlite_path is not None
    assert make_settings(database_url="sqlite+aiosqlite:///:memory:").sqlite_path is None
    pg = make_settings(database_url="postgresql+asyncpg://u:p@localhost/db")
    assert pg.sqlite_path is None
