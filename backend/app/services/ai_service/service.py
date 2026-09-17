import logging

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services.ai_service import crud
from app.services.ai_service.models import AiCheck
from app.services.ai_service.providers.base import AIProvider
from app.services.ai_service.providers.factory import get_provider
from app.services.submission_service import crud as submission_crud
from app.services.task_service import crud as task_crud
from app.services.user_service.models import User
from app.shared.enums import AiCheckStatus, Role, SubmissionStatus
from app.services.submission_service.models import Submission
from arq.connections import ArqRedis

logger = logging.getLogger(__name__)


# ---------- Утилиты (используются и сервисом, и воркером) ----------

def get_provider_for_task(ctx: dict | None = None) -> AIProvider:
    """В ctx можно передать заранее созданный провайдер (для кэша)."""
    if ctx and "ai_provider" in ctx:
        return ctx["ai_provider"]
    return get_provider()


async def get_task_for_submission(db: AsyncSession, sub):
    return await task_crud.get_by_id(db, sub.task_id)


async def collect_submission_text(db: AsyncSession, sub) -> str:
    """
    Пока только student_comment. Парсинг файлов — отдельная фича.
    """
    return ""


def _collect_text(submission_text: str | None, student_comment: str) -> str:
    parts = []
    if student_comment.strip():
        parts.append(student_comment.strip())
    if submission_text:
        parts.append(submission_text)
    return "\n\n".join(parts)


# ---------- Проверка прав ----------

async def _assert_can_access_submission(
    db: AsyncSession, submission_id: int, user: User
) -> "Submission": 
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


# ---------- Постановка в очередь ----------

async def enqueue_check(
    db: AsyncSession,
    submission_id: int,
    user: User,
    *,
    force: bool = False,
) -> AiCheck:
    await _assert_can_access_submission(db, submission_id, user)

    existing = await crud.get_by_submission(db, submission_id)
    if existing and existing.status == AiCheckStatus.RUNNING and not force:
        raise ConflictError("Проверка уже выполняется")
    if existing and existing.status == AiCheckStatus.DONE and not force:
        raise ConflictError("Проверка уже выполнена. Используйте force=true для перезапуска")

    if existing:
        check = await crud.update(
            db,
            existing,
            status=AiCheckStatus.PENDING,
            score=None,
            feedback=None,
            error=None,
        )
    else:
        check = await crud.create(
            db,
            submission_id=submission_id,
            status=AiCheckStatus.PENDING,
            provider=settings.AI_PROVIDER,
        )

    # положим задачу в очередь
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    try:
        redis: ArqRedis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    except Exception as e:  # noqa: BLE001
        logger.error("Redis unavailable: %s", e)
        from app.core.exceptions import AppException
        from fastapi import status as _st

        class _ServiceUnavailable(AppException):
            status_code = _st.HTTP_503_SERVICE_UNAVAILABLE
            detail = "Очередь задач временно недоступна. Попробуйте позже."

        raise _ServiceUnavailable()

    try:
        await redis.enqueue_job("run_ai_check", submission_id, force)
    finally:
        await redis.close()

# ---------- Синхронный режим (для отладки) ----------

async def run_check_sync(
    db: AsyncSession,
    submission_id: int,
    user: User,
    *,
    force: bool = False,
) -> AiCheck:
    sub = await _assert_can_access_submission(db, submission_id, user)

    existing = await crud.get_by_submission(db, submission_id)
    if existing and existing.status == AiCheckStatus.DONE and not force:
        raise ConflictError("Проверка уже выполнена. Используйте force=true")
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

    task = await task_crud.get_by_id(db, sub.task_id)
    text = _collect_text(await collect_submission_text(db, sub), sub.student_comment)

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
        await submission_crud.update(db, sub, status=SubmissionStatus.SUBMITTED)
        raise

    check = await crud.mark_done(db, check, result.score, result.feedback)
    await submission_crud.update(db, sub, status=SubmissionStatus.CHECKED)
    return check


# ---------- Чтение ----------

async def get_check(db: AsyncSession, submission_id: int, user: User) -> AiCheck | None:
    await _assert_can_access_submission(db, submission_id, user)
    return await crud.get_by_submission(db, submission_id)