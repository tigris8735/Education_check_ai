from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.file_service.schemas import FileOut


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=5000)
    deadline: datetime
    group_ids: list[int] = Field(..., min_length=1)
    max_attempts: int = Field(0, ge=0, description="0 = без ограничений")

    @field_validator("deadline")
    @classmethod
    def _ensure_future(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            raise ValueError("deadline должен содержать timezone (ISO 8601 с offset)")
        if v <= now:
            raise ValueError("deadline должен быть в будущем")
        return v


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    deadline: datetime | None = None
    max_attempts: int | None = Field(None, ge=0)

    @field_validator("deadline")
    @classmethod
    def _ensure_future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            raise ValueError("deadline должен содержать timezone")
        if v <= now:
            raise ValueError("deadline должен быть в будущем")
        return v


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    title: str
    description: str
    deadline: datetime
    created_at: datetime
    is_expired: bool = False
    max_attempts: int = 0
    group_names: list[str] = []
    members_count: int = 0
    submissions_count: int = 0
    attachments: list[FileOut] = []     # ← НОВОЕ: файлы задания


class TaskDetail(TaskOut):
    pass