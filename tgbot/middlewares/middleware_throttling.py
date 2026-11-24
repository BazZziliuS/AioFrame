import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, User
from cachetools import TTLCache

from tgbot.services.locale import Locale, language_code_to_locale

THROTTLE_PENALTIES = [
    (0, True),  # count=0: пропускаем, но увеличиваем rate на 2
    (2, True),  # count=1: пропускаем, rate += 3
    (3, False),  # count=2: блокируем с предупреждением, rate += 5
    (5, False),  # count=3+: молча блокируем
]


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, default_rate: float = 0.5) -> None:
        self.default_rate = default_rate
        self.users = TTLCache(maxsize=10_000, ttl=600)

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data,
    ):
        this_user: User = data.get("event_from_user")

        rate = get_flag(data, "rate") or self.default_rate
        if rate == 0:
            return await handler(event, data)

        now = time.monotonic()
        user_data = self.users.get(this_user.id)

        # Первое сообщение или cooldown прошёл — пропускаем
        if user_data is None or (now - user_data[0]) >= user_data[2]:
            self.users[this_user.id] = (now, 0, rate)
            return await handler(event, data)

        # Спам — эскалация
        count = user_data[1]
        penalty_idx = min(count, len(THROTTLE_PENALTIES) - 1)
        rate_add, allow = THROTTLE_PENALTIES[penalty_idx]

        self.users[this_user.id] = (now, count + 1, rate + rate_add)

        if allow:
            return await handler(event, data)

        if count == 2:  # first blocked message
            locale: Locale = data.get("locale") or Locale(
                language_code_to_locale(this_user.language_code)
            )
            await event.reply(locale("throttling.spam_warning"))

        # count >= 2: молча игнорируем
        return None
