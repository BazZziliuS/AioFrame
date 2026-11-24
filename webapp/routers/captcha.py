from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from tgbot.data.config import settings
from webapp.auth import CurrentUser
from webapp.captcha import create_challenge

router = APIRouter(prefix="/api", tags=["captcha"])


class CaptchaChallengeOut(BaseModel):
    enabled: bool
    challenge: dict[str, Any] | None = None


@router.get("/captcha")
async def get_captcha(user: CurrentUser) -> CaptchaChallengeOut:
    """A new challenge for the current user (or `enabled: false` if captcha is off)."""
    if not settings.captcha_enabled:
        return CaptchaChallengeOut(enabled=False)
    return CaptchaChallengeOut(enabled=True, challenge=create_challenge(user.user_id))
