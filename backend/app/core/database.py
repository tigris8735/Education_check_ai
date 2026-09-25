from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.shared.base_model import Base

from app.services.user_service import models as _user_models          # noqa: F401
from app.services.group_service import models as _group_models        # noqa: F401
from app.services.task_service import models as _task_models          # noqa: F401
from app.services.submission_service import models as _submission_models  # noqa: F401
from app.services.file_service import models as _file_models          # noqa: F401
from app.services.ai_service import models as _ai_models              # noqa: F401

engine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True
)

SessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(_sync_schema)

    # Однократно мигрируем старые tasks в новую связь task_groups
    async with engine.begin() as conn:
        await conn.run_sync(_migrate_task_groups_once)


def _sync_schema(conn) -> None:
    inspector = inspect(conn)
    Base.metadata.create_all(conn, checkfirst=True)

    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
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


def _migrate_task_groups_once(conn) -> None:
    """Для каждого задания без записей в task_groups — создаём по его group_id."""
    inspector = inspect(conn)
    if not inspector.has_table("task_groups") or not inspector.has_table("tasks"):
        return

    existing = {row[0] for row in conn.execute(text(
        "SELECT DISTINCT task_id FROM task_groups"
    )).all()}

    rows = conn.execute(text(
        "SELECT id, group_id FROM tasks WHERE group_id IS NOT NULL"
    )).all()
    for task_id, group_id in rows:
        if task_id in existing:
            continue
        conn.execute(text(
            "INSERT INTO task_groups (task_id, group_id) VALUES (:t, :g)"
        ), {"t": task_id, "g": group_id})