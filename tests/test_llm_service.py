from unittest.mock import MagicMock

import pytest
import requests

from pdf_converter.exceptions import LLMRetryError
from pdf_converter.services.llm_service import LLMService


def test_summarize_tracks_normalized_usage() -> None:
    provider = MagicMock()
    provider.call_api.return_value = {
        "content": "Summary",
        "usage": {"prompt_tokens": 7, "completion_tokens": 3},
    }
    provider.estimate_cost.return_value = 0.25
    tracker = MagicMock()
    service = LLMService(provider, "test", tracker=tracker)

    assert service.summarize_text("Text", "System") == "Summary"
    provider.call_api.assert_called_once_with("System", "Text")
    provider.estimate_cost.assert_called_once_with(10)
    tracker.track_request.assert_called_once_with(10, 0.25)


def test_summarize_retries_rate_limit_without_sleeping_after_last_attempt() -> None:
    response = MagicMock(status_code=429)
    rate_limit = requests.HTTPError("limited", response=response)
    provider = MagicMock()
    provider.call_api.side_effect = [rate_limit, rate_limit]
    sleep = MagicMock()
    service = LLMService(provider, tracker=MagicMock(), sleep=sleep)

    with pytest.raises(LLMRetryError, match="HTTP 429"):
        service.summarize_text("Text", max_retries=2)

    sleep.assert_called_once_with(1)


def test_summarize_does_not_retry_programming_errors() -> None:
    provider = MagicMock()
    provider.call_api.side_effect = KeyError("content")
    service = LLMService(provider, tracker=MagicMock(), sleep=MagicMock())

    with pytest.raises(KeyError):
        service.summarize_text("Text")

    provider.call_api.assert_called_once()
