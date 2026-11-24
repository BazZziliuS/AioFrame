import aiofiles
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.media_group import MediaGroupBuilder

from tgbot.data.config import settings
from tgbot.database.engine import async_session
from tgbot.database.repositories import SettingsRepository, UserRepository
from tgbot.keyboards.inline_main import admin_panel_inline
from tgbot.services.backup import database_backup
from tgbot.services.locale import Locale
from tgbot.utils.const_functions import get_date
from tgbot.utils.misc.bot_callbacks import AdminAction, AdminCallback
from tgbot.utils.misc.bot_filters import IsAdmin, LocaleText

router = Router(name=__name__)
# Every handler of this router is admin-only: messages AND button callbacks
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


def _log_files() -> list[str]:
    log_dir = settings.path_logs.parent
    candidates = [settings.path_logs, log_dir / "sv_log_err.log", log_dir / "sv_log_out.log"]
    # Telegram rejects empty files
    return [str(path) for path in candidates if path.is_file() and path.stat().st_size > 0]


async def _stats_text(locale: Locale) -> str:
    async with async_session() as session:
        stats = await UserRepository(session).get_stats()

    return locale(
        "admin.stats",
        total=stats.total,
        new_day=stats.new_day,
        new_week=stats.new_week,
        active=stats.active,
        banned=stats.banned,
        blocked=stats.blocked,
    )


async def _send_backup(message: Message, locale: Locale) -> None:
    backup = await database_backup()
    if backup is None:
        await message.answer(locale("admin.backup_unsupported"))
        return

    await message.answer_document(
        backup,
        caption=f"<b>{locale('admin.backup_caption', date=get_date())}</b>",
    )


async def _send_logs(message: Message, locale: Locale) -> None:
    files = _log_files()
    caption = f"<b>{locale('admin.logs_caption', date=get_date(full=False))}</b>"

    if not files:
        await message.answer(locale("admin.logs_empty"))
    elif len(files) == 1:
        # sendMediaGroup needs at least 2 items
        await message.answer_document(FSInputFile(files[0]), caption=caption)
    else:
        media_group = MediaGroupBuilder(caption=caption)
        for path in files:
            media_group.add_document(media=FSInputFile(path))
        await message.answer_media_group(media=media_group.build())


################################### PANEL ####################################
@router.message(LocaleText("menu.admin_button"))
@router.message(Command(commands=["admin"]))
async def admin_panel(message: Message, state: FSMContext, locale: Locale):
    await state.clear()

    async with async_session() as session:
        is_maintenance = await SettingsRepository(session).is_maintenance()

    await message.answer(
        locale("admin.panel"),
        reply_markup=admin_panel_inline(locale, is_maintenance),
    )


@router.callback_query(AdminCallback.filter(F.action == AdminAction.STATS))
async def admin_stats_callback(call: CallbackQuery, locale: Locale):
    await call.answer()
    if isinstance(call.message, Message):
        await call.message.answer(await _stats_text(locale))


@router.callback_query(AdminCallback.filter(F.action == AdminAction.MAINTENANCE))
async def admin_maintenance_callback(call: CallbackQuery, locale: Locale):
    async with async_session() as session:
        repo = SettingsRepository(session)
        enabled = not await repo.is_maintenance()
        await repo.set_maintenance(enabled)
        await session.commit()

    await call.answer(
        locale("admin.maintenance_on" if enabled else "admin.maintenance_off")
        .replace("<b>", "")
        .replace("</b>", ""),
        show_alert=True,
    )
    if isinstance(call.message, Message):
        await call.message.edit_reply_markup(reply_markup=admin_panel_inline(locale, enabled))


@router.callback_query(AdminCallback.filter(F.action == AdminAction.BACKUP))
async def admin_backup_callback(call: CallbackQuery, locale: Locale):
    await call.answer()
    if isinstance(call.message, Message):
        await _send_backup(call.message, locale)


@router.callback_query(AdminCallback.filter(F.action == AdminAction.LOGS))
async def admin_logs_callback(call: CallbackQuery, locale: Locale):
    await call.answer()
    if isinstance(call.message, Message):
        await _send_logs(call.message, locale)


################################## COMMANDS ##################################
@router.message(Command(commands=["stats"]))
async def admin_stats(message: Message, locale: Locale):
    await message.answer(await _stats_text(locale))


# Get Database file
@router.message(Command(commands=["db", "database"]))
async def admin_database(message: Message, state: FSMContext, locale: Locale):
    await state.clear()
    await _send_backup(message, locale)


# Get Logs file
@router.message(Command(commands=["log", "logs"]))
async def admin_log(message: Message, state: FSMContext, locale: Locale):
    await state.clear()
    await _send_logs(message, locale)


# Clear logs file
@router.message(Command(commands=["clear_log", "clear_logs", "log_clear", "logs_clear"]))
async def admin_logs_clear(message: Message, state: FSMContext, locale: Locale):
    await state.clear()

    for path in _log_files():
        async with aiofiles.open(path, "w", encoding="utf-8") as file:
            await file.write(f"{get_date()} | LOGS WAS CLEAR\n")

    await message.answer(locale("admin.logs_cleared"))


# Ban / unban: /ban 123456789
@router.message(Command(commands=["ban", "unban"]))
async def admin_ban(message: Message, command: CommandObject, locale: Locale):
    args = (command.args or "").strip()
    if not args.isdigit():
        await message.answer(locale("admin.ban_usage"))
        return

    user_id = int(args)
    banned = command.command == "ban"
    if banned and settings.is_admin(user_id):
        await message.answer(locale("admin.ban_admin"))
        return

    async with async_session() as session:
        found = await UserRepository(session).set_banned(user_id, banned)
        await session.commit()

    if not found:
        await message.answer(locale("admin.user_not_found", user_id=user_id))
    else:
        await message.answer(
            locale("admin.ban_done" if banned else "admin.unban_done", user_id=user_id)
        )
