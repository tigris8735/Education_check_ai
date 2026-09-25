from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.group_service import crud as group_crud
from app.services.submission_service import crud as submission_crud
from app.services.task_service import crud as task_crud
from app.services.task_service import service as task_service
from app.services.task_service.models import Task
from app.services.task_service.schemas import TaskCreate, TaskDetail, TaskOut, TaskUpdate
from app.services.user_service.models import User
from app.shared.permissions import get_current_user, require_teacher

router = APIRouter()


async def _to_task_out(db: AsyncSession, t: Task) -> TaskOut:
    gids = await task_crud.group_ids_for_task(db, t.id)
    group_names: list[str] = []
    for gid in gids:
        g = await group_crud.get_by_id(db, gid)
        if g:
            group_names.append(g.name)

    subs = await submission_crud.list_by_task(db, t.id)
    members = await task_crud.total_members_for_task(db, t.id)

    return TaskOut(
        id=t.id,
        teacher_id=t.teacher_id,
        title=t.title,
        description=t.description,
        deadline=t.deadline,
        created_at=t.created_at,
        is_expired=task_crud.is_expired(t),
        max_attempts=t.max_attempts or 0,          # ← защита от NULL из старых строк
        group_names=group_names,
        members_count=members,
        submissions_count=len(subs),
    )


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    group_id: int | None = Query(None),
):
    tasks = await task_service.list_tasks(db, current_user, group_id)
    return [await _to_task_out(db, t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await task_service.create_task(db, payload, current_user)
    return await _to_task_out(db, task)


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await task_service.get_task(db, task_id, current_user)
    out = await _to_task_out(db, task)
    return TaskDetail(**out.model_dump())


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    task = await task_service.update_task(db, task_id, payload, current_user)
    return await _to_task_out(db, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await task_service.delete_task(db, task_id, current_user)