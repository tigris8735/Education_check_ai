from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.services.file_service.schemas import FileOut
from app.shared.enums import AiCheckStatus, SubmissionStatus


class SubmissionCreate(BaseModel):
    task_id: int
    student_comment: str = Field("", max_length=5000)


class SubmissionUpdate(BaseModel):
    student_comment: str | None = Field(None, max_length=5000)


class SubmissionStatusUpdate(BaseModel):
    status: SubmissionStatus


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    author_id: int
    text: str
    created_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    student_id: int
    status: SubmissionStatus
    student_comment: str
    submitted_at: datetime
    created_at: datetime
    ai_status: AiCheckStatus | None = None
    ai_score: int | None = None
    ai_feedback: str | None = None
    ai_error: str | None = None
    final_score: int | None = None
    teacher_feedback: str | None = None
    student_first_name: str = ""
    student_last_name: str = ""
    student_group_name: str = ""
    task_title: str = ""


class SubmissionDetail(SubmissionOut):
    files: list[FileOut] = []
    comments: list[CommentOut] = []
    attempt_number: int = 1
    total_attempts: int = 1
    max_attempts: int = 0


class FinalScoreIn(BaseModel):
    final_score: int = Field(..., ge=0, le=100)
    teacher_feedback: str | None = None