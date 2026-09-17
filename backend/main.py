from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers
from app.core.loggin import get_logger, setup_logging
from app.core.middleware import add_middlewares

setup_logging(settings.DEBUG)
logger = get_logger(__name__)

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s (debug=%s)", settings.APP_NAME, APP_VERSION, settings.DEBUG)
    await init_db()
    logger.info("DB initialized")
    yield
    logger.info("Shutting down…")


app = FastAPI(
    title=settings.APP_NAME,
    version=APP_VERSION,
    description="API для системы проверки учебных работ с AI-ассистентом.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

add_middlewares(app)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
async def health():
    """Health-check с проверкой БД. Render дёргает его для мониторинга."""
    from sqlalchemy import text

    from app.core.database import SessionLocal

    db_ok = False
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:  # noqa: BLE001
        logger.warning("Health check DB failed: %s", e)

    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": APP_VERSION,
        "db": "ok" if db_ok else "error",
    }