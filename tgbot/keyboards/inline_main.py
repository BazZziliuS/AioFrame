from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.services.locale import Locale
from tgbot.utils.const_functions import ikb


# Inline keyboards for users
def user_inline(locale: Locale) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb(locale("buttons.user_x"), data="user_inline_x"),
        ikb(locale("buttons.user_1"), data="user_inline:user_btn"),
        ikb(locale("buttons.user_2"), data="..."),
    ).row(
        ikb(locale("buttons.user_unknown"), data="unknown"),
    )

    return keyboard.as_markup()


# Inline keyboards for admins
def admin_inline(locale: Locale) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb(locale("buttons.admin_x"), data="admin_inline_x"),
        ikb(locale("buttons.admin_1"), data="admin_inline:admin_btn"),
        ikb(locale("buttons.admin_2"), data="..."),
    ).row(
        ikb(locale("buttons.admin_unknown"), data="unknown"),
    )

    return keyboard.as_markup()
