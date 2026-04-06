from textwrap import dedent
from typing import Union

from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    KeyboardButton,
    WebAppInfo,
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)

from tgbot.data.config import get_admins


#################################### AIOGRAM ###################################
def rkb(text: str) -> KeyboardButton:
    return KeyboardButton(text=text)


def ikb(
    text: str,
    data: str = None,
    url: str = None,
    switch: str = None,
    web: str = None,
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
    except Exception:
        pass


async def smart_message(
    bot: Bot,
    user_id: int,
    text: str,
    keyboard: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = None,
    photo: Union[str, None] = None,
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
            except Exception:
                pass


##################################### MISC #####################################
def ded(get_text: str) -> str:
    if get_text is None:
        return ""
    return dedent(get_text).strip()


def clear_html(get_text: str) -> str:
    if get_text is None:
        return ""
    return get_text.replace("<", "&lt;").replace(">", "&gt;")


def get_date(full: bool = True) -> str:
    from datetime import datetime

    import pytz

    from tgbot.data.config import BOT_TIMEZONE

    now = datetime.now(pytz.timezone(BOT_TIMEZONE))
    if full:
        return now.strftime("%d.%m.%Y %H:%M:%S")
    return now.strftime("%d.%m.%Y")
