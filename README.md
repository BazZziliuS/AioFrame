### [![Python](https://img.shields.io/badge/Python-3.13+-blue)](https://www.python.org/) [![Aiogram](https://img.shields.io/badge/aiogram-3.x-blue)](https://pypi.org/project/aiogram/) [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-green)](https://www.sqlalchemy.org/) [![Alembic](https://img.shields.io/badge/Alembic-migrations-green)](https://alembic.sqlalchemy.org/)

# AioFrame — Telegram Bot Template

Production-ready template for building Telegram bots on **aiogram 3** with async SQLAlchemy, Alembic migrations, repository pattern, and i18n localization.

## Features

- **Aiogram 3** — async Telegram Bot framework
- **SQLAlchemy 2.0** — async ORM with `aiosqlite`
- **Alembic** — database migrations with autogenerate
- **Repository pattern** — clean data access layer with session injection
- **i18n** — JSON-based localization with fallback (`en_us`, `ru_ru`)
- **Middlewares** — auto user sync, anti-spam throttling with escalation
- **Admin / User separation** — filtered routers with `IsAdmin` guard
- **Dotenv config** — all settings via `.env`, no hardcoded secrets
- **APScheduler** — built-in task scheduler (daily DB backup)
- **Ruff** — linted and formatted

## Project Structure

```
.
├── main.py                        # Entry point
├── .env                           # Configuration (from .env.example)
├── alembic/                       # Database migrations
│   ├── env.py
│   └── versions/
├── tgbot/
│   ├── data/
│   │   └── config.py              # Env loader
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── engine.py              # Async engine & session
│   │   └── repositories/
│   │       ├── base.py            # Generic CRUD
│   │       ├── user.py            # UserRepository
│   │       └── settings.py        # SettingsRepository
│   ├── locales/
│   │   ├── en_us.json             # English (default)
│   │   └── ru_ru.json             # Russian
│   ├── middlewares/
│   │   ├── middleware_user.py     # User sync & locale injection
│   │   └── middleware_throttling.py # Anti-spam
│   ├── routers/
│   │   ├── main_start.py         # /start command
│   │   ├── main_errors.py        # Error handlers
│   │   ├── main_missed.py        # Fallback handlers
│   │   ├── admin/                # Admin-only routes
│   │   └── user/                 # User routes
│   ├── keyboards/
│   │   ├── inline_main.py        # Inline keyboards
│   │   └── reply_main.py         # Reply keyboards
│   ├── services/
│   │   ├── locale.py             # Localization service
│   │   └── api_session.py        # Async HTTP client
│   └── utils/
│       ├── const_functions.py    # Helpers (buttons, HTML escape, etc.)
│       ├── misc_functions.py     # Startup notify, autobackup
│       └── misc/                 # Logging, filters, commands
```

## Quick Start

```bash
# Clone
git clone https://github.com/your-username/aioframe.git
cd aioframe

# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env — set BOT_TOKEN and ADMIN_IDS

# Run migrations
alembic upgrade head

# Start
python main.py
```

## Configuration

All settings are in `.env`:

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather | — |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs | — |
| `DATABASE_URL` | SQLAlchemy async URL | `sqlite+aiosqlite:///tgbot/data/database.db` |
| `PATH_LOGS` | Log file path | `tgbot/data/logs.log` |
| `BOT_TIMEZONE` | Timezone for scheduler & dates | `Europe/Moscow` |
| `BOT_STATUS_NOTIFICATION` | Notify admins on bot start | `true` |

## Database Migrations

```bash
# After changing models.py — generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Adding a New Locale

1. Create `tgbot/locales/xx_xx.json` (copy structure from `en_us.json`)
2. Add mapping in `tgbot/services/locale.py` → `language_code_to_locale()`
