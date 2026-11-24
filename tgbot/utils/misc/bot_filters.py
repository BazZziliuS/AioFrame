from aiogram.filters import BaseFilter
from aiogram.types import Message, TelegramObject, User

from tgbot.data.config import settings
from tgbot.services.locale import get_translations


class IsAdmin(BaseFilter):
    """Passes only admins. Works for any event type (messages, callbacks, ...)."""

    async def __call__(self, event: TelegramObject, event_from_user: User | None = None) -> bool:
        return event_from_user is not None and settings.is_admin(event_from_user.id)


class LocaleText(BaseFilter):
    """Matches a reply-keyboard button by locale key in any available language.

    Example: `@router.message(LocaleText("menu.admin_button"))`
    """

    def __init__(self, key: str) -> None:
        self.key = key

    async def __call__(self, message: Message) -> bool:
        return message.text is not None and message.text in get_translations(self.key)
