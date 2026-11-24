import asyncio

from aiohttp.test_utils import TestClient, TestServer
from pydantic import SecretStr

from tgbot.data.config import settings

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


async def test_webhook_app_checks_secret_and_handles_updates(tg, monkeypatch):
    from main import create_webhook_app

    monkeypatch.setattr(settings, "webhook_secret", SecretStr("s3cret"))
    app = create_webhook_app(tg.bot, tg.dp)

    async with TestClient(TestServer(app)) as client:
        assert await (await client.get("/health")).text() == "ok"

        response = await client.post(settings.webhook_path, json=UPDATE)
        assert response.status == 401  # no secret header

        headers = {"X-Telegram-Bot-Api-Secret-Token": "s3cret"}
        response = await client.post(settings.webhook_path, json=UPDATE, headers=headers)
        assert response.status == 200

        # Updates are processed in background: wait for the answer
        for _ in range(100):
            if tg.session.texts():
                break
            await asyncio.sleep(0.02)
        assert tg.session.texts()[-1].startswith("🔸 Hello, Web")
