"""Last router: closes messages and answers unknown buttons and messages."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from tgbot.services.locale import Locale
from tgbot.utils.telegram import delete_message

router = Router(name=__name__)


@router.callback_query(F.data == "close_this")
async def close_message(call: CallbackQuery) -> None:
    await call.answer()
    if isinstance(call.message, Message):
        await delete_message(call.message)


@router.callback_query(F.data == "...")
async def placeholder_button(call: CallbackQuery) -> None:
    await call.answer(cache_time=30)


@router.callback_query()
async def unknown_button(call: CallbackQuery, locale: Locale) -> None:
    await call.answer(locale("missed.miss_callback", data=call.data), show_alert=True)


@router.message()
async def unknown_message(message: Message, locale: Locale) -> None:
    await message.answer(locale("missed.unknown_command"))
