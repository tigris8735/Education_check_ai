from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Education_check_ai"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # S3
    S3_ENDPOINT: str = ""
    S3_REGION: str = "auto"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_PRESIGN_EXPIRE: int = 3600

    # Files
    MAX_FILE_SIZE_MB: int = 20

    # AI
    AI_PROVIDER: str = "mock"          # mock | openai
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Redis
    REDIS_URL: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        if not isinstance(v, str):
            return v

        # 1. Приводим схему к postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 2. Разбираем URL и чистим query-параметры
        parsed = urlparse(v)
        query = parse_qs(parsed.query)

        # Удаляем параметры, которые не понимает asyncpg
        for key in ["sslmode", "channel_binding", "options"]:
            query.pop(key, None)

        # Если был sslmode=require, ставим ssl=require
        # (parse_qs уже удалил sslmode, поэтому проверяем исходную строку)
        if "sslmode=require" in v and "ssl" not in query:
            query["ssl"] = ["require"]

        # Собираем URL обратно
        new_query = urlencode(query, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
        


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()