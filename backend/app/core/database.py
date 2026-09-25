from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.shared.base_model import Base

# Импорты моделей — обязательны, чтобы Base.metadata знал о всех таблицах
from app.services.user_service import models as _user_models  # noqa: F401
from app.services.group_service import models as _group_models  # noqa: F401
from app.services.task_service import models as _task_models  # noqa: F401
from app.services.submission_service import models as _submission_models  # noqa: F401
from app.services.file_service import models as _file_models  # noqa: F401
from app.services.ai_service import models as _ai_models  # noqa: F401

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Создаёт таблицы и ДОБАВЛЯЕТ недостающие колонки в старые таблицы."""
    async with engine.begin() as conn:
        await conn.run_sync(_sync_schema)


def _sync_schema(conn) -> None:
    inspector = inspect(conn)
    Base.metadata.create_all(conn, checkfirst=True)

    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue  # таблица создана только что — колонки уже все
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing_cols:
                continue
            try:
                col_type = col.type.compile(conn.dialect)
                conn.execute(text(
                    f'ALTER TABLE {table.name} '
                    f'ADD COLUMN IF NOT EXISTS {col.name} {col_type} NULL'
                ))
            except Exception:
                pass