from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.enums import AiCheckStatus


class AiCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    status: AiCheckStatus
    provider: str
    score: int | None
    feedback: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class AiCheckRequest(BaseModel):
    force: bool = Field(
        False,
        description="Перезапустить проверку, если она уже выполнена",
    )