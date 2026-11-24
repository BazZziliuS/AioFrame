from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.config import settings
from tgbot.services.locale import Locale
from tgbot.utils.telegram import rkb


# Main menu buttons
def menu_reply(user_id: int, locale: Locale) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb(locale("menu.user_button")),
        rkb(locale("menu.feedback_button")),
    )

    if settings.is_admin(user_id):
        keyboard.row(
            rkb(locale("menu.admin_button")),
        )

    return keyboard.as_markup(resize_keyboard=True)
