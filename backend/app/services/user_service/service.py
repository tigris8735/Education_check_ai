from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from user_service import crud
from user_service.models import User
from user_service.schemas import UserCreate, UserUpdate


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await crud.get_by_email(db, data.email)
    if existing:
        raise ConflictError("Пользователь с таким e-mail уже существует")

    return await crud.create(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        group_hint=data.group_hint,
    )


async def get_user(db: AsyncSession, user_id: int) -> User:
    user = await crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundError("Пользователь не найден")
    return user


async def update_profile(db: AsyncSession, user: User, data: UserUpdate) -> User:
    return await crud.update(db, user, **data.model_dump(exclude_unset=True))