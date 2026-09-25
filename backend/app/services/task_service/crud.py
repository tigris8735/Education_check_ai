from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.group_service.models import GroupMember
from app.services.task_service.models import Task, TaskGroupAssignment


async def get_by_id(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def create(
    db: AsyncSession, *, teacher_id: int, title: str, description: str,
    deadline: datetime, max_attempts: int, group_ids: list[int]
) -> Task:
    task = Task(
        teacher_id=teacher_id,
        title=title,
        description=description,
        deadline=deadline,
        max_attempts=max_attempts,
        group_id=group_ids[0] if group_ids else None,   # legacy, для совместимости
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    for gid in group_ids:
        db.add(TaskGroupAssignment(task_id=task.id, group_id=gid))
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
        select(Task)
        .join(TaskGroupAssignment, TaskGroupAssignment.task_id == Task.id)
        .where(TaskGroupAssignment.group_id == group_id)
        .order_by(Task.deadline)
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
        .join(TaskGroupAssignment, TaskGroupAssignment.task_id == Task.id)
        .join(GroupMember, GroupMember.group_id == TaskGroupAssignment.group_id)
        .where(GroupMember.user_id == user_id)
        .order_by(Task.deadline)
        .distinct()
    )
    return list(result.scalars().all())


def is_expired(task: Task) -> bool:
    deadline = task.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)


async def group_ids_for_task(db: AsyncSession, task_id: int) -> list[int]:
    result = await db.execute(
        select(TaskGroupAssignment.group_id).where(
            TaskGroupAssignment.task_id == task_id
        )
    )
    return list(result.scalars().all())


async def total_members_for_task(db: AsyncSession, task_id: int) -> int:
    """Сумма участников всех групп задания (без дублей)."""
    result = await db.execute(
        select(func.count(func.distinct(GroupMember.user_id)))
        .select_from(TaskGroupAssignment)
        .join(GroupMember, GroupMember.group_id == TaskGroupAssignment.group_id)
        .where(TaskGroupAssignment.task_id == task_id)
    )
    return int(result.scalar_one())