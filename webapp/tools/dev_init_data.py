"""Signed initData for opening the Mini App in a regular browser during development.

Usage:
    uv run python -m webapp.tools.dev_init_data 123456789 >> frontend/.env.local

Prints `VITE_DEV_INIT_DATA=...` signed with BOT_TOKEN, valid for WEBAPP_AUTH_TTL.
Never use it in production: anyone with this string can act as that user until it expires.
"""

import hashlib
import hmac
import json
import sys
import time
from urllib.parse import urlencode

from tgbot.config import settings


def sign_init_data(user: dict[str, object], token: str) -> str:
    fields = {
        "query_id": "dev",
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
        "auth_date": str(int(time.time())),
        # Ed25519 signature for third parties: Telegram always sends it, SDKs require it
        "signature": "dev",
    }
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        sys.exit("Usage: python -m webapp.tools.dev_init_data <telegram_user_id> [language_code]")

    user = {
        "id": int(sys.argv[1]),
        "first_name": "Dev",
        "last_name": "User",
        "username": "dev_user",
        "language_code": sys.argv[2] if len(sys.argv) > 2 else "ru",
    }
    print(f"VITE_DEV_INIT_DATA={sign_init_data(user, settings.bot_token.get_secret_value())}")


if __name__ == "__main__":
    main()
