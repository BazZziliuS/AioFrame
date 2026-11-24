import html
from datetime import datetime
from textwrap import dedent

from tgbot.config import settings


def escape(text: str | None) -> str:
    """Escape user text for Telegram HTML parse mode (`<`, `>` and `&`).

    Store raw values in the database and escape only when building HTML messages.
    """
    return html.escape(text or "", quote=False)


def dedent_text(text: str | None) -> str:
    """Remove common indentation from a multi-line string literal."""
    return dedent(text or "").strip()


def format_now(with_time: bool = True) -> str:
    """Current date (and time) in the bot timezone, e.g. for backup captions."""
    now = datetime.now(settings.timezone)
    return now.strftime("%d.%m.%Y %H:%M:%S" if with_time else "%d.%m.%Y")


def user_link(user_id: int, name: str) -> str:
    """HTML mention of a user; `name` is escaped."""
    return f'<a href="tg://user?id={user_id}">{escape(name) or user_id}</a>'
