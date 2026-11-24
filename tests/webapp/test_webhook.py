import asyncio

from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from tgbot.config import settings

UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 1,
        "date": 1_700_000_000,
        "chat": {"id": 700, "type": "private"},
        "from": {"id": 700, "is_bot": False, "first_name": "Web", "language_code": "en"},
        "text": "/start",
        "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
    },
}


async def test_webhook_checks_secret_and_handles_updates(tg, monkeypatch):
    from webapp.app import create_app

    monkeypatch.setattr(settings, "bot_mode", "webhook")
    monkeypatch.setattr(settings, "webhook_secret", SecretStr("s3cret"))
    app = create_app(tg.bot, tg.dp)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/health")).text == "ok"

        response = await client.post(settings.webhook_path, json=UPDATE)
        assert response.status_code == 401  # no secret header

        headers = {"X-Telegram-Bot-Api-Secret-Token": "s3cret"}
        response = await client.post(settings.webhook_path, json=UPDATE, headers=headers)
        assert response.status_code == 200

        # Updates are processed in background: wait for the answer
        for _ in range(100):
            if tg.session.texts():
                break
            await asyncio.sleep(0.02)
        assert tg.session.texts()[-1].startswith("🔸 Hello, Web")


async def test_webhook_route_absent_in_polling_mode(tg):
    from webapp.app import create_app

    app = create_app(tg.bot, tg.dp)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(settings.webhook_path, json=UPDATE)
        assert response.status_code in (404, 405)
