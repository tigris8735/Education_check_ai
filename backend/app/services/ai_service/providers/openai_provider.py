import json
import logging

from openai import AsyncOpenAI, BadRequestError

from app.core.config import settings
from app.services.ai_service.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.ai_service.providers.base import AIProvider, AiResult

logger = logging.getLogger(__name__)

# Семейства моделей, которым НЕЛЬЗЯ слать max_tokens/temperature
_REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4", "o5")


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY не задан")

        kwargs = {"api_key": settings.OPENAI_API_KEY, "timeout": 90.0}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
            logger.info("OpenAI-совместимый эндпоинт: %s", settings.OPENAI_BASE_URL)

        self._client = AsyncOpenAI(**kwargs)
        self._model = settings.OPENAI_MODEL

    def _is_reasoning_model(self) -> bool:
        return self._model.lower().startswith(_REASONING_PREFIXES)

    async def _create(self, messages: list[dict]) -> str:
        """Делаем запрос с умными фолбэками по параметрам.

        1) параметры под семейство модели (gpt-5/o-series vs классика);
        2) урезанный набор без лимитов/температуры;
        3) совсем «голый» запрос без response_format.
        """
        attempts: list[dict] = []
        if self._is_reasoning_model():
            attempts.append({"max_completion_tokens": 1500})
        else:
            attempts.append({"max_tokens": 1500, "temperature": 0.2})
        attempts.append({})                 # минимум без лимитов
        attempts.append({"plain": True})    # без response_format

        last_error: Exception | None = None
        for i, extra in enumerate(attempts, start=1):
            plain = extra.pop("plain", False)
            params = {"model": self._model, "messages": messages}
            if not plain:
                params["response_format"] = {"type": "json_object"}
            params.update(extra)

            try:
                response = await self._client.chat.completions.create(**params)
                if i > 1:
                    logger.info("OpenAI: сработал фолбэк-вариант запроса №%s", i)
                return response.choices[0].message.content or "{}"
            except BadRequestError as e:
                last_error = e
                logger.warning("OpenAI отклонил параметры (попытка %s): %s", i, e)
                continue

        raise last_error or RuntimeError("OpenAI request failed")

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
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        content = await self._create(messages)

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("AI вернул не-JSON: %s", content[:500])
            return AiResult(
                score=50,
                feedback="AI вернул некорректный формат ответа, требуется ручная проверка.",
            )

        try:
            score = int(data.get("score", 50))
        except (TypeError, ValueError):
            score = 50
        score = max(0, min(100, score))
        feedback = str(data.get("feedback", "")).strip() or "—"
        return AiResult(score=score, feedback=feedback)