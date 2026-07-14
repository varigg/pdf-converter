"""Retry, usage tracking, and response handling for LLM providers."""

import time
from collections.abc import Callable
from typing import Any

import requests

from pdf_converter.exceptions import InvalidRetryCountError, LLMRetryError

from .llm_providers import LLMProvider
from .usage_tracker import UsageTracker


class LLMService:
    """Orchestrate LLM calls independently of provider-specific APIs."""

    def __init__(
        self,
        provider: LLMProvider,
        provider_name: str = "unknown",
        tracker: UsageTracker | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.provider = provider
        self.provider_name = provider_name
        self.tracker = tracker if tracker is not None else UsageTracker(provider=provider_name)
        self._sleep = sleep

    def summarize_text(
        self,
        text: str,
        system_prompt: str = "",
        max_retries: int = 3,
    ) -> str:
        """Generate a summary, retrying transient HTTP failures."""
        if max_retries < 1:
            raise InvalidRetryCountError

        for attempt in range(max_retries):
            try:
                response = self.provider.call_api(system_prompt, text)
            except requests.HTTPError as error:
                status_code = error.response.status_code if error.response is not None else 0
                if status_code not in (429, 503):
                    raise
                if attempt == max_retries - 1:
                    raise LLMRetryError(max_retries, status_code) from error
                delay = 2**attempt if status_code == 429 else 2 ** (attempt + 1)
                self._sleep(delay)
                continue
            except requests.RequestException as error:
                if attempt == max_retries - 1:
                    raise LLMRetryError(max_retries) from error
                self._sleep(1)
                continue

            usage = response["usage"]
            tokens = usage.get("total_tokens", 0)
            if tokens == 0:
                tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            self.tracker.track_request(tokens, self.provider.estimate_cost(tokens))
            return response["content"]

        raise LLMRetryError(max_retries)

    def get_usage_stats(self) -> dict[str, Any]:
        """Return normalized usage statistics for the current month."""
        stats = self.tracker.get_current_month_stats()
        return {
            "requests": stats.get("requests", 0),
            "total_tokens": stats.get("tokens", 0),
            "estimated_cost_usd": stats.get("cost", 0.0),
        }
