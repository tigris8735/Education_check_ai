from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.services.group_service import crud as group_crud
from app.services.task_service import crud
from app.services.task_service.models import Task
from app.services.task_service.schemas import TaskCreate, TaskUpdate
from app.services.user_service.models import User
from app.shared.enums import Role


def _ensure_teacher_owns_group(group, teacher: User) -> None:
    if group.teacher_id != teacher.id:
        raise ForbiddenError("Вы не являетесь преподавателем этой группы")


def _ensure_teacher_owns_task(task: Task, teacher: User) -> None:
    if task.teacher_id != teacher.id:
        raise ForbiddenError("Это задание создано другим преподавателем")


async def create_task(db: AsyncSession, data: TaskCreate, teacher: User) -> Task:
    # Проверяем право препода на ВСЕ указанные группы
    for gid in data.group_ids:
        group = await group_crud.get_by_id(db, gid)
        if not group:
            raise NotFoundError(f"Группа {gid} не найдена")
        _ensure_teacher_owns_group(group, teacher)

    return await crud.create(
        db,
        teacher_id=teacher.id,
        title=data.title,
        description=data.description,
        deadline=data.deadline,
        max_attempts=data.max_attempts,
        group_ids=data.group_ids,
    )


async def list_tasks(db: AsyncSession, user: User, group_id: int | None = None) -> list[Task]:
    if user.role == Role.TEACHER:
        if group_id is not None:
            group = await group_crud.get_by_id(db, group_id)
            if not group:
                raise NotFoundError("Группа не найдена")
            _ensure_teacher_owns_group(group, user)
            return await crud.list_by_group(db, group_id)
        return await crud.list_by_teacher(db, user.id)

    # student
    if group_id is not None:
        member = await group_crud.get_member(db, group_id, user.id)
        if not member:
            raise ForbiddenError("Вы не состоите в этой группе")
        return await crud.list_by_group(db, group_id)

    return await crud.list_for_student(db, user.id)


async def get_task(db: AsyncSession, task_id: int, user: User) -> Task:
    task = await crud.get_by_id(db, task_id)
    if not task:
        raise NotFoundError("Задание не найдено")

    if user.role == Role.TEACHER:
        _ensure_teacher_owns_task(task, user)
        return task

    # студент должен быть хотя бы в одной из групп задания
    task_groups = await crud.group_ids_for_task(db, task.id)
    for gid in task_groups:
        if await group_crud.get_member(db, gid, user.id):
            return task
    raise ForbiddenError("Нет доступа к этому заданию")


async def update_task(
    db: AsyncSession, task_id: int, data: TaskUpdate, teacher: User
) -> Task:
    task = await crud.get_by_id(db, task_id)
    if not task:
        raise NotFoundError("Задание не найдено")
    _ensure_teacher_owns_task(task, teacher)
    return await crud.update(db, task, **data.model_dump(exclude_unset=True))


async def delete_task(db: AsyncSession, task_id: int, teacher: User) -> None:
    task = await crud.get_by_id(db, task_id)
    if not task:
        raise NotFoundError("Задание не найдено")
    _ensure_teacher_owns_task(task, teacher)
    await crud.delete(db, task)