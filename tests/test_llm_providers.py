from unittest.mock import MagicMock, patch

import pytest

from pdf_converter.exceptions import MissingAPIKeyError, ProviderResponseError
from pdf_converter.services.llm_providers import AnthropicProvider, OpenAIProvider


def test_provider_requires_api_key() -> None:
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(MissingAPIKeyError, match="OPENAI_API_KEY"),
    ):
        OpenAIProvider()


@patch("pdf_converter.services.llm_providers.requests.post")
def test_openai_provider_normalizes_response(mock_post: MagicMock) -> None:
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Summary"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
    }

    response = OpenAIProvider(api_key="secret").call_api("System", "Text")

    assert response == {
        "content": "Summary",
        "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
    }
    mock_post.return_value.raise_for_status.assert_called_once_with()


@patch("pdf_converter.services.llm_providers.requests.post")
def test_anthropic_provider_normalizes_token_names(mock_post: MagicMock) -> None:
    mock_post.return_value.json.return_value = {
        "content": [{"text": "Summary"}],
        "usage": {"input_tokens": 5, "output_tokens": 3},
    }

    response = AnthropicProvider(api_key="secret").call_api("System", "Text")

    assert response["usage"]["total_tokens"] == 8


@patch("pdf_converter.services.llm_providers.requests.post")
def test_provider_rejects_malformed_response(mock_post: MagicMock) -> None:
    mock_post.return_value.json.return_value = {"choices": []}

    with pytest.raises(ProviderResponseError, match="invalid response"):
        OpenAIProvider(api_key="secret").call_api("System", "Text")
