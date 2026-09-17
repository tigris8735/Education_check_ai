from fastapi import APIRouter

from app.services.auth_service.router import router as auth_router
from app.services.user_service.router import router as user_router
from app.services.group_service.router import router as group_router
from app.services.task_service.router import router as task_router
from app.services.file_service.router import router as file_router
from app.services.submission_service.router import router as submission_router
from app.services.ai_service.router import router as ai_router


api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(user_router, prefix="/users", tags=["users"])
api_router.include_router(group_router, prefix="/groups", tags=["groups"])
api_router.include_router(task_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(file_router, prefix="/files", tags=["files"])
api_router.include_router(submission_router, prefix="/submissions", tags=["submissions"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])