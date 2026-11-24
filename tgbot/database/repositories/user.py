from collections.abc import Sequence

from tgbot.database.models import User
from tgbot.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_user_id(self, user_id: int) -> User | None:
        return await self.get_one(user_id=user_id)

    async def create_user(
        self,
        user_id: int,
        user_login: str = "",
        user_name: str = "",
        user_surname: str = "",
        user_fullname: str = "",
        user_locale: str = "en_us",
    ) -> User:
        return await self.create(
            user_id=user_id,
            user_login=user_login,
            user_name=user_name,
            user_surname=user_surname,
            user_fullname=user_fullname,
            user_locale=user_locale,
        )

    async def update_user(self, user_id: int, **values) -> None:
        await self.update_by(filters={"user_id": user_id}, **values)

    async def get_all_users(self) -> Sequence[User]:
        return await self.get_all()
