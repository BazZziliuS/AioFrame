from fastapi import APIRouter

from tgbot.config import settings
from webapp.api.deps import CurrentUser, TelegramUser
from webapp.schemas import MeOut

router = APIRouter(tags=["user"])


@router.get("/me")
async def get_me(user: CurrentUser, tg_user: TelegramUser) -> MeOut:
    """The current user's profile (photo comes from Telegram, not stored)."""
    return MeOut.build(user, is_admin=settings.is_admin(user.user_id), photo_url=tg_user.photo_url)
