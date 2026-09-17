from app.core.config import settings
from app.services.ai_service.providers.base import AIProvider
from app.services.ai_service.providers.mock_provider import MockProvider
from app.services.ai_service.providers.openai_provider import OpenAIProvider


def get_provider(name: str | None = None) -> AIProvider:
    name = (name or settings.AI_PROVIDER or "mock").lower()
    if name == "openai":
        return OpenAIProvider()
    return MockProvider()