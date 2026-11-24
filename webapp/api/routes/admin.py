from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from tgbot.config import settings
from tgbot.database.repositories import SettingsRepository, UserRepository
from webapp.api.deps import SessionDep, get_admin
from webapp.schemas import (
    BotSettingsOut,
    BotSettingsUpdate,
    StatsOut,
    UserOut,
    UsersPage,
    UserUpdate,
)

# Every endpoint here requires an admin (checked by the router dependency)
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin)])


@router.get("/stats")
async def get_stats(session: SessionDep) -> StatsOut:
    return StatsOut.model_validate(await UserRepository(session).get_stats())


@router.get("/users")
async def list_users(
    session: SessionDep,
    q: Annotated[str, Query(max_length=64)] = "",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> UsersPage:
    items, total = await UserRepository(session).search(q, offset=offset, limit=limit)
    return UsersPage(
        items=[UserOut.model_validate(user) for user in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch("/users/{user_id}")
async def update_user(user_id: int, body: UserUpdate, session: SessionDep) -> UserOut:
    if body.is_banned and settings.is_admin(user_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="cannot_ban_admin")

    repo = UserRepository(session)
    if not await repo.set_banned(user_id, body.is_banned):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user_not_found")
    await session.commit()
    return UserOut.model_validate(await repo.get_by_user_id(user_id))


@router.get("/settings")
async def get_settings(session: SessionDep) -> BotSettingsOut:
    return BotSettingsOut(is_maintenance=await SettingsRepository(session).is_maintenance())


@router.patch("/settings")
async def update_settings(body: BotSettingsUpdate, session: SessionDep) -> BotSettingsOut:
    await SettingsRepository(session).set_maintenance(body.is_maintenance)
    await session.commit()
    return BotSettingsOut(is_maintenance=body.is_maintenance)
