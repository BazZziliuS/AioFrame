import time

import pytest
from httpx import ASGITransport, AsyncClient

from tests.helpers import ADMIN_ID, auth
from tgbot.config import settings
from tgbot.database import SettingsRepository, UserRepository, async_session


################################### AUTH #####################################
async def test_me_creates_user_from_init_data(api):
    response = await api.get("/api/me", headers=auth(800))
    assert response.status_code == 200
    body = response.json()
    assert body["is_admin"] is False
    assert body["user"]["user_id"] == 800
    assert body["user"]["user_fullname"] == "Web User"
    assert body["user"]["user_locale"] == "ru_ru"


@pytest.mark.parametrize(
    ("headers", "detail"),
    [
        ({}, "missing_init_data"),
        ({"Authorization": "Bearer abc"}, "missing_init_data"),
        ({"Authorization": "tma user=1&hash=deadbeef"}, "invalid_init_data"),
    ],
)
async def test_requests_without_valid_init_data_are_rejected(api, headers, detail):
    response = await api.get("/api/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == detail


async def test_init_data_signed_by_another_bot_is_rejected(api):
    response = await api.get("/api/me", headers=auth(801, token="999:OTHER-BOT"))
    assert response.status_code == 401


async def test_expired_init_data_is_rejected(api):
    old = int(time.time()) - settings.webapp_auth_ttl - 60
    response = await api.get("/api/me", headers=auth(802, auth_date=old))
    assert response.json()["detail"] == "init_data_expired"


async def test_banned_and_maintenance(api):
    await api.get("/api/me", headers=auth(803))
    async with async_session() as session:
        await UserRepository(session).set_banned(803, True)
        await session.commit()
    assert (await api.get("/api/me", headers=auth(803))).status_code == 403

    async with async_session() as session:
        await SettingsRepository(session).set_maintenance(True)
        await session.commit()
    response = await api.get("/api/me", headers=auth(804))
    assert response.status_code == 503
    assert (await api.get("/api/me", headers=auth(ADMIN_ID))).status_code == 200


################################### ADMIN ####################################
async def test_admin_endpoints_require_admin(api):
    for method, url in [
        ("GET", "/api/admin/stats"),
        ("GET", "/api/admin/users"),
        ("PATCH", "/api/admin/users/1"),
        ("GET", "/api/admin/settings"),
        ("PATCH", "/api/admin/settings"),
    ]:
        response = await api.request(method, url, headers=auth(805), json={})
        assert response.status_code == 403, url
        assert response.json()["detail"] == "admin_only"


async def test_admin_stats_users_search_and_ban(api):
    admin = auth(ADMIN_ID)
    for user_id in (900, 901, 902):
        await api.get("/api/me", headers=auth(user_id))

    stats = (await api.get("/api/admin/stats", headers=admin)).json()
    assert stats["total"] == 4  # 3 users + admin

    page = (await api.get("/api/admin/users", headers=admin, params={"limit": 2})).json()
    assert page["total"] == 4 and len(page["items"]) == 2

    found = (await api.get("/api/admin/users", headers=admin, params={"q": "901"})).json()
    assert [u["user_id"] for u in found["items"]] == [901]

    response = await api.patch("/api/admin/users/901", headers=admin, json={"is_banned": True})
    assert response.json()["is_banned"] is True
    assert (await api.get("/api/me", headers=auth(901))).status_code == 403

    response = await api.patch(
        f"/api/admin/users/{ADMIN_ID}", headers=admin, json={"is_banned": True}
    )
    assert response.json()["detail"] == "cannot_ban_admin"
    response = await api.patch("/api/admin/users/123", headers=admin, json={"is_banned": True})
    assert response.status_code == 404


async def test_admin_maintenance_toggle(api):
    admin = auth(ADMIN_ID)
    response = await api.patch("/api/admin/settings", headers=admin, json={"is_maintenance": True})
    assert response.json() == {"is_maintenance": True}
    assert (await api.get("/api/admin/settings", headers=admin)).json()["is_maintenance"] is True


################################## FRONTEND ##################################
async def test_unknown_api_path_is_json_404_not_spa(api):
    response = await api.get("/api/nope")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")


async def test_spa_fallback(api, tmp_path, monkeypatch):
    from webapp import frontend as app_module

    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<div id=root></div>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    monkeypatch.setattr(app_module, "STATIC_DIR", tmp_path)

    assert "id=root" in (await api.get("/admin/users")).text  # client-side route
    asset = await api.get("/assets/app.js")
    assert "immutable" in asset.headers["cache-control"]
    assert (await api.get("/../pyproject.toml")).status_code == 200  # falls back to index
    assert "id=root" in (await api.get("/../pyproject.toml")).text


async def test_webapp_can_be_disabled(tg, monkeypatch):
    from webapp.app import create_app

    monkeypatch.setattr(settings, "webapp_enabled", False)
    app = create_app(tg.bot, tg.dp)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/me", headers=auth(ADMIN_ID))).status_code == 404
        assert (await client.get("/")).status_code == 404
        assert (await client.get("/health")).text == "ok"


async def test_menu_button_follows_webapp_switch(tg, monkeypatch):
    from aiogram.methods import SetChatMenuButton
    from aiogram.types import MenuButtonDefault, MenuButtonWebApp

    from tgbot.bot import setup_menu_button

    await setup_menu_button(tg.bot)
    assert isinstance(tg.session.of_type(SetChatMenuButton)[-1].menu_button, MenuButtonWebApp)

    monkeypatch.setattr(settings, "webapp_enabled", False)
    await setup_menu_button(tg.bot)
    assert isinstance(tg.session.of_type(SetChatMenuButton)[-1].menu_button, MenuButtonDefault)
