from arq.connections import RedisSettings

from app.core.config import settings
from app.core.loggin import setup_logging
from app.workers.ai_tasks import run_ai_check


def _redis_settings() -> RedisSettings:
    if not settings.REDIS_URL:
        raise RuntimeError("REDIS_URL не задан — ARQ не сможет стартовать")
    return RedisSettings.from_dsn(settings.REDIS_URL)


async def startup(ctx: dict) -> None:
    setup_logging(settings.DEBUG)
    ctx["settings"] = settings


async def shutdown(ctx: dict) -> None:
    pass


class WorkerSettings:
    """Запуск: `arq app.workers.queue.WorkerSettings`"""

    functions = [run_ai_check]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = _redis_settings()
    max_jobs = 4              # параллельно не больше 4 AI-проверок
    job_timeout = 300         # 5 минут на задачу
    keep_result = 60 * 60     # результаты живут час
    max_tries = 2             # одна повторная попытка при сбое