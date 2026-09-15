from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.shared.base_model import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость: одна сессия на запрос."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Создаёт таблицы при старте приложения.
    ВАЖНО: здесь нужно импортировать все модели, чтобы они попали в Base.metadata.
    По мере добавления сервисов — расширяем список импортов.
    """
    # --- импорты моделей (по мере разработки) ---
    # from app.services.user_service import models as _user_models
    # from app.services.group_service import models as _group_models
    # from app.services.task_service import models as _task_models
    # from app.services.submission_service import models as _submission_models
    # from app.services.file_service import models as _file_models
    # from app.services.ai_service import models as _ai_models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)