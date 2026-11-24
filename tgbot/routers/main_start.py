from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.database.models import User as UserModel
from tgbot.keyboards.reply_main import menu_reply
from tgbot.services.locale import Locale

router = Router(name=__name__)


# Main menu
@router.message(F.text.in_(("menu", "return", "start")))
@router.message(Command(commands=["start"]))
async def main_start(message: Message, state: FSMContext, User: UserModel, locale: Locale):
    await state.clear()

    await message.answer(
        locale("start.greeting", user_name=User.user_name),
        reply_markup=menu_reply(User.user_id, locale),
    )


# Cancel any FSM dialog (works from every state)
@router.message(Command(commands=["cancel"]))
async def main_cancel(message: Message, state: FSMContext, User: UserModel, locale: Locale):
    if await state.get_state() is None:
        await message.answer(locale("common.nothing_to_cancel"))
        return

    await state.clear()
    await message.answer(
        locale("common.cancelled"),
        reply_markup=menu_reply(User.user_id, locale),
    )
