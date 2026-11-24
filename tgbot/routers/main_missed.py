from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from tgbot.database.models import User as UserModel
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import del_message
from tgbot.utils.misc.bot_models import ARS, FSM

router = Router(name=__name__)


# Callback with delete message
@router.callback_query(F.data == "close_this")
async def main_callback_close(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await del_message(call.message)


# Callback with processing miss button
@router.callback_query(F.data == "...")
async def main_callback_answer(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await call.answer(cache_time=30)


# Callback with processing miss callback data
@router.callback_query()
async def main_callback_missed(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await call.answer(locale("missed.miss_callback", data=call.data), True)


# Processing all unknowns callback datas
@router.message()
async def main_message_missed(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await message.answer(locale("missed.unknown_command"))
