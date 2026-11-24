"""Validation of Telegram Mini App `initData`.

Telegram signs initData with the bot token (HMAC-SHA256): a valid signature proves the
data was issued for this bot and not modified. `auth_date` limits how long it stays valid.
Never trust `initDataUnsafe` on the client - only data validated here.
"""

from datetime import UTC, datetime

from aiogram.utils.web_app import WebAppInitData, WebAppUser, safe_parse_webapp_init_data


class InitDataError(Exception):
    """initData is missing, forged or too old. `code` is returned to the client."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def validate_init_data(raw: str, *, bot_token: str, max_age: int) -> WebAppUser:
    """Return the Telegram user from a signed, fresh initData string."""
    if not raw:
        raise InitDataError("missing_init_data")

    try:
        init_data: WebAppInitData = safe_parse_webapp_init_data(bot_token, raw)
    except ValueError as error:
        raise InitDataError("invalid_init_data") from error

    if init_data.user is None:
        raise InitDataError("invalid_init_data")

    age = (datetime.now(UTC) - init_data.auth_date).total_seconds()
    if age > max_age:
        raise InitDataError("init_data_expired")

    return init_data.user
