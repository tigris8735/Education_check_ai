from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.user_service.schemas import UserOut
from app.shared.validators import validate_group_name


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=20)

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        return validate_group_name(v)


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    joined_at: datetime


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    teacher_id: int | None
    created_by_id: int
    created_at: datetime
    members_count: int = 0


class GroupDetail(GroupOut):
    members: list[UserOut] = []


class AddMemberIn(BaseModel):
    user_id: int