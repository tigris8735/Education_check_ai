from enum import Enum


class Role(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"                # создано, но не отправлено
    SUBMITTED = "submitted"        # сдано студентом
    CHECKING = "checking"          # AI проверяет
    CHECKED = "checked"            # AI + препод завершили
    FAILED = "failed"              # ошибка при проверке


class AiCheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"