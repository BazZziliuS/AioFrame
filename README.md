### [![Python](https://img.shields.io/badge/Python-3.14+-blue)](https://www.python.org/) [![Aiogram](https://img.shields.io/badge/aiogram-3.x-blue)](https://pypi.org/project/aiogram/) [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1-green)](https://www.sqlalchemy.org/) [![Alembic](https://img.shields.io/badge/Alembic-migrations-green)](https://alembic.sqlalchemy.org/) [![CI](https://github.com/BazZziliuS/AioFrame/actions/workflows/ci.yml/badge.svg)](https://github.com/BazZziliuS/AioFrame/actions/workflows/ci.yml)

# AioFrame — Telegram Bot Template

Production-ready template for building Telegram bots on **aiogram 3** with async SQLAlchemy, Alembic migrations, repository pattern, i18n, an admin panel and Docker.

## Features

**Core**
- **Aiogram 3** — async Telegram Bot framework, polling or **webhook** mode
- **SQLAlchemy 2.1** — async ORM: SQLite out of the box, PostgreSQL via `asyncpg`
- **Alembic** — migrations are applied automatically on startup
- **Repository pattern** — clean data access layer
- **Typed config** — `pydantic-settings`, invalid `.env` fails fast with a clear error
- **i18n** — JSON locales with fallback; buttons and command menus in every language
- **FSM storage** — in memory or **Redis** (dialogs survive restarts)

**Built-in features**
- **Admin panel** (`/admin`) — statistics, broadcast, maintenance mode, backup, logs
- **Broadcast** — any message type, preview and confirmation, rate limiting,
  flood-control retry, users who blocked the bot are detected and skipped
- **Ban / unban** — `/ban <user_id>`, banned users are ignored completely
- **Maintenance mode** — one button closes the bot for everyone except admins
- **Feedback** — FSM example: users write to admins (`/feedback`, `/cancel`)
- **Anti-spam** — throttling with escalation and a warning
- **Daily backup** — consistent SQLite snapshot sent to admins (APScheduler)

**Telegram Mini App**
- **React + Vite + TypeScript** with **HeroUI** components, light/dark mode follows Telegram
- **FastAPI** backend in the same process as the bot, shares models and repositories
- **Authorization** by Telegram `initData` (HMAC signature + expiry) on every request
- **Admin panel** in the app: audience stats, user search with ban/unban, maintenance switch
- Ban and maintenance mode apply to the bot and the app at once

**Tooling**
- **Tests** — pytest suite with a fake Telegram API (handlers, middlewares, migrations, webhook)
- **CI** — GitHub Actions: Ruff, tests on Python 3.14 and 3.15, Docker build
- **Docker** — `Dockerfile` and `docker-compose.yml` (optional PostgreSQL + Redis)

## Project Structure

```
.
├── main.py                        # Entry point: polling / webhook, startup & shutdown
├── .env                           # Configuration (from .env.example)
├── Dockerfile, docker-compose.yml
├── alembic/                       # Database migrations
├── tests/                         # pytest suite (fake Telegram API in helpers.py)
├── frontend/                      # Mini App: React + Vite + HeroUI
├── webapp/                        # FastAPI: webhook, Mini App API, built frontend
│   ├── app.py                     # App factory, static files, webhook route
│   ├── auth.py                    # initData validation, user / admin dependencies
│   └── routers/                   # /api/me, /api/admin/*
└── tgbot/
    ├── data/config.py             # Settings (pydantic-settings)
    ├── database/
    │   ├── models.py              # SQLAlchemy models
    │   ├── engine.py              # Async engine & session
    │   ├── migrations.py          # alembic upgrade on startup
    │   └── repositories/          # UserRepository, SettingsRepository
    ├── locales/                   # en_us.json, ru_ru.json
    ├── middlewares/
    │   ├── middleware_user.py     # User sync & locale injection
    │   ├── middleware_access.py   # Ban & maintenance mode
    │   └── middleware_throttling.py # Anti-spam
    ├── routers/
    │   ├── main_start.py          # /start, /cancel
    │   ├── main_errors.py         # Error handlers
    │   ├── main_missed.py         # Fallback handlers
    │   ├── admin/                 # Admin panel, broadcast (IsAdmin inside)
    │   └── user/                  # User menu, feedback (FSM example)
    ├── keyboards/                 # Inline & reply keyboards
    ├── services/                  # locale, broadcast, backup, HTTP session
    └── utils/                     # helpers, filters, callbacks, commands, logging
```

## Quick Start

```bash
git clone https://github.com/BazZziliuS/AioFrame.git
cd AioFrame

uv sync                 # add --extra postgres / --extra redis if needed
cp .env.example .env    # set BOT_TOKEN and ADMIN_IDS

uv run python main.py   # migrations are applied automatically
```

### Docker

```bash
cp .env.example .env    # set BOT_TOKEN and ADMIN_IDS
docker compose up -d --build
```

SQLite database and logs are stored in the `bot-data` volume.
For PostgreSQL and Redis start the `full` profile and set in `.env`:

```bash
DOCKER_DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/bot
REDIS_URL=redis://redis:6379/0
```

```bash
docker compose --profile full up -d --build
```

### Webhook mode

```bash
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.example.com   # public HTTPS URL (reverse proxy -> :8080)
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=some-long-random-string     # checked on every request
```

The server also answers `GET /health` with `ok` for health checks.

## Telegram Mini App

The web server (FastAPI + uvicorn) starts when `WEBAPP_URL` is set or in webhook mode.
It serves the Telegram webhook, the API (`/api/...`) and the built frontend.

```bash
cd frontend
npm install
npm run build           # -> webapp/static, served by the bot
```

Set the public HTTPS address in `.env` and restart the bot. The chat menu button opens the app:

```bash
WEBAPP_URL=https://app.example.com
```

The frontend sends `Authorization: tma <initData>` with every request. The backend checks
the signature with the bot token and the age of the data (`WEBAPP_AUTH_TTL`), then loads
the user from the database. Admin endpoints additionally require the user to be in `ADMIN_IDS`.

### Frontend development

Inside Telegram (real client):

```bash
uv run python main.py                       # bot + API on :8080, WEBAPP_URL = tunnel URL
cd frontend && npm run dev                  # Vite on :5173, /api is proxied to :8080
cloudflared tunnel --url http://localhost:5173
```

In a regular browser, without Telegram: generate signed initData for your account and
the app emulates the Telegram client (dev mode only):

```bash
uv run python -m webapp.dev_init_data <your_telegram_id> > frontend/.env.local
cd frontend && npm run dev                  # open http://localhost:5173
```

`VITE_DEV_THEME=light` in `frontend/.env.local` switches the emulated theme.

## Configuration

All settings are in `.env` (real environment variables take priority):

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather | **required** |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs | — |
| `DATABASE_URL` | SQLAlchemy async URL | `sqlite+aiosqlite:///tgbot/data/database.db` |
| `REDIS_URL` | Redis for FSM storage, empty = memory | — |
| `PATH_LOGS` | Log file path | `tgbot/data/logs.log` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `BOT_TIMEZONE` | Timezone for scheduler & dates | `Europe/Moscow` |
| `BOT_STATUS_NOTIFICATION` | Notify admins on bot start | `true` |
| `AUTOBACKUP_HOUR` | Hour of the daily backup (0–23) | `0` |
| `THROTTLE_RATE` | Anti-spam interval in seconds, `0` disables | `0.5` |
| `BROADCAST_RATE` | Broadcast speed, messages per second | `25` |
| `BOT_MODE` | `polling` or `webhook` | `polling` |
| `WEBHOOK_BASE_URL` | Public URL, required for webhook mode | — |
| `WEBHOOK_PATH` | Webhook path | `/webhook` |
| `WEBHOOK_SECRET` | Secret token checked by the webhook server | — |
| `WEBAPP_HOST` / `WEBAPP_PORT` | Web server address | `0.0.0.0` / `8080` |
| `WEBAPP_URL` | Public HTTPS URL of the Mini App, enables it | — |
| `WEBAPP_AUTH_TTL` | Max age of Telegram `initData`, seconds | `86400` |

## Admin Commands

| Command | Description |
|---|---|
| `/admin` | Admin panel: stats, broadcast, maintenance, backup, logs |
| `/stats` | User statistics |
| `/broadcast` | Send a message to all users |
| `/ban <id>`, `/unban <id>` | Ban or unban a user |
| `/db` | Database backup (SQLite) |
| `/log`, `/clear_log` | Get or clear log files |

## Database Migrations

Migrations run on every startup. To change the schema:

```bash
# After changing models.py — generate a migration and review it
uv run alembic revision --autogenerate -m "description"

# Apply manually (optional, the bot does it on start)
uv run alembic upgrade head
```

## Development

```bash
uv sync --all-extras
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # format

cd frontend
npm run lint            # ESLint
npm run build           # type check + production build
```

## Adding a New Locale

1. Create `tgbot/locales/xx_xx.json` (copy structure from `en_us.json`)
2. Done: the language is picked by the Telegram language code (`xx`), buttons and command menus are translated automatically. The test suite checks that all locales have the same keys.
