"""Proof-of-work captcha for sensitive Mini App actions.

The client asks for a challenge, spends some CPU solving it (about 0.5-1 s on a phone)
and sends the solution back. It costs nothing for a person and makes mass automated
requests expensive. No third-party service and no user data leave the server.

Guarantees:
- the challenge is signed (HMAC) and cannot be forged or modified;
- it is bound to the Telegram user who requested it;
- it expires after CAPTCHA_TTL seconds;
- every solution is accepted only once (replay protection).

Used solutions are remembered in process memory. With several bot instances behind
a load balancer move `_used` to Redis.

The FastAPI dependency that protects endpoints lives in `webapp.api.deps`.
"""

import asyncio
import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any

import altcha
from cachetools import TTLCache

from tgbot.config import settings

ALGORITHM = "PBKDF2/SHA-256"  # native WebCrypto in every Telegram client: fast and reliable

# Signatures of already used challenges, kept until they would expire anyway
_used: TTLCache[str, bool] = TTLCache(maxsize=100_000, ttl=settings.captcha_ttl)


class CaptchaError(Exception):
    """The solution is missing, invalid, expired or reused. `code` is returned to the client."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


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
    result: dict[str, Any] = challenge.to_dict()
    return result


async def verify_captcha(payload: str | None, user_id: int) -> None:
    """Raise CaptchaError unless `payload` is a valid, fresh, unused solution of this user."""
    if not payload:
        raise CaptchaError("captcha_required")

    try:
        parsed = altcha.Payload.from_base64(payload)
    except Exception as error:  # malformed base64 / JSON / fields
        raise CaptchaError("captcha_invalid") from error

    result = await asyncio.to_thread(altcha.verify_solution, parsed, _secret())
    if result.expired:
        raise CaptchaError("captcha_expired")
    if not result.verified:
        raise CaptchaError("captcha_invalid")

    data = parsed.challenge.parameters.data or {}
    if data.get("uid") != str(user_id):
        raise CaptchaError("captcha_invalid")  # issued for another user

    signature = parsed.challenge.signature or ""
    if signature in _used:
        raise CaptchaError("captcha_used")
    _used[signature] = True
