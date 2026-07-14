"""
LLM Service - orchestrates prompt building, LLM API calls with retry logic.

Simplified service for PDF summarization: handles retry, error handling, and usage tracking.
"""

import time
from typing import Any

import requests

from .llm_providers import LLMProvider
from .usage_tracker import UsageTracker


class LLMService:
    """Service that orchestrates LLM API calls with retry and tracking."""

    def __init__(
        self,
        provider: LLMProvider,
        provider_name: str = "unknown",
    ):
        """
        Initialize LLM service.

        Args:
            provider: LLM provider client (e.g., GeminiProvider, PerplexityProvider)
            provider_name: Name of the provider for usage tracking (e.g., "gemini", "perplexity")
        """
        self.provider = provider
        self.provider_name = provider_name
        self.tracker = UsageTracker(provider=provider_name)

    def summarize_text(
        self,
        text: str,
        system_prompt: str = "",
        max_retries: int = 3,
    ) -> str:
        """
        Generate summary for given text.

        Args:
            text: Text to summarize
            system_prompt: System instructions for the LLM
            max_retries: Maximum retry attempts

        Returns:
            Summary text from LLM
        """
        # Build user prompt with the text to summarize
        user_prompt = text

        # Call LLM with retry logic
        for attempt in range(max_retries):
            try:
                response = self.provider.call_api(system_prompt, user_prompt)

                # Track usage
                usage = response.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                # Fallback for providers with different usage keys
                if tokens == 0:
                    tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                
                estimated_cost = self._estimate_cost(tokens)
                self.tracker.track_request(tokens, estimated_cost)

                # Return summary content
                return response["content"]

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                
                if status_code == 429:  # Rate limit
                    wait_time = 2**attempt
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif status_code == 503:  # Service unavailable
                    wait_time = 2**(attempt + 1)  # Longer wait for 503
                    print(f"  Service unavailable (503), waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  Failed after {max_retries} attempts due to service unavailability")
                        raise RuntimeError(f"LLM service unavailable after {max_retries} attempts. The model may be experiencing high demand.")
                
                # Re-raise other HTTP errors
                print(f"HTTP error occurred: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
            except Exception as e:
                print(f"Error during summarization (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        # If all retries exhausted
        raise RuntimeError(f"Failed to generate summary after {max_retries} attempts")

    def get_usage_stats(self) -> dict[str, Any]:
        """Get usage statistics for current month."""
        stats = self.tracker.get_current_month_stats()
        return {
            "requests": stats.get("requests", 0),
            "total_tokens": stats.get("tokens", 0),
            "estimated_cost_usd": stats.get("cost", 0.0),
        }

    def _estimate_cost(self, tokens: int) -> float:
        """
        Estimate cost based on token usage and provider pricing.

        Args:
            tokens: Number of tokens used

        Returns:
            Estimated cost in USD
        """
        return self.provider.estimate_cost(tokens)
