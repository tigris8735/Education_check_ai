from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=5000)
    deadline: datetime
    group_id: int

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
    group_id: int
    teacher_id: int
    title: str
    description: str
    deadline: datetime
    created_at: datetime
    is_expired: bool = False


class TaskDetail(TaskOut):
    group_name: str = ""