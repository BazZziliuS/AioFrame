import asyncio
from collections.abc import Iterable
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter

from tgbot.database.engine import async_session
from tgbot.database.repositories import UserRepository
from tgbot.utils.misc.bot_logging import bot_logger

# Running broadcast tasks: keeps references so tasks are not garbage collected
running_tasks: set[asyncio.Task[BroadcastResult]] = set()


@dataclass(slots=True)
class BroadcastResult:
    sent: int = 0
    blocked: int = 0
    failed: int = 0


def is_running() -> bool:
    return any(not task.done() for task in running_tasks)


async def _copy_with_retry(bot: Bot, user_id: int, from_chat_id: int, message_id: int) -> None:
    try:
        await bot.copy_message(user_id, from_chat_id, message_id)
    except TelegramRetryAfter as error:
        # Flood control: wait as long as Telegram asks and retry once
        await asyncio.sleep(error.retry_after)
        await bot.copy_message(user_id, from_chat_id, message_id)


async def broadcast(
    bot: Bot,
    user_ids: Iterable[int],
    from_chat_id: int,
    message_id: int,
    rate: float,
) -> BroadcastResult:
    """Copy a message to users with rate limiting.

    Users who blocked the bot are marked with `is_blocked` and skipped next time.
    """
    result = BroadcastResult()
    blocked_ids: list[int] = []
    delay = 1 / rate

    for user_id in user_ids:
        try:
            await _copy_with_retry(bot, user_id, from_chat_id, message_id)
            result.sent += 1
        except TelegramForbiddenError:
            result.blocked += 1
            blocked_ids.append(user_id)
        except TelegramAPIError as error:
            result.failed += 1
            bot_logger.warning("Broadcast to %s failed: %s", user_id, error)
        await asyncio.sleep(delay)

    if blocked_ids:
        async with async_session() as session:
            repo = UserRepository(session)
            for user_id in blocked_ids:
                await repo.set_blocked(user_id, True)
            await session.commit()

    bot_logger.info("Broadcast finished: %s", result)
    return result
