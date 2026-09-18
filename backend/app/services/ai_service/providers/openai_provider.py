import json

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.ai_service.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.ai_service.providers.base import AIProvider, AiResult


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY не задан")
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    async def check(
        self,
        *,
        task_title: str,
        task_description: str,
        submission_text: str,
        student_comment: str | None = None,
    ) -> AiResult:
        user_prompt = build_user_prompt(
            task_title=task_title,
            task_description=task_description,
            submission_text=submission_text,
            student_comment=student_comment,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        verdict = str(data.get("verdict","incorrect")).strip().lower()
        score = 100 if verdict == "correct" else 0
        feedback = str(data.get("feedback", "")).strip() or "—"
        return AiResult(score=score, feedback=feedback)