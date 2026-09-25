from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHECKING = "checking"
    CHECKED = "checked"
    REVIEWED = "reviewed"
    FAILED = "failed"


class AiCheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class FileStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"