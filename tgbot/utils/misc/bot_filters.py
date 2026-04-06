from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.data.config import get_admins


# Filter on admin right
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in get_admins()
