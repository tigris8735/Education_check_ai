from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers
from app.core.loggin import get_logger, setup_logging
from app.core.middleware import add_middlewares

setup_logging(settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up…")
    await init_db()
    logger.info("DB initialized")
    yield
    logger.info("Shutting down…")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

add_middlewares(app)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}