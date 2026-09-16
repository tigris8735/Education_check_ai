from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.services.user_service import crud as user_crud
from app.services.user_service.models import User
from app.services.user_service.schemas import UserCreate
from app.services.user_service.service import register_user


async def register(db: AsyncSession, data: UserCreate) -> User:
    return await register_user(db, data)


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await user_crud.get_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Неверный e-mail или пароль")
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    return create_access_token(user.id), create_refresh_token(user.id)


async def user_from_refresh_token(db: AsyncSession, token: str) -> User:
    try:
        payload = decode_token(token, expected_type="refresh")
    except JWTError:
        raise UnauthorizedError("Невалидный refresh-токен")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Невалидный refresh-токен")

    user = await user_crud.get_by_id(db, int(user_id))
    if not user:
        raise UnauthorizedError("Пользователь не найден")
    return user