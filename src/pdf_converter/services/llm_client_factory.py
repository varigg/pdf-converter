"""
Factory for creating LLM services from different providers.

Supports creating services for Gemini, Perplexity, OpenAI, Anthropic.
"""

from .llm_providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAIProvider,
    PerplexityProvider,
)
from .llm_service import LLMService


class LLMClientFactory:
    """Factory for creating LLM clients from different providers."""

    # Supported providers
    PROVIDERS = ["gemini", "perplexity", "openai", "anthropic"]

    @staticmethod
    def create_client(
        provider: str = "gemini",
        api_key: str | None = None,
        model: str | None = None,
    ) -> LLMService:
        """
        Create an LLM service.

        Args:
            provider: LLM provider ('gemini', 'perplexity', 'openai', 'anthropic')
            api_key: Optional API key (uses env var if not provided)
            model: Optional model name (uses provider default if not provided)

        Returns:
            LLMService instance configured with provider

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()

        if provider not in LLMClientFactory.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider}. Choose from: {', '.join(LLMClientFactory.PROVIDERS)}"
            )

        # Create service with appropriate provider
        if provider == "gemini":
            provider_client = GeminiProvider(api_key=api_key, model=model)
            return LLMService(provider=provider_client, provider_name="gemini")

        elif provider == "perplexity":
            provider_client = PerplexityProvider(api_key=api_key, model=model)
            return LLMService(provider=provider_client, provider_name="perplexity")

        elif provider == "openai":
            provider_client = OpenAIProvider(api_key=api_key, model=model)
            return LLMService(provider=provider_client, provider_name="openai")

        elif provider == "anthropic":
            provider_client = AnthropicProvider(api_key=api_key, model=model)
            return LLMService(provider=provider_client, provider_name="anthropic")

        else:
            raise ValueError(
                f"Unknown provider: {provider}. Supported providers: {', '.join(LLMClientFactory.PROVIDERS)}"
            )

    @staticmethod
    def get_client_type_name(provider: str = "gemini") -> str:
        """
        Get a human-readable name for the client configuration.

        Args:
            provider: LLM provider name

        Returns:
            String describing the client configuration
        """
        return provider.replace("-", " ").title()
