from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service.models import AiCheck
from app.shared.enums import AiCheckStatus


async def get_by_submission(db: AsyncSession, submission_id: int) -> AiCheck | None:
    result = await db.execute(
        select(AiCheck).where(AiCheck.submission_id == submission_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, **data) -> AiCheck:
    check = AiCheck(**data)
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


async def update(db: AsyncSession, check: AiCheck, **data) -> AiCheck:
    for key, value in data.items():
        setattr(check, key, value)
    await db.commit()
    await db.refresh(check)
    return check


async def mark_running(db: AsyncSession, check: AiCheck, provider: str) -> AiCheck:
    return await update(
        db,
        check,
        status=AiCheckStatus.RUNNING,
        provider=provider,
        error=None,
    )


async def mark_done(
    db: AsyncSession, check: AiCheck, score: int, feedback: str
) -> AiCheck:
    return await update(
        db,
        check,
        status=AiCheckStatus.DONE,
        score=score,
        feedback=feedback,
        error=None,
    )


async def mark_error(db: AsyncSession, check: AiCheck, error: str) -> AiCheck:
    return await update(
        db,
        check,
        status=AiCheckStatus.ERROR,
        error=error[:2000],
    )

async def reset(db: AsyncSession, check: AiCheck) -> AiCheck:
    return await update(
        db,
        check,
        status=AiCheckStatus.PENDING,
        score=None,
        feedback=None,
        error=None,
    )