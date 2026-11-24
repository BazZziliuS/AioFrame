from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from tgbot.data.config import settings
from tgbot.database.engine import async_session
from tgbot.database.repositories import SettingsRepository, UserRepository
from webapp.auth import get_admin
from webapp.schemas import (
    BotSettingsOut,
    BotSettingsUpdate,
    StatsOut,
    UserOut,
    UsersPage,
    UserUpdate,
)

# Every endpoint here requires an admin (checked by the router dependency)
router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_admin)])


@router.get("/stats")
async def get_stats() -> StatsOut:
    async with async_session() as session:
        stats = await UserRepository(session).get_stats()
    return StatsOut(
        total=stats.total,
        new_day=stats.new_day,
        new_week=stats.new_week,
        active=stats.active,
        banned=stats.banned,
        blocked=stats.blocked,
    )


@router.get("/users")
async def list_users(
    q: Annotated[str, Query(max_length=64)] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UsersPage:
    async with async_session() as session:
        items, total = await UserRepository(session).search(q, offset=offset, limit=limit)
    return UsersPage(
        items=[UserOut.model_validate(user) for user in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch("/users/{user_id}")
async def update_user(user_id: int, body: UserUpdate) -> UserOut:
    if body.is_banned and settings.is_admin(user_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cannot_ban_admin")

    async with async_session() as session:
        repo = UserRepository(session)
        if not await repo.set_banned(user_id, body.is_banned):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user_not_found")
        await session.commit()
        user = await repo.get_by_user_id(user_id)

    return UserOut.model_validate(user)


@router.get("/settings")
async def get_settings() -> BotSettingsOut:
    async with async_session() as session:
        return BotSettingsOut(is_maintenance=await SettingsRepository(session).is_maintenance())


@router.patch("/settings")
async def update_settings(body: BotSettingsUpdate) -> BotSettingsOut:
    async with async_session() as session:
        await SettingsRepository(session).set_maintenance(body.is_maintenance)
        await session.commit()
    return BotSettingsOut(is_maintenance=body.is_maintenance)
