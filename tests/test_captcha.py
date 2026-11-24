import base64
import json
from datetime import UTC, datetime, timedelta

import altcha
import pytest
from aiogram.methods import SendMessage
from httpx import ASGITransport, AsyncClient

from tests.conftest import ADMIN_ID
from tests.test_webapp_api import auth
from tgbot.data.config import settings
from webapp import captcha as captcha_module


@pytest.fixture
async def api(tg):
    from webapp.app import create_app

    app = create_app(tg.bot, tg.dp)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def solve(api: AsyncClient, user_id: int) -> str:
    """Do what the frontend does: get a challenge, solve it, encode the payload."""
    response = await api.get("/api/captcha", headers=auth(user_id))
    body = response.json()
    assert body["enabled"] is True
    challenge = altcha.Challenge.from_dict(body["challenge"])
    solution = altcha.solve_challenge(challenge)
    assert solution is not None
    return altcha.Payload(challenge=challenge, solution=solution).to_base64()


async def send(api: AsyncClient, user_id: int, captcha: str | None, text: str = "Hello"):
    headers = auth(user_id) | ({"X-Captcha": captcha} if captcha else {})
    return await api.post("/api/feedback", headers=headers, json={"text": text})


async def test_valid_solution_is_accepted_once(api, tg):
    payload = await solve(api, 1000)

    response = await send(api, 1000, payload, "Hi <admins>")
    assert response.status_code == 200
    to_admin = [m for m in tg.session.of_type(SendMessage) if m.chat_id == ADMIN_ID][-1]
    assert "Hi &lt;admins&gt;" in to_admin.text

    replay = await send(api, 1000, payload)
    assert replay.json()["detail"] == "captcha_used"


async def test_missing_and_malformed_captcha(api):
    assert (await send(api, 1001, None)).json()["detail"] == "captcha_required"
    assert (await send(api, 1001, "not-base64!")).json()["detail"] == "captcha_invalid"


async def test_challenge_of_another_user_is_rejected(api):
    payload = await solve(api, 1002)
    response = await send(api, 1003, payload)
    assert response.json()["detail"] == "captcha_invalid"


async def test_tampered_solution_is_rejected(api):
    payload = json.loads(base64.b64decode(await solve(api, 1004)))
    payload["solution"]["counter"] += 1
    forged = base64.b64encode(json.dumps(payload).encode()).decode()
    assert (await send(api, 1004, forged)).json()["detail"] == "captcha_invalid"


async def test_challenge_signed_with_another_secret_is_rejected(api):
    challenge = altcha.create_challenge(
        captcha_module.ALGORITHM,
        1000,
        data={"uid": "1005"},
        hmac_secret="attacker-secret",
        expires_at=datetime.now(UTC) + timedelta(minutes=5),
    )
    solution = altcha.solve_challenge(challenge)
    payload = altcha.Payload(challenge=challenge, solution=solution).to_base64()
    assert (await send(api, 1005, payload)).json()["detail"] == "captcha_invalid"


async def test_expired_challenge_is_rejected(api, monkeypatch):
    monkeypatch.setattr(settings, "captcha_ttl", -1)  # already expired when issued
    payload = await solve(api, 1006)
    assert (await send(api, 1006, payload)).json()["detail"] == "captcha_expired"


async def test_disabled_captcha_is_not_required(api, monkeypatch):
    monkeypatch.setattr(settings, "captcha_enabled", False)
    assert (await api.get("/api/captcha", headers=auth(1007))).json() == {
        "enabled": False,
        "challenge": None,
    }
    assert (await send(api, 1007, None)).status_code == 200


async def test_feedback_validates_text(api):
    payload = await solve(api, 1008)
    assert (await send(api, 1008, payload, text="")).status_code == 422
