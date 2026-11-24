from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from tgbot.services.locale import Locale
from tgbot.utils.const_functions import del_message

router = Router(name=__name__)


# Callback with delete message
@router.callback_query(F.data == "close_this")
async def main_callback_close(call: CallbackQuery):
    await call.answer()
    if isinstance(call.message, Message):
        await del_message(call.message)


# Callback with processing miss button
@router.callback_query(F.data == "...")
async def main_callback_answer(call: CallbackQuery):
    await call.answer(cache_time=30)


# Callback with processing miss callback data
@router.callback_query()
async def main_callback_missed(call: CallbackQuery, locale: Locale):
    await call.answer(locale("missed.miss_callback", data=call.data), True)


# Processing all unknown messages
@router.message()
async def main_message_missed(message: Message, locale: Locale):
    await message.answer(locale("missed.unknown_command"))
