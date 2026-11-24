"""Example of a captcha-protected action: a message from the Mini App to the admins."""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tgbot.services.locale import Locale
from tgbot.utils.const_functions import clear_html, send_admins
from webapp.auth import CurrentUser
from webapp.captcha import Captcha

router = APIRouter(prefix="/api", tags=["feedback"])


class FeedbackIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class FeedbackOut(BaseModel):
    ok: bool = True


@router.post("/feedback", dependencies=[Captcha])
async def send_feedback(body: FeedbackIn, user: CurrentUser, request: Request) -> FeedbackOut:
    name = user.user_fullname or str(user.user_id)
    text = Locale()(
        "feedback.admin_message",
        user=f'<a href="tg://user?id={user.user_id}">{name}</a>',
        user_id=user.user_id,
        text=clear_html(body.text.strip()),
    )
    await send_admins(request.app.state.bot, text)
    return FeedbackOut()
