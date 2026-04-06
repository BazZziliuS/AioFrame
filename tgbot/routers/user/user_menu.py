from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from tgbot.database.models import User as UserModel
from tgbot.keyboards.inline_main import user_inline
from tgbot.keyboards.reply_main import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


# Message - User button
@router.message(F.text.in_(("User button", "Пользователь")))
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
async def user_command_menu(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    await message.answer(
        locale("menu.enter_menu"),
        reply_markup=menu_reply(message.from_user.id, locale),
    )


# Callback - User X
@router.callback_query(F.data == "user_inline_x")
async def user_callback_inline_x(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await call.answer("Click User X")


# Callback - User
@router.callback_query(F.data.startswith("user_inline:"))
async def user_callback_inline(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    get_data = call.data.split(":")[1]

    await call.answer(f"Click User - {get_data}", True)
