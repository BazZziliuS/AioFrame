from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.database.models import User as UserModel
from tgbot.filters import LocaleText
from tgbot.keyboards.inline import user_inline
from tgbot.keyboards.reply import menu_reply
from tgbot.services.locale import Locale

router = Router(name=__name__)


@router.message(LocaleText("menu.user_button"))  # the button text in any language
async def user_button(message: Message, state: FSMContext, locale: Locale) -> None:
    await state.clear()
    await message.answer(locale("user.inline_keyboards"), reply_markup=user_inline(locale))


@router.message(Command("menu"))
async def menu_command(
    message: Message, state: FSMContext, db_user: UserModel, locale: Locale
) -> None:
    await state.clear()
    await message.answer(
        locale("menu.enter_menu"),
        reply_markup=menu_reply(db_user.user_id, locale),
    )


# Inline button examples
@router.callback_query(F.data == "user_inline_x")
async def user_button_x(call: CallbackQuery) -> None:
    await call.answer("Click User X")


@router.callback_query(F.data.startswith("user_inline:"))
async def user_button_with_data(call: CallbackQuery) -> None:
    value = (call.data or "").split(":", 1)[1]
    await call.answer(f"Click User - {value}", show_alert=True)
