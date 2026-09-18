from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import service as auth_service
from app.services.auth_service.schemas import (
    AuthResponse,
    LoginIn,
    RefreshIn,
    TokenPair,
)
from app.services.user_service.schemas import UserCreate, UserOut
from app.services.user_service import crud
router = APIRouter()


def _to_auth_response(user) -> AuthResponse:
    access, refresh = auth_service.issue_tokens(user)
    return AuthResponse(
        user=UserOut.model_validate(user),
        tokens=TokenPair(access_token=access, refresh_token=refresh),
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await auth_service.register(db, payload)
    return _to_auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginIn,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await auth_service.authenticate(db, payload.email, payload.password)
    return _to_auth_response(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    payload: RefreshIn,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await auth_service.user_from_refresh_token(db, payload.refresh_token)
    access, refresh_token = auth_service.issue_tokens(user)
    return TokenPair(access_token=access, refresh_token=refresh_token)