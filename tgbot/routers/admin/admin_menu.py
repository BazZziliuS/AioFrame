import os

import aiofiles
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.media_group import MediaGroupBuilder

from tgbot.data.config import PATH_DATABASE, PATH_LOGS
from tgbot.database.models import User as UserModel
from tgbot.keyboards.inline_main import admin_inline
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import get_date
from tgbot.utils.misc.bot_models import ARS, FSM

router = Router(name=__name__)


# Message - Admin button
@router.message(F.text.in_(("Admin button", "Админ панель")))
async def admin_button_inline(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    await message.answer(
        locale("admin.inline_keyboards"), reply_markup=admin_inline(locale)
    )


# Callback - Admin X
@router.callback_query(F.data == "admin_inline_x")
async def admin_callback_inline_x(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await call.answer("Click Admin X")


# Callback - Admin
@router.callback_query(F.data.startswith("admin_inline:"))
async def admin_callback_inline(
    call: CallbackQuery,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    get_data = call.data.split(":")[1]

    await call.answer(f"Click Admin - {get_data}", True)


# Get Database file
@router.message(Command(commands=["db", "database"]))
async def admin_database(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    await message.answer_document(
        FSInputFile(PATH_DATABASE),
        caption=f"<b>{locale('admin.backup_caption', date=get_date())}</b>",
    )


# Get Logs file
@router.message(Command(commands=["log", "logs"]))
async def admin_log(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    media_group = MediaGroupBuilder(
        caption=f"<b>{locale('admin.logs_caption', date=get_date(full=False))}</b>",
    )

    if os.path.isfile(PATH_LOGS):
        media_group.add_document(media=FSInputFile(PATH_LOGS))

    if os.path.isfile("tgbot/data/sv_log_err.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_err.log"))

    if os.path.isfile("tgbot/data/sv_log_out.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_out.log"))

    await message.answer_media_group(media=media_group.build())


# Clear logs file
@router.message(
    Command(commands=["clear_log", "clear_logs", "log_clear", "logs_clear"])
)
async def admin_logs_clear(
    message: Message,
    bot: Bot,
    state: FSM,
    arSession: ARS,
    User: UserModel,
    locale: Locale,
):
    await state.clear()

    if os.path.isfile(PATH_LOGS):
        async with aiofiles.open(PATH_LOGS, "w") as file:
            await file.write(f"{get_date()} | LOGS WAS CLEAR")

    if os.path.isfile("tgbot/data/sv_log_err.log"):
        async with aiofiles.open("tgbot/data/sv_log_err.log", "w") as file:
            await file.write(f"{get_date()} | LOGS WAS CLEAR")

    if os.path.isfile("tgbot/data/sv_log_out.log"):
        async with aiofiles.open("tgbot/data/sv_log_out.log", "w") as file:
            await file.write(f"{get_date()} | LOGS WAS CLEAR")

    await message.answer(locale("admin.logs_cleared"))
