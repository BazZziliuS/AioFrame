"""Example of a captcha-protected action: a message from the Mini App to the admins."""

from fastapi import APIRouter

from tgbot.services.locale import Locale
from tgbot.utils.telegram import send_admins
from tgbot.utils.text import escape, user_link
from webapp.api.deps import BotDep, CaptchaRequired, CurrentUser
from webapp.schemas import FeedbackIn, FeedbackOut

router = APIRouter(tags=["feedback"])


@router.post("/feedback", dependencies=[CaptchaRequired])
async def send_feedback(body: FeedbackIn, user: CurrentUser, bot: BotDep) -> FeedbackOut:
    text = Locale()(
        "feedback.admin_message",
        user=user_link(user.user_id, user.user_fullname),
        user_id=user.user_id,
        text=escape(body.text.strip()),
    )
    await send_admins(bot, text)
    return FeedbackOut()
