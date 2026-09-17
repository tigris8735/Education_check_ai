from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.group_service import crud as group_crud
from app.services.task_service import crud as task_crud
from app.services.task_service import service as task_service
from app.services.task_service.schemas import TaskCreate, TaskDetail, TaskOut, TaskUpdate
from app.services.user_service.models import User
from app.shared.permissions import get_current_user, require_teacher

router = APIRouter()


async def _to_task_out(db: AsyncSession, task) -> TaskOut:
    return TaskOut(
        id=task.id,
        group_id=task.group_id,
        teacher_id=task.teacher_id,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        created_at=task.created_at,
        is_expired=task_crud.is_expired(task),
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
    group = await group_crud.get_by_id(db, task.group_id)
    return TaskDetail(
        id=task.id,
        group_id=task.group_id,
        teacher_id=task.teacher_id,
        title=task.title,
        description=task.description,
        deadline=task.deadline,
        created_at=task.created_at,
        is_expired=task_crud.is_expired(task),
        group_name=group.name if group else "",
    )


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