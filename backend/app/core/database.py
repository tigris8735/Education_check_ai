from sqlalchemy import inspect, text

async def init_db() -> None:
    from app.services.user_service import models as _user_models
    from app.services.group_service import models as _group_models
    from app.services.task_service import models as _task_models
    from app.services.submission_service import models as _submission_models
    from app.services.file_service import models as _file_models
    from app.services.ai_service import models as _ai_models

    async with engine.begin() as conn:
        await conn.run_sync(_sync_schema)


def _sync_schema(conn) -> None:
    """create_all + до-добавление недостающих колонок в старые таблицы."""
    inspector = inspect(conn)
    Base.metadata.create_all(conn, checkfirst=True)

    for table in Base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue  # таблица создана только что — колонки уже все
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            col_type = col.type.compile(conn.dialect)
            conn.execute(text(
                f'ALTER TABLE {table.name} '
                f'ADD COLUMN IF NOT EXISTS {col.name} {col_type} NULL'
            ))