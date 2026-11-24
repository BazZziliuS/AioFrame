from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.callbacks import AdminAction, AdminCallback, BroadcastCallback
from tgbot.services.locale import Locale
from tgbot.utils.telegram import ikb


# Inline keyboards for users (example)
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


# Admin panel
def admin_panel_inline(locale: Locale, is_maintenance: bool) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    def button(key: str, action: AdminAction) -> InlineKeyboardButton:
        return ikb(locale(key), data=AdminCallback(action=action).pack())

    maintenance_key = (
        "buttons.admin_maintenance_on" if is_maintenance else "buttons.admin_maintenance_off"
    )

    keyboard.row(
        button("buttons.admin_stats", AdminAction.STATS),
        button("buttons.admin_broadcast", AdminAction.BROADCAST),
    ).row(
        button(maintenance_key, AdminAction.MAINTENANCE),
    ).row(
        button("buttons.admin_backup", AdminAction.BACKUP),
        button("buttons.admin_logs", AdminAction.LOGS),
    ).row(
        ikb(locale("buttons.close"), data="close_this"),
    )

    return keyboard.as_markup()


# Broadcast confirmation
def broadcast_confirm_inline(locale: Locale) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()

    keyboard.row(
        ikb(locale("buttons.confirm"), data=BroadcastCallback(confirm=True).pack()),
        ikb(locale("buttons.cancel"), data=BroadcastCallback(confirm=False).pack()),
    )

    return keyboard.as_markup()
