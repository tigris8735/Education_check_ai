from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.file_service.models import FileMeta
from app.shared.enums import FileStatus


async def get_by_id(db: AsyncSession, file_id: int) -> FileMeta | None:
    return await db.get(FileMeta, file_id)


async def create(db: AsyncSession, **data) -> FileMeta:
    f = FileMeta(**data)
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


async def mark_uploaded(
    db: AsyncSession,
    file: FileMeta,
    *,
    size: int,
    submission_id: int | None = None,
    task_id: int | None = None,
) -> FileMeta:
    file.status = FileStatus.UPLOADED
    file.size = size
    if submission_id is not None:
        file.submission_id = submission_id
    if task_id is not None:
        file.task_id = task_id
    await db.commit()
    await db.refresh(file)
    return file


async def delete(db: AsyncSession, file: FileMeta) -> None:
    await db.delete(file)
    await db.commit()


async def list_by_submission(db: AsyncSession, submission_id: int) -> list[FileMeta]:
    result = await db.execute(
        select(FileMeta).where(FileMeta.submission_id == submission_id)
    )
    return list(result.scalars().all())


async def list_by_task(db: AsyncSession, task_id: int) -> list[FileMeta]:
    result = await db.execute(
        select(FileMeta)
        .where(FileMeta.task_id == task_id, FileMeta.status == FileStatus.UPLOADED)
        .order_by(FileMeta.created_at)
    )
    return list(result.scalars().all())


async def list_by_owner(db: AsyncSession, owner_id: int) -> list[FileMeta]:
    result = await db.execute(
        select(FileMeta)
        .where(FileMeta.uploaded_by_id == owner_id)
        .order_by(FileMeta.created_at.desc())
    )
    return list(result.scalars().all())