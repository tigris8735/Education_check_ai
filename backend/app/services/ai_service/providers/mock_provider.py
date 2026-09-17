import asyncio
import hashlib

from app.services.ai_service.providers.base import AIProvider, AiResult


class MockProvider(AIProvider):
    """
    Заглушка: не тратит токены, но даёт стабильный результат.
    score детерминирован от содержимого submission_text — одинаковый вход = одинаковый балл.
    """

    name = "mock"

    async def check(
        self,
        *,
        task_title: str,
        task_description: str,
        submission_text: str,
        student_comment: str | None = None,
    ) -> AiResult:
        await asyncio.sleep(0.5)  # имитация сетевого вызова

        if not submission_text.strip():
            return AiResult(
                score=0,
                feedback=(
                    "Решение пустое или не содержит текста. "
                    "Прикрепите файл с текстовым содержанием или добавьте комментарий."
                ),
            )

        digest = hashlib.sha256(submission_text.encode("utf-8")).hexdigest()
        score = int(digest[:4], 16) % 61 + 40  # 40..100

        feedback = (
            f"Автоматическая проверка (mock-провайдер) по заданию «{task_title}».\n"
            f"Балл: {score}/100.\n"
            f"Рекомендации: проверьте соответствие условию задания, "
            f"добавьте комментарии к коду и убедитесь, что все пункты ТЗ выполнены.\n"
            f"Длина решения: {len(submission_text)} символов."
        )
        return AiResult(score=score, feedback=feedback)