from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AiResult:
    score: int
    feedback: str


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def check(
        self,
        *,
        task_title: str,
        task_description: str,
        submission_text: str,
        student_comment: str | None = None,
    ) -> AiResult:
        """Вернуть оценку и фидбек по решению студента."""