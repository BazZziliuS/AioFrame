"""Small helpers around aiogram: keyboard buttons, safe delete, messages to admins."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from tgbot.config import settings

logger = logging.getLogger(__name__)


def rkb(text: str) -> KeyboardButton:
    """Reply keyboard button."""
    return KeyboardButton(text=text)


def ikb(
    text: str,
    data: str | None = None,
    url: str | None = None,
    switch: str | None = None,
    web: str | None = None,
) -> InlineKeyboardButton:
    """Inline keyboard button: exactly one of callback data, URL, inline query or Web App."""
    if data is not None:
        return InlineKeyboardButton(text=text, callback_data=data)
    if url is not None:
        return InlineKeyboardButton(text=text, url=url)
    if switch is not None:
        return InlineKeyboardButton(text=text, switch_inline_query=switch)
    if web is not None:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web))
    raise ValueError("ikb() requires one of: data, url, switch, web")


async def delete_message(message: Message) -> None:
    """Delete a message, ignoring messages that are too old or already deleted."""
    try:
        await message.delete()
    except TelegramAPIError as error:
        logger.debug("Failed to delete message: %s", error)


async def send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    keyboard: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    photo: str | None = None,
) -> Message:
    """Send text, or a photo with the text as caption when `photo` is given."""
    if photo:
        return await bot.send_photo(chat_id, photo=photo, caption=text, reply_markup=keyboard)
    return await bot.send_message(chat_id, text, reply_markup=keyboard)


async def send_admins(
    bot: Bot,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
    exclude: int | None = None,
) -> None:
    """Send a message to every admin; delivery errors are logged, not raised."""
    for admin in settings.admin_ids:
        if admin == exclude:
            continue
        try:
            await bot.send_message(admin, text, reply_markup=markup, disable_web_page_preview=True)
        except TelegramAPIError as error:
            logger.warning("Failed to send message to admin %s: %s", admin, error)
