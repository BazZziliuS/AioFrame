from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.database.models import User as UserModel
from tgbot.keyboards.reply import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.text import escape

router = Router(name=__name__)


@router.message(CommandStart())
@router.message(F.text.in_(("menu", "return", "start")))
async def start(message: Message, state: FSMContext, db_user: UserModel, locale: Locale) -> None:
    await state.clear()
    await message.answer(
        locale("start.greeting", user_name=escape(db_user.user_name)),
        reply_markup=menu_reply(db_user.user_id, locale),
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext, db_user: UserModel, locale: Locale) -> None:
    """Leave any FSM dialog (works from every state)."""
    if await state.get_state() is None:
        await message.answer(locale("common.nothing_to_cancel"))
        return

    await state.clear()
    await message.answer(
        locale("common.cancelled"),
        reply_markup=menu_reply(db_user.user_id, locale),
    )
