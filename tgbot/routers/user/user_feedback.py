"""FSM example: the user writes a message, the bot forwards it to admins."""

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from tgbot.database.models import User as UserModel
from tgbot.keyboards.reply_main import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import clear_html, send_admins
from tgbot.utils.misc.bot_filters import LocaleText

router = Router(name=__name__)


class FeedbackStates(StatesGroup):
    waiting_text = State()


# Step 1: ask for the message
@router.message(LocaleText("menu.feedback_button"))
@router.message(Command(commands=["feedback"]))
async def feedback_start(message: Message, state: FSMContext, locale: Locale):
    await state.set_state(FeedbackStates.waiting_text)
    await message.answer(locale("feedback.ask"))


# Step 2: forward the text to admins (commands like /cancel are handled elsewhere)
@router.message(FeedbackStates.waiting_text, F.text, ~F.text.startswith("/"))
async def feedback_text(
    message: Message,
    bot: Bot,
    state: FSMContext,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    user_link = f'<a href="tg://user?id={User.user_id}">{User.user_fullname or User.user_id}</a>'
    admin_locale = Locale()
    await send_admins(
        bot,
        admin_locale(
            "feedback.admin_message",
            user=user_link,
            user_id=User.user_id,
            text=clear_html(message.text),
        ),
    )

    await message.answer(locale("feedback.sent"), reply_markup=menu_reply(User.user_id, locale))


# Anything else while waiting (photo, sticker, ...)
@router.message(FeedbackStates.waiting_text, ~F.text.startswith("/"))
async def feedback_wrong_content(message: Message, locale: Locale):
    await message.answer(locale("feedback.text_only"))
