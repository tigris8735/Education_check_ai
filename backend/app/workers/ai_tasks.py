import logging

from app.core.database import SessionLocal
from app.services.ai_service import crud as ai_crud
from app.services.ai_service import service as ai_service
from app.services.submission_service import crud as submission_crud
from app.shared.enums import AiCheckStatus, SubmissionStatus

logger = logging.getLogger(__name__)


async def run_ai_check(
    ctx: dict,
    submission_id: int,
    force: bool = False,
) -> dict:
    """
    Фоновая AI-проверка сдачи.
    Открывает собственную сессию БД (воркер живёт вне FastAPI).
    """
    logger.info("AI check task started: submission=%s force=%s", submission_id, force)

    async with SessionLocal() as db:
        check = await ai_crud.get_by_submission(db, submission_id)
        if check is None:
            # на всякий случай: ставим в error, если записи нет
            logger.error("AiCheck row not found for submission %s", submission_id)
            return {"submission_id": submission_id, "status": "not_found"}

        if check.status == AiCheckStatus.DONE and not force:
            logger.info("AiCheck already done for submission %s, skip", submission_id)
            return {"submission_id": submission_id, "status": "skipped"}

        provider = ai_service.get_provider_for_task(ctx)
        await ai_crud.mark_running(db, check, provider.name)

        sub = await submission_crud.get_by_id(db, submission_id)
        if sub is None:
            await ai_crud.mark_error(db, check, "Submission disappeared")
            return {"submission_id": submission_id, "status": "no_submission"}

        # соберём данные задания
        task = await ai_service.get_task_for_submission(db, sub)
        text = await ai_service.collect_submission_text(db, sub)

        try:
            result = await provider.check(
                task_title=task.title if task else "",
                task_description=task.description if task else "",
                submission_text=text,
                student_comment=sub.student_comment,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("AI provider failed for submission %s", submission_id)
            await ai_crud.mark_error(db, check, str(e))
            await submission_crud.update(db, sub, status=SubmissionStatus.SUBMITTED)
            return {"submission_id": submission_id, "status": "error", "error": str(e)}

        await ai_crud.mark_done(db, check, result.score, result.feedback)
        await submission_crud.update(db, sub, status=SubmissionStatus.CHECKED)

    logger.info("AI check done for submission %s: score=%s", submission_id, result.score)
    return {
        "submission_id": submission_id,
        "status": "done",
        "score": result.score,
    }