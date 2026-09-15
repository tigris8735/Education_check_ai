from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.shared.enums import Role

# auto_error=False — чтобы вернуть свой 401, а не дефолтный
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    ВНИМАНИЕ: здесь мы ещё не импортировали модель User — раскомментируем,
    когда появится user_service. Пока просто возвращаем payload.
    """
    if credentials is None:
        raise UnauthorizedError("Missing Authorization header")

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    # --- раскомментировать после user_service ---
    # result = await db.execute(select(User).where(User.id == int(user_id)))
    # user = result.scalar_one_or_none()
    # if user is None:
    #     raise UnauthorizedError("User not found")
    # return user

    return {"id": int(user_id)}  # временная заглушка


def require_role(role: Role):
    async def _checker(user=Depends(get_current_user)):
        # когда user станет ORM-объектом — проверка будет user.role == role
        user_role = user.get("role") if isinstance(user, dict) else getattr(user, "role", None)
        if user_role != role:
            raise ForbiddenError(f"Требуется роль: {role.value}")
        return user
    return _checker


require_teacher = require_role(Role.TEACHER)
require_student = require_role(Role.STUDENT)