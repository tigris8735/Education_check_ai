from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.ai_service import service as ai_service
from app.services.ai_service.schemas import AiCheckOut, AiCheckRequest
from app.services.user_service.models import User
from app.shared.permissions import get_current_user

router = APIRouter()


@router.post(
    "/check/{submission_id}",
    response_model=AiCheckOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_check(
    submission_id: int,
    payload: AiCheckRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    sync: bool = Query(
        False,
        description="Если true — выполнить проверку синхронно (для отладки без Redis)",
    ),
):
    if sync:
        return await ai_service.run_check_sync(
            db, submission_id, current_user, force=payload.force
        )
    return await ai_service.enqueue_check(
        db, submission_id, current_user, force=payload.force
    )


@router.get("/check/{submission_id}", response_model=AiCheckOut | None)
async def get_check(
    submission_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ai_service.get_check(db, submission_id, current_user)