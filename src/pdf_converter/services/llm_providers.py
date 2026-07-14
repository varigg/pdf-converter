"""Provider-specific clients implementing the common LLM response contract."""

import os
from collections.abc import Mapping
from typing import Any, Protocol, TypedDict, cast

import requests
from google import genai
from google.genai import types

from pdf_converter.exceptions import MissingAPIKeyError, ProviderResponseError


class LLMUsage(TypedDict, total=False):
    """Normalized token counts returned by a provider."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(TypedDict):
    """Normalized response consumed by :class:`LLMService`."""

    content: str
    usage: LLMUsage


class LLMProvider(Protocol):
    """Interface implemented by all provider clients."""

    def call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return generated content and normalized token usage."""
        ...

    def estimate_cost(self, tokens: int) -> float:
        """Estimate request cost from total token usage."""
        ...

    def get_default_model(self) -> str:
        """Return the configured model name."""
        ...


def _get_api_key(api_key: str | None, environment_variable: str, provider: str) -> str:
    configured_key = api_key or os.getenv(environment_variable)
    if not configured_key:
        raise MissingAPIKeyError(provider, environment_variable)
    return configured_key


def _normalize_usage(raw_usage: object) -> LLMUsage:
    if not isinstance(raw_usage, Mapping):
        return {}

    usage = cast(Mapping[str, object], raw_usage)
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens", 0))
    completion_tokens = usage.get("completion_tokens", usage.get("output_tokens", 0))
    total_tokens = usage.get("total_tokens", 0)
    prompt = int(prompt_tokens) if isinstance(prompt_tokens, int | float) else 0
    completion = int(completion_tokens) if isinstance(completion_tokens, int | float) else 0
    total = int(total_tokens) if isinstance(total_tokens, int | float) else prompt + completion
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total or prompt + completion,
    }


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], provider: str) -> dict[str, Any]:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        raise ProviderResponseError(provider)
    return cast(dict[str, Any], data)


def _call_chat_completions(
    *,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
) -> LLMResponse:
    data = _post_json(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        },
        provider=provider,
    )
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderResponseError(provider) from error
    if not isinstance(content, str):
        raise ProviderResponseError(provider)
    return {"content": content, "usage": _normalize_usage(data.get("usage"))}


class GeminiProvider:
    """API client for Google Gemini."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = _get_api_key(api_key, "GOOGLE_API_KEY", "Google")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model or "gemini-3-flash-preview"

    def call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=types.GenerateContentConfig(temperature=0.2),
        )
        raw_content = getattr(response, "text", None)
        content = raw_content if isinstance(raw_content, str) else ""
        usage_metadata = getattr(response, "usage_metadata", None)
        usage: LLMUsage = {}
        if usage_metadata:
            usage = _normalize_usage({
                "prompt_tokens": usage_metadata.prompt_token_count,
                "completion_tokens": usage_metadata.candidates_token_count,
                "total_tokens": usage_metadata.total_token_count,
            })
        return {"content": content, "usage": usage}

    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost using an average input/output token rate."""
        return (tokens / 1_000_000) * 0.15

    def get_default_model(self) -> str:
        return self.model_name


class PerplexityProvider:
    """API client for Perplexity's OpenAI-compatible endpoint."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = _get_api_key(api_key, "PERPLEXITY_API_KEY", "Perplexity")
        self.base_url = "https://api.perplexity.ai"
        self.model = model or "sonar"

    def call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return _call_chat_completions(
            provider="Perplexity",
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

    def estimate_cost(self, tokens: int) -> float:
        return 0.005 if tokens > 0 else 0.0

    def get_default_model(self) -> str:
        return self.model


class OpenAIProvider:
    """API client for OpenAI."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = _get_api_key(api_key, "OPENAI_API_KEY", "OpenAI")
        self.base_url = "https://api.openai.com/v1"
        self.model = model or "gpt-4o-mini"

    def call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return _call_chat_completions(
            provider="OpenAI",
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=16000,
        )

    def estimate_cost(self, tokens: int) -> float:
        return (tokens / 1_000_000) * 0.30

    def get_default_model(self) -> str:
        return self.model


class AnthropicProvider:
    """API client for Anthropic."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = _get_api_key(api_key, "ANTHROPIC_API_KEY", "Anthropic")
        self.base_url = "https://api.anthropic.com/v1"
        self.model = model or "claude-3-5-haiku-20241022"
        self.api_version = "2023-06-01"

    def call_api(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = _post_json(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": self.api_version,
                "content-type": "application/json",
            },
            payload=payload,
            provider="Anthropic",
        )
        try:
            content = data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as error:
            raise ProviderResponseError("Anthropic") from error
        if not isinstance(content, str):
            raise ProviderResponseError("Anthropic")
        return {"content": content, "usage": _normalize_usage(data.get("usage"))}

    def estimate_cost(self, tokens: int) -> float:
        return (tokens / 1_000_000) * 0.50

    def get_default_model(self) -> str:
        return self.model
