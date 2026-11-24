"""Proof-of-work captcha for sensitive Mini App actions.

The client asks for a challenge, spends some CPU solving it (about 0.5-1 s on a phone)
and sends the solution in the `X-Captcha` header. It costs nothing for a person and
makes mass automated requests expensive. No third-party service and no user data
leave the server.

Protect any endpoint with one dependency:

    @router.post("/something", dependencies=[Depends(require_captcha)])

Guarantees:
- the challenge is signed (HMAC) and cannot be forged or modified;
- it is bound to the Telegram user who requested it;
- it expires after CAPTCHA_TTL seconds;
- every solution is accepted only once (replay protection).

Note: used solutions are remembered in process memory. With several bot instances
behind a load balancer move `_used` to Redis.
"""

import asyncio
import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import altcha
from cachetools import TTLCache
from fastapi import Depends, Header, HTTPException, status

from tgbot.data.config import settings
from tgbot.database.models import User
from webapp.auth import get_current_user

ALGORITHM = "PBKDF2/SHA-256"  # Native WebCrypto in every Telegram client: fast and reliable

# Signatures of already used challenges, kept until they would expire anyway
_used: TTLCache[str, bool] = TTLCache(maxsize=100_000, ttl=settings.captcha_ttl)


def _secret() -> str:
    if settings.captcha_secret:
        return settings.captcha_secret.get_secret_value()
    # Stable per bot, never leaves the server, independent from the token itself
    token = settings.bot_token.get_secret_value().encode()
    return hmac.new(token, b"aioframe-captcha", hashlib.sha256).hexdigest()


def create_challenge(user_id: int) -> dict[str, Any]:
    challenge = altcha.create_challenge(
        ALGORITHM,
        settings.captcha_cost,
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.captcha_ttl),
        data={"uid": str(user_id)},  # signed together with the challenge
        hmac_secret=_secret(),
    )
    return challenge.to_dict()


def _reject(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail)


async def verify_captcha(payload: str, user_id: int) -> None:
    """Raise HTTP 400 unless `payload` is a valid, fresh, unused solution of this user."""
    try:
        parsed = altcha.Payload.from_base64(payload)
    except Exception as error:  # malformed base64 / JSON / fields
        raise _reject("captcha_invalid") from error

    result = await asyncio.to_thread(altcha.verify_solution, parsed, _secret())
    if result.expired:
        raise _reject("captcha_expired")
    if not result.verified:
        raise _reject("captcha_invalid")

    data = parsed.challenge.parameters.data or {}
    if data.get("uid") != str(user_id):
        raise _reject("captcha_invalid")  # solved by / issued for another user

    signature = parsed.challenge.signature or ""
    if signature in _used:
        raise _reject("captcha_used")
    _used[signature] = True


async def require_captcha(
    user: Annotated[User, Depends(get_current_user)],
    x_captcha: Annotated[str | None, Header()] = None,
) -> None:
    """FastAPI dependency: the request must carry a solved captcha (if enabled)."""
    if not settings.captcha_enabled:
        return
    if not x_captcha:
        raise _reject("captcha_required")
    await verify_captcha(x_captcha, user.user_id)


Captcha = Depends(require_captcha)
