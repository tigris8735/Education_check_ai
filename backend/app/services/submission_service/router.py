from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ai_service import service as ai_service
from app.services.ai_service.schemas import AiCheckOut, AiCheckRequest
from app.services.submission_service import service as sub_service
from app.services.submission_service.schemas import (
    CommentCreate,
    CommentOut,
    FinalScoreIn,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionOut,
    SubmissionStatusUpdate,
    SubmissionUpdate,
)
from app.services.user_service.models import User
from app.shared.enums import SubmissionStatus
from app.shared.permissions import get_current_user, require_teacher

router = APIRouter()


@router.get("", response_model=list[SubmissionOut])
async def list_submissions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    task_id: int | None = Query(None),
):
    items = await sub_service.list_submissions(db, current_user, task_id)
    return [await sub_service.build_detail(db, s) for s in items]


@router.post("", response_model=SubmissionDetail, status_code=status.HTTP_201_CREATED)
async def create_submission(
    payload: SubmissionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await sub_service.create_submission(db, payload, current_user)
    return await sub_service.build_detail(db, sub)


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await sub_service.get_submission(db, submission_id, current_user)
    return await sub_service.build_detail(db, sub)


@router.patch("/{submission_id}", response_model=SubmissionDetail)
async def update_submission(
    submission_id: int,
    payload: SubmissionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await sub_service.update_own_submission(db, submission_id, payload, current_user)
    return await sub_service.build_detail(db, sub)


@router.patch("/{submission_id}/status", response_model=SubmissionDetail)
async def change_status(
    submission_id: int,
    payload: SubmissionStatusUpdate,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await sub_service.change_status(db, submission_id, payload, current_user)
    return await sub_service.build_detail(db, sub)


@router.delete("/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await sub_service.delete_submission(db, submission_id, current_user)


@router.post(
    "/{submission_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    submission_id: int,
    payload: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await sub_service.add_comment(db, submission_id, payload, current_user)


@router.post("/{submission_id}/check", response_model=AiCheckOut)
async def trigger_ai_check(
    submission_id: int,
    payload: AiCheckRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ai_service.run_check(
        db, submission_id, current_user, force=payload.force
    )


@router.post("/{submission_id}/final-score", response_model=SubmissionDetail)
async def save_final_score(
    submission_id: int,
    payload: FinalScoreIn,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    sub = await sub_service.get_submission(db, submission_id, current_user)
    sub.final_score = payload.final_score
    sub.teacher_feedback = payload.teacher_feedback
    sub.status = SubmissionStatus.REVIEWED
    await db.commit()
    await db.refresh(sub)
    return await sub_service.build_detail(db, sub)