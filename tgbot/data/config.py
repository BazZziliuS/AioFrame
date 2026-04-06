import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Пути
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///tgbot/data/database.db")
PATH_DATABASE = DATABASE_URL.split("///", 1)[-1]  # Путь к файлу БД (для бэкапов)
PATH_LOGS = os.getenv("PATH_LOGS", "tgbot/data/logs.log")

# Конфиги
BOT_STATUS_NOTIFICATION = os.getenv("BOT_STATUS_NOTIFICATION", "true").lower() in (
    "true",
    "1",
    "yes",
)
BOT_TIMEZONE = os.getenv("BOT_TIMEZONE", "Europe/Moscow")
BOT_SCHEDULER = AsyncIOScheduler(timezone=BOT_TIMEZONE)


def get_admins() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    return [int(x) for x in ids if x.isdigit()]
