from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.services.user_service.models import User
from app.shared.enums import Role

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing Authorization header")

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await db.get(User, int(user_id))
    if user is None:
        raise UnauthorizedError("User not found")
    return user


def require_role(role: Role):
    async def _checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role != role:
            raise ForbiddenError(f"Требуется роль: {role.value}")
        return user
    return _checker


require_teacher = require_role(Role.TEACHER)
require_student = require_role(Role.STUDENT)