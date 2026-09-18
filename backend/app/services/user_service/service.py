from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.services.user_service import crud
from app.services.user_service.models import User
from app.services.user_service.schemas import UserCreate, UserUpdate 
from app.shared.enums import Role

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

async def register_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await crud.get_by_email(db, data.email)
    if existing:
        raise ConflictError("Пользователь с таким e-mail уже существует")

    user = await crud.create(
        db,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        group_hint=data.group_hint,
    )

    # Если это студент и он указал имя группы — попробуем сразу присоединить
    if data.role == Role.STUDENT and data.group_hint:
        from app.services.group_service import crud as group_crud

        group = await group_crud.get_by_name(db, data.group_hint)
        if group is None:
            # создаём группу "на лету" — студент сразу в ней, teacher_id = None
            group = await group_crud.create(
                db,
                name=data.group_hint,
                teacher_id=None,
                created_by_id=user.id,
            )
        # добавляем студента в members (если ещё не там)
        if await group_crud.get_member(db, group.id, user.id) is None:
            await group_crud.add_member(db, group.id, user.id)

    return user