from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from tgbot.database.models import User as UserModel
from tgbot.keyboards.inline_main import user_inline
from tgbot.keyboards.reply_main import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.misc.bot_filters import LocaleText
from tgbot.utils.misc.bot_models import ARS, FSM

router = Router(name=__name__)


# Message - User button (matches the button text in any language)
@router.message(LocaleText("menu.user_button"))
async def user_button_inline(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    await message.answer(
        locale("user.inline_keyboards"),
        reply_markup=user_inline(locale),
    )


# Command - /menu
@router.message(Command(commands="menu"))
async def user_command_menu(message: Message, state: FSM, User: UserModel, locale: Locale):
    await state.clear()

    await message.answer(
        locale("menu.enter_menu"),
        reply_markup=menu_reply(User.user_id, locale),
    )


# Callback - User X
@router.callback_query(F.data == "user_inline_x")
async def user_callback_inline_x(call: CallbackQuery):
    await call.answer("Click User X")


# Callback - User
@router.callback_query(F.data.startswith("user_inline:"))
async def user_callback_inline(call: CallbackQuery):
    get_data = (call.data or "").split(":")[1]

    await call.answer(f"Click User - {get_data}", True)
