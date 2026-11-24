from pathlib import Path
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"  # runtime files: database, logs
LEGACY_DATA_DIR = PROJECT_ROOT / "tgbot" / "data"  # location used by older versions


def _default_database_url() -> str:
    """SQLite in data/, or the database of an older version if it was never moved."""
    legacy, current = LEGACY_DATA_DIR / "database.db", DATA_DIR / "database.db"
    path = legacy if legacy.is_file() and not current.exists() else current
    return f"sqlite+aiosqlite:///{path.as_posix()}"


class Settings(BaseSettings):
    """Bot configuration from environment variables and `.env`.

    Real environment variables take priority over the `.env` file.
    Invalid values fail fast at startup with a readable error.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: SecretStr
    admin_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    # Storage
    database_url: str = Field(default_factory=_default_database_url)
    redis_url: str | None = None  # FSM storage; in-memory when empty

    # Logging
    path_logs: Path = DATA_DIR / "logs.log"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Behaviour
    bot_timezone: str = "Europe/Moscow"
    bot_status_notification: bool = True
    autobackup_hour: int = Field(default=0, ge=0, le=23)
    throttle_rate: float = Field(default=0.5, ge=0)  # seconds; 0 disables anti-spam
    broadcast_rate: float = Field(default=25, gt=0)  # messages per second

    # Run mode
    bot_mode: Literal["polling", "webhook"] = "polling"
    webhook_base_url: str | None = None  # e.g. https://bot.example.com
    webhook_path: str = "/webhook"
    webhook_secret: SecretStr | None = None
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080

    # Telegram Mini App (served by the same web server)
    webapp_enabled: bool = False  # Mini App: API, frontend and the chat menu button
    webapp_url: str | None = None  # public HTTPS URL of the Mini App
    webapp_auth_ttl: int = Field(default=24 * 3600, gt=0)  # max age of initData, seconds

    # Captcha for sensitive Mini App actions (proof-of-work, no third-party service)
    captcha_enabled: bool = True
    captcha_secret: SecretStr | None = None  # HMAC key; derived from BOT_TOKEN when empty
    captcha_cost: int = Field(default=5000, ge=1000)  # work per attempt: higher = slower to solve
    captcha_ttl: int = Field(default=300, gt=0)  # seconds to solve and submit

    @field_validator(
        "redis_url",
        "webhook_base_url",
        "webhook_secret",
        "webapp_url",
        "captcha_secret",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: Any) -> Any:
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def _default_if_empty(cls, value: Any) -> Any:
        return _default_database_url() if isinstance(value, str) and not value.strip() else value

    @field_validator("path_logs", mode="before")
    @classmethod
    def _default_logs_if_empty(cls, value: Any) -> Any:
        return DATA_DIR / "logs.log" if isinstance(value, str) and not value.strip() else value

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_path(cls, value: str) -> str:
        """Relative SQLite paths are relative to the project, not to the current directory."""
        try:
            url = make_url(value)
        except ArgumentError as error:
            raise ValueError(
                "DATABASE_URL must be a SQLAlchemy URL, e.g. sqlite+aiosqlite:///data/database.db"
            ) from error
        if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
            return value
        path = Path(url.database)
        if path.is_absolute():
            return value
        absolute = (PROJECT_ROOT / path).resolve().as_posix()
        return url.set(database=absolute).render_as_string(hide_password=False)

    @field_validator("path_logs")
    @classmethod
    def _resolve_logs_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else PROJECT_ROOT / value

    @field_validator("bot_token")
    @classmethod
    def _check_token(cls, value: SecretStr) -> SecretStr:
        bot_id, _, secret = value.get_secret_value().partition(":")
        if not bot_id.isdigit() or not secret:
            raise ValueError("BOT_TOKEN must look like 123456:ABC-DEF (get it from @BotFather)")
        return value

    @field_validator("bot_timezone")
    @classmethod
    def _check_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"Unknown timezone: {value}") from error
        return value

    @field_validator("webhook_path")
    @classmethod
    def _normalize_webhook_path(cls, value: str) -> str:
        return value if value.startswith("/") else f"/{value}"

    @model_validator(mode="after")
    def _check_webhook(self) -> Settings:
        if self.bot_mode == "webhook" and not self.webhook_base_url:
            raise ValueError("WEBHOOK_BASE_URL is required when BOT_MODE=webhook")
        if self.webapp_enabled and not self.webapp_url:
            raise ValueError("WEBAPP_URL is required when WEBAPP_ENABLED=true")
        if self.webapp_url and not self.webapp_url.startswith("https://"):
            raise ValueError("WEBAPP_URL must be an https:// URL (Telegram requirement)")
        return self

    @property
    def web_server_enabled(self) -> bool:
        """The HTTP server is needed for webhook updates and/or the Mini App."""
        return self.bot_mode == "webhook" or self.webapp_enabled

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.bot_timezone)

    @property
    def webhook_url(self) -> str:
        return f"{(self.webhook_base_url or '').rstrip('/')}{self.webhook_path}"

    @property
    def uses_legacy_data_dir(self) -> bool:
        path = self.sqlite_path
        return path is not None and path.parent == LEGACY_DATA_DIR

    @property
    def sqlite_path(self) -> Path | None:
        """SQLite database file path, or None for other databases / in-memory."""
        url = make_url(self.database_url)
        if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
            return None
        return Path(url.database)

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.admin_ids


settings = Settings()  # values come from the environment
