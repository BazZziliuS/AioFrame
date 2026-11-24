"""FastAPI dependencies: database session, bot, current user and captcha.

Use the `Annotated` aliases in endpoint signatures:

    @router.get("/something")
    async def endpoint(user: CurrentUser, session: SessionDep) -> ...: ...

    @router.post("/protected", dependencies=[CaptchaRequired])
    async def protected(user: CurrentUser) -> ...: ...
"""

from collections.abc import AsyncIterator
from typing import Annotated

from aiogram import Bot
from aiogram.utils.web_app import WebAppUser
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.config import settings
from tgbot.database.engine import async_session
from tgbot.database.models import User
from tgbot.database.repositories import SettingsRepository
from tgbot.services.users import sync_user
from webapp.core.captcha import CaptchaError, verify_captcha
from webapp.core.init_data import InitDataError, validate_init_data


async def get_session() -> AsyncIterator[AsyncSession]:
    """One database session per request; endpoints commit explicitly."""
    async with async_session() as session:
        yield session


def get_bot(request: Request) -> Bot:
    bot: Bot = request.app.state.bot
    return bot


SessionDep = Annotated[AsyncSession, Depends(get_session)]
BotDep = Annotated[Bot, Depends(get_bot)]


async def get_telegram_user(authorization: Annotated[str | None, Header()] = None) -> WebAppUser:
    """The frontend sends `Authorization: tma <initData>` with every request."""
    scheme, _, raw = (authorization or "").partition(" ")
    try:
        if scheme.lower() != "tma":
            raise InitDataError("missing_init_data")
        return validate_init_data(
            raw,
            bot_token=settings.bot_token.get_secret_value(),
            max_age=settings.webapp_auth_ttl,
        )
    except InitDataError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=error.code,
            headers={"WWW-Authenticate": "tma"},
        ) from error


TelegramUser = Annotated[WebAppUser, Depends(get_telegram_user)]


async def get_current_user(tg_user: TelegramUser, session: SessionDep) -> User:
    """The user from the database; banned users and maintenance mode are rejected."""
    user = await sync_user(tg_user)
    if settings.is_admin(user.user_id):
        return user

    if user.is_banned:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="banned")
    if await SettingsRepository(session).is_maintenance():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="maintenance")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_admin(user: CurrentUser) -> User:
    if not settings.is_admin(user.user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="admin_only")
    return user


AdminUser = Annotated[User, Depends(get_admin)]


async def require_captcha(
    user: CurrentUser,
    x_captcha: Annotated[str | None, Header()] = None,
) -> None:
    """The request must carry a solved captcha in the `X-Captcha` header (if enabled)."""
    if not settings.captcha_enabled:
        return
    try:
        await verify_captcha(x_captcha, user.user_id)
    except CaptchaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=error.code) from error


CaptchaRequired = Depends(require_captcha)
