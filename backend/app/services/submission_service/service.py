from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.services.ai_service import crud as ai_crud
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
from app.services.user_service import crud as user_crud
from app.services.user_service.models import User
from app.shared.enums import Role, SubmissionStatus


def _is_task_expired(task) -> bool:
    deadline = task.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)


LOCKED = (
    SubmissionStatus.CHECKING,
    SubmissionStatus.CHECKED,
    SubmissionStatus.REVIEWED,
)


async def create_submission(
    db: AsyncSession, data: SubmissionCreate, student: User
) -> Submission:
    if student.role != Role.STUDENT:
        raise ForbiddenError("Только студент может сдавать задания")

    task = await task_crud.get_by_id(db, data.task_id)
    if not task:
        raise NotFoundError("Задание не найдено")

    member = await group_crud.get_member(db, task.group_id, student.id)
    if not member:
        raise ForbiddenError("Вы не состоите в группе этого задания")

    if await crud.get_by_task_and_student(db, task.id, student.id):
        raise ConflictError("Вы уже сдали это задание")

    if _is_task_expired(task):
        raise ValidationError("Срок сдачи задания истёк")

    return await crud.create(
        db,
        task_id=task.id,
        student_id=student.id,
        status=SubmissionStatus.SUBMITTED,
        student_comment=data.student_comment,
    )


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


async def build_detail(db: AsyncSession, sub: Submission) -> SubmissionDetail:
    files = await file_crud.list_by_submission(db, sub.id)
    ai_check = await ai_crud.get_by_submission(db, sub.id)

    task = await task_crud.get_by_id(db, sub.task_id)
    student = await user_crud.get_by_id(db, sub.student_id)
    group_name = ""
    if task:
        group = await group_crud.get_by_id(db, task.group_id)
        group_name = group.name if group else ""

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
        ai_status=ai_check.status if ai_check else None,
        ai_score=ai_check.score if ai_check else None,
        ai_feedback=ai_check.feedback if ai_check else None,
        ai_error=ai_check.error if ai_check else None,
        final_score=sub.final_score,
        teacher_feedback=sub.teacher_feedback,
        student_first_name=student.first_name if student else "",
        student_last_name=student.last_name if student else "",
        student_group_name=group_name,
        task_title=task.title if task else "",
    )


async def list_submissions(
    db: AsyncSession, user: User, task_id: int | None = None
) -> list[Submission]:
    if user.role == Role.STUDENT:
        if task_id is not None:
            sub = await crud.get_by_task_and_student(db, task_id, user.id)
            return [sub] if sub else []
        return await crud.list_by_student(db, user.id)

    if task_id is None:
        tasks = await task_crud.list_by_teacher(db, user.id)
        result: list[Submission] = []
        for t in tasks:
            result.extend(await crud.list_by_task(db, t.id))
        return result

    task = await task_crud.get_by_id(db, task_id)
    if not task:
        raise NotFoundError("Задание не найдено")
    if task.teacher_id != user.id:
        raise ForbiddenError("Это задание создано другим преподавателем")
    return await crud.list_by_task(db, task_id)


async def update_own_submission(
    db: AsyncSession, submission_id: int, data: SubmissionUpdate, student: User
) -> Submission:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")
    if sub.student_id != student.id:
        raise ForbiddenError("Это не ваша сдача")
    if sub.status in LOCKED:
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


async def delete_submission(db: AsyncSession, submission_id: int, user: User) -> None:
    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    if user.role == Role.STUDENT:
        if sub.student_id != user.id:
            raise ForbiddenError("Это не ваша сдача")
        if sub.status in LOCKED:
            raise ConflictError("Сдача уже на проверке/проверена")
    else:
        task = await task_crud.get_by_id(db, sub.task_id)
        if not task or task.teacher_id != user.id:
            raise ForbiddenError("Это сдача по чужому заданию")

    files = await file_crud.list_by_submission(db, sub.id)
    for f in files:
        try:
            from app.services.file_service.service import delete_file as _delete_file
            await _delete_file(db, f.id, user)
        except Exception:
            pass

    await crud.delete(db, sub)


async def add_comment(
    db: AsyncSession, submission_id: int, data: CommentCreate, user: User
) -> Comment:
    """Комментарии — только преподаватель, как дополнение к проверке работы."""
    if user.role != Role.TEACHER:
        raise ForbiddenError("Комментарии к работе может оставлять только преподаватель")

    sub = await crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    task = await task_crud.get_by_id(db, sub.task_id)
    if not task or task.teacher_id != user.id:
        raise ForbiddenError("Это сдача по чужому заданию")

    return await crud.add_comment(db, submission_id, user.id, data.text)


async def delete_comment(db: AsyncSession, comment_id: int, user: User) -> None:
    c = await crud.get_comment(db, comment_id)
    if not c:
        raise NotFoundError("Комментарий не найден")
    if user.role != Role.TEACHER:
        raise ForbiddenError("Комментарии может удалять только преподаватель")
    await crud.delete_comment(db, c)