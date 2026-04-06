from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.data.config import get_admins
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import rkb


# Кнопки главного меню
def menu_reply(user_id: int, locale: Locale) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb(locale("menu.user_button")),
    )

    if user_id in get_admins():
        keyboard.row(
            rkb(locale("menu.admin_button")),
        )

    return keyboard.as_markup(resize_keyboard=True)
