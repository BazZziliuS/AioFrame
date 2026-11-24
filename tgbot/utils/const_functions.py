from datetime import datetime
from textwrap import dedent
from zoneinfo import ZoneInfo

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

from tgbot.data.config import BOT_TIMEZONE, get_admins
from tgbot.utils.misc.bot_logging import bot_logger


#################################### AIOGRAM ###################################
def rkb(text: str) -> KeyboardButton:
    return KeyboardButton(text=text)


def ikb(
    text: str,
    data: str | None = None,
    url: str | None = None,
    switch: str | None = None,
    web: str | None = None,
) -> InlineKeyboardButton:
    if data is not None:
        return InlineKeyboardButton(text=text, callback_data=data)
    elif url is not None:
        return InlineKeyboardButton(text=text, url=url)
    elif switch is not None:
        return InlineKeyboardButton(text=text, switch_inline_query=switch)
    elif web is not None:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web))
    raise ValueError("ikb() requires one of: data, url, switch, web")


async def del_message(message: Message):
    try:
        await message.delete()
    except TelegramAPIError as error:
        bot_logger.debug("Failed to delete message: %s", error)


async def smart_message(
    bot: Bot,
    user_id: int,
    text: str,
    keyboard: InlineKeyboardMarkup | ReplyKeyboardMarkup | None = None,
    photo: str | None = None,
):
    if photo is not None and photo.title() != "None":
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=text,
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
        )


async def send_admins(bot: Bot, text: str, markup=None, not_me=0):
    for admin in get_admins():
        if str(admin) != str(not_me):
            try:
                await bot.send_message(
                    admin,
                    text,
                    reply_markup=markup,
                    disable_web_page_preview=True,
                )
            except TelegramAPIError as error:
                bot_logger.warning(
                    "Failed to send message to admin %s: %s", admin, error
                )


##################################### MISC #####################################
def ded(get_text: str | None) -> str:
    if get_text is None:
        return ""
    return dedent(get_text).strip()


def clear_html(get_text: str | None) -> str:
    if get_text is None:
        return ""
    return get_text.replace("<", "&lt;").replace(">", "&gt;")


def get_date(full: bool = True) -> str:
    now = datetime.now(ZoneInfo(BOT_TIMEZONE))
    if full:
        return now.strftime("%d.%m.%Y %H:%M:%S")
    return now.strftime("%d.%m.%Y")
