from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.enums import FileStatus

ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "text/plain",
    "image/",
    "application/msword",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.oasis.opendocument",
)


class PresignUploadIn(BaseModel):
    original_name: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=128)
    size: int = Field(..., gt=0)

    @field_validator("original_name")
    @classmethod
    def _safe_name(cls, v: str) -> str:
        # запрещаем path traversal и управляющие символы
        cleaned = v.strip().replace("\\", "/").split("/")[-1]
        if not cleaned:
            raise ValueError("Некорректное имя файла")
        return cleaned


class PresignUploadOut(BaseModel):
    file_id: int
    upload_url: str
    s3_key: str
    expires_in: int


class FileConfirmIn(BaseModel):
    submission_id: int | None = None


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    content_type: str
    size: int
    status: FileStatus
    uploaded_by_id: int
    submission_id: int | None
    created_at: datetime


class DownloadUrlOut(BaseModel):
    url: str
    expires_in: int