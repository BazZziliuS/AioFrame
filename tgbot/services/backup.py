import asyncio
import sqlite3
import tempfile
from pathlib import Path

from aiogram.types import BufferedInputFile

from tgbot.config import settings
from tgbot.utils.text import format_now


def _sqlite_snapshot(source: Path) -> bytes:
    """Consistent copy of a live SQLite database via the online backup API."""
    with tempfile.TemporaryDirectory() as tmp:
        target_path = Path(tmp) / "backup.db"
        source_conn = sqlite3.connect(source)
        target_conn = sqlite3.connect(target_path)
        try:
            source_conn.backup(target_conn)
        finally:
            target_conn.close()
            source_conn.close()
        return target_path.read_bytes()


async def database_backup() -> BufferedInputFile | None:
    """Database snapshot ready to send, or None if backups are not supported.

    Only SQLite is supported; for PostgreSQL use `pg_dump` on the server side.
    """
    path = settings.sqlite_path
    if path is None or not path.is_file():
        return None

    data = await asyncio.to_thread(_sqlite_snapshot, path)
    stamp = format_now().replace(".", "-").replace(":", "-").replace(" ", "_")
    return BufferedInputFile(data, filename=f"{path.stem}_{stamp}{path.suffix or '.db'}")
