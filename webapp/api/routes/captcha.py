from fastapi import APIRouter

from tgbot.config import settings
from webapp.api.deps import CurrentUser
from webapp.core.captcha import create_challenge
from webapp.schemas import CaptchaChallengeOut

router = APIRouter(tags=["captcha"])


@router.get("/captcha")
async def get_captcha(user: CurrentUser) -> CaptchaChallengeOut:
    """A new challenge for the current user (or `enabled: false` if captcha is off)."""
    if not settings.captcha_enabled:
        return CaptchaChallengeOut(enabled=False)
    return CaptchaChallengeOut(enabled=True, challenge=create_challenge(user.user_id))
