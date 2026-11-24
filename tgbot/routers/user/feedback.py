"""FSM example: the user writes a message, the bot forwards it to admins."""

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from tgbot.database.models import User as UserModel
from tgbot.filters import LocaleText
from tgbot.keyboards.reply import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.telegram import send_admins
from tgbot.utils.text import escape, user_link

router = Router(name=__name__)


class FeedbackStates(StatesGroup):
    waiting_text = State()


@router.message(LocaleText("menu.feedback_button"))
@router.message(Command("feedback"))
async def feedback_start(message: Message, state: FSMContext, locale: Locale) -> None:
    """Step 1: ask for the message."""
    await state.set_state(FeedbackStates.waiting_text)
    await message.answer(locale("feedback.ask"))


@router.message(FeedbackStates.waiting_text, F.text, ~F.text.startswith("/"))
async def feedback_text(
    message: Message,
    bot: Bot,
    state: FSMContext,
    db_user: UserModel,
    locale: Locale,
) -> None:
    """Step 2: forward the text to admins (commands like /cancel are handled elsewhere)."""
    await state.clear()
    await send_admins(
        bot,
        Locale()(
            "feedback.admin_message",
            user=user_link(db_user.user_id, db_user.user_fullname),
            user_id=db_user.user_id,
            text=escape(message.text),
        ),
    )
    await message.answer(locale("feedback.sent"), reply_markup=menu_reply(db_user.user_id, locale))


@router.message(FeedbackStates.waiting_text, ~F.text.startswith("/"))
async def feedback_wrong_content(message: Message, locale: Locale) -> None:
    """Anything else while waiting (photo, sticker, ...)."""
    await message.answer(locale("feedback.text_only"))
