"""Fake Telegram: feeds updates to the dispatcher and records outgoing API calls."""

import itertools
from collections.abc import Callable
from datetime import datetime
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.base import StorageKey
from aiogram.methods import (
    CopyMessage,
    EditMessageReplyMarkup,
    EditMessageText,
    GetMe,
    SendDocument,
    SendMediaGroup,
    SendMessage,
    TelegramMethod,
)
from aiogram.types import CallbackQuery, Chat, Message, MessageEntity, MessageId, Update, User

_ids = itertools.count(1)


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        # chat_id -> exception factory, to simulate errors for specific users
        self.errors: dict[int, Callable[[TelegramMethod[Any]], Exception]] = {}

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None):  # noqa: ASYNC109 - aiogram API
        self.requests.append(method)

        chat_id = getattr(method, "chat_id", None)
        if chat_id in self.errors:
            raise self.errors[chat_id](method)

        chat = Chat(id=chat_id if isinstance(chat_id, int) else 0, type="private")
        now = datetime.now()
        if isinstance(method, SendMessage | SendDocument | EditMessageText):
            text = getattr(method, "text", None) or getattr(method, "caption", None)
            return Message(message_id=next(_ids), date=now, chat=chat, text=text)
        if isinstance(method, SendMediaGroup):
            return [Message(message_id=next(_ids), date=now, chat=chat) for _ in method.media]
        if isinstance(method, CopyMessage):
            return MessageId(message_id=next(_ids))
        if isinstance(method, EditMessageReplyMarkup):
            return Message(message_id=next(_ids), date=now, chat=chat)
        if isinstance(method, GetMe):
            return User(id=123456, is_bot=True, first_name="Bot", username="test_bot")
        return True

    async def close(self) -> None:
        pass

    async def stream_content(self, *args: Any, **kwargs: Any):
        yield b""

    # Helpers for assertions
    def of_type[T](self, method_type: type[T]) -> list[T]:
        return [m for m in self.requests if isinstance(m, method_type)]

    def texts(self) -> list[str]:
        result = []
        for m in self.requests:
            text = getattr(m, "text", None) or getattr(m, "caption", None)
            if isinstance(text, str):
                result.append(text)
        return result

    def clear(self) -> None:
        self.requests.clear()


class TgClient:
    """Sends fake updates from users to the dispatcher."""

    def __init__(self, dp: Dispatcher, bot: Bot, session: FakeSession) -> None:
        self.dp = dp
        self.bot = bot
        self.session = session
        self._users: set[int] = set()

    @staticmethod
    def user(user_id: int, lang: str = "en", first_name: str = "Ivan") -> User:
        return User(id=user_id, is_bot=False, first_name=first_name, language_code=lang)

    async def send(self, user_id: int, text: str | None = None, lang: str = "en", **extra: Any):
        self._users.add(user_id)
        entities = None
        if text and text.startswith("/"):
            entities = [MessageEntity(type="bot_command", offset=0, length=len(text.split()[0]))]
        message = Message(
            message_id=next(_ids),
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            from_user=self.user(user_id, lang),
            text=text,
            entities=entities,
            **extra,
        )
        return await self.dp.feed_update(self.bot, Update(update_id=next(_ids), message=message))

    async def click(self, user_id: int, data: str, lang: str = "en"):
        self._users.add(user_id)
        message = Message(
            message_id=next(_ids),
            date=datetime.now(),
            chat=Chat(id=user_id, type="private"),
            text="keyboard",
        )
        query = CallbackQuery(
            id=str(next(_ids)),
            from_user=self.user(user_id, lang),
            chat_instance="test",
            message=message,
            data=data,
        )
        return await self.dp.feed_update(
            self.bot, Update(update_id=next(_ids), callback_query=query)
        )

    async def state(self, user_id: int) -> str | None:
        key = StorageKey(bot_id=self.bot.id, chat_id=user_id, user_id=user_id)
        return await self.dp.storage.get_state(key)

    async def reset_states(self) -> None:
        for user_id in self._users:
            key = StorageKey(bot_id=self.bot.id, chat_id=user_id, user_id=user_id)
            await self.dp.storage.set_state(key, None)
            await self.dp.storage.set_data(key, {})
