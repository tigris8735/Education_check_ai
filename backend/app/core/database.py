from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.shared.base_model import Base

from app.services.user_service import models as _user_models              # noqa: F401
from app.services.group_service import models as _group_models           # noqa: F401
from app.services.task_service import models as _task_models             # noqa: F401
from app.services.submission_service import models as _submission_models # noqa: F401
from app.services.file_service import models as _file_models             # noqa: F401
from app.services.ai_service import models as _ai_models                 # noqa: F401

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
    async with engine.begin() as conn:
        await conn.run_sync(_migrate_legacy_data)


def _sync_schema(conn) -> None:
    """create_all + аккуратное добавление недостающих колонок.

    NOT NULL колонки добавляются С DEFAULT, чтобы старые строки
    не остались с NULL (иначе чтение падает с 500).
    """
    inspector = inspect(conn)
    Base.metadata.create_all(conn, checkfirst=True)

    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing_cols:
                continue
            ddl = (
                f'ALTER TABLE {table.name} '
                f'ADD COLUMN IF NOT EXISTS {col.name} {col.type.compile(conn.dialect)}'
            )
            if col.server_default is not None:
                arg = col.server_default.arg
                ddl += f' DEFAULT {arg.text if hasattr(arg, "text") else arg}'
            ddl += ' NULL' if col.nullable else ' NOT NULL'
            try:
                conn.execute(text(ddl))
            except Exception:
                pass


def _migrate_legacy_data(conn) -> None:
    """1) Чиним NULL в max_attempts у старых заданий.
    2) Переносим старые task.group_id в связь task_groups.
    """
    inspector = inspect(conn)

    # --- 1) max_attempts: NULL -> 0 ---
    if inspector.has_table("tasks"):
        cols = {c["name"] for c in inspector.get_columns("tasks")}
        if "max_attempts" in cols:
            conn.execute(text(
                "UPDATE tasks SET max_attempts = 0 WHERE max_attempts IS NULL"
            ))

    # --- 2) task_groups из старых group_id ---
    if not inspector.has_table("task_groups") or not inspector.has_table("tasks"):
        return

    existing = {
        row[0] for row in conn.execute(
            text("SELECT DISTINCT task_id FROM task_groups")
        ).all()
    }
    rows = conn.execute(
        text("SELECT id, group_id FROM tasks WHERE group_id IS NOT NULL")
    ).all()
    for task_id, group_id in rows:
        if task_id in existing:
            continue
        conn.execute(
            text("INSERT INTO task_groups (task_id, group_id) VALUES (:t, :g)"),
            {"t": task_id, "g": group_id},
        )