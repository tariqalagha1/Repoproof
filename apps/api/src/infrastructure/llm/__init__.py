"""LLM provider factory."""

from ..config import get_settings
from .fake_provider import FAKE_SENTINEL, FakeLLMProvider
from .hermes_adapter import HermesLLMAdapter
from .interface import LLMProvider


def create_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return FakeLLMProvider()
    if settings.llm_provider == "hermes":
        return HermesLLMAdapter(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    # Default: fall back to fake provider for safety
    return FakeLLMProvider()
