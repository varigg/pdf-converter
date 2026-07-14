"""Factory for creating configured LLM services."""

from collections.abc import Callable
from typing import ClassVar

from pdf_converter.exceptions import UnknownProviderError

from .llm_providers import (
    AnthropicProvider,
    GeminiProvider,
    LLMProvider,
    OpenAIProvider,
    PerplexityProvider,
)
from .llm_service import LLMService

ProviderFactory = Callable[[str | None, str | None], LLMProvider]

PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "gemini": GeminiProvider,
    "perplexity": PerplexityProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}
SUPPORTED_PROVIDERS: tuple[str, ...] = tuple(PROVIDER_FACTORIES)


class LLMClientFactory:
    """Create LLM services from the authoritative provider registry."""

    PROVIDERS: ClassVar[tuple[str, ...]] = SUPPORTED_PROVIDERS

    @staticmethod
    def create_client(
        provider: str = "gemini",
        api_key: str | None = None,
        model: str | None = None,
    ) -> LLMService:
        provider_name = provider.lower()
        provider_factory = PROVIDER_FACTORIES.get(provider_name)
        if provider_factory is None:
            raise UnknownProviderError(provider_name, ", ".join(SUPPORTED_PROVIDERS))
        return LLMService(
            provider=provider_factory(api_key, model),
            provider_name=provider_name,
        )

    @staticmethod
    def get_client_type_name(provider: str = "gemini") -> str:
        """Return a provider name suitable for display."""
        return provider.replace("-", " ").title()
