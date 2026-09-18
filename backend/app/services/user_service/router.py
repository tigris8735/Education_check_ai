from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.user_service import service as user_service
from app.services.user_service.models import User
from app.services.user_service.schemas import UserOut, UserUpdate
from app.shared.permissions import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.update_profile(db, current_user, payload)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await user_service.get_user(db, user_id)