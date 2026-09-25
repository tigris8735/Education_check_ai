from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.group_service import crud
from app.services.group_service import service as group_service
from app.services.group_service.models import Group
from app.services.group_service.schemas import (
    AddMemberIn,
    GroupCreate,
    GroupDetail,
    GroupOut,
)
from app.services.user_service.models import User
from app.shared.permissions import get_current_user, require_teacher

router = APIRouter()


async def _to_out(db: AsyncSession, g: Group) -> GroupOut:
    return GroupOut(
        id=g.id,
        name=g.name,
        teacher_id=g.teacher_id,
        created_by_id=g.created_by_id,
        created_at=g.created_at,
        members_count=await crud.members_count(db, g.id),
    )


@router.get("", response_model=list[GroupOut])
async def list_my_groups(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    groups = await group_service.list_my_groups(db, current_user)
    return [await _to_out(db, g) for g in groups]


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await group_service.create_group(db, payload, current_user)
    return await _to_out(db, group)


# ВАЖНО: /search объявлен ДО /{group_id}, иначе маршрут съедается динамическим
@router.get("/search", response_model=list[GroupOut])
async def search_groups(
    name: str,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    q = (
        select(Group)
        .where(Group.name.ilike(f"%{name.strip()}%"))
        .order_by(Group.name)
        .limit(20)
    )
    result = await db.execute(q)
    groups = list(result.scalars().all())
    return [await _to_out(db, g) for g in groups]


@router.get("/{group_id}", response_model=GroupDetail)
async def get_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await group_service.get_group_detail(db, group_id, current_user)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await group_service.delete_group(db, group_id, current_user)


@router.post("/{group_id}/claim", response_model=GroupOut)
async def claim_group(
    group_id: int,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    group = await group_service.claim_group(db, group_id, current_user)
    return await _to_out(db, group)


@router.post("/{group_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await group_service.join_group(db, group_id, current_user)


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await group_service.leave_group(db, group_id, current_user)


@router.post("/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    group_id: int,
    payload: AddMemberIn,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await group_service.add_member(db, group_id, payload, current_user)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await group_service.remove_member(db, group_id, user_id, current_user)