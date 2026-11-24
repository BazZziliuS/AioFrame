"""Mini App authorization: every request carries Telegram `initData`.

The frontend sends `Authorization: tma <initData>`. The signature (HMAC with the bot
token) proves the data came from Telegram for this bot; `auth_date` limits its age.
Never trust `initDataUnsafe` on the client.
"""

from datetime import UTC, datetime
from typing import Annotated

from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data
from fastapi import Depends, Header, HTTPException, status

from tgbot.data.config import settings
from tgbot.database.engine import async_session
from tgbot.database.models import User
from tgbot.database.repositories import SettingsRepository
from tgbot.services.users import sync_user


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "tma"},
    )


async def get_init_data(
    authorization: Annotated[str | None, Header()] = None,
) -> WebAppInitData:
    scheme, _, raw = (authorization or "").partition(" ")
    if scheme.lower() != "tma" or not raw:
        raise _unauthorized("missing_init_data")

    try:
        init_data = safe_parse_webapp_init_data(settings.bot_token.get_secret_value(), raw)
    except ValueError as error:
        raise _unauthorized("invalid_init_data") from error

    if init_data.user is None:
        raise _unauthorized("invalid_init_data")

    age = (datetime.now(UTC) - init_data.auth_date).total_seconds()
    if age > settings.webapp_auth_ttl:
        raise _unauthorized("init_data_expired")

    return init_data


InitData = Annotated[WebAppInitData, Depends(get_init_data)]


async def get_current_user(init_data: InitData) -> User:
    assert init_data.user is not None  # checked in get_init_data
    user = await sync_user(init_data.user)

    if settings.is_admin(user.user_id):
        return user

    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="banned")

    async with async_session() as session:
        if await SettingsRepository(session).is_maintenance():
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="maintenance")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_admin(user: CurrentUser) -> User:
    if not settings.is_admin(user.user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user


AdminUser = Annotated[User, Depends(get_admin)]
