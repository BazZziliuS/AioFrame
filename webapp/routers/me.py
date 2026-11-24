from fastapi import APIRouter

from tgbot.data.config import settings
from webapp.auth import CurrentUser, InitData
from webapp.schemas import MeOut

router = APIRouter(prefix="/api", tags=["user"])


@router.get("/me")
async def get_me(user: CurrentUser, init_data: InitData) -> MeOut:
    photo_url = init_data.user.photo_url if init_data.user else None
    return MeOut.build(user, is_admin=settings.is_admin(user.user_id), photo_url=photo_url)
