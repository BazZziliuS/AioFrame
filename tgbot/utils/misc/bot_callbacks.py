from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class AdminAction(StrEnum):
    PANEL = "panel"
    STATS = "stats"
    BROADCAST = "broadcast"
    MAINTENANCE = "maintenance"
    BACKUP = "backup"
    LOGS = "logs"


class AdminCallback(CallbackData, prefix="adm"):
    action: AdminAction


class BroadcastCallback(CallbackData, prefix="bc"):
    confirm: bool
