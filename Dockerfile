# Stage 1: build the Mini App (React + Vite) into webapp/static
FROM node:24-alpine AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime with the bot, API and the built frontend
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    # Persistent data lives in the /app/data volume
    DATABASE_URL=sqlite+aiosqlite:////app/data/database.db \
    PATH_LOGS=/app/data/logs.log

# Dependencies first: this layer is cached until pyproject.toml / uv.lock change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --all-extras --no-install-project

COPY . .
COPY --from=frontend /build/webapp/static ./webapp/static

RUN useradd --create-home --uid 1000 bot \
    && mkdir -p /app/data \
    && chown -R bot:bot /app/data
USER bot

VOLUME ["/app/data"]
EXPOSE 8080

CMD ["python", "main.py"]
