from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.services.file_service import crud as file_crud
from app.services.group_service import crud as group_crud
from app.services.submission_service import crud
from app.services.submission_service.models import Comment, Submission
from app.services.submission_service.schemas import (
    CommentCreate,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionStatusUpdate,
    SubmissionUpdate,
)
from app.services.task_service import crud as task_crud
from app.services.user_service.models import User
from app.shared.enums import FileStatus, Role, SubmissionStatus


def _is_task_expired(task) -> bool:
    deadline = task.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)


# ---------- Создание сдачи ----------

async def create_submission(
    db: AsyncSession, data: SubmissionCreate, student: User
) -> Submission:
    if student.role != Role.STUDENT:
        raise ForbiddenError("Только студент может сдавать задания")

    task = await task_crud.get_by_id(db, data.task_id)
    if not task:
        raise NotFoundError("Задание не найдено")

    # студент должен быть в группе задания
    member = await group_crud.get_member(db, task.group_id, student.id)
    if not member:
        raise ForbiddenError("Вы не состоите в группе этого задания")

    # одна сдача на задание
    if await crud.get_by_task_and_student(db, task.id, student.id):
        raise ConflictError("Вы уже сдали это задание")

    # после дедлайна — не принимаем
    if _is_task_expired(task):
        raise ValidationError("Срок сдачи задания истёк")

    return await crud.create(
        db,
        task_id=task.id,
        student_id=student.id,
        status=SubmissionStatus.SUBMITTED,
        student_comment=data.student_comment,
    )


# ---------- Чтение ----------

async def get_submission(db: AsyncSession, submission_id: int, user: User) -> Submission:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    if user.role == Role.TEACHER:
        task = await task_crud.get_by_id(db, sub.task_id)
        if not task or task.teacher_id != user.id:
            raise ForbiddenError("Это сдача по чужому заданию")
        return sub

    if sub.student_id != user.id:
        raise ForbiddenError("Нет доступа к этой сдаче")
    return sub


async def build_detail(
    db: AsyncSession, sub: Submission
) -> SubmissionDetail:
    files = await file_crud.list_by_submission(db, sub.id)
    return SubmissionDetail(
        id=sub.id,
        task_id=sub.task_id,
        student_id=sub.student_id,
        status=sub.status,
        student_comment=sub.student_comment,
        submitted_at=sub.submitted_at,
        created_at=sub.created_at,
        files=[f for f in files],
        comments=[c for c in sub.comments],
    )


async def list_submissions(
    db: AsyncSession, user: User, task_id: int | None = None
) -> list[Submission]:
    if user.role == Role.STUDENT:
        if task_id is not None:
            sub = await crud.get_by_task_and_student(db, task_id, user.id)
            return [sub] if sub else []
        return await crud.list_by_student(db, user.id)

    # teacher
    if task_id is None:
        raise ValidationError("Преподавателю нужно указать task_id")

    task = await task_crud.get_by_id(db, task_id)
    if not task:
        raise NotFoundError("Задание не найдено")
    if task.teacher_id != user.id:
        raise ForbiddenError("Это задание создано другим преподавателем")

    return await crud.list_by_task(db, task_id)


# ---------- Изменение ----------

async def update_own_submission(
    db: AsyncSession, submission_id: int, data: SubmissionUpdate, student: User
) -> Submission:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")
    if sub.student_id != student.id:
        raise ForbiddenError("Это не ваша сдача")
    if sub.status in (SubmissionStatus.CHECKING, SubmissionStatus.CHECKED):
        raise ConflictError("Сдача уже на проверке/проверена, изменения запрещены")

    return await crud.update(db, sub, student_comment=data.student_comment)


async def change_status(
    db: AsyncSession, submission_id: int, data: SubmissionStatusUpdate, teacher: User
) -> Submission:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    task = await task_crud.get_by_id(db, sub.task_id)
    if not task or task.teacher_id != teacher.id:
        raise ForbiddenError("Это сдача по чужому заданию")

    return await crud.update(db, sub, status=data.status)


async def delete_submission(
    db: AsyncSession, submission_id: int, user: User
) -> None:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    if user.role == Role.STUDENT:
        if sub.student_id != user.id:
            raise ForbiddenError("Это не ваша сдача")
        if sub.status in (SubmissionStatus.CHECKING, SubmissionStatus.CHECKED):
            raise ConflictError("Сдача уже на проверке/проверена")
    else:
        task = await task_crud.get_by_id(db, sub.task_id)
        if not task or task.teacher_id != user.id:
            raise ForbiddenError("Это сдача по чужому заданию")

    # удалим связанные файлы из S3
    from app.services.file_service.service import delete_file as _delete_file  # локальный импорт
    files = await file_crud.list_by_submission(db, sub.id)
    for f in files:
        try:
            await _delete_file(db, f.id, user)
        except Exception:
            pass  # best-effort

    await crud.delete(db, sub)


# ---------- Комментарии ----------

async def add_comment(
    db: AsyncSession, submission_id: int, data: CommentCreate, user: User
) -> Comment:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    if user.role == Role.TEACHER:
        task = await task_crud.get_by_id(db, sub.task_id)
        if not task or task.teacher_id != user.id:
            raise ForbiddenError("Это сдача по чужому заданию")
    else:
        if sub.student_id != user.id:
            raise ForbiddenError("Это не ваша сдача")

    return await crud.add_comment(db, submission_id, user.id, data.text)


async def delete_comment(
    db: AsyncSession, comment_id: int, user: User
) -> None:
    c = await crud.get_comment(db, comment_id)
    if not c:
        raise NotFoundError("Комментарий не найден")
    if c.author_id != user.id and user.role != Role.TEACHER:
        raise ForbiddenError("Можно удалять только свои комментарии")
    await crud.delete_comment(db, c)