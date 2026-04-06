from aiogram import BaseMiddleware

from tgbot.database.engine import async_session
from tgbot.database.repositories import UserRepository
from tgbot.services.locale import Locale, language_code_to_locale
from tgbot.utils.const_functions import clear_html


class ExistsUserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        this_user = data.get("event_from_user")

        if not this_user.is_bot:
            user_login = (this_user.username or "").lower()
            user_name = clear_html(this_user.first_name) or ""
            user_surname = clear_html(this_user.last_name) or ""
            user_fullname = user_name
            user_locale = language_code_to_locale(this_user.language_code)
            if user_surname:
                user_fullname += f" {user_surname}"

            async with async_session() as session:
                repo = UserRepository(session)
                user = await repo.get_by_user_id(this_user.id)

                if user is None:
                    user = await repo.create_user(
                        user_id=this_user.id,
                        user_login=user_login,
                        user_name=user_name,
                        user_surname=user_surname,
                        user_fullname=user_fullname,
                        user_locale=user_locale,
                    )
                else:
                    changes = {}
                    if user_name != user.user_name:
                        changes["user_name"] = user_name
                    if user_surname != user.user_surname:
                        changes["user_surname"] = user_surname
                    if user_fullname != user.user_fullname:
                        changes["user_fullname"] = user_fullname
                    if user_login != user.user_login:
                        changes["user_login"] = user_login
                    if user_locale != user.user_locale:
                        changes["user_locale"] = user_locale

                    if changes:
                        await repo.update_user(user.user_id, **changes)
                        user = await repo.get_by_user_id(this_user.id)

                await session.commit()
                data["User"] = user

            data["locale"] = Locale(user.user_locale)

        return await handler(event, data)
