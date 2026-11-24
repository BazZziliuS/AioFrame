"""Broadcast: admin sends any message, confirms the preview, the bot copies it to all users."""

import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from tgbot.callbacks import AdminAction, AdminCallback, BroadcastCallback
from tgbot.config import settings
from tgbot.database.engine import async_session
from tgbot.database.repositories import UserRepository
from tgbot.filters import IsAdmin
from tgbot.keyboards.inline import broadcast_confirm_inline
from tgbot.services import broadcast as broadcast_service
from tgbot.services.locale import Locale

logger = logging.getLogger(__name__)

router = Router(name=__name__)
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class BroadcastStates(StatesGroup):
    waiting_message = State()
    confirm = State()


async def _ask_message(message: Message, state: FSMContext, locale: Locale) -> None:
    if broadcast_service.is_running():
        await message.answer(locale("broadcast.already_running"))
        return

    await state.set_state(BroadcastStates.waiting_message)
    await message.answer(locale("broadcast.ask"))


@router.message(Command(commands=["broadcast"]))
async def broadcast_command(message: Message, state: FSMContext, locale: Locale) -> None:
    await _ask_message(message, state, locale)


@router.callback_query(AdminCallback.filter(F.action == AdminAction.BROADCAST))
async def broadcast_callback(call: CallbackQuery, state: FSMContext, locale: Locale) -> None:
    await call.answer()
    if isinstance(call.message, Message):
        await _ask_message(call.message, state, locale)


# Any content except commands becomes the broadcast message
@router.message(BroadcastStates.waiting_message, ~F.text.startswith("/"))
async def broadcast_message(message: Message, state: FSMContext, locale: Locale) -> None:
    async with async_session() as session:
        count = len(await UserRepository(session).get_reachable_ids())

    if count == 0:
        await state.clear()
        await message.answer(locale("broadcast.no_users"))
        return

    await state.update_data(from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastStates.confirm)
    await message.reply(
        locale("broadcast.preview", count=count),
        reply_markup=broadcast_confirm_inline(locale),
    )


async def _run_broadcast(
    bot: Bot,
    user_ids: list[int],
    from_chat_id: int,
    message_id: int,
    locale: Locale,
) -> broadcast_service.BroadcastResult:
    try:
        result = await broadcast_service.broadcast(
            bot, user_ids, from_chat_id, message_id, rate=settings.broadcast_rate
        )
    except Exception:
        logger.exception("Broadcast crashed")
        raise

    await bot.send_message(
        from_chat_id,
        locale(
            "broadcast.finished", sent=result.sent, blocked=result.blocked, failed=result.failed
        ),
    )
    return result


@router.callback_query(BroadcastStates.confirm, BroadcastCallback.filter())
async def broadcast_confirm(
    call: CallbackQuery,
    callback_data: BroadcastCallback,
    bot: Bot,
    state: FSMContext,
    locale: Locale,
) -> None:
    data = await state.get_data()
    await state.clear()
    await call.answer()

    if not isinstance(call.message, Message):
        return

    if not callback_data.confirm:
        await call.message.edit_text(locale("common.cancelled"))
        return

    if broadcast_service.is_running():
        await call.message.edit_text(locale("broadcast.already_running"))
        return

    async with async_session() as session:
        user_ids = await UserRepository(session).get_reachable_ids()

    # Run in background: a long broadcast must not block other updates
    task = asyncio.create_task(
        _run_broadcast(bot, user_ids, data["from_chat_id"], data["message_id"], locale)
    )
    broadcast_service.running_tasks.add(task)
    task.add_done_callback(broadcast_service.running_tasks.discard)

    await call.message.edit_text(locale("broadcast.started", count=len(user_ids)))
