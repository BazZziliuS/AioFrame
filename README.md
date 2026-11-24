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
- **Captcha** for sensitive actions: proof-of-work, solved in the background, no third-party
  service; one dependency protects any endpoint (example: feedback form)

**Tooling**
- **Tests** — pytest suite with a fake Telegram API (handlers, middlewares, migrations, webhook)
- **CI** — GitHub Actions: Ruff, tests on Python 3.14 and 3.15, Docker build
- **Docker** — `Dockerfile` and `docker-compose.yml` (optional PostgreSQL + Redis)

## Project Structure

```
.
├── main.py                      # Entry point: database, bot, polling / webhook, web server
├── migrations/                  # Alembic migrations (applied automatically on startup)
├── data/                        # Runtime files: SQLite database, logs (git-ignored)
├── tgbot/                       # Telegram bot
│   ├── config.py                # Settings from .env (pydantic-settings, validated on start)
│   ├── logger.py                # Logging setup
│   ├── bot.py                   # Bot, Dispatcher, FSM storage, scheduler, commands, menu button
│   ├── callbacks.py             # CallbackData factories
│   ├── filters.py               # IsAdmin, LocaleText
│   ├── database/
│   │   ├── models.py            # SQLAlchemy models (UTC datetimes on every database)
│   │   ├── engine.py            # Async engine, SQLite tuning (WAL, busy timeout)
│   │   ├── migrations.py        # `alembic upgrade head` on startup
│   │   └── repositories/        # UserRepository, SettingsRepository
│   ├── middlewares/             # user sync, access (ban, maintenance), throttling
│   ├── routers/                 # start, errors, fallback, admin/, user/
│   ├── keyboards/               # inline, reply
│   ├── services/                # users, broadcast, backup, notifications, locale, http
│   ├── utils/                   # telegram helpers, text (HTML escaping, dates)
│   └── locales/                 # en_us.json, ru_ru.json
├── webapp/                      # Mini App backend (FastAPI, runs in the bot process)
│   ├── app.py                   # Application factory
│   ├── server.py                # uvicorn server
│   ├── api/
│   │   ├── deps.py              # Depends: session, bot, current user, admin, captcha
│   │   └── routes/              # /api/me, /api/captcha, /api/feedback, /api/admin/*
│   ├── core/                    # Framework-free logic: initData validation, captcha
│   ├── schemas/                 # Request / response models
│   ├── webhook.py               # Telegram webhook endpoint
│   ├── frontend.py              # Serves the built frontend (SPA fallback)
│   └── tools/                   # dev_init_data: sign initData for local development
├── frontend/                    # Mini App frontend (React + Vite + HeroUI)
│   └── src/
│       ├── app/                 # App shell, providers, query client, error screens
│       ├── api/                 # HTTP client, endpoints, types, query keys
│       ├── features/            # profile, feedback, captcha, admin (overview, users, settings)
│       ├── shared/              # ui, hooks, i18n (en, ru), telegram SDK helpers
│       └── styles/
└── tests/                       # pytest: bot/, database/, webapp/ (fake Telegram API)
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

The Mini App is optional: it is off by default (`WEBAPP_ENABLED=false`). The web server
(FastAPI + uvicorn) starts when the Mini App is enabled or in webhook mode.
It serves the Telegram webhook, the API (`/api/...`) and the built frontend.

```bash
cd frontend
npm install
npm run build           # -> webapp/static, served by the bot
```

Enable it in `.env` and restart the bot. The chat menu button opens the app:

```bash
WEBAPP_ENABLED=true
WEBAPP_URL=https://app.example.com
```

With `WEBAPP_ENABLED=false` the API, the frontend and the menu button are turned off;
the frontend does not need to be built.

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
uv run python -m webapp.tools.dev_init_data <your_telegram_id> > frontend/.env.local
cd frontend && npm run dev                  # open http://localhost:5173
```

`VITE_DEV_THEME=light` in `frontend/.env.local` switches the emulated theme.

### Captcha

Sensitive actions (forms, bonuses, anything that bots would spam) are protected by a
proof-of-work captcha. The app requests a challenge signed by the server and solves it in
the background (≈0.5–1 s on a phone) while the user fills in the form. There are no
pictures to click and no third-party service: nothing leaves your server.

Each challenge is bound to the Telegram user, expires after `CAPTCHA_TTL` seconds and is
accepted only once. Protect an endpoint with one dependency:

```python
from webapp.api.deps import CaptchaRequired


@router.post("/api/bonus", dependencies=[CaptchaRequired])
async def claim_bonus(user: CurrentUser): ...
```

On the frontend use the hook and the status component (see `screens/Feedback.tsx`):

```tsx
const captcha = useCaptcha();
await api.something(data, captcha.payload);   // sent as the X-Captcha header
captcha.refresh();                            // a solution is single-use
```

`CAPTCHA_COST` controls how much work a solution takes; raise it if the protected action is
attacked. Used solutions are kept in process memory: with several bot instances move them to Redis.

## Configuration

All settings are in `.env` (real environment variables take priority):

| Variable | Description | Default |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather | **required** |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs | — |
| `DATABASE_URL` | SQLAlchemy async URL (relative paths: from the project root) | `sqlite+aiosqlite:///data/database.db` |
| `REDIS_URL` | Redis for FSM storage, empty = memory | — |
| `PATH_LOGS` | Log file path | `data/logs.log` |
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
| `WEBAPP_ENABLED` | Turn the Mini App on | `false` |
| `WEBAPP_URL` | Public HTTPS URL of the Mini App, required when enabled | — |
| `WEBAPP_AUTH_TTL` | Max age of Telegram `initData`, seconds | `86400` |
| `CAPTCHA_ENABLED` | Require captcha on protected actions | `true` |
| `CAPTCHA_SECRET` | HMAC key for challenges, derived from `BOT_TOKEN` if empty | — |
| `CAPTCHA_COST` | Work per attempt (higher = slower to solve) | `5000` |
| `CAPTCHA_TTL` | Seconds to solve and submit a challenge | `300` |

## Admin Commands

| Command | Description |
|---|---|
| `/admin` | Admin panel: stats, broadcast, maintenance, backup, logs |
| `/stats` | User statistics |
| `/broadcast` | Send a message to all users |
| `/ban <id>`, `/unban <id>` | Ban or unban a user |
| `/db` | Database backup (SQLite) |
| `/log`, `/clear_log` | Get or clear log files |

## Database

- **SQLite** by default (`data/database.db`), **PostgreSQL** with `uv sync --extra postgres`
  and `DATABASE_URL=postgresql+asyncpg://...`. CI runs the whole test suite on both.
- Relative SQLite paths are resolved against the project root, so the bot uses the same
  database whatever the current directory is.
- SQLite runs in WAL mode with a busy timeout: the bot, the webhook and the Mini App write
  concurrently without "database is locked" errors.
- Dates are stored and returned in UTC with the time zone on every database.
- Names are stored as Telegram sends them; escape them only when building HTML messages
  (`tgbot.utils.text.escape`).
- Upgrading from an older version keeps `tgbot/data/database.db` working; move it to
  `data/database.db` when convenient.

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
uv run pytest           # tests (set TEST_DATABASE_URL to run them on PostgreSQL)
uv run mypy             # type checking
uv run ruff check .     # lint
uv run ruff format .    # format

cd frontend
npm test                # unit tests (Vitest)
npm run lint            # ESLint
npm run format          # Prettier
npm run build           # type check + production build
```

## Adding a New Locale

1. Create `tgbot/locales/xx_xx.json` (copy structure from `en_us.json`)
2. Done: the language is picked by the Telegram language code (`xx`), buttons and command menus are translated automatically. The test suite checks that all locales have the same keys.
