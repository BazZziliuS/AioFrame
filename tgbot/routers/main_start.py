from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message

from tgbot.database.models import User as UserModel
from tgbot.keyboards.reply_main import menu_reply
from tgbot.services.locale import Locale
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


# Main menu
@router.message(F.text.in_(("menu", "return", "start")))
@router.message(Command(commands=["start"]))
async def main_start(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    await message.answer(
        locale("start.greeting", user_name=User.user_name),
        reply_markup=menu_reply(message.from_user.id, locale),
    )
