import asyncio

from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import (
    AnswerCallbackQuery,
    CopyMessage,
    EditMessageReplyMarkup,
    SendDocument,
    SendMessage,
    SetMyCommands,
)
from aiogram.types import PhotoSize

from tests.conftest import ADMIN_ID
from tgbot.database import SettingsRepository, UserRepository, async_session
from tgbot.services import broadcast as broadcast_service
from tgbot.services.locale import Locale
from tgbot.utils.misc.bot_callbacks import AdminAction, AdminCallback, BroadcastCallback

EN, RU = Locale("en_us"), Locale("ru_ru")


def cb(action: AdminAction) -> str:
    return AdminCallback(action=action).pack()


async def get_user(user_id: int):
    async with async_session() as session:
        return await UserRepository(session).get_by_user_id(user_id)


#################################### BASICS ##################################
async def test_start_registers_user_and_uses_language(tg):
    await tg.send(100, "/start", lang="ru", first_name="Ив<ан>")
    assert tg.session.texts()[-1].startswith("🔸 Привет")

    user = await get_user(100)
    assert user.user_locale == "ru_ru"


async def test_reply_buttons_match_any_language(tg):
    await tg.send(101, "Пользователь", lang="en")  # Russian button text, English user
    assert tg.session.texts()[-1] == EN("user.inline_keyboards")


async def test_unknown_message_and_callback(tg):
    await tg.send(102, "hello")
    assert tg.session.texts()[-1] == EN("missed.unknown_command")

    await tg.click(102, "garbage")
    answer = tg.session.of_type(AnswerCallbackQuery)[-1]
    assert answer.text == EN("missed.miss_callback", data="garbage")


async def test_set_commands_for_every_language(tg):
    from tgbot.utils.misc.bot_commands import set_commands

    await set_commands(tg.bot)
    calls = tg.session.of_type(SetMyCommands)
    assert {c.language_code for c in calls} == {None, "ru"}
    admin_calls = [c for c in calls if getattr(c.scope, "chat_id", None) == ADMIN_ID]
    assert any(cmd.command == "broadcast" for cmd in admin_calls[0].commands)


################################# ADMIN ACCESS ###############################
async def test_non_admin_cannot_use_admin_buttons_or_commands(tg):
    await tg.send(200, "/start")
    tg.session.clear()

    # Callbacks used to bypass the IsAdmin filter
    for action in AdminAction:
        await tg.click(200, cb(action))
    await tg.send(200, "/stats")
    await tg.send(200, "Admin button")

    answers = tg.session.of_type(AnswerCallbackQuery)
    assert len(answers) == len(AdminAction)
    assert all(a.text.startswith("❗️ Miss callback") for a in answers)
    assert tg.session.texts()[-2:] == [EN("missed.unknown_command")] * 2

    async with async_session() as session:
        assert await SettingsRepository(session).is_maintenance() is False


async def test_admin_panel_and_stats(tg):
    await tg.send(ADMIN_ID, "Админ панель", lang="ru")
    panel = tg.session.of_type(SendMessage)[-1]
    assert panel.text == RU("admin.panel")

    await tg.click(ADMIN_ID, cb(AdminAction.STATS), lang="ru")
    assert "Всего пользователей: <code>1</code>" in tg.session.texts()[-1]


################################# MAINTENANCE ################################
async def test_maintenance_mode_blocks_users_but_not_admins(tg):
    await tg.send(300, "/start")
    await tg.click(ADMIN_ID, cb(AdminAction.MAINTENANCE))
    assert tg.session.of_type(EditMessageReplyMarkup)  # panel button switched

    tg.session.clear()
    await tg.send(300, "/start")
    assert tg.session.texts() == [EN("access.maintenance")]

    await tg.click(300, "user_inline_x")
    assert tg.session.of_type(AnswerCallbackQuery)[-1].show_alert

    await tg.send(ADMIN_ID, "/start")
    assert tg.session.texts()[-1].startswith("🔸 Hello")

    await tg.click(ADMIN_ID, cb(AdminAction.MAINTENANCE))  # switch off
    tg.session.clear()
    await tg.send(300, "/start")
    assert tg.session.texts()[-1].startswith("🔸 Hello")


##################################### BAN ####################################
async def test_ban_and_unban(tg):
    await tg.send(400, "/start")

    await tg.send(ADMIN_ID, "/ban 400")
    assert tg.session.texts()[-1] == EN("admin.ban_done", user_id=400)

    tg.session.clear()
    await tg.send(400, "/start")
    await tg.click(400, "user_inline_x")
    assert tg.session.texts() == []  # banned user is ignored
    assert tg.session.of_type(AnswerCallbackQuery)[0].text is None  # only spinner stopped

    await tg.send(ADMIN_ID, "/unban 400")
    tg.session.clear()
    await tg.send(400, "/start")
    assert tg.session.texts()[-1].startswith("🔸 Hello")


async def test_ban_validation(tg):
    await tg.send(ADMIN_ID, "/ban")
    assert tg.session.texts()[-1] == EN("admin.ban_usage")
    await tg.send(ADMIN_ID, f"/ban {ADMIN_ID}")
    assert tg.session.texts()[-1] == EN("admin.ban_admin")
    await tg.send(ADMIN_ID, "/ban 987654")
    assert tg.session.texts()[-1] == EN("admin.user_not_found", user_id=987654)


################################## FEEDBACK ##################################
async def test_feedback_dialog_sends_to_admins(tg):
    await tg.send(500, "✉️ Feedback")
    assert tg.session.texts()[-1] == EN("feedback.ask")

    photo = [PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]
    await tg.send(500, None, photo=photo)
    assert tg.session.texts()[-1] == EN("feedback.text_only")

    await tg.send(500, "Hi <admin>!")
    to_admin = [m for m in tg.session.of_type(SendMessage) if m.chat_id == ADMIN_ID][-1]
    assert "#FEEDBACK" in to_admin.text and "Hi &lt;admin&gt;!" in to_admin.text
    assert tg.session.texts()[-1] == EN("feedback.sent")
    assert await tg.state(500) is None


async def test_cancel_leaves_dialog(tg):
    await tg.send(501, "/cancel")
    assert tg.session.texts()[-1] == EN("common.nothing_to_cancel")

    await tg.send(501, "/feedback")
    await tg.send(501, "/cancel")
    assert tg.session.texts()[-1] == EN("common.cancelled")
    assert await tg.state(501) is None


################################# BROADCAST ##################################
async def test_broadcast_flow_marks_blocked_users(tg):
    for user_id in (600, 601, 602):
        await tg.send(user_id, "/start")

    def forbidden(method):
        message = "Forbidden: bot was blocked by the user"
        return TelegramForbiddenError(method=method, message=message)

    tg.session.errors[601] = forbidden

    await tg.click(ADMIN_ID, cb(AdminAction.BROADCAST))
    assert tg.session.texts()[-1] == EN("broadcast.ask")

    await tg.send(ADMIN_ID, "Big news!")
    assert tg.session.texts()[-1] == EN("broadcast.preview", count=4)  # 3 users + admin

    await tg.click(ADMIN_ID, BroadcastCallback(confirm=True).pack())
    await asyncio.gather(*broadcast_service.running_tasks)

    copies = tg.session.of_type(CopyMessage)
    assert sorted(c.chat_id for c in copies) == [ADMIN_ID, 600, 601, 602]
    report = tg.session.texts()[-1]
    assert report == EN("broadcast.finished", sent=3, blocked=1, failed=0)
    assert (await get_user(601)).is_blocked

    # Blocked user writes again -> unblocked
    await tg.send(601, "/start")
    assert not (await get_user(601)).is_blocked


async def test_broadcast_cancel(tg):
    await tg.send(ADMIN_ID, "/broadcast")
    await tg.send(ADMIN_ID, "text")
    await tg.click(ADMIN_ID, BroadcastCallback(confirm=False).pack())
    assert tg.session.texts()[-1] == EN("common.cancelled")
    assert not tg.session.of_type(CopyMessage)


############################### BACKUP AND LOGS ##############################
async def test_backup_is_a_valid_sqlite_snapshot(tg):
    await tg.send(ADMIN_ID, "/db")
    document = tg.session.of_type(SendDocument)[-1]
    assert document.document.data.startswith(b"SQLite format 3")


async def test_autobackup_and_startup_notify(tg):
    from tgbot.utils.misc_functions import autobackup_admin, startup_notify

    await startup_notify(tg.bot)
    await autobackup_admin(tg.bot)
    assert tg.session.texts()[0] == EN("admin.bot_started")
    assert tg.session.of_type(SendDocument)[0].chat_id == ADMIN_ID


async def test_logs_single_file_sent_as_document(tg):
    from tgbot.utils.misc.bot_logging import bot_logger

    bot_logger.warning("something to log")
    await tg.send(ADMIN_ID, "/log")
    assert tg.session.of_type(SendDocument)  # 1 file -> sendDocument, not a media group
