from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.group_service.models import GroupMember
from app.services.task_service.models import Task


async def get_by_id(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def create(db: AsyncSession, **data) -> Task:
    task = Task(**data)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update(db: AsyncSession, task: Task, **data) -> Task:
    for key, value in data.items():
        if value is not None:
            setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()


async def list_by_group(db: AsyncSession, group_id: int) -> list[Task]:
    result = await db.execute(
        select(Task).where(Task.group_id == group_id).order_by(Task.deadline)
    )
    return list(result.scalars().all())


async def list_by_teacher(db: AsyncSession, teacher_id: int) -> list[Task]:
    result = await db.execute(
        select(Task).where(Task.teacher_id == teacher_id).order_by(Task.deadline)
    )
    return list(result.scalars().all())


async def list_for_student(db: AsyncSession, user_id: int) -> list[Task]:
    """Задания всех групп, в которых состоит студент."""
    result = await db.execute(
        select(Task)
        .join(GroupMember, GroupMember.group_id == Task.group_id)
        .where(GroupMember.user_id == user_id)
        .order_by(Task.deadline)
    )
    return list(result.scalars().all())


def is_expired(task: Task) -> bool:
    deadline = task.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)