from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.submission_service.models import Comment, Submission


async def get_by_id(db: AsyncSession, submission_id: int) -> Submission | None:
    return await db.get(Submission, submission_id)


async def list_by_task_and_student(
    db: AsyncSession, task_id: int, student_id: int
) -> list[Submission]:
    """Все попытки студента по заданию, последние — в начале."""
    result = await db.execute(
        select(Submission)
        .where(Submission.task_id == task_id, Submission.student_id == student_id)
        .order_by(Submission.submitted_at.desc())
    )
    return list(result.scalars().all())


async def count_by_task_and_student(
    db: AsyncSession, task_id: int, student_id: int
) -> int:
    result = await db.execute(
        select(Submission)
        .where(Submission.task_id == task_id, Submission.student_id == student_id)
    )
    return len(list(result.scalars().all()))


async def create(db: AsyncSession, **data) -> Submission:
    sub = Submission(**data)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def update(db: AsyncSession, sub: Submission, **data) -> Submission:
    for key, value in data.items():
        if value is not None:
            setattr(sub, key, value)
    await db.commit()
    await db.refresh(sub)
    return sub


async def delete(db: AsyncSession, sub: Submission) -> None:
    await db.delete(sub)
    await db.commit()


async def list_by_task(db: AsyncSession, task_id: int) -> list[Submission]:
    result = await db.execute(
        select(Submission)
        .where(Submission.task_id == task_id)
        .order_by(Submission.submitted_at.desc())
    )
    return list(result.scalars().all())


async def list_by_student(db: AsyncSession, student_id: int) -> list[Submission]:
    result = await db.execute(
        select(Submission)
        .where(Submission.student_id == student_id)
        .order_by(Submission.submitted_at.desc())
    )
    return list(result.scalars().all())


# ---------- Comments ----------

async def get_comment(db: AsyncSession, comment_id: int) -> Comment | None:
    return await db.get(Comment, comment_id)


async def add_comment(
    db: AsyncSession, submission_id: int, author_id: int, text: str
) -> Comment:
    c = Comment(submission_id=submission_id, author_id=author_id, text=text)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def delete_comment(db: AsyncSession, comment: Comment) -> None:
    await db.delete(comment)
    await db.commit()