import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.ai_service import crud
from app.services.ai_service.models import AiCheck
from app.services.ai_service.providers.factory import get_provider
from app.services.file_service import crud as file_crud
from app.services.file_service import storage
from app.services.submission_service import crud as submission_crud
from app.services.submission_service.models import Submission
from app.services.task_service import crud as task_crud
from app.services.user_service.models import User
from app.shared.enums import AiCheckStatus, Role, SubmissionStatus

logger = logging.getLogger(__name__)

_TEXT_EXTENSIONS = (".txt", ".md", ".csv", ".py", ".js", ".html", ".css", ".json", ".log")


async def _collect_submission_text(db: AsyncSession, sub: Submission) -> str:
    """Текст из прикреплённых файлов (текстовые читаем, бинарные — помечаем)."""
    parts: list[str] = []
    files = await file_crud.list_by_submission(db, sub.id)

    for f in files:
        if f.status.value != "uploaded":
            continue
        name_lower = (f.original_name or "").lower()
        ct = (f.content_type or "").lower()
        is_text = ct.startswith("text/") or name_lower.endswith(_TEXT_EXTENSIONS)

        if not is_text:
            parts.append(f"--- Прикреплён файл: {f.original_name} (бинарный, AI не читает) ---")
            continue

        try:
            url = await storage.generate_download_url(f.s3_key, f.original_name, expires=60)
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
            if resp.status_code == 200:
                parts.append(
                    f"--- Файл: {f.original_name} ---\n{resp.text[:50000]}"
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Не удалось прочитать файл %s: %s", f.original_name, e)
            parts.append(f"--- Файл: {f.original_name} (ошибка чтения) ---")

    return "\n\n".join(parts)


def _collect_text(submission_text: str | None, student_comment: str) -> str:
    parts = []
    if student_comment and student_comment.strip():
        parts.append(student_comment.strip())
    if submission_text and submission_text.strip():
        parts.append(submission_text.strip())
    return "\n\n".join(parts)


async def _assert_can_access_submission(
    db: AsyncSession, submission_id: int, user: User
) -> Submission:
    sub = await submission_crud.get_by_id(db, submission_id)
    if not sub:
        raise NotFoundError("Сдача не найдена")

    if user.role == Role.TEACHER:
        task = await task_crud.get_by_id(db, sub.task_id)
        if not task or task.teacher_id != user.id:
            raise ForbiddenError("Это сдача по чужому заданию")
    else:
        if sub.student_id != user.id:
            raise ForbiddenError("Это не ваша сдача")
    return sub


async def run_check(
    db: AsyncSession,
    submission_id: int,
    user: User,
    *,
    force: bool = False,
) -> AiCheck:
    sub = await _assert_can_access_submission(db, submission_id, user)

    existing = await crud.get_by_submission(db, submission_id)
    if existing and existing.status == AiCheckStatus.DONE and not force:
        raise ConflictError("Проверка уже выполнена. Используйте force=true для перезапуска")
    if existing and existing.status == AiCheckStatus.RUNNING and not force:
        raise ConflictError("Проверка уже выполняется")

    provider = get_provider()

    if existing:
        check = await crud.mark_running(db, existing, provider.name)
    else:
        check = await crud.create(
            db,
            submission_id=submission_id,
            status=AiCheckStatus.RUNNING,
            provider=provider.name,
        )

    await submission_crud.update(db, sub, status=SubmissionStatus.CHECKING)

    task = await task_crud.get_by_id(db, sub.task_id)
    files_text = await _collect_submission_text(db, sub)
    text = _collect_text(files_text, sub.student_comment)

    try:
        result = await provider.check(
            task_title=task.title if task else "",
            task_description=task.description if task else "",
            submission_text=text,
            student_comment=sub.student_comment,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("AI check failed for submission %s", submission_id)
        await crud.mark_error(db, check, str(e))
        await submission_crud.update(db, sub, status=SubmissionStatus.FAILED)
        raise

    check = await crud.mark_done(db, check, result.score, result.feedback)
    await submission_crud.update(db, sub, status=SubmissionStatus.CHECKED)
    return check


async def get_check(db: AsyncSession, submission_id: int, user: User) -> AiCheck | None:
    await _assert_can_access_submission(db, submission_id, user)
    return await crud.get_by_submission(db, submission_id)