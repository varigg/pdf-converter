"""
LLM provider API clients.

Each provider client handles only the API-specific communication logic.
They receive prompts and return raw responses.
"""

import os
from typing import Any, Protocol

import requests
from google import genai
from google.genai import types


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM provider API clients."""

    def call_api(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Make API call to the LLM provider.

        Args:
            system_prompt: System message/instruction
            user_prompt: User's prompt/question

        Returns:
            Dict with provider-specific response structure
        """
        ...

    def estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost for a request based on token usage.

        Args:
            tokens: Number of tokens used.

        Returns:
            Estimated cost in USD.
        """
        ...

    def get_default_model(self) -> str:
        """Get the name of the default model used by this provider."""
        ...


class GeminiProvider:
    """API client for Google Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize Gemini provider.

        Args:
            api_key: API key (reads from GOOGLE_API_KEY env var if None)
            model: Model name (defaults to gemini-3-flash-preview if None)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")
        
        # Create client with API key
        self.client = genai.Client(api_key=self.api_key)
        # Use current generation model (gemini-3-flash-preview has 1M token context)
        self.model_name = model or "gemini-3-flash-preview"

    def call_api(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Call Gemini API using the official SDK.

        Args:
            system_prompt: System message
            user_prompt: User prompt

        Returns:
            Dict with 'content' (response text) and 'usage' (token stats) keys
        """
        # Combine system and user prompts for Gemini
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Configure generation parameters
        generation_config = types.GenerateContentConfig(
            temperature=0.2,
            #max_output_tokens=32000,
        )

        # Generate content
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=combined_prompt,
            config=generation_config,
        )

        # Extract content
        content = response.text if hasattr(response, 'text') and response.text else ""

        # Extract usage metadata
        usage = {}
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return {
            "content": content,
            "usage": usage,
        }

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for Gemini 3 Flash."""
        # Gemini 3 Flash pricing (as of Feb 2026):
        # Note: Pricing may differ from legacy models
        # Using conservative estimate similar to previous generation
        # Input: $0.075/1M tokens, Output: $0.30/1M tokens
        # Approximation: $0.15 per 1M tokens average
        return (tokens / 1_000_000) * 0.15

    def get_default_model(self) -> str:
        """Get default model name."""
        return self.model_name


class PerplexityProvider:
    """API client for Perplexity."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize Perplexity provider.

        Args:
            api_key: API key (reads from PERPLEXITY_API_KEY env var if None)
            model: Model name (defaults to sonar if None)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Perplexity API key required. Set PERPLEXITY_API_KEY environment variable."
            )
        self.base_url = "https://api.perplexity.ai"
        self.model = model or "sonar"

    def call_api(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Call Perplexity chat completions API.

        Args:
            system_prompt: System message
            user_prompt: User prompt

        Returns:
            Dict with 'content' (response text) and 'usage' (token stats) keys
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 8192,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
        }

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for Perplexity sonar model."""
        # Using a flat estimate as in original implementation
        return 0.005 if tokens > 0 else 0.0

    def get_default_model(self) -> str:
        """Get default model name."""
        return self.model


class OpenAIProvider:
    """API client for OpenAI."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize OpenAI provider.

        Args:
            api_key: API key (reads from OPENAI_API_KEY env var if None)
            model: Model name (defaults to gpt-4o-mini if None)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        self.base_url = "https://api.openai.com/v1"
        self.model = model or "gpt-4o-mini"  # Cost-effective model for summarization

    def call_api(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Call OpenAI chat completions API.

        Args:
            system_prompt: System message
            user_prompt: User prompt

        Returns:
            Dict with 'content' (response text) and 'usage' (token stats) keys
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 16000,
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        return {
            "content": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
        }

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for OpenAI gpt-4o-mini."""
        # gpt-4o-mini: $0.15 / 1M input, $0.60 / 1M output.
        # Approximation: $0.30 per 1M tokens total.
        return (tokens / 1_000_000) * 0.30

    def get_default_model(self) -> str:
        """Get default model name."""
        return self.model


class AnthropicProvider:
    """API client for Anthropic."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize Anthropic provider.

        Args:
            api_key: API key (reads from ANTHROPIC_API_KEY env var if None)
            model: Model name (defaults to claude-3-5-haiku-20241022 if None)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )
        self.base_url = "https://api.anthropic.com/v1"
        self.model = model or "claude-3-5-haiku-20241022"  # Fast and cost-effective model
        self.api_version = "2023-06-01"  # API version for Messages API

    def call_api(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """
        Call Anthropic messages API.

        Args:
            system_prompt: System message
            user_prompt: User prompt

        Returns:
            Dict with 'content' (response text) and 'usage' (token stats) keys
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

        # Build payload according to Anthropic Messages API spec
        payload = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        response = requests.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=payload,
            timeout=30,
        )

        # Add better error handling
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            error_detail = ""
            try:
                error_detail = f" - {response.json()}"
            except (ValueError, requests.JSONDecodeError):
                error_detail = f" - {response.text}"
            raise requests.HTTPError(f"{e}{error_detail}", response=response) from e

        data = response.json()

        # Extract text content from response
        content_text = ""
        if "content" in data and len(data["content"]) > 0:
            content_text = data["content"][0].get("text", "")

        return {
            "content": content_text,
            "usage": data.get("usage", {}),
        }

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for Anthropic claude-3-5-haiku."""
        # claude-3-5-haiku: $0.25 / 1M input, $1.25 / 1M output.
        # Approximation: $0.50 per 1M tokens total.
        return (tokens / 1_000_000) * 0.50

    def get_default_model(self) -> str:
        """Get default model name."""
        return self.model
