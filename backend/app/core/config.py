from functools import lru_cache
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # S3 / R2
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
    # Эндпоинт OpenAI-совместимого сервиса.
    # Понимаем несколько имён env-переменных сразу — как бы ты её ни назвал.
    OPENAI_BASE_URL: str = Field(
        "",
        validation_alias=AliasChoices(
            "OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_ENDPOINT"
        ),
    )

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @field_validator("OPENAI_BASE_URL", mode="before")
    @classmethod
    def _strip_base_url(cls, v):
        if isinstance(v, str):
            return v.strip().rstrip("/")
        return ""

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        if not isinstance(v, str):
            return v

        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        parsed = urlparse(v)
        query = parse_qs(parsed.query)

        for key in ["sslmode", "channel_binding", "options"]:
            query.pop(key, None)

        if "sslmode=require" in v and "ssl" not in query:
            query["ssl"] = ["require"]

        new_query = urlencode(query, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()